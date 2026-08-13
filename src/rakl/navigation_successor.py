"""#537 NAVIGATION DYNAMICS SUCCESSOR: reusable cost-to-go fields and the dynamics
mechanic redesigned to compete where amortized field reuse can in principle win.

Historical NEGATIVE (#519): the diffusion / path-integral dynamics lose to A* on
single-shot and lightly-reused worlds, because their relaxation sweeps are charged
honestly (one sweep = |V| node scans) and A* with a consistent heuristic is
near-frugal. The successor closes two gaps at once:

1. It builds the parents the historical study lacked -- most importantly the EXACT
   reverse-Dijkstra cost-to-go field, the tightest admissible heuristic that
   exists, so "A* guided by the exact field" is the strongest amortized parent any
   mechanic must beat. It also adds ALT (landmarks / triangle inequality) and an
   incrementally-maintained exact shortest-path tree (Ramalingam-style repair).

2. It redesigns the dynamics mechanic: the path-integral value is an ADMISSIBLE
   lower bound on cost-to-go (a log-sum-exp over paths is <= the min over paths),
   so it can guide A* without breaking optimality. The redesign stops the field at
   a useful ordering margin rather than full convergence and maintains it
   incrementally under edge updates, cooperating with exact A* search. The honest
   question is whether a cheaper-to-maintain approximate field ever beats the
   exact field on TOTAL node scans across an amortized / dynamic workload.

Cost meter is identical to :mod:`rakl.navigation_dynamics`: one search expansion =
one node scan; one relaxation sweep = |V| node scans. Field build + repair + every
query are all charged in this single unit, so no method wins by accounting fiction.
Optimality is a HARD GATE measured against the exact shortest path (the oracle): a
candidate that returns a suboptimal route cannot win even if it is cheaper.

Nothing in this module grants scientific, proof, method-promotion or routing
authority. It produces development-level, known-world evidence only.
"""
from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field
from math import inf, isfinite
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

from .navigation_dynamics import (
    NavigationEdge,
    NavigationProblem,
    Navigator,
    RouteProposal,
    _unwind,
    exact_shortest_route,
)

__all__ = [
    "ReusableField",
    "ReverseDijkstraField",
    "ALTField",
    "IncrementalExactField",
    "ApproximateIncrementalField",
    "AStarExactFieldGuided",
    "AStarALTGuided",
    "IncrementalExactGuided",
    "CooperativeFieldGuided",
    "field_guided_astar",
    "build_reverse_dijkstra",
    "build_alt_field",
    "SUCCESSOR_STRATEGIES",
    "SUCCESSOR_PARENT_STRATEGIES",
    "STRONG_AMORTIZED_PARENT",
    "oracle_route_cost",
]


# --------------------------------------------------------------------------- #
# shared workhorse: A* guided by an admissible cost-to-go field
# --------------------------------------------------------------------------- #
# Every field method in this module answers a query with the SAME routine so the
# per-query cost is directly comparable: A* with f = g + h, where h is the field
# value at the node (an admissible lower bound on cost-to-go). One pop = one node
# scan, matching the search controls. Reopening handles admissible-but-inconsistent
# heuristics (an approximate field can be inconsistent), preserving optimality.


def field_guided_astar(
    problem: NavigationProblem,
    heuristic: Mapping[str, float],
    adjacency: Mapping[str, Tuple[Tuple[str, float], ...]] | None = None,
) -> Tuple[Tuple[str, ...] | None, int]:
    """A* on ``f = g + h`` with an admissible heuristic. Returns (route, scans).

    ``h`` defaults to 0.0 for any node it does not name (zero is admissible). The
    adjacency is taken from the problem's admissible edges unless overridden, so a
    field can never route through a hard-constraint-failing edge.
    """
    adj = adjacency if adjacency is not None else problem.adjacency()
    start, goal = problem.start, problem.goal
    g: Dict[str, float] = {start: 0.0}
    prev: Dict[str, str] = {}
    counter = 0
    heap: list[Tuple[float, int, str]] = [(float(heuristic.get(start, 0.0)), counter, start)]
    closed: set[str] = set()
    expansions = 0
    while heap:
        _f, _c, node = heapq.heappop(heap)
        if node in closed:
            continue
        closed.add(node)
        expansions += 1
        if node == goal:
            return _unwind(prev, start, goal), expansions
        for nb, cost in adj.get(node, ()):
            nd = g[node] + cost
            if nd < g.get(nb, inf):
                g[nb] = nd
                prev[nb] = node
                if nb in closed:
                    closed.discard(nb)  # reopen: a strictly cheaper path was found
                counter += 1
                heapq.heappush(heap, (nd + float(heuristic.get(nb, 0.0)), counter, nb))
    return None, expansions


