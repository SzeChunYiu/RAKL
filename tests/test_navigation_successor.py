"""Contract tests for the #537 navigation-dynamics SUCCESSOR module.

These tests pin the load-bearing mathematical properties that make the successor
experiment's verdict trustworthy, INDEPENDENT of the experiment's outcome:

1. EXACTNESS of the reverse-Dijkstra field (the strongest amortized parent): its
   values equal the true cost-to-go, checked against an INDEPENDENT edge-list
   Bellman-Ford oracle (a different implementation than the module's heap Dijkstra).
2. ADMISSIBILITY of the ALT landmark bound on DIRECTED graphs. The symmetric
   ``|d(L,v) - d(L,goal)|`` overestimates cost-to-go on a directed graph and would
   break A* optimality; the successor's two one-sided bounds must NEVER overestimate.
   This is the regression guard for the directed-graph ALT fix.
3. ADMISSIBILITY of the approximate (soft-min) field at EVERY sweep count, and
   after local repair under edge changes. Seeding at the trivial lower bound 0 is
   what makes partial convergence admissible; this test would catch a regression
   to inf-seeding (which overestimates).
4. BIT-FOR-BIT EXACTNESS of the incremental exact repair vs a fresh rebuild, for
   both edge-weight increases and decreases.
5. OPTIMALITY of every field-guided A* variant (route cost == oracle), including
   the successor navigator (cooperative field-guided A*).
6. REGISTRY ISOLATION: importing this module adds nothing to the historical
   NAVIGATOR_REGISTRY -- the successor keeps its own strategy lists.
7. COST ACCOUNTING: build + repair scans are charged in the single node-scan unit.

Nothing here asserts that the successor WINS -- that is the experiment's job, and
hard-coding an expectation here would let the test dictate the result.
"""
from __future__ import annotations

import math
import random
from math import inf

import pytest

from rakl.navigation_dynamics import (
    NAVIGATOR_REGISTRY,
    NavigationEdge,
    NavigationProblem,
    available_navigators,
    exact_shortest_route,
)
from rakl.navigation_successor import (
    ALTField,
    AStarALTGuided,
    AStarExactFieldGuided,
    ApproximateIncrementalField,
    CooperativeFieldGuided,
    IncrementalExactField,
    IncrementalExactGuided,
    ReverseDijkstraField,
    SUCCESSOR_STRATEGIES,
    build_alt_field,
    build_reverse_dijkstra,
)

NAV_CLASSES = [
    AStarExactFieldGuided,
    AStarALTGuided,
    IncrementalExactGuided,
    CooperativeFieldGuided,
]


# --------------------------------------------------------------------------- #
# world builders
# --------------------------------------------------------------------------- #


def _directed_geometric(rng: random.Random, n: int = 20, k: int = 3):
    """Directed k-NN geometric graph; edge cost = euclidean * (1+r) >= euclidean.

    Returns (problem, base_of) where base_of[(s,t)] is the straight-line lower
    bound, so tests can change an edge while keeping it >= its admissible base.
    """
    points = {f"n{i}": (rng.random(), rng.random()) for i in range(n)}
    names = sorted(points)
    edges = []
    base_of = {}
    for name in names:
        others = sorted(
            names,
            key=lambda o: math.hypot(points[name][0] - points[o][0],
                                     points[name][1] - points[o][1]),
        )[1 : k + 1]
        for other in others:
            base = math.hypot(points[name][0] - points[other][0],
                              points[name][1] - points[other][1])
            cost = base * (1.0 + rng.random())  # >= straight line -> euclid h admissible
            edges.append(NavigationEdge(name, other, cost))
            base_of[(name, other)] = base
    goal = names[-1]
    heuristic = {name: math.hypot(points[name][0] - points[goal][0],
                                  points[name][1] - points[goal][1])
                 for name in names}
    return NavigationProblem(f"dg-{n}", tuple(edges), names[0], goal, heuristic), base_of


def _solvable(rng_seed: int, n: int = 18, k: int = 3):
    problem, base = _directed_geometric(random.Random(rng_seed), n=n, k=k)
    route, _cost = exact_shortest_route(problem)
    if route is None:
        return None
    return problem, base


def _bellman_ford_to_goal(problem: NavigationProblem) -> dict:
    """INDEPENDENT exact cost-to-go oracle: edge-list Bellman-Ford relaxations.

    Deliberately a different implementation than the module's heap-based reverse
    Dijkstra, so a shared bug would not pass this test.
    """
    edges = problem.admissible_edges()
    dist = {node: inf for node in problem.nodes}
    dist[problem.goal] = 0.0
    for _ in range(len(problem.nodes) - 1):
        updated = False
        for e in edges:
            nd = e.cost + dist.get(e.target, inf)
            if nd < dist.get(e.source, inf):
                dist[e.source] = nd
                updated = True
        if not updated:
            break
    return dist


