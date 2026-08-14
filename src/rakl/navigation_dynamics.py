"""Flow / diffusion / Physarum / path-integral navigation dynamics, and the search
controls they must beat to matter.

The design documents in ``docs/design/orion_mechanics_multiscale_plan`` repeatedly
name a family of "natural" navigation dynamics -- lightning/dielectric-breakdown
fronts, slime-mould conductance, diffusion geometry, path-integral weighting -- as
candidate replacements for classical search. They were named but never implemented,
and never compared against a strong control. That is the coordinate this module
closes: it gives each candidate an *honest* formalization with an identical
interface, an identical cost meter, and identical hard-constraint obligations, so
the comparison is decidable rather than rhetorical.

What is implemented
-------------------
Dynamics (the candidates):
  * :class:`DiffusionNavigator`      -- heat/diffusion kernel propagated backwards
    from the goal; the route follows the concentration gradient.
  * :class:`PhysarumNavigator`       -- Tero-style adaptive conductance:
    ``Q_ij = D_ij (p_i - p_j) / L_ij`` with pressures from a grounded Kirchhoff
    solve and reinforcement ``dD/dt = f(|Q|) - D``, iterated until flow
    concentrates on a channel. This is the honest formalization of the
    "lightning / slime mould" intuition: a physical relaxation, not a metaphor.
  * :class:`PathIntegralNavigator`   -- soft-min (Boltzmann) path value
    ``V_i = -T log sum_j exp(-(L_ij + V_j)/T)``, i.e. a log-sum-exp over all paths
    at temperature ``T``; the route is greedy on the soft value.

Controls (what they must beat):
  * :class:`UninformedBFS`           -- weak control; hop-count breadth-first, blind
    to edge cost. On weighted worlds it is *not* cost-optimal, by construction.
  * :class:`GreedyBestFirst`         -- heuristic-only control.
  * :class:`AStarWithGivenHeuristic` -- STRONG control. With an admissible
    heuristic this is cost-optimal and expansion-frugal. A dynamics that does not
    beat this on the measured axis has not earned its place.

Three invariants hold for every strategy, enforced structurally rather than by
convention:

1. **Routing only, no authority.** Every :class:`RouteProposal` reports
   ``grants_scientific_authority = False`` and ``grants_target_authority = False``.
   A proposal is a *proposal*: it says "this route is worth executing", never
   "this route is correct" and never "this claim is established".
2. **Noncompensatory hard-constraint admissibility.** Hard constraints come from
   :mod:`rakl.path_cost` (:class:`~rakl.path_cost.PathAdmissibility`) and are
   applied *before* any cost comparison. An inadmissible edge is not expensive, it
   is absent: no cheapness anywhere else can buy it back. Dynamics are the obvious
   place for this to leak (a diffusion kernel or a conductance field will happily
   smear probability mass through a forbidden edge), so
   :meth:`Navigator.propose` re-validates every returned route against the hard
   constraints and fails closed if a subclass smuggled one through.
3. **Each strategy carries its own compute cost.** All strategies are metered in
   the same unit, the *node scan* (see :class:`RouteProposal.equivalent_expansions`):
   one search expansion = one node scan; one dynamics relaxation sweep = ``|V|``
   node scans, because it touches every node. A 100-iteration diffusion solve on a
   120-node graph is charged 12,000 node scans, not zero. Without this the exotic
   dynamics win by accounting fiction.

Nothing in this module grants scientific, proof, method-promotion or routing
authority. It produces development-level, known-world evidence only.
"""
from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass, field
from math import inf, isfinite
from typing import Callable, Dict, Iterable, Mapping, Sequence, Tuple

from .path_cost import PathAdmissibility

__all__ = [
    "NavigationEdge",
    "NavigationProblem",
    "RouteProposal",
    "GoalField",
    "Navigator",
    "STRONG_CONTROL",
    "DiffusionNavigator",
    "PhysarumNavigator",
    "PathIntegralNavigator",
    "UninformedBFS",
    "GreedyBestFirst",
    "AStarWithGivenHeuristic",
    "register_navigator",
    "get_navigator",
    "available_navigators",
    "NAVIGATOR_REGISTRY",
    "CONTROL_STRATEGIES",
    "DYNAMICS_STRATEGIES",
    "admissible_everywhere",
    "forbidden_edge",
    "exact_shortest_route",
    "route_cost",
    "InadmissibleRouteError",
]


# --------------------------------------------------------------------------- #
# hard-constraint helpers (noncompensatory: filtered before any cost compare)
# --------------------------------------------------------------------------- #


def admissible_everywhere() -> PathAdmissibility:
    """A hard-constraint profile with every gate satisfied."""
    return PathAdmissibility(
        licensed_assumptions=True,
        trusted_verifier=True,
        specification_aligned=True,
        portal_valid=True,
        root_scope_preserved=True,
    )


