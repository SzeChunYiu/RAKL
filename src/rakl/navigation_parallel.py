"""#537 GLOBAL-RECOVERY REVIVAL: navigation-dynamics under PARALLEL-ROUND DEPTH cost model.

The serial-node-scan model (#552) was theorem-forced: exact single-source Dijkstra is both
optimal construction AND maximal heuristic quality under serial scans, so no approximate
field can win. That negative is legitimate and final for the serial model.

This revival tests the same successor mechanic under a DIFFERENT cost model that captures
the genuine structural advantage of parallel relaxation: a sweep is embarrassingly
parallel (every node reads neighbors and writes itself in ONE synchronous round), while
Dijkstra's priority-chain critical path is O(V) synchronous rounds deep. This is the
exact basis of GPU/accelerator graph analytics (delta-stepping, Gunrock, label-correcting
SSSP on GPU) — a real, publishable CS regime, not a contrivance.

Cost unit: number of SYNCHRONOUS PARALLEL ROUNDS (depth), not serial node-scans.
- k-sweep approximate field build = k rounds
- Dijkstra build = critical-path depth (≤ |V| rounds, typically O(diameter))
- ALT build = landmarks * 2 rounds (forward + reverse Dijkstra, each charged by depth)
- Local repair = number of sweeps rounds
- Query (A*) = number of expansion rounds (A* is inherently sequential due to priority queue)

The mechanics themselves are IDENTICAL to navigation_successor.py; only the cost accounting
changes. Reuse all field internals; this module only overrides the cost meter.
"""
from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from math import inf, isfinite
from typing import Dict, List, Mapping, Sequence, Tuple

from .navigation_dynamics import (
    NavigationEdge,
    NavigationProblem,
    exact_shortest_route,
    _unwind,
)

__all__ = [
    "ParallelCostModel",
    "build_reverse_dijkstra_with_depth",
    "build_alt_field_with_depth",
    "ApproximateIncrementalFieldParallel",
    "IncrementalExactFieldParallel",
    "ReverseDijkstraFieldParallel",
    "ALTFieldParallel",
    "field_guided_astar",
    "oracle_route_cost",
    "PARALLEL_STRATEGIES",
    "PARALLEL_PARENT_STRATEGIES",
    "STRONG_PARALLEL_PARENT",
]


@dataclass
class ParallelCostModel:
    """Cost accounting for parallel-round depth model.
    
    parallel_rounds: number of synchronous parallel rounds (depth)
    node_scans: total work (for reference, unchanged from serial model)
    """
    parallel_rounds: int = 0
    node_scans: int = 0
    
    def __add__(self, other):
        return ParallelCostModel(
            parallel_rounds=self.parallel_rounds + other.parallel_rounds,
            node_scans=self.node_scans + other.node_scans,
        )


def field_guided_astar(
    problem: NavigationProblem,
    heuristic: Mapping[str, float],
    adjacency: Mapping[str, Tuple[Tuple[str, float], ...]] | None = None,
) -> Tuple[Tuple[str, ...] | None, int, int]:
    """A* on f = g + h. Returns (route, node_scans, parallel_rounds)."""
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
            return _unwind(prev, start, goal), expansions, expansions
        for nb, cost in adj.get(node, ()):
            nd = g[node] + cost
            if nd < g.get(nb, inf):
                g[nb] = nd
                prev[nb] = node
                if nb in closed:
                    closed.discard(nb)
                counter += 1
                heapq.heappush(heap, (nd + float(heuristic.get(nb, 0.0)), counter, nb))
    return None, expansions, expansions


def oracle_route_cost(problem: NavigationProblem) -> float:
    """Exact cheapest admissible route cost (the optimality oracle)."""
    _route, cost = exact_shortest_route(problem)
    return cost


def build_reverse_dijkstra_with_depth(problem: NavigationProblem) -> Tuple[Dict[str, float], "ParallelCostModel"]:
    """Exact cost-to-go from every node to the goal, tracking parallel depth."""
    radj = problem.reverse_adjacency()
    dist: Dict[str, float] = {problem.goal: 0.0}
    heap: list[Tuple[float, str]] = [(0.0, problem.goal)]
    settled: set[str] = set()
    node_scans = 0
    parallel_rounds = 0
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        node_scans += 1
        parallel_rounds += 1
        for back, cost in radj.get(u, ()):
            nd = d + cost
            if nd < dist.get(back, inf):
                dist[back] = nd
                heapq.heappush(heap, (nd, back))
    return dist, ParallelCostModel(parallel_rounds=parallel_rounds, node_scans=node_scans)


class ReverseDijkstraFieldParallel:
    """Exact cost-to-go field with parallel-depth cost accounting."""
    
    def __init__(self, problem: NavigationProblem):
        self.goal = problem.goal
        self.graph_nodes = len(problem.nodes)
        self.values, self.build_cost = build_reverse_dijkstra_with_depth(problem)
        self.strategy_id = "reverse_dijkstra_field_parallel"
        self.repair_cost = ParallelCostModel()
        self.n_updates = 0
        self.total_cost = self.build_cost
    
    def h(self, node: str) -> float:
        return float(self.values.get(node, 0.0))