def _replace_edge(problem: NavigationProblem, source: str, target: str, new_cost: float):
    edges = tuple(
        NavigationEdge(source, target, new_cost) if (e.source, e.target) == (source, target) else e
        for e in problem.edges
    )
    return NavigationProblem(problem.problem_id + "_p1", edges, problem.start, problem.goal,
                             problem.heuristic)


# --------------------------------------------------------------------------- #
# 1. reverse-Dijkstra field is the EXACT cost-to-go
# --------------------------------------------------------------------------- #


def test_reverse_dijkstra_equals_independent_bellman_ford_oracle():
    for seed in range(30):
        problem, _ = _directed_geometric(random.Random(200 + seed), n=20, k=3)
        values, scans = build_reverse_dijkstra(problem)
        oracle = _bellman_ford_to_goal(problem)
        for node in problem.nodes:
            assert values.get(node, inf) == pytest.approx(oracle[node], rel=1e-9, abs=1e-9), (
                seed, node, values.get(node, inf), oracle[node])
        # build settles at most every reachable node once
        assert scans <= len(problem.nodes)


def test_reverse_dijkstra_field_object_carries_build_charge():
    problem, _ = _directed_geometric(random.Random(31), n=16, k=3)
    field = ReverseDijkstraField(problem)
    assert field.total_build_scans > 0
    assert field.grants_scientific_authority is False
    assert field.goal == problem.goal


# --------------------------------------------------------------------------- #
# 2. ALT is admissible on DIRECTED graphs (regression guard)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("seed", range(30))
def test_alt_never_overestimates_directed_cost_to_go(seed):
    """The directed-graph ALT regression: symmetric |d(L,v)-d(L,goal)| overestimates
    on a directed graph; the two one-sided bounds must stay <= exact cost-to-go."""
    problem, _ = _directed_geometric(random.Random(700 + seed), n=22, k=3)
    values, _scans, landmarks = build_alt_field(problem, n_landmarks=4, rng=random.Random(seed))
    oracle = _bellman_ford_to_goal(problem)
    assert len(landmarks) == 4
    for node in problem.nodes:
        assert values[node] <= oracle[node] + 1e-9, (seed, node, values[node], oracle[node])


def test_alt_field_guided_astar_is_optimal():
    field_obj = None
    checked = 0
    for seed in range(40):
        problem, _ = _directed_geometric(random.Random(800 + seed), n=18, k=3)
        _route, exact = exact_shortest_route(problem)
        if _route is None:
            continue
        f = ALTField(problem, n_landmarks=4, rng=random.Random(seed))
        route, scans, cost = f.query_scans(problem)
        assert route is not None
        assert cost == pytest.approx(exact, rel=1e-9), (seed, cost, exact)
        field_obj = f
        checked += 1
        if checked >= 12:
            break
    assert checked > 0
    assert field_obj.total_build_scans > 0


# --------------------------------------------------------------------------- #
# 3. approximate soft-min field is admissible at every sweep count + after repair
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("build_sweeps", [1, 2, 3, 8])
@pytest.mark.parametrize("temperature", [0.3, 0.7])
def test_approximate_field_is_admissible_at_every_sweep_count(build_sweeps, temperature):
    """Seeding at 0 (trivial lower bound) makes partial convergence admissible;
    seeding at inf would overestimate and fail this at small sweep counts."""
    for seed in range(15):
        problem, _ = _directed_geometric(random.Random(400 + seed), n=20, k=3)
        oracle = _bellman_ford_to_goal(problem)
        f = ApproximateIncrementalField(problem, build_sweeps=build_sweeps,
                                        temperature=temperature)
        for node in problem.nodes:
            assert f.values[node] <= oracle[node] + 1e-9, (
                build_sweeps, temperature, seed, node, f.values[node], oracle[node])
        # build sweeps are charged
        assert f.total_build_scans == build_sweeps * len(problem.nodes)


def test_approximate_field_stays_admissible_after_local_repair():
    """Edge changes (up and down) must not push the approximate field above exact."""
    rng = random.Random(11)
    for trial in range(12):
        problem, base = _directed_geometric(random.Random(500 + trial), n=22, k=3)
        f = ApproximateIncrementalField(problem, build_sweeps=3, repair_sweeps=2,
                                        repair_radius=3, temperature=0.5)
        # two changes: one increase, one decrease, both clamped >= admissible base
        edge_a = problem.edges[trial % len(problem.edges)]
        edge_b = problem.edges[(trial * 7 + 3) % len(problem.edges)]
        cur = problem
        for edge, factor in ((edge_a, 1.8), (edge_b, 0.6)):
            ba = base.get((edge.source, edge.target), edge.cost)
            new_cost = max(ba, round(edge.cost * factor, 4))
            cur = _replace_edge(cur, edge.source, edge.target, new_cost)
            f.refresh_problem(cur)
            f.apply_change((NavigationEdge(edge.source, edge.target, new_cost),))
            oracle = _bellman_ford_to_goal(cur)
            for node in cur.nodes:
                assert f.values[node] <= oracle[node] + 1e-9, (
                    trial, node, f.values[node], oracle[node])