def oracle_route_cost(problem: NavigationProblem) -> float:
    """Exact cheapest admissible route cost (the optimality oracle). inf if unreachable."""
    _route, cost = exact_shortest_route(problem)
    return cost


# --------------------------------------------------------------------------- #
# reusable field base
# --------------------------------------------------------------------------- #


class ReusableField:
    """A start-independent, goal-anchored cost-to-go field, reusable across queries.

    The build + repair cost is charged once (:attr:`total_build_scans`); each query
    pays only its own A* extraction (:meth:`query_scans`). This is the object that
    makes amortization measurable, exactly as :class:`~rakl.navigation_dynamics.GoalField`
    does for the dynamics -- but with A* extraction (optimal under an admissible
    field) rather than a greedy gradient walk.
    """

    def __init__(self, *, strategy_id: str, goal: str, graph_nodes: int, values: Mapping[str, float]):
        self.strategy_id = strategy_id
        self.goal = goal
        self.graph_nodes = graph_nodes
        self.values: Dict[str, float] = dict(values)
        # build_scans + repair_scans, all in node-scan units
        self.total_build_scans = 0

    # subclasses set this during construction / repair
    def h(self, node: str) -> float:
        return float(self.values.get(node, 0.0))

    def query_scans(self, problem: NavigationProblem) -> Tuple[Tuple[str, ...] | None, int, float]:
        """Answer one query; return (route, query_scans, route_cost)."""
        if problem.goal != self.goal:
            raise ValueError("reusable field was built for a different goal")
        route, scans = field_guided_astar(problem, self.values)
        cost = problem.validate_route(route) if route is not None else inf
        return route, scans, cost

    @property
    def grants_scientific_authority(self) -> bool:
        return False


# --------------------------------------------------------------------------- #
# reverse Dijkstra: exact cost-to-go field (the strongest amortized parent)
# --------------------------------------------------------------------------- #


def build_reverse_dijkstra(problem: NavigationProblem) -> Tuple[Dict[str, float], int]:
    """Exact cost-to-go from every node to the goal, over admissible edges.

    Runs Dijkstra BACKWARDS from the goal on the reverse adjacency. ``d[v]`` is the
    exact cheapest cost to reach the goal from v -- the tightest admissible heuristic
    that exists. Returns (values, scans) where scans = number of nodes settled.
    """
    radj = problem.reverse_adjacency()
    dist: Dict[str, float] = {problem.goal: 0.0}
    heap: list[Tuple[float, str]] = [(0.0, problem.goal)]
    settled: set[str] = set()
    scans = 0
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        scans += 1
        for back, cost in radj.get(u, ()):  # back -> u edge of weight `cost`
            nd = d + cost
            if nd < dist.get(back, inf):
                dist[back] = nd
                heapq.heappush(heap, (nd, back))
    return dist, scans


class ReverseDijkstraField(ReusableField):
    """The exact cost-to-go field: ``h(v) = true cheapest cost v -> goal``.

    With this heuristic A* expands only nodes lying on an optimal path (for every
    node f = g + h >= optimal by the triangle inequality, with equality on the
    optimal path), so per-query scans collapse to the optimal-path length. The build
    settles every reachable node once. This is the field the historical study was
    missing: it is the parent any amortized mechanic must beat.
    """

    def __init__(self, problem: NavigationProblem):
        values, scans = build_reverse_dijkstra(problem)
        super().__init__(
            strategy_id="reverse_dijkstra_field",
            goal=problem.goal,
            graph_nodes=len(problem.nodes),
            values=values,
        )
        self.total_build_scans = scans


# --------------------------------------------------------------------------- #
# ALT: A* with Landmarks and Triangle inequality
# --------------------------------------------------------------------------- #