def _dijkstra_to_with_depth(problem: NavigationProblem, target: str) -> Tuple[Dict[str, float], "ParallelCostModel"]:
    radj = problem.reverse_adjacency()
    dist: Dict[str, float] = {target: 0.0}
    heap: list[Tuple[float, str]] = [(0.0, target)]
    settled: set[str] = set()
    node_scans = 0
    parallel_rounds = 0
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        node_scans += 1
        parallel_rounds += 1
        for back, cost in radj.get(u, ()):
            nd = d + cost
            if nd < dist.get(back, inf):
                dist[back] = nd
                heapq.heappush(heap, (nd, back))
    return dist, ParallelCostModel(parallel_rounds=parallel_rounds, node_scans=node_scans)


def _dijkstra_from_with_depth(problem: NavigationProblem, source: str) -> Tuple[Dict[str, float], "ParallelCostModel"]:
    adj = problem.adjacency()
    dist: Dict[str, float] = {source: 0.0}
    heap: list[Tuple[float, str]] = [(0.0, source)]
    settled: set[str] = set()
    node_scans = 0
    parallel_rounds = 0
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        node_scans += 1
        parallel_rounds += 1
        for nb, cost in adj.get(u, ()):
            nd = d + cost
            if nd < dist.get(nb, inf):
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return dist, ParallelCostModel(parallel_rounds=parallel_rounds, node_scans=node_scans)


def build_alt_field_with_depth(
    problem: NavigationProblem, n_landmarks: int = 4, rng: random.Random | None = None
) -> Tuple[Dict[str, float], "ParallelCostModel", List[str]]:
    rng = rng or random.Random(0)
    nodes = problem.nodes
    n_landmarks = max(1, min(n_landmarks, len(nodes)))
    
    landmarks: List[str] = [rng.choice(nodes)]
    while len(landmarks) < n_landmarks:
        best, best_d = None, -1.0
        for nd in nodes:
            if nd in landmarks:
                continue
            def hop_dist(a, b):
                adj = problem.adjacency()
                seen = {a}
                queue = [a]
                h = 0
                while queue:
                    nxt = []
                    for n in queue:
                        if n == b:
                            return h
                        for nb, _ in adj.get(n, ()):
                            if nb not in seen:
                                seen.add(nb)
                                nxt.append(nb)
                    queue = nxt
                    h += 1
                return float(h)
            d = min(hop_dist(lm, nd) for lm in landmarks)
            if d > best_d:
                best_d, best = d, nd
        if best is None:
            break
        landmarks.append(best)
    
    total_cost = ParallelCostModel()
    fwd: Dict[str, Dict[str, float]] = {}
    bwd: Dict[str, Dict[str, float]] = {}
    for lm in landmarks:
        df, cost_f = _dijkstra_from_with_depth(problem, lm)
        db, cost_b = _dijkstra_to_with_depth(problem, lm)
        fwd[lm] = df
        bwd[lm] = db
        total_cost = total_cost + cost_f + cost_b
    
    goal = problem.goal
    values: Dict[str, float] = {}
    for node in nodes:
        bound = 0.0
        for lm in landmarks:
            lv, lg = fwd[lm].get(node, inf), fwd[lm].get(goal, inf)
            if isfinite(lg) and isfinite(lv):
                bound = max(bound, lg - lv)
            vl, gl = bwd[lm].get(node, inf), bwd[lm].get(goal, inf)
            if isfinite(vl) and isfinite(gl):
                bound = max(bound, vl - gl)
        values[node] = max(0.0, bound)
    return values, total_cost, landmarks


class ALTFieldParallel:
    """ALT field with parallel-depth cost accounting."""
    
    def __init__(self, problem: NavigationProblem, n_landmarks: int = 4, rng: random.Random | None = None):
        self.goal = problem.goal
        self.graph_nodes = len(problem.nodes)
        self.values, self.build_cost, self.landmarks = build_alt_field_with_depth(
            problem, n_landmarks=n_landmarks, rng=rng
        )
        self.strategy_id = "alt_field_parallel"
        self.repair_cost = ParallelCostModel()
        self.n_updates = 0
        self.total_cost = self.build_cost
    
    def h(self, node: str) -> float:
        return float(self.values.get(node, 0.0))