def forbidden_edge(*, reason: str = "licensed_assumptions") -> PathAdmissibility:
    """A hard-constraint profile that fails one gate (default: unlicensed assumption).

    ``PathAdmissibility.admissible`` is an AND over gates, so failing (or leaving
    ``None``/unknown) any single gate makes the edge unroutable regardless of cost.
    """
    fields = {
        "licensed_assumptions": True,
        "trusted_verifier": True,
        "specification_aligned": True,
        "portal_valid": True,
        "root_scope_preserved": True,
    }
    if reason not in fields:
        raise ValueError(f"unknown hard-constraint gate: {reason}")
    fields[reason] = False
    return PathAdmissibility(**fields)


class InadmissibleRouteError(RuntimeError):
    """A navigator proposed a route through a hard-constraint-failing edge.

    This is a fail-closed programming error, not a search outcome: the whole point
    of the noncompensatory rule is that such a route can never be *offered*, not
    that it is offered and then scored badly.
    """


# --------------------------------------------------------------------------- #
# world
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class NavigationEdge:
    """One directed operator step with a nonnegative cost and its hard constraints."""

    source: str
    target: str
    cost: float
    admissibility: PathAdmissibility = field(default_factory=admissible_everywhere)

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("navigation edge requires source and target identities")
        if not isfinite(self.cost) or self.cost < 0:
            raise ValueError(f"edge cost must be finite and nonnegative: {self.source}->{self.target}={self.cost}")

    @property
    def hard_constraints_satisfied(self) -> bool:
        return self.admissibility.admissible


@dataclass(frozen=True)
class NavigationProblem:
    """A known world: directed weighted operator graph, start, goal, given heuristic.

    ``heuristic`` is the cost-to-go estimate handed to the heuristic controls. It is
    *given*, not learned here; the experiment supplies an admissible (never
    over-estimating) heuristic so that :class:`AStarWithGivenHeuristic` is a genuinely
    strong, cost-optimal control rather than a straw man.
    """

    problem_id: str
    edges: Tuple[NavigationEdge, ...]
    start: str
    goal: str
    heuristic: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.problem_id:
            raise ValueError("problem_id is required")
        if not self.edges:
            raise ValueError("navigation problem requires at least one edge")
        if self.start == self.goal:
            raise ValueError("start and goal must differ (a zero-step routing problem is degenerate)")
        for value in self.heuristic.values():
            if not isfinite(value) or value < 0:
                raise ValueError("heuristic values must be finite and nonnegative")

    # -- structure ---------------------------------------------------------- #

    @property
    def nodes(self) -> Tuple[str, ...]:
        seen: Dict[str, None] = {}
        for edge in self.edges:
            seen.setdefault(edge.source, None)
            seen.setdefault(edge.target, None)
        return tuple(sorted(seen))

    def admissible_edges(self) -> Tuple[NavigationEdge, ...]:
        """Hard-constraint filter. Applied BEFORE any cost is looked at.

        This is the noncompensatory boundary from :mod:`rakl.path_cost`: an edge that
        fails a gate is removed from the world, not penalised in the world.
        """
        return tuple(edge for edge in self.edges if edge.hard_constraints_satisfied)

    def adjacency(self) -> Dict[str, Tuple[Tuple[str, float], ...]]:
        """Forward adjacency over admissible edges only (parallel edges reduced to min)."""
        best: Dict[str, Dict[str, float]] = {node: {} for node in self.nodes}
        for edge in self.admissible_edges():
            row = best.setdefault(edge.source, {})
            if edge.target not in row or edge.cost < row[edge.target]:
                row[edge.target] = edge.cost
        return {node: tuple(sorted(row.items())) for node, row in best.items()}

    def reverse_adjacency(self) -> Dict[str, Tuple[Tuple[str, float], ...]]:
        rev: Dict[str, Dict[str, float]] = {node: {} for node in self.nodes}
        for source, row in self.adjacency().items():
            for target, cost in row:
                back = rev.setdefault(target, {})
                if source not in back or cost < back[source]:
                    back[source] = cost
        return {node: tuple(sorted(row.items())) for node, row in rev.items()}

    def h(self, node: str) -> float:
        return float(self.heuristic.get(node, 0.0))

    # -- validation --------------------------------------------------------- #

    def validate_route(self, route: Sequence[str]) -> float:
        """Return the route's cost, or raise if it is not a legal admissible route.

        Legality is checked against the *admissible* adjacency, so a route that uses
        a hard-constraint-failing edge raises :class:`InadmissibleRouteError` even
        when every step exists in the raw edge list.
        """
        if len(route) < 2:
            raise InadmissibleRouteError("a route must contain at least start and goal")
        if route[0] != self.start or route[-1] != self.goal:
            raise InadmissibleRouteError(f"route must run {self.start} -> {self.goal}, got {route[0]} -> {route[-1]}")
        raw = {(edge.source, edge.target) for edge in self.edges}
        adjacency = self.adjacency()
        total = 0.0
        for a, b in zip(route, route[1:]):
            step = dict(adjacency.get(a, ()))
            if b not in step:
                if (a, b) in raw:
                    raise InadmissibleRouteError(
                        f"route uses hard-constraint-failing edge {a}->{b}; hard constraints are "
                        "noncompensatory and cannot be bought back by cost"
                    )
                raise InadmissibleRouteError(f"route uses a nonexistent edge {a}->{b}")
            total += step[b]
        return total


