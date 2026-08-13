"""Tests for #537 parallel-model revival: navigation_dynamics_parallel.

Tests focus on load-bearing properties independent of outcome:
- Parallel-round depth accounting correctness
- Admissibility preserved under depth model
- Optimality gate (A* + admissible field = optimal routes)
- Cross-check: parallel-rounds vs serial-scans on known graph
"""
from __future__ import annotations

import math
import random

import pytest

from rakl.navigation_dynamics import NavigationProblem, NavigationEdge
from rakl.navigation_parallel import (
    ParallelCostModel,
    build_reverse_dijkstra_with_depth,
    build_alt_field_with_depth,
    ApproximateIncrementalFieldParallel,
    IncrementalExactFieldParallel,
    ReverseDijkstraFieldParallel,
    ALTFieldParallel,
    field_guided_astar,
    oracle_route_cost,
)


def _small_graph():
    """Tiny geometric graph for targeted tests."""
    edges = (
        NavigationEdge("a", "b", 1.0),
        NavigationEdge("b", "c", 1.0),
        NavigationEdge("a", "c", 3.0),
        NavigationEdge("c", "d", 1.0),
    )
    return NavigationProblem("test", edges, "a", "d", {})


def test_parallel_cost_model_addition():
    """ParallelCostModel adds rounds and scans correctly."""
    c1 = ParallelCostModel(parallel_rounds=5, node_scans=100)
    c2 = ParallelCostModel(parallel_rounds=3, node_scans=50)
    total = c1 + c2
    assert total.parallel_rounds == 8
    assert total.node_scans == 150


def test_reverse_dijkstra_depth_accounting():
    """Exact reverse-Dijkstra depth accounting: rounds <= nodes settled."""
    p = _small_graph()
    values, cost = build_reverse_dijkstra_with_depth(p)
    
    # Depth should equal number of settled nodes (worst-case chain)
    assert cost.parallel_rounds == cost.node_scans  # 1 round per node settled
    assert cost.parallel_rounds <= len(p.nodes)
    
    # Values should be exact
    assert values["d"] == 0.0  # goal
    assert values["c"] == 1.0  # c->d
    assert values["b"] == 2.0  # b->c->d
    assert values["a"] == 3.0  # a->c->d (optimal) or a->b->c->d = 3


def test_approximate_field_build_accounting():
    """Approximate field build cost: k_sweeps rounds, not k_sweeps * |V| scans."""
    p = _small_graph()
    
    for k in (1, 3, 5):
        field = ApproximateIncrementalFieldParallel(p, build_sweeps=k)
        # PARALLEL: k rounds (key structural advantage)
        assert field.build_cost.parallel_rounds == k
        # SERIAL REFERENCE: k * |V| node scans (for comparison)
        assert field.build_cost.node_scans == k * len(p.nodes)


def test_approximate_field_repair_accounting():
    """Local repair cost: repair_sweeps rounds over region."""
    p = _small_graph()
    field = ApproximateIncrementalFieldParallel(p, build_sweeps=3, repair_sweeps=2, repair_radius=2)
    
    # Apply an edge update
    updated_edges = (NavigationEdge("a", "b", 2.0),)
    cost = field.apply_change(updated_edges)
    
    # Repair should charge exactly repair_sweeps parallel rounds
    assert cost.parallel_rounds == 2
    # Node scans = repair_sweeps * |region| (for reference)
    assert cost.node_scans == 2 * len(set("abcd"))  # region covers all nodes


def test_incremental_exact_repair_accounting():
    """Incremental exact repair: charged in neighborhood-depth rounds."""
    p = _small_graph()
    field = IncrementalExactFieldParallel(p)
    
    # Apply an edge update
    updated_edges = (NavigationEdge("a", "b", 2.0),)
    cost = field.apply_change(updated_edges)
    
    # Repair depth should be <= graph size (worklist iterations)
    assert cost.parallel_rounds <= len(p.nodes)
    assert cost.parallel_rounds >= 1  # at least one iteration
    # Node_scans tracks the actual work
    assert cost.node_scans >= cost.parallel_rounds


def test_alt_field_accounting():
    """ALT field build: landmarks * 2 * dijkstra_depth."""
    p = _small_graph()
    field = ALTFieldParallel(p, n_landmarks=2, rng=random.Random(0))
    
    # Build cost should be landmarks * forward_dijkstra + reverse_dijkstra
    # Each Dijkstra depth <= |V|
    assert field.build_cost.parallel_rounds <= 2 * 2 * len(p.nodes)  # 2 landmarks * 2 directions
    assert field.build_cost.node_scans >= field.build_cost.parallel_rounds


def test_admissibility_preserved_under_parallel_model():
    """Approximate field is admissible at every sweep count under parallel model."""
    p = _small_graph()
    
    # Build exact field for reference
    exact_field = ReverseDijkstraFieldParallel(p)
    exact_values = exact_field.values
    
    # Test various sweep counts
    for sweeps in (1, 3, 10):
        apx_field = ApproximateIncrementalFieldParallel(p, build_sweeps=sweeps)
        for node in p.nodes:
            # Admissibility: h(node) <= exact_cost_to_goal
            apx_h = apx_field.h(node)
            exact_h = exact_values.get(node, float("inf"))
            assert apx_h <= exact_h + 1e-9, f"node={node}, sweeps={sweeps}, apx={apx_h}, exact={exact_h}"