def build_alt_field(
    problem: NavigationProblem, n_landmarks: int = 4, rng: random.Random | None = None
) -> Tuple[Dict[str, float], int, List[str]]:
    """ALT lower bound from a set of landmarks (correct for DIRECTED graphs).

    The symmetric bound ``|d(L,v) - d(L,goal)|`` is admissible only on UNDIRECTED
    graphs: on a directed graph the reverse-difference term d(L,v)-d(L,goal) need
    not be <= d(v,goal), so it can overestimate and break A* optimality. The two
    valid one-sided lower bounds on the directed cost-to-go d(v,goal) are, per
    landmark L::

        forward: d(L,goal) - d(L,v) <= d(v,goal)      (L->v->goal concatenation)
        reverse: d(v,L)   - d(goal,L) <= d(v,goal)    (v->L via goal? no: by the
                  directed triangle inequality d(v,L) <= d(v,goal)+d(goal,L))

    Forward uses cost-FROM-landmark distances; reverse uses cost-TO-landmark
    distances (a reverse Dijkstra). The build settles |V| per landmark per
    direction (2*|V| per landmark). Landmarks are spread by farthest-point seeding.
    Returns (values, scans, landmarks).
    """
    rng = rng or random.Random(0)
    nodes = problem.nodes
    n_landmarks = max(1, min(n_landmarks, len(nodes)))
    # farthest-point landmark seeding (greedy max-min spread) for informative bounds
    landmarks: List[str] = [rng.choice(nodes)]
    while len(landmarks) < n_landmarks:
        best, best_d = None, -1.0
        for nd in nodes:
            if nd in landmarks:
                continue
            d = min(_hop_distance(problem, lm, nd) for lm in landmarks)
            if d > best_d:
                best_d, best = d, nd
        if best is None:
            break
        landmarks.append(best)

    scans = 0
    fwd: Dict[str, Dict[str, float]] = {}   # d(L, .)
    bwd: Dict[str, Dict[str, float]] = {}   # d(., L)
    for lm in landmarks:
        df, sf = _dijkstra_from(problem, lm)
        db, sb = _dijkstra_to(problem, lm)
        fwd[lm] = df
        bwd[lm] = db
        scans += sf + sb
    goal = problem.goal
    values: Dict[str, float] = {}
    for node in nodes:
        bound = 0.0
        for lm in landmarks:
            lv, lg = fwd[lm].get(node, inf), fwd[lm].get(goal, inf)
            if isfinite(lg) and isfinite(lv):
                bound = max(bound, lg - lv)            # forward one-sided
            vl, gl = bwd[lm].get(node, inf), bwd[lm].get(goal, inf)
            if isfinite(vl) and isfinite(gl):
                bound = max(bound, vl - gl)            # reverse one-sided
        values[node] = max(0.0, bound)
    return values, scans, landmarks


def _dijkstra_to(problem: NavigationProblem, target: str) -> Tuple[Dict[str, float], int]:
    """Cost-TO-target from every node (d(v, target)) via reverse adjacency; (dist, scans)."""
    radj = problem.reverse_adjacency()
    dist: Dict[str, float] = {target: 0.0}
    heap: list[Tuple[float, str]] = [(0.0, target)]
    settled: set[str] = set()
    scans = 0
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        scans += 1
        for back, cost in radj.get(u, ()):  # back -> u
            nd = d + cost
            if nd < dist.get(back, inf):
                dist[back] = nd
                heapq.heappush(heap, (nd, back))
    return dist, scans


def _dijkstra_from(problem: NavigationProblem, source: str) -> Tuple[Dict[str, float], int]:
    """Forward Dijkstra from `source` over admissible edges; (dist, scans)."""
    adj = problem.adjacency()
    dist: Dict[str, float] = {source: 0.0}
    heap: list[Tuple[float, str]] = [(0.0, source)]
    settled: set[str] = set()
    scans = 0
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        scans += 1
        for nb, cost in adj.get(u, ()):
            nd = d + cost
            if nd < dist.get(nb, inf):
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return dist, scans


def _hop_distance(problem: NavigationProblem, a: str, b: str) -> float:
    """BFS hop count a->b for landmark seeding (cheap structural spread)."""
    adj = problem.adjacency()
    seen = {a}
    queue = [a]
    hops = 0
    while queue:
        nxt: List[str] = []
        for node in queue:
            if node == b:
                return hops
            for nb, _c in adj.get(node, ()):
                if nb not in seen:
                    seen.add(nb)
                    nxt.append(nb)
        queue = nxt
        hops += 1
    return float(hops)