def route_cost(problem: NavigationProblem, route: Sequence[str]) -> float:
    return problem.validate_route(route)


def exact_shortest_route(problem: NavigationProblem) -> Tuple[Tuple[str, ...] | None, float]:
    """Ground truth: exact cheapest admissible route (Dijkstra over admissible edges).

    This is the oracle the optimality ratio is measured against. It is deliberately
    *not* registered as a navigator: it is not a competitor, it is the answer key.
    """
    adjacency = problem.adjacency()
    dist = {problem.start: 0.0}
    prev: Dict[str, str] = {}
    heap: list[tuple[float, str]] = [(0.0, problem.start)]
    settled: set[str] = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        if u == problem.goal:
            break
        for v, c in adjacency.get(u, ()):
            nd = d + c
            if nd < dist.get(v, inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if problem.goal not in dist:
        return None, inf
    route = [problem.goal]
    while route[-1] != problem.start:
        route.append(prev[route[-1]])
    route.reverse()
    return tuple(route), dist[problem.goal]


# --------------------------------------------------------------------------- #
# proposal
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RouteProposal:
    """A routing proposal. Carries no authority of any kind.

    Cost accounting is uniform across strategies so that "the dynamics won" can
    never mean "the dynamics were not billed":

    ``search_expansions``
        node scans performed by a frontier search (one pop = one scan of a node and
        its out-edges).
    ``relaxation_sweeps``
        full relaxation sweeps performed by a dynamics (diffusion step, Kirchhoff
        Gauss-Seidel sweep, soft-Bellman backup). Each sweep touches every node.
    ``sweep_node_scans``
        ``relaxation_sweeps * |V|`` -- the sweeps converted into the same unit as
        search expansions.
    ``equivalent_expansions``
        ``search_expansions + sweep_node_scans``. This is the matched-cost number.
    """

    strategy_id: str
    problem_id: str
    route: Tuple[str, ...] | None
    proposed_cost: float
    search_expansions: int
    relaxation_sweeps: int
    graph_nodes: int
    diagnostics: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.strategy_id:
            raise ValueError("strategy_id is required")
        if self.search_expansions < 0 or self.relaxation_sweeps < 0 or self.graph_nodes < 0:
            raise ValueError("cost counters must be nonnegative")
        if self.route is None and isfinite(self.proposed_cost):
            raise ValueError("a proposal with no route must have infinite proposed cost")
        if self.route is not None and not isfinite(self.proposed_cost):
            raise ValueError("a proposal with a route must have finite proposed cost")

    @property
    def found_route(self) -> bool:
        return self.route is not None

    @property
    def sweep_node_scans(self) -> int:
        return self.relaxation_sweeps * self.graph_nodes

    @property
    def equivalent_expansions(self) -> int:
        """Total compute in node scans. Dynamics iterations are NOT free."""
        return self.search_expansions + self.sweep_node_scans

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion(self) -> bool:
        return False

    def as_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "problem_id": self.problem_id,
            "route": list(self.route) if self.route is not None else None,
            "proposed_cost": self.proposed_cost if isfinite(self.proposed_cost) else None,
            "search_expansions": self.search_expansions,
            "relaxation_sweeps": self.relaxation_sweeps,
            "sweep_node_scans": self.sweep_node_scans,
            "equivalent_expansions": self.equivalent_expansions,
            "found_route": self.found_route,
            "diagnostics": dict(self.diagnostics),
            "grants_scientific_authority": False,
            "grants_target_authority": False,
            "grants_method_promotion": False,
        }


# --------------------------------------------------------------------------- #
# navigator base + registry
# --------------------------------------------------------------------------- #


NAVIGATOR_REGISTRY: Dict[str, Callable[..., "Navigator"]] = {}


def register_navigator(cls):
    """Class decorator registering a navigator under its ``strategy_id``."""
    strategy_id = getattr(cls, "strategy_id", "")
    if not strategy_id:
        raise ValueError("a navigator must declare a nonempty strategy_id")
    if strategy_id in NAVIGATOR_REGISTRY:
        raise ValueError(f"duplicate navigator strategy_id: {strategy_id}")
    NAVIGATOR_REGISTRY[strategy_id] = cls
    return cls