def test_admissibility_preserved_after_parallel_repair():
    """Admissibility is preserved after local repair under parallel model."""
    p = _small_graph()
    exact_field = ReverseDijkstraFieldParallel(p)
    
    apx_field = ApproximateIncrementalFieldParallel(p, build_sweeps=3, repair_sweeps=2)
    
    # Apply edge update (increase cost)
    updated_edges = (NavigationEdge("a", "b", 5.0),)
    apx_field.apply_change(updated_edges)
    
    # Rebuild exact field on the updated graph
    p_updated = NavigationProblem("test2", (NavigationEdge("a", "b", 5.0), NavigationEdge("b", "c", 1.0), NavigationEdge("a", "c", 3.0), NavigationEdge("c", "d", 1.0)), "a", "d", {})
    exact_updated = ReverseDijkstraFieldParallel(p_updated)
    
    # Admissibility still holds
    for node in p.nodes:
        apx_h = apx_field.h(node)
        exact_h = exact_updated.values.get(node, float("inf"))
        assert apx_h <= exact_h + 1e-9, f"node={node}, apx={apx_h}, exact={exact_h}"


def test_optimality_gate_astar_with_approximate_parallel():
    """A* guided by admissible approximate field produces optimal routes."""
    rng = random.Random(537)
    
    # Generate several random graphs
    for _ in range(10):
        n = rng.randint(8, 16)
        nodes = [f"n{i}" for i in range(n)]
        goal = nodes[-1]
        edges = []
        for i in range(n - 1):
            edges.append(NavigationEdge(nodes[i], nodes[i+1], 1.0))
        # Add some random edges
        for _ in range(n):
            a = rng.choice(nodes[:-1])
            b = rng.choice(nodes[1:])
            if a != b:
                edges.append(NavigationEdge(a, b, rng.random() * 2 + 0.5))
        
        p = NavigationProblem("test", tuple(edges), nodes[0], goal, {})
        oracle = oracle_route_cost(p)
        
        if not math.isfinite(oracle):
            continue
        
        # Build approximate field
        apx_field = ApproximateIncrementalFieldParallel(p, build_sweeps=3)
        
        # A* search with approximate heuristic
        route, scans, rounds = field_guided_astar(p, apx_field.values)
        
        if route is None:
            assert oracle == float("inf")
        else:
            route_cost = p.validate_route(route)
            # Optimality gate: route_cost == oracle
            assert abs(route_cost - oracle) < 1e-9, f"route_cost={route_cost}, oracle={oracle}"


def test_parallel_vs_serial_cross_check():
    """Cross-check: parallel_rounds vs node_scans relationship on known graph."""
    p = _small_graph()
    
    # Approximate field: k rounds, k*|V| scans
    for k in (1, 3, 5):
        field = ApproximateIncrementalFieldParallel(p, build_sweeps=k)
        assert field.build_cost.parallel_rounds == k
        assert field.build_cost.node_scans == k * len(p.nodes)
    
    # Exact Dijkstra: rounds == node_scans (worst case 1 round per node)
    exact_field = ReverseDijkstraFieldParallel(p)
    assert exact_field.build_cost.parallel_rounds == exact_field.build_cost.node_scans
    assert exact_field.build_cost.parallel_rounds <= len(p.nodes)


def test_query_cost_accounting():
    """Query cost (A*): charged as expansion rounds = node_scans."""
    p = _small_graph()
    apx_field = ApproximateIncrementalFieldParallel(p, build_sweeps=3)
    
    route, scans, rounds = field_guided_astar(p, apx_field.values)
    
    # A* query: rounds == scans (each expansion is one round)
    assert rounds == scans
    
    # Query is much cheaper than build for small queries
    assert rounds < apx_field.build_cost.parallel_rounds or rounds <= len(p.nodes)


def test_parallel_rounds_positive_regime_static_single_query():
    """Verify the positive regime: static, single-query (Q=1, U=0).
    
    In this regime, the approximate field should beat exact Dijkstra on
    parallel rounds because k_sweeps << |V| for small k and moderate N.
    """
    # N=32, Q=1, U=0 (static, one query)
    n = 32
    nodes = [f"n{i}" for i in range(n)]
    goal = nodes[-1]
    edges = []
    rng = random.Random(537)
    
    # k-nearest-neighbour geometric graph
    positions = {node: (rng.random(), rng.random()) for node in nodes}
    def dist(a, b):
        return math.hypot(positions[a][0] - positions[b][0], positions[a][1] - positions[b][1])
    
    for a in nodes:
        others = sorted(nodes, key=lambda o: dist(a, o))[1:4]  # k=3
        for b in others:
            d = dist(a, b)
            edges.append(NavigationEdge(a, b, d * (1.0 + rng.random())))
    
    p = NavigationProblem("test", tuple(edges), nodes[0], goal, {})
    
    # Build fields
    apx_field = ApproximateIncrementalFieldParallel(p, build_sweeps=3)
    exact_field = ReverseDijkstraFieldParallel(p)
    
    # Approximate field build: 3 rounds
    assert apx_field.build_cost.parallel_rounds == 3
    
    # Exact field build: up to N rounds
    assert exact_field.build_cost.parallel_rounds <= n
    
    # For N=32, 3 rounds < 32 rounds (approximate wins on build)
    assert apx_field.build_cost.parallel_rounds < exact_field.build_cost.parallel_rounds
    
    # Single query cost is similar for both (A* with good heuristic)
    # So total cost favors approximate in this regime
    apx_total = apx_field.build_cost.parallel_rounds
    exact_total = exact_field.build_cost.parallel_rounds
    
    # Successor wins on parallel rounds in static single-query regime
    assert apx_total < exact_total
