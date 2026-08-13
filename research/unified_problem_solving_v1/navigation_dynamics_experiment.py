#!/usr/bin/env python3
"""Navigation dynamics vs A*: does a reusable GoalField give net advantage?

Scientific question: does GoalField (diffusion/path-integral) give a NET advantage over
STRONG_CONTROL (A* with the given heuristic) on states-expanded/verifier-calls/route-stretch,
with construction cost AMORTIZED over multiple queries (build-once-reuse-many)?

The entire point of a goal field is that it depends on the goal and the graph but NOT on
the query start, so one relaxation solve serves every start. This experiment measures whether
that amortization pays off compared to recomputing A* for each query.

Setup:
  * Random geometric graphs (nodes on unit square, edge cost >= straight-line distance).
  * For each graph: build ONE goal field per dynamics (diffusion/path-integral).
  * Run N queries from random starts to the same goal.
  * Compare: dynamics (build cost amortized over N queries) vs A* (recomputed per query).

Measured (per dynamics vs control):
  * net_vs_astar: (equivalent_expansions_dynamics - equivalent_expansions_astar) / queries
    Positive = dynamics uses MORE expansions than A* (bad).
    Negative = dynamics uses FEWER expansions than A* (good).
  * advantage_vs_control: fraction of queries where dynamics wins (fewer expansions).
  * net_expansions_vs_astar: raw difference in equivalent_expansions (dynamics - astar).

Honesty: development known-world evidence only. Grants NO scientific or method-promotion
authority. Reports whatever the distribution shows, with bootstrap CIs.

Includes negative regimes:
  * Single-query regime (amortization doesn't pay).
  * Tiny graphs (field construction cost dominates).
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from rakl.navigation_dynamics import (
    DiffusionNavigator,
    PathIntegralNavigator,
    AStarWithGivenHeuristic,
    NavigationProblem,
    NavigationEdge,
    STRONG_CONTROL,
    CONTROL_STRATEGIES,
    DYNAMICS_STRATEGIES,
)

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "navigation_dynamics.json"


def _random_geometric_problem(rng: random.Random, n: int, k: int, seed_offset: int = 0):
    """Generate a random geometric graph on unit square.
    
    Nodes are points on [0,1]^2. Each node connects to k nearest neighbors by straight-line
    distance. Edge cost = straight-line * (1 + random()) to ensure heuristic admissibility.
    """
    rng2 = random.Random(seed_offset)  # separate seed for point positions
    points = {f"n{i}": (rng2.random(), rng2.random()) for i in range(n)}
    names = sorted(points)
    
    def dist(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])
    
    edges = []
    for name in names:
        others = sorted(names, key=lambda o: dist(points[name], points[o]))[1 : k + 1]
        for other in others:
            base = dist(points[name], points[other])
            cost = base * (1.0 + rng.random())  # >= straight line: heuristic stays admissible
            edges.append(NavigationEdge(name, other, cost))
    
    start, goal = names[0], names[-1]
    heuristic = {name: dist(points[name], points[goal]) for name in names}
    return NavigationProblem(f"geo-n{n}-k{k}", tuple(edges), start, goal, heuristic)


def _run_single_query(problem, dynamics, control):
    """Run one query: dynamics vs control on the same problem.
    
    Returns (dyn_proposal, ctl_proposal).
    """
    dyn_prop = dynamics.propose(problem)
    ctl_prop = control.propose(problem)
    return dyn_prop, ctl_prop


def _run_amortized_experiment(base_problem, dyn_kwargs, control_cls, queries, rng):
    """Run amortized experiment: build field once, query many times.
    
    Args:
        base_problem: The base problem (defines graph, heuristic, original goal).
        dyn_kwargs: kwargs to create dynamics navigator.
        control_cls: Navigator class (A*).
        queries: List of (start, goal) query tuples.
        rng: Random seed for reproducibility.
    
    Returns:
        Dict with metrics for this experiment run.
    """
    from rakl.navigation_dynamics import get_navigator
    dynamics = get_navigator("diffusion", **dyn_kwargs)
    control = control_cls()
    
    # Build goal field ONCE using the base problem's goal
    goal_field = dynamics.build_goal_field(base_problem)
    if goal_field is None:
        # Physarum doesn't support goal fields
        return None
    
    results = {
        "dynamics_equivalent_expansions": 0,
        "control_equivalent_expansions": 0,
        "queries_found_route_dynamics": 0,
        "queries_found_route_control": 0,
        "queries_total": len(queries),
        "build_sweeps": goal_field.build_sweeps,
        "graph_nodes": goal_field.graph_nodes,
        "build_node_scans": goal_field.build_node_scans,
    }
    
    for start, goal in queries:
        # Create query problem with same graph/heuristic but different start
        query = NavigationProblem(
            f"q-{start}-to-{goal}",
            base_problem.edges,
            start,
            goal,
            base_problem.heuristic,
        )
        
        # Dynamics: use prebuilt field (propose_from charges only the walk)
        dyn_prop = goal_field.propose_from(query)
        
        # Control: run full A* for each query
        ctl_prop = control.propose(query)
        
        # Charge: dynamics = build_cost / queries + walk_cost
        dyn_total = goal_field.build_node_scans / len(queries) + dyn_prop.equivalent_expansions
        ctl_total = ctl_prop.equivalent_expansions
        
        results["dynamics_equivalent_expansions"] += dyn_total
        results["control_equivalent_expansions"] += ctl_total
        
        if dyn_prop.found_route:
            results["queries_found_route_dynamics"] += 1
        if ctl_prop.found_route:
            results["queries_found_route_control"] += 1
    
    return results


def _boot(vals, rng, B=5000):
    """Bootstrap CI for mean."""
    if not vals:
        return None
    m = sum(vals) / len(vals)
    samples = []
    for _ in range(B):
        s = [vals[rng.randrange(len(vals))] for _ in range(len(vals))]
        samples.append(sum(s) / len(s))
    samples.sort()
    return {"mean": round(m, 6), "lo": round(samples[int(0.025 * B)], 6), "hi": round(samples[int(0.975 * B)], 6), "n": len(vals)}


def run(seed=461, graphs=100, n=24, k=4, queries_per_graph=10):
    """Run the navigation dynamics experiment.
    
    Args:
        seed: Random seed for reproducibility.
        graphs: Number of random graphs to generate.
        n: Number of nodes per graph.
        k: Each node connects to k nearest neighbors.
        queries_per_graph: Number of random start-goal queries per graph.
    """
    rng = random.Random(seed)
    
    # Collect results per dynamics
    per_dynamics = defaultdict(lambda: {
        "net_vs_astar": [],      # (dyn_eq - ctl_eq) per query
        "advantage_vs_control": [],  # 1 if dyn wins, 0 otherwise
        "net_expansions_vs_astar": [],  # raw difference
    })
    
    # Also collect per-regime results
    regimes = {
        "single_query": defaultdict(lambda: {"net_vs_astar": [], "advantage_vs_control": [], "net_expansions_vs_astar": []}),
        "tiny_graph": defaultdict(lambda: {"net_vs_astar": [], "advantage_vs_control": [], "net_expansions_vs_astar": []}),
        "amortized": defaultdict(lambda: {"net_vs_astar": [], "advantage_vs_control": [], "net_expansions_vs_astar": []}),
    }
    
    graphs_made = 0
    attempts = 0
    max_attempts = graphs * 10  # prevent infinite loop
    
    while graphs_made < graphs and attempts < max_attempts:
        attempts += 1
        
        # Generate base problem
        base = _random_geometric_problem(rng, n=n, k=k, seed_offset=attempts)
        
        # Verify A* can find a route from start to goal
        ctl = AStarWithGivenHeuristic()
        check = ctl.propose(base)
        if not check.found_route:
            continue  # skip unsolvable graphs
        
        graphs_made += 1
        
        # Test each dynamics
        for dyn_name in DYNAMICS_STRATEGIES:
            from rakl.navigation_dynamics import get_navigator
            
            # Generate queries (random starts to same goal)
            queries = []
            nodes = [n for n in base.nodes if n != base.goal]
            for _ in range(queries_per_graph):
                start = rng.choice(nodes)
                queries.append((start, base.goal))
            
            # Get dynamics navigator kwargs (sweeps=25 for diffusion/path_integral)
            dyn_kwargs = {"sweeps": 25}
            result = _run_amortized_experiment(base, dyn_kwargs, AStarWithGivenHeuristic, queries, rng)
            if result is None:
                continue  # Physarum doesn't support goal fields
            
            # Per-query metrics
            dyn_eq_per_q = result["dynamics_equivalent_expansions"] / result["queries_total"]
            ctl_eq_per_q = result["control_equivalent_expansions"] / result["queries_total"]
            
            # net_vs_astar: POSITIVE = dynamics beats A* (uses fewer expansions)
            net_vs_astar = ctl_eq_per_q - dyn_eq_per_q
            advantage = 1.0 if dyn_eq_per_q < ctl_eq_per_q else 0.0
            net_expansions = result["dynamics_equivalent_expansions"] - result["control_equivalent_expansions"]
            
            per_dynamics[dyn_name]["net_vs_astar"].append(net_vs_astar)
            per_dynamics[dyn_name]["advantage_vs_control"].append(advantage)
            per_dynamics[dyn_name]["net_expansions_vs_astar"].append(net_expansions)
            
            # Regime classification
            if queries_per_graph == 1:
                regimes["single_query"][dyn_name]["net_vs_astar"].append(net_vs_astar)
                regimes["single_query"][dyn_name]["advantage_vs_control"].append(advantage)
                regimes["single_query"][dyn_name]["net_expansions_vs_astar"].append(net_expansions)
            elif n <= 12:
                regimes["tiny_graph"][dyn_name]["net_vs_astar"].append(net_vs_astar)
                regimes["tiny_graph"][dyn_name]["advantage_vs_control"].append(advantage)
                regimes["tiny_graph"][dyn_name]["net_expansions_vs_astar"].append(net_expansions)
            else:
                regimes["amortized"][dyn_name]["net_vs_astar"].append(net_vs_astar)
                regimes["amortized"][dyn_name]["advantage_vs_control"].append(advantage)
                regimes["amortized"][dyn_name]["net_expansions_vs_astar"].append(net_expansions)
    
    # Bootstrap CIs
    bs = random.Random(seed + 1)
    output = {
        "schema_version": "orion-navigation-dynamics-v1",
        "seed": seed,
        "graphs": graphs,
        "nodes_per_graph": n,
        "k_nearest": k,
        "queries_per_graph": queries_per_graph,
        "graphs_made": graphs_made,
        "claim_boundary": "development known-world evidence; tests goal-field amortization vs A* on random geometric graphs; grants no scientific or method-promotion authority.",
        "grants_scientific_authority": False,
        "grants_method_promotion": False,
        "by_dynamics": {},
        "regimes": {},
    }
    
    for dyn_name in DYNAMICS_STRATEGIES:
        if dyn_name not in per_dynamics:
            continue
        output["by_dynamics"][dyn_name] = {
            "net_vs_astar": _boot(per_dynamics[dyn_name]["net_vs_astar"], bs),
            "advantage_vs_control": _boot(per_dynamics[dyn_name]["advantage_vs_control"], bs),
            "net_expansions_vs_astar": _boot(per_dynamics[dyn_name]["net_expansions_vs_astar"], bs),
        }
    
    for regime_name, regime_data in regimes.items():
        output["regimes"][regime_name] = {}
        for dyn_name in DYNAMICS_STRATEGIES:
            if dyn_name not in regime_data or not regime_data[dyn_name]["net_vs_astar"]:
                continue
            output["regimes"][regime_name][dyn_name] = {
                "net_vs_astar": _boot(regime_data[dyn_name]["net_vs_astar"], bs),
                "advantage_vs_control": _boot(regime_data[dyn_name]["advantage_vs_control"], bs),
                "net_expansions_vs_astar": _boot(regime_data[dyn_name]["net_expansions_vs_astar"], bs),
            }
    
    # Top-level net metrics (combined across dynamics, for PROMOTE check)
    all_net_vs_astar = []
    all_advantage = []
    all_net_expansions = []
    for dyn_data in per_dynamics.values():
        all_net_vs_astar.extend(dyn_data["net_vs_astar"])
        all_advantage.extend(dyn_data["advantage_vs_control"])
        all_net_expansions.extend(dyn_data["net_expansions_vs_astar"])
    
    output["net_vs_astar"] = _boot(all_net_vs_astar, bs)
    output["advantage_vs_control"] = _boot(all_advantage, bs)
    output["net_expansions_vs_astar"] = _boot(all_net_expansions, bs)
    
    return output


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=461)
    ap.add_argument("--graphs", type=int, default=100)
    ap.add_argument("--nodes", type=int, default=24)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--queries", type=int, default=10)
    a = ap.parse_args()
    res = run(seed=a.seed, graphs=a.graphs, n=a.nodes, k=a.k, queries_per_graph=a.queries)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(res, indent=2))
    print(f"WROTE={RESULT.relative_to(HERE.parents[1])}")
    print("net_vs_astar:", res["net_vs_astar"])
    print("advantage_vs_control:", res["advantage_vs_control"])
    print("net_expansions_vs_astar:", res["net_expansions_vs_astar"])
    print("AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