def get_navigator(strategy_id: str, **kwargs) -> "Navigator":
    if strategy_id not in NAVIGATOR_REGISTRY:
        raise KeyError(f"unregistered navigator: {strategy_id}")
    return NAVIGATOR_REGISTRY[strategy_id](**kwargs)


def available_navigators() -> Tuple[str, ...]:
    return tuple(sorted(NAVIGATOR_REGISTRY))


class GoalField:
    """A start-independent, goal-anchored routing field, reusable across queries.

    This is the object that makes the re-planning regime measurable. Diffusion and
    path-integral values depend on the goal and the graph but *not* on the query
    start, so one relaxation solve serves every start: the build cost amortizes and
    the per-query cost collapses to the field walk. A* has no such object -- its
    work is start-specific and must be repaid on every query.

    Physarum deliberately does **not** produce one: its pressure field is driven by
    a current injected at the start, so the solve is start-dependent by
    construction. That is a property of the dynamics, not an implementation gap, and
    it is reported rather than papered over.
    """

    def __init__(
        self,
        *,
        strategy_id: str,
        goal: str,
        build_sweeps: int,
        graph_nodes: int,
        adjacency: Mapping[str, Tuple[Tuple[str, float], ...]],
        edge_score: Callable[[str, str, float], float],
        better,
        diagnostics: Mapping[str, float] | None = None,
        max_route_steps: int | None = None,
    ):
        self.strategy_id = strategy_id
        self.goal = goal
        self.build_sweeps = build_sweeps
        self.graph_nodes = graph_nodes
        self._adjacency = adjacency
        self._edge_score = edge_score
        self._better = better
        self.diagnostics = dict(diagnostics or {})
        self._max_route_steps = max_route_steps

    @property
    def build_node_scans(self) -> int:
        """One-off construction cost, in the same node-scan unit as expansions."""
        return self.build_sweeps * self.graph_nodes

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    def propose_from(self, problem: NavigationProblem) -> RouteProposal:
        """Answer a query with this prebuilt field; charges only the walk.

        The build cost is *not* recharged here -- that is the whole point of
        amortization -- so the caller is responsible for adding
        :attr:`build_node_scans` once. The experiment does exactly that.
        """
        if problem.goal != self.goal:
            raise ValueError("goal field was built for a different goal")
        route, expansions = _gradient_route(
            problem,
            self._adjacency,
            score=None,
            better=self._better,
            max_steps=self._max_route_steps,
            edge_score=self._edge_score,
        )
        diag = dict(self.diagnostics)
        diag["amortized_extraction"] = 1.0
        if route is None:
            return RouteProposal(
                strategy_id=self.strategy_id,
                problem_id=problem.problem_id,
                route=None,
                proposed_cost=inf,
                search_expansions=expansions,
                relaxation_sweeps=0,
                graph_nodes=self.graph_nodes,
                diagnostics=diag,
            )
        return RouteProposal(
            strategy_id=self.strategy_id,
            problem_id=problem.problem_id,
            route=tuple(route),
            proposed_cost=problem.validate_route(route),
            search_expansions=expansions,
            relaxation_sweeps=0,
            graph_nodes=self.graph_nodes,
            diagnostics=diag,
        )


class Navigator:
    """Common interface. Subclasses implement ``_propose`` and nothing else.

    ``propose`` is deliberately final-ish: it wraps the subclass result in the
    noncompensatory admissibility re-check, so a dynamics cannot leak a forbidden
    edge into a proposal even by accident.
    """

    strategy_id: str = ""
    family: str = "control"

    def build_goal_field(self, problem: NavigationProblem) -> GoalField | None:
        """Return a reusable start-independent goal field, or ``None``.

        ``None`` means "this strategy has no start-independent field and must redo
        its work for every query". That is the honest default: A*, greedy, BFS and
        Physarum all return ``None``.
        """
        return None

    def propose(self, problem: NavigationProblem) -> RouteProposal:
        proposal = self._propose(problem)
        if proposal.strategy_id != self.strategy_id:
            raise ValueError("proposal strategy_id must match the navigator")
        if proposal.route is not None:
            # Fail-closed re-check: hard constraints are applied before any cost
            # comparison, and again here before the proposal escapes the navigator.
            validated = problem.validate_route(proposal.route)
            if abs(validated - proposal.proposed_cost) > 1e-9:
                raise InadmissibleRouteError(
                    f"{self.strategy_id} reported cost {proposal.proposed_cost} but the "
                    f"admissible route costs {validated}"
                )
        return proposal

    def _propose(self, problem: NavigationProblem) -> RouteProposal:  # pragma: no cover - abstract
        raise NotImplementedError

    # -- shared helpers ----------------------------------------------------- #

    def _no_route(self, problem: NavigationProblem, *, search_expansions: int, relaxation_sweeps: int, **diag) -> RouteProposal:
        return RouteProposal(
            strategy_id=self.strategy_id,
            problem_id=problem.problem_id,
            route=None,
            proposed_cost=inf,
            search_expansions=search_expansions,
            relaxation_sweeps=relaxation_sweeps,
            graph_nodes=len(problem.nodes),
            diagnostics=diag,
        )

    def _routed(
        self,
        problem: NavigationProblem,
        route: Sequence[str],
        *,
        search_expansions: int,
        relaxation_sweeps: int,
        **diag,
    ) -> RouteProposal:
        cost = problem.validate_route(route)
        return RouteProposal(
            strategy_id=self.strategy_id,
            problem_id=problem.problem_id,
            route=tuple(route),
            proposed_cost=cost,
            search_expansions=search_expansions,
            relaxation_sweeps=relaxation_sweeps,
            graph_nodes=len(problem.nodes),
            diagnostics=diag,
        )