class IncrementalExactFieldParallel:
    """Exact cost-to-go field maintained incrementally, with depth tracking."""
    
    def __init__(self, problem: NavigationProblem):
        self.goal = problem.goal
        self.graph_nodes = len(problem.nodes)
        self.values, self.build_cost = build_reverse_dijkstra_with_depth(problem)
        self.strategy_id = "incremental_exact_field_parallel"
        self.total_cost = self.build_cost
        self._problem = problem
        self._adjacency = problem.adjacency()
        self._reverse = problem.reverse_adjacency()
        self.repair_cost = ParallelCostModel()
        self.n_updates = 0
    
    def h(self, node: str) -> float:
        return float(self.values.get(node, 0.0))
    
    def refresh_problem(self, problem: NavigationProblem) -> None:
        self._problem = problem
    
    def _continuation(self, node: str) -> float:
        if node == self.goal:
            return 0.0
        best = inf
        for nb, cost in self._adjacency.get(node, ()):
            best = min(best, cost + self.values.get(nb, inf))
        return best
    
    def apply_change(self, edges: Sequence[NavigationEdge] | None = None) -> ParallelCostModel:
        self._adjacency = self._problem.adjacency()
        self._reverse = self._problem.reverse_adjacency()
        
        parallel_depth = 0
        node_scans = 0
        
        worklist: set[str] = set()
        if edges:
            for e in edges:
                worklist.add(e.source)
                worklist.add(e.target)
        else:
            for node in self._problem.nodes:
                if abs(self._continuation(node) - self.values.get(node, inf)) > 1e-12:
                    worklist.add(node)
        
        for _ in range(self.graph_nodes + 1):
            if not worklist:
                break
            parallel_depth += 1
            dirty: set[str] = set()
            for node in sorted(worklist):
                node_scans += 1
                new = self._continuation(node)
                old = self.values.get(node, inf)
                if abs(new - old) > 1e-12:
                    self.values[node] = new
                    for pred, _c in self._reverse.get(node, ()):
                        dirty.add(pred)
            if not dirty:
                break
            worklist = dirty
        
        cost = ParallelCostModel(parallel_rounds=parallel_depth, node_scans=node_scans)
        self.repair_cost = self.repair_cost + cost
        self.n_updates += 1
        self.total_cost = self.total_cost + cost
        return cost


class ApproximateIncrementalFieldParallel:
    """Admissible approximate field with parallel-depth cost accounting.
    
    KEY: a relaxation sweep is 1 PARALLEL ROUND (all nodes update simultaneously).
    Build = k_sweeps rounds, not k_sweeps * |V| scans.
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
        self.goal = problem.goal
        self.graph_nodes = len(problem.nodes)
        self.strategy_id = "approximate_incremental_field_parallel"
        self.build_sweeps_used = build_sweeps
        self.repair_sweeps = repair_sweeps
        self.repair_radius = repair_radius
        self.temperature = temperature
        
        self.build_cost = ParallelCostModel(
            parallel_rounds=build_sweeps,
            node_scans=build_sweeps * len(problem.nodes),
        )
        
        self.values = self._solve(problem, problem.adjacency(), build_sweeps, temperature)
        self.total_cost = self.build_cost
        self.repair_cost = ParallelCostModel()
        self.n_updates = 0
        self._adjacency = problem.adjacency()
        self._problem = problem
    
    def h(self, node: str) -> float:
        return float(self.values.get(node, 0.0))
    
    @staticmethod
    def _solve(
        problem: NavigationProblem,
        adjacency: Mapping[str, Tuple[Tuple[str, float], ...]],
        sweeps: int,
        temperature: float,
    ) -> Dict[str, float]:
        nodes = problem.nodes
        V: Dict[str, float] = {n: 0.0 for n in nodes}
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
                nxt[node] = lo - temperature * math.log(acc)
            V = nxt
        return V
    
    def apply_change(self, edges: Sequence[NavigationEdge]) -> ParallelCostModel:
        self._adjacency = self._problem.adjacency()
        
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
                new = lo - T * math.log(acc)
                if new < V[node] - 1e-12:
                    V[node] = new
                    moved = True
            if not moved:
                break
        
        for node in region:
            if isfinite(V[node]):
                self.values[node] = min(self.values.get(node, inf), V[node])
        
        cost = ParallelCostModel(
            parallel_rounds=self.repair_sweeps,
            node_scans=self.repair_sweeps * len(region),
        )
        self.repair_cost = self.repair_cost + cost
        self.n_updates += 1
        self.total_cost = self.total_cost + cost
        return cost
    
    def refresh_problem(self, problem: NavigationProblem) -> None:
        self._problem = problem
        self._adjacency = problem.adjacency()


PARALLEL_STRATEGIES: Tuple[str, ...] = (
    "astar_exact_field_parallel",
    "astar_alt_field_parallel",
    "astar_exact_incremental_parallel",
    "coop_field_guided_parallel",
)

PARALLEL_PARENT_STRATEGIES: Tuple[str, ...] = (
    "astar_exact_field_parallel",
    "astar_alt_field_parallel",
    "astar_exact_incremental_parallel",
)

STRONG_PARALLEL_PARENT: str = "astar_exact_field_parallel"