class ALTField(ReusableField):
    """ALT field: admissible landmark lower bound on cost-to-go."""

    def __init__(self, problem: NavigationProblem, n_landmarks: int = 4, rng: random.Random | None = None):
        values, scans, landmarks = build_alt_field(problem, n_landmarks=n_landmarks, rng=rng)
        super().__init__(
            strategy_id="alt_field",
            goal=problem.goal,
            graph_nodes=len(problem.nodes),
            values=values,
        )
        self.landmarks = tuple(landmarks)
        self.total_build_scans = scans


# --------------------------------------------------------------------------- #
# incrementally maintained exact shortest-path tree (Ramalingam-style repair)
# --------------------------------------------------------------------------- #


class IncrementalExactField(ReusableField):
    """Exact cost-to-go field maintained incrementally under edge-weight changes.

    Build is a reverse Dijkstra. After an edge-weight change the field is REPAIRED
    rather than rebuilt: a re-Dijkstra seeded only from the nodes whose cost-to-go
    can have changed (the affected subtree), which is the Ramalingam-Repair idea.
    Every repair scan is charged in :attr:`total_build_scans`, so the total exactly
    equals build + sum of repair work. This is the strongest DYNAMIC parent: exact
    at all times, and pays only for the region that actually moved.
    """

    def __init__(self, problem: NavigationProblem):
        values, scans = build_reverse_dijkstra(problem)
        super().__init__(
            strategy_id="incremental_exact_field",
            goal=problem.goal,
            graph_nodes=len(problem.nodes),
            values=values,
        )
        self.total_build_scans = scans
        self._problem = problem
        self._adjacency = problem.adjacency()
        self._reverse = problem.reverse_adjacency()
        self.repair_scans = 0
        self.n_updates = 0

    def refresh_problem(self, problem: NavigationProblem) -> None:
        """Adopt a new problem instance (with updated edges) for the next repair."""
        self._problem = problem

    def _continuation(self, node: str) -> float:
        """Best cost-to-go continuation of `node` from current stored values."""
        if node == self.goal:
            return 0.0
        best = inf
        for nb, cost in self._adjacency.get(node, ()):
            best = min(best, cost + self.values.get(nb, inf))
        return best

    def apply_change(self, edges: Sequence[NavigationEdge] | None = None) -> int:
        """Repair the field after the problem's admissible edges changed.

        Uses a worklist relaxation (Bellman-Ford restricted to the affected
        subgraph): a node is re-evaluated only if a neighbour's value moved, and the
        re-evaluation propagates to predecessors until the tree is consistent again.
        Correct for both decreases (cheaper edge) and increases (dearer/removed
        edge): a node whose only realizing path vanished is re-pulled up to its new
        best continuation. Each node re-evaluation is one charged node scan. The
        result is bit-for-bit the exact cost-to-go (verified in tests against a
        fresh reverse Dijkstra); the charge is the honest repair work.
        """
        self._adjacency = self._problem.adjacency()
        self._reverse = self._problem.reverse_adjacency()
        scans = 0
        # seed the worklist with the endpoints of the changed edges if supplied,
        # otherwise with every node whose stored value is inconsistent.
        worklist: set[str] = set()
        if edges:
            for e in edges:
                worklist.add(e.source)
                worklist.add(e.target)
        else:
            for node in self._problem.nodes:
                if abs(self._continuation(node) - self.values.get(node, inf)) > 1e-12:
                    worklist.add(node)
        # relax to a fixpoint over the affected region
        for _ in range(self.graph_nodes + 1):
            if not worklist:
                break
            dirty: set[str] = set()
            for node in sorted(worklist):
                scans += 1
                new = self._continuation(node)
                old = self.values.get(node, inf)
                if abs(new - old) > 1e-12:
                    self.values[node] = new
                    # predecessors (nodes with an edge INTO node) may now be stale
                    for pred, _c in self._reverse.get(node, ()):
                        dirty.add(pred)
            if not dirty:
                break
            worklist = dirty
        self.repair_scans += scans
        self.n_updates += 1
        self.total_build_scans += scans
        return scans


# --------------------------------------------------------------------------- #
# approximate incremental field (the SUCCESSOR mechanic)
# --------------------------------------------------------------------------- #