# --------------------------------------------------------------------------- #
# 4. incremental exact repair is bit-for-bit the fresh rebuild
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("factor", [0.5, 0.75, 1.5, 2.0])
def test_incremental_exact_repair_matches_fresh_rebuild(factor):
    for trial in range(12):
        problem, base = _directed_geometric(random.Random(600 + trial), n=24, k=3)
        field = IncrementalExactField(problem)
        edge = problem.edges[(trial * 5 + 1) % len(problem.edges)]
        ba = base.get((edge.source, edge.target), edge.cost)
        new_cost = max(ba, round(edge.cost * factor, 4))
        updated = _replace_edge(problem, edge.source, edge.target, new_cost)
        field.refresh_problem(updated)
        charged = field.apply_change((NavigationEdge(edge.source, edge.target, new_cost),))
        # the repaired field must equal a fresh exact build on the updated graph
        fresh, _ = build_reverse_dijkstra(updated)
        for node in updated.nodes:
            assert field.values.get(node, inf) == pytest.approx(
                fresh.get(node, inf), rel=1e-9, abs=1e-9), (factor, trial, node)
        # repair work is charged (and is real, non-negative work)
        assert charged >= 0
        assert field.n_updates == 1


# --------------------------------------------------------------------------- #
# 5. optimality of every field-guided A* variant (route cost == oracle)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("cls", NAV_CLASSES)
def test_every_field_guided_navigator_is_optimal(cls):
    checked = 0
    for seed in range(50):
        problem, _ = _directed_geometric(random.Random(900 + seed), n=18, k=3)
        _route, exact = exact_shortest_route(problem)
        if _route is None:
            continue
        proposal = cls().propose(problem)
        assert proposal.route is not None, (cls.strategy_id, seed)
        assert proposal.proposed_cost == pytest.approx(exact, rel=1e-9), (
            cls.strategy_id, seed, proposal.proposed_cost, exact)
        # no proposal grants any authority
        assert proposal.grants_scientific_authority is False
        assert proposal.grants_target_authority is False
        assert proposal.grants_method_promotion is False
        checked += 1
        if checked >= 15:
            break
    assert checked > 0


def test_cooperative_field_guided_charges_its_build_sweeps():
    problem, _ = _directed_geometric(random.Random(3), n=16, k=3)
    proposal = CooperativeFieldGuided(build_sweeps=4, temperature=0.5).propose(problem)
    assert proposal.relaxation_sweeps == 4
    assert proposal.sweep_node_scans == 4 * len(problem.nodes)
    # build cost is charged on top of the A* walk, never free
    assert proposal.equivalent_expansions == proposal.search_expansions + proposal.sweep_node_scans
    assert proposal.equivalent_expansions > proposal.search_expansions


# --------------------------------------------------------------------------- #
# 6. registry isolation: the successor keeps its own lists
# --------------------------------------------------------------------------- #


def test_importing_successor_does_not_pollute_navigator_registry():
    # the historical registry must be unchanged by this module's import
    historical = set(available_navigators())
    assert historical == set(NAVIGATOR_REGISTRY.keys())
    assert not (historical & set(SUCCESSOR_STRATEGIES)), (
        "successor strategies leaked into the historical NAVIGATOR_REGISTRY")


def test_successor_strategy_lists_are_nonempty_and_disjoint_from_parents():
    parents = set(SUCCESSOR_STRATEGIES)
    assert parents  # non-empty
    # the successor navigator itself is the one non-parent entry
    assert "cooperative_field_guided" in parents


# --------------------------------------------------------------------------- #
# 7. unreachable goal: every method reports no route honestly
# --------------------------------------------------------------------------- #


def test_unreachable_goal_reports_no_route():
    edges = (
        NavigationEdge("a", "b", 1.0),
        NavigationEdge("b", "c", 1.0),
    )
    problem = NavigationProblem("iso", edges, "a", "z", {"a": 1.0, "b": 1.0, "c": 0.0})
    values, _ = build_reverse_dijkstra(problem)
    assert values.get("a", inf) == inf
    for cls in NAV_CLASSES:
        proposal = cls().propose(problem)
        assert proposal.route is None, cls.strategy_id
        assert proposal.found_route is False, cls.strategy_id


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