# --------------------------------------------------------------------------- #
# controls
# --------------------------------------------------------------------------- #


@register_navigator
class UninformedBFS(Navigator):
    """Weak control: breadth-first on hop count, blind to edge cost.

    Honest by construction: on a weighted world BFS returns a *hop*-optimal route,
    which is generally not cost-optimal. It is included as the floor, not as a
    serious competitor.
    """

    strategy_id = "uninformed_bfs"
    family = "control"

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        adjacency = problem.adjacency()
        prev: Dict[str, str] = {}
        seen = {problem.start}
        queue = deque([problem.start])
        expansions = 0
        while queue:
            node = queue.popleft()
            expansions += 1
            if node == problem.goal:
                route = _unwind(prev, problem.start, problem.goal)
                return self._routed(problem, route, search_expansions=expansions, relaxation_sweeps=0)
            for nb, _cost in adjacency.get(node, ()):
                if nb not in seen:
                    seen.add(nb)
                    prev[nb] = node
                    queue.append(nb)
        return self._no_route(problem, search_expansions=expansions, relaxation_sweeps=0)


@register_navigator
class GreedyBestFirst(Navigator):
    """Heuristic-only control: expand the frontier node with the smallest ``h``."""

    strategy_id = "greedy_best_first"
    family = "control"

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        adjacency = problem.adjacency()
        prev: Dict[str, str] = {}
        seen = {problem.start}
        heap: list[tuple[float, int, str]] = [(problem.h(problem.start), 0, problem.start)]
        tie = 1
        expansions = 0
        while heap:
            _, _, node = heapq.heappop(heap)
            expansions += 1
            if node == problem.goal:
                route = _unwind(prev, problem.start, problem.goal)
                return self._routed(problem, route, search_expansions=expansions, relaxation_sweeps=0)
            for nb, _cost in adjacency.get(node, ()):
                if nb not in seen:
                    seen.add(nb)
                    prev[nb] = node
                    heapq.heappush(heap, (problem.h(nb), tie, nb))
                    tie += 1
        return self._no_route(problem, search_expansions=expansions, relaxation_sweeps=0)


@register_navigator
class AStarWithGivenHeuristic(Navigator):
    """STRONG control: A* on ``f = g + h`` with the problem's given heuristic.

    Heuristic contract (admissibility): for every node ``v``,
    ``h(v) <= true_dist(v, goal)``. Under admissibility this returns an exactly
    optimal route while expanding far fewer nodes than uninformed search. Any
    dynamics in this module has to beat *this* on the measured axis to be worth
    its complexity.

    Implementation: a node whose ``g`` improves after it was first expanded is
    *reopened* (removed from the closed set and re-inserted in the frontier).
    Reopening is required for optimality when the heuristic is admissible but
    inconsistent; when the heuristic is consistent the reopen branch is never
    taken and the search behaves as an efficient closed-set A*. The implementation
    therefore matches the admissible-optimality theorem without narrowing the
    contract to consistent heuristics.
    """

    strategy_id = "astar_given_heuristic"
    family = "control"

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        adjacency = problem.adjacency()
        g = {problem.start: 0.0}
        prev: Dict[str, str] = {}
        heap: list[tuple[float, int, str]] = [(problem.h(problem.start), 0, problem.start)]
        tie = 1
        closed: set[str] = set()
        expansions = 0
        while heap:
            _f, _t, node = heapq.heappop(heap)
            if node in closed:
                continue
            closed.add(node)
            expansions += 1
            if node == problem.goal:
                route = _unwind(prev, problem.start, problem.goal)
                return self._routed(problem, route, search_expansions=expansions, relaxation_sweeps=0)
            for nb, cost in adjacency.get(node, ()):
                nd = g[node] + cost
                if nd < g.get(nb, inf):
                    g[nb] = nd
                    prev[nb] = node
                    if nb in closed:
                        closed.discard(nb)  # reopen: a strictly cheaper path was found
                    heapq.heappush(heap, (nd + problem.h(nb), tie, nb))
                    tie += 1
        return self._no_route(problem, search_expansions=expansions, relaxation_sweeps=0)