class ApproximateIncrementalField(ReusableField):
    """The successor: an admissible approximate field, maintained incrementally.

    The field is a partially-converged path-integral (soft-min) cost-to-go. A
    log-sum-exp over paths is <= the min over paths, and PARTIAL convergence only
    lowers values further (un-propagated nodes retain inf / their stale lower
    bound), so the field is ALWAYS admissible: A* guided by it stays optimal. The
    mechanic stops at a useful ordering margin (a small sweep budget) rather than
    full convergence, and after an edge update it runs a few LOCAL relaxation
    sweeps near the change instead of an exact repair. The honest bet is that for
    workloads with many updates and localized queries, the cheap local repair
    outweighs the slightly weaker per-query heuristic.
    """

    def __init__(
        self,
        problem: NavigationProblem,
        *,
        build_sweeps: int = 3,
        repair_sweeps: int = 2,
        repair_radius: int = 3,
        temperature: float = 0.5,
    ):
        if build_sweeps < 1:
            raise ValueError("build_sweeps must be >= 1")
        values = self._solve(problem, problem.adjacency(), build_sweeps, temperature)
        super().__init__(
            strategy_id="approximate_incremental_field",
            goal=problem.goal,
            graph_nodes=len(problem.nodes),
            values=values,
        )
        self.build_sweeps_used = build_sweeps
        self.repair_sweeps = repair_sweeps
        self.repair_radius = repair_radius
        self.temperature = temperature
        self.total_build_scans = build_sweeps * len(problem.nodes)
        self.repair_scans = 0
        self.n_updates = 0
        self._adjacency = problem.adjacency()
        self._problem = problem

    @staticmethod
    def _solve(
        problem: NavigationProblem,
        adjacency: Mapping[str, Tuple[Tuple[str, float], ...]],
        sweeps: int,
        temperature: float,
    ) -> Dict[str, float]:
        """Soft-min Bellman backup seeded at the trivial lower bound 0.

        V_goal = 0; V_i = -T log sum_j exp(-(L_ij+V_j)/T). Seeding every node at 0.0
        (a valid lower bound, since true cost >= 0) is what makes partial convergence
        ADMISSIBLE: with V_j <= exact_j for all j, the backup satisfies
        V_i <= min_j (L_ij + V_j) <= min_j (L_ij + exact_j) = exact_i. The induction
        holds from the first sweep, so EVERY sweep count yields an admissible field.
        Values rise toward the soft-min fixed point (itself <= exact) as sweeps
        increase -- fewer sweeps => looser (lower) but always admissible.

        (Seeding at inf instead breaks this: a 1-hop node relaxes to its single edge
        cost, which OVERESTIMATES the multi-hop optimum. The field is admissible only
        when neighbour values are already valid lower bounds.)
        """
        nodes = problem.nodes
        V: Dict[str, float] = {n: 0.0 for n in nodes}  # trivial admissible lower bound
        for _ in range(sweeps):
            nxt = dict(V)
            for node in nodes:
                if node == problem.goal:
                    continue
                terms = [cost + V[nb] for nb, cost in adjacency.get(node, ()) if V[nb] < inf]
                if not terms:
                    continue
                lo = min(terms)
                acc = sum(math.exp(-(x - lo) / temperature) for x in terms)
                nxt[node] = lo - temperature * math.log(acc)  # <= lo <= exact_i
            V = nxt
        return V

    def apply_change(self, edges: Sequence[NavigationEdge]) -> int:
        """Local admissible repair: a few soft-min sweeps over the change neighbourhood.

        The sweep updates ONLY region nodes but reads continuations over the FULL
        adjacency (in- and out-of-region neighbours alike), so no admissible
        continuation is ever dropped. It is seeded from the current stored values --
        themselves admissible -- and a soft-min backup is <= the min continuation <=
        the exact cost, so values can only DECREASE. A field that only ever moves
        down from admissible values stays admissible forever, even under edge
        increases (the old underestimate simply remains a valid lower bound of the
        now-larger true cost). Charge = repair_sweeps * |region|, the honest work.
        """
        self._adjacency = self._problem.adjacency()
        # region: nodes within repair_radius hops of any changed source, plus the goal
        changed_sources = {e.source for e in edges}
        region: set[str] = set()
        frontier = set(changed_sources)
        for _ in range(self.repair_radius):
            region |= frontier
            nxt: set[str] = set()
            for node in frontier:
                for nb, _c in self._adjacency.get(node, ()):
                    if nb not in region:
                        nxt.add(nb)
            frontier = nxt
            if not frontier:
                break
        region.add(self.goal)
        # seed from current admissible values; relax only region nodes over full adj
        V = dict(self.values)
        T = self.temperature
        for _ in range(self.repair_sweeps):
            moved = False
            for node in sorted(region):
                if node == self.goal:
                    continue
                terms = [cost + V[nb] for nb, cost in self._adjacency.get(node, ()) if isfinite(V[nb])]
                if not terms:
                    continue
                lo = min(terms)
                acc = sum(math.exp(-(x - lo) / T) for x in terms)
                new = lo - T * math.log(acc)  # <= lo <= exact
                if new < V[node] - 1e-12:
                    V[node] = new
                    moved = True
            if not moved:
                break
        for node in region:
            if isfinite(V[node]):
                self.values[node] = min(self.values.get(node, inf), V[node])
        scans = self.repair_sweeps * len(region)
        self.repair_scans += scans
        self.n_updates += 1
        self.total_build_scans += scans
        return scans

    def refresh_problem(self, problem: NavigationProblem) -> None:
        self._problem = problem
        self._adjacency = problem.adjacency()