# --------------------------------------------------------------------------- #
# dynamics
# --------------------------------------------------------------------------- #


@register_navigator
class DiffusionNavigator(Navigator):
    """Heat/diffusion kernel over the operator graph; route follows the gradient.

    A concentration ``u`` is clamped to 1 at the goal and propagated *backwards*
    along admissible operator edges (a node is "warm" if it can reach the goal):

    ``u_i <- sum_j c_ij exp(-L_ij / tau) u_j / sum_j c_ij``,  ``c_ij = 1 / (L_ij + eps)``

    so a step of length ``L`` attenuates concentration by ``exp(-L/tau)`` and cheap
    edges conduct more. The route is steepest ascent on the *gradient*, i.e. each
    step maximises the directional derivative ``(u_j - u_i) / L_ij`` rather than raw
    concentration -- otherwise a long expensive hop into a warm region would always
    beat a short cheap hop, which is a route-extraction artefact rather than a
    property of the field.

    Known weakness, stated up front rather than discovered later: the update is a
    conductance-weighted *average*, so ``u_i`` is depressed by a node's bad
    neighbours as well as raised by its good one. A node whose single good exit sits
    among many dead ends can be colder than a node on a worse but more uniform
    route. The gradient is therefore not a value function and the route is not
    guaranteed optimal.
    """

    strategy_id = "diffusion"
    family = "dynamics"

    def __init__(self, *, sweeps: int = 40, tau: float | None = None, eps: float = 1e-9, max_route_steps: int | None = None):
        if sweeps < 1:
            raise ValueError("diffusion requires at least one sweep")
        if tau is not None and tau <= 0:
            raise ValueError("tau must be positive")
        self.sweeps = sweeps
        self.tau = tau
        self.eps = eps
        self.max_route_steps = max_route_steps

    def build_goal_field(self, problem: NavigationProblem) -> GoalField:
        adjacency = problem.adjacency()
        nodes = problem.nodes
        costs = [c for row in adjacency.values() for _n, c in row]
        tau = self.tau if self.tau is not None else max(1e-6, (sum(costs) / len(costs)) if costs else 1.0)

        u = {node: 0.0 for node in nodes}
        u[problem.goal] = 1.0
        sweeps = 0
        for _ in range(self.sweeps):
            nxt = dict(u)
            for node in nodes:
                if node == problem.goal:
                    continue  # clamped source
                row = adjacency.get(node, ())
                if not row:
                    nxt[node] = 0.0
                    continue
                num = 0.0
                den = 0.0
                for nb, cost in row:
                    conductance = 1.0 / (cost + self.eps)
                    num += conductance * math.exp(-cost / tau) * u[nb]
                    den += conductance
                nxt[node] = num / den if den else 0.0
            u = nxt
            sweeps += 1

        return GoalField(
            strategy_id=self.strategy_id,
            goal=problem.goal,
            build_sweeps=sweeps,
            graph_nodes=len(nodes),
            adjacency=adjacency,
            # steepest ascent on the concentration gradient (u_j - u_i) / L_ij
            edge_score=lambda a, b, cost: (u[b] - u[a]) / (cost + self.eps),
            better=max,
            diagnostics={"tau": tau},
            max_route_steps=self.max_route_steps,
        )

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        goal_field = self.build_goal_field(problem)
        walk = goal_field.propose_from(problem)
        # single-query mode: the relaxation solve is charged in full
        diag = dict(goal_field.diagnostics)
        return RouteProposal(
            strategy_id=self.strategy_id,
            problem_id=problem.problem_id,
            route=walk.route,
            proposed_cost=walk.proposed_cost,
            search_expansions=walk.search_expansions,
            relaxation_sweeps=goal_field.build_sweeps,
            graph_nodes=goal_field.graph_nodes,
            diagnostics=diag,
        )