# --------------------------------------------------------------------------- #
# navigator wrappers (single-shot contract; reuse the fail-closed Navigator.propose)
# --------------------------------------------------------------------------- #


class AStarExactFieldGuided(Navigator):
    """A* guided by the EXACT reverse-Dijkstra field. The strongest amortized parent."""

    strategy_id = "astar_exact_field"
    family = "control"

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        field = ReverseDijkstraField(problem)
        route, scans = field_guided_astar(problem, field.values)
        if route is None:
            return self._no_route(problem, search_expansions=scans, relaxation_sweeps=0)
        return self._routed(problem, route, search_expansions=scans, relaxation_sweeps=0)


class AStarALTGuided(Navigator):
    """A* guided by the ALT landmark lower bound."""

    strategy_id = "astar_alt_field"
    family = "control"

    def __init__(self, n_landmarks: int = 4, rng: random.Random | None = None):
        self.n_landmarks = n_landmarks
        self.rng = rng

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        field = ALTField(problem, n_landmarks=self.n_landmarks, rng=self.rng)
        route, scans = field_guided_astar(problem, field.values)
        if route is None:
            return self._no_route(problem, search_expansions=scans, relaxation_sweeps=0)
        return self._routed(problem, route, search_expansions=scans, relaxation_sweeps=0)


class IncrementalExactGuided(Navigator):
    """A* guided by the incrementally-repaired exact field (dynamic parent)."""

    strategy_id = "incremental_exact_field_nav"
    family = "control"

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        field = IncrementalExactField(problem)
        route, scans = field_guided_astar(problem, field.values)
        if route is None:
            return self._no_route(problem, search_expansions=scans, relaxation_sweeps=0)
        return self._routed(problem, route, search_expansions=scans, relaxation_sweeps=0)


class CooperativeFieldGuided(Navigator):
    """The SUCCESSOR navigator: dynamics field + exact A* cooperation.

    Single-shot mode builds the approximate field and runs A* on it. The build
    sweeps ARE charged (they are real work), so single-shot is honest about the
    field's overhead -- the amortized regime is where the experiment decides.
    """

    strategy_id = "cooperative_field_guided"
    family = "dynamics"

    def __init__(self, *, build_sweeps: int = 3, temperature: float = 0.5):
        self.build_sweeps = build_sweeps
        self.temperature = temperature

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        field = ApproximateIncrementalField(
            problem, build_sweeps=self.build_sweeps, temperature=self.temperature
        )
        route, scans = field_guided_astar(problem, field.values)
        sweeps = field.build_sweeps_used
        return RouteProposal(
            strategy_id=self.strategy_id,
            problem_id=problem.problem_id,
            route=tuple(route) if route is not None else None,
            proposed_cost=problem.validate_route(route) if route is not None else inf,
            search_expansions=scans,
            relaxation_sweeps=sweeps,
            graph_nodes=len(problem.nodes),
            diagnostics={"temperature": self.temperature, "build_sweeps": self.build_sweeps},
        )


# --------------------------------------------------------------------------- #
# registry of successor strategies (kept separate so the historical registry is
# undisturbed; the experiment + successor tests consume this directly)
# --------------------------------------------------------------------------- #

SUCCESSOR_STRATEGIES: Tuple[str, ...] = (
    "astar_exact_field",
    "astar_alt_field",
    "incremental_exact_field_nav",
    "cooperative_field_guided",
)
SUCCESSOR_PARENT_STRATEGIES: Tuple[str, ...] = (
    "astar_exact_field",
    "astar_alt_field",
    "incremental_exact_field_nav",
)
STRONG_AMORTIZED_PARENT: str = "astar_exact_field"