@register_navigator
class PhysarumNavigator(Navigator):
    """Tero-style adaptive conductance dynamics (slime mould / lightning channel).

    State is a conductance ``D_ij`` on every admissible edge. Each iteration:

    1. solve the Kirchhoff network for pressures ``p`` with unit current injected at
       the start and withdrawn at the goal (grounded at ``p_goal = 0``), by
       Gauss-Seidel relaxation on the grounded Laplacian:
       ``p_i <- (b_i + sum_j c_ij p_j) / sum_j c_ij`` with ``c_ij = D_ij / L_ij``;
    2. read the flows ``Q_ij = D_ij (p_i - p_j) / L_ij``;
    3. reinforce: ``dD/dt = f(|Q|) - D`` with ``f(x) = x`` (Tero's linear rule),
       integrated explicitly as ``D <- D + dt (f(|Q|) - D)``.

    High-flow tubes thicken, low-flow tubes atrophy, and the network concentrates on
    a channel. The route is then read off by following the surviving conductance.

    The tube network is undirected (pressure is a scalar potential), but *routing*
    is directed: route extraction only ever traverses admissible directed edges, so
    a tube that thickened in the wrong direction cannot be used.
    """

    strategy_id = "physarum"
    family = "dynamics"

    def __init__(
        self,
        *,
        iterations: int = 20,
        pressure_sweeps: int = 3,
        dt: float = 0.35,
        flow_exponent: float = 1.0,
        current: float = 1.0,
        initial_conductance: float = 1.0,
        eps: float = 1e-9,
        max_route_steps: int | None = None,
    ):
        if iterations < 1 or pressure_sweeps < 1:
            raise ValueError("physarum requires at least one iteration and one pressure sweep")
        if not 0 < dt <= 1:
            raise ValueError("dt must be in (0, 1]")
        self.iterations = iterations
        self.pressure_sweeps = pressure_sweeps
        self.dt = dt
        self.flow_exponent = flow_exponent
        self.current = current
        self.initial_conductance = initial_conductance
        self.eps = eps
        self.max_route_steps = max_route_steps

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        adjacency = problem.adjacency()
        nodes = problem.nodes

        # undirected tube skeleton over admissible edges (length = min directed cost)
        length: Dict[Tuple[str, str], float] = {}
        for source, row in adjacency.items():
            for target, cost in row:
                key = (source, target) if source <= target else (target, source)
                if key not in length or cost < length[key]:
                    length[key] = cost
        if not length:
            return self._no_route(problem, search_expansions=0, relaxation_sweeps=0)

        tube_neighbours: Dict[str, list[Tuple[str, Tuple[str, str]]]] = {node: [] for node in nodes}
        for key in length:
            a, b = key
            tube_neighbours[a].append((b, key))
            tube_neighbours[b].append((a, key))

        conductance = {key: self.initial_conductance for key in length}
        pressure = {node: 0.0 for node in nodes}
        sweeps = 0
        for _ in range(self.iterations):
            # (1) pressures: Gauss-Seidel on the grounded Laplacian
            for _s in range(self.pressure_sweeps):
                for node in nodes:
                    if node == problem.goal:
                        pressure[node] = 0.0  # ground
                        continue
                    num = self.current if node == problem.start else 0.0
                    den = 0.0
                    for nb, key in tube_neighbours[node]:
                        c = conductance[key] / (length[key] + self.eps)
                        num += c * pressure[nb]
                        den += c
                    pressure[node] = num / den if den > 0 else 0.0
                sweeps += 1
            # (2)+(3) flows and conductance reinforcement dD/dt = f(|Q|) - D
            for key, D in list(conductance.items()):
                a, b = key
                flow = abs(D * (pressure[a] - pressure[b]) / (length[key] + self.eps))
                reinforcement = flow if self.flow_exponent == 1.0 else flow ** self.flow_exponent
                conductance[key] = max(0.0, D + self.dt * (reinforcement - D))
            sweeps += 1  # the reinforcement pass also touches every tube

        def tube_conductance(a: str, b: str) -> float:
            return conductance.get((a, b) if a <= b else (b, a), 0.0)

        route, expansions = _gradient_route(
            problem,
            adjacency,
            score=None,
            better=max,
            max_steps=self.max_route_steps,
            edge_score=lambda a, b, cost: tube_conductance(a, b),
        )
        peak = max(conductance.values()) if conductance else 0.0
        alive = sum(1 for value in conductance.values() if value > 0.05 * peak) if peak > 0 else 0
        diag = {"peak_conductance": peak, "tubes": float(len(conductance)), "surviving_tubes": float(alive)}
        if route is None:
            return self._no_route(problem, search_expansions=expansions, relaxation_sweeps=sweeps, **diag)
        return self._routed(problem, route, search_expansions=expansions, relaxation_sweeps=sweeps, **diag)


@register_navigator
class PathIntegralNavigator(Navigator):
    """Soft-min / Boltzmann path-integral value; route is greedy on the soft value.

    The free energy of all admissible routes from ``i`` to the goal at temperature
    ``T`` satisfies the soft Bellman backup

    ``V_i = -T log sum_j exp(-(L_ij + V_j) / T)``,  ``V_goal = 0``

    which is a log-sum-exp over paths: as ``T -> 0`` it converges to the exact
    shortest-path value (hard min), and at ``T > 0`` it is a strict *under*-estimate
    that rewards states with many near-optimal continuations ("path entropy").

    That under-estimate is the honest cost of the method: at usable temperatures the
    greedy descent can prefer a fat bundle of mediocre routes over a single thin
    optimal one. Backups are run to a fixed sweep budget and every sweep is billed.
    """

    strategy_id = "path_integral"
    family = "dynamics"

    def __init__(self, *, sweeps: int = 30, temperature: float = 0.25, max_route_steps: int | None = None):
        if sweeps < 1:
            raise ValueError("path integral requires at least one sweep")
        if temperature <= 0:
            raise ValueError("temperature must be positive (T -> 0 is the hard-min limit)")
        self.sweeps = sweeps
        self.temperature = temperature
        self.max_route_steps = max_route_steps

    def build_goal_field(self, problem: NavigationProblem) -> GoalField:
        adjacency = problem.adjacency()
        nodes = problem.nodes
        T = self.temperature
        V = {node: (0.0 if node == problem.goal else inf) for node in nodes}
        sweeps = 0
        for _ in range(self.sweeps):
            nxt = dict(V)
            for node in nodes:
                if node == problem.goal:
                    continue
                terms = [cost + V[nb] for nb, cost in adjacency.get(node, ()) if isfinite(V[nb])]
                if not terms:
                    continue
                lo = min(terms)
                # numerically stable log-sum-exp; -T log sum exp(-x/T)
                acc = sum(math.exp(-(x - lo) / T) for x in terms)
                nxt[node] = lo - T * math.log(acc)
            V = nxt
            sweeps += 1

        # For path integrals, V[goal] = 0 and V[other] < 0 (soft-minimum values).
        # To go toward the goal, we follow the neighbor with HIGHEST V (closest to 0).
        # Use edge_score = V[neighbor] and better = max.
        return GoalField(
            strategy_id=self.strategy_id,
            goal=problem.goal,
            build_sweeps=sweeps,
            graph_nodes=len(nodes),
            adjacency=adjacency,
            edge_score=lambda a, b, cost: V[b] if isfinite(V[b]) else inf,
            better=max,
            diagnostics={"temperature": T},
            max_route_steps=self.max_route_steps,
        )

    def _propose(self, problem: NavigationProblem) -> RouteProposal:
        goal_field = self.build_goal_field(problem)
        walk = goal_field.propose_from(problem)
        return RouteProposal(
            strategy_id=self.strategy_id,
            problem_id=problem.problem_id,
            route=walk.route,
            proposed_cost=walk.proposed_cost,
            search_expansions=walk.search_expansions,
            relaxation_sweeps=goal_field.build_sweeps,
            graph_nodes=goal_field.graph_nodes,
            diagnostics=dict(goal_field.diagnostics),
        )


CONTROL_STRATEGIES: Tuple[str, ...] = ("uninformed_bfs", "greedy_best_first", "astar_given_heuristic")
DYNAMICS_STRATEGIES: Tuple[str, ...] = ("diffusion", "physarum", "path_integral")
STRONG_CONTROL: str = "astar_given_heuristic"


# --------------------------------------------------------------------------- #
# route extraction shared by the dynamics
# --------------------------------------------------------------------------- #


def _unwind(prev: Mapping[str, str], start: str, goal: str) -> Tuple[str, ...]:
    route = [goal]
    while route[-1] != start:
        route.append(prev[route[-1]])
    route.reverse()
    return tuple(route)


def _gradient_route(
    problem: NavigationProblem,
    adjacency: Mapping[str, Tuple[Tuple[str, float], ...]],
    *,
    score: Callable[[str], float] | None,
    better,
    max_steps: int | None,
    edge_score: Callable[[str, str, float], float] | None = None,
) -> Tuple[Tuple[str, ...] | None, int]:
    """Walk the field from start to goal, one node scan per step.

    Only admissible adjacency is ever consulted, so a field that has smeared mass
    across a forbidden edge still cannot route through it -- the hard constraint is
    applied before the field is compared, not after.

    Visited nodes are excluded so the walk cannot cycle; if every continuation is
    exhausted the walk fails (this is a genuine "no route found", which the
    experiment counts as a failure whenever the oracle says a route exists).
    """
    if score is None and edge_score is None:
        raise ValueError("_gradient_route needs a node score or an edge score")
    limit = max_steps if max_steps is not None else 4 * len(problem.nodes) + 8
    node = problem.start
    route = [node]
    visited = {node}
    expansions = 0
    while node != problem.goal and len(route) <= limit:
        expansions += 1
        candidates = [(nb, cost) for nb, cost in adjacency.get(node, ()) if nb not in visited]
        if not candidates:
            return None, expansions
        if edge_score is not None:
            valued = [(edge_score(node, nb, cost), cost, nb) for nb, cost in candidates]
        else:
            valued = [(score(nb), cost, nb) for nb, cost in candidates]
        valued = [item for item in valued if isfinite(item[0])]
        if not valued:
            return None, expansions
        if better is max:
            # tie-break toward the cheaper step, then lexicographically (determinism)
            pick = max(valued, key=lambda item: (item[0], -item[1], item[2]))
        else:
            pick = min(valued, key=lambda item: (item[0], item[1], item[2]))
        node = pick[2]
        visited.add(node)
        route.append(node)
    if node != problem.goal:
        return None, expansions
    return tuple(route), expansions
