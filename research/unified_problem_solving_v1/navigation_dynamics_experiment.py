#!/usr/bin/env python3
"""Navigation dynamics crossover: fair benchmark vs A* across regimes.

PREREGISTRATION (GitHub issue #519):
We test whether GoalField dynamics (diffusion/path-integral) give NET advantage over
A* STRONG_CONTROL across a regime grid of:
  1. Graph size (n ∈ {12, 24, 48})
  2. Heuristic quality (good=Euclidean vs poor=random)
  3. Reuse count (queries ∈ {1, 5, 20})

Hypothesis: dynamics benefit from amortization on large graphs with good heuristics
and many queries. A* dominates on small graphs, poor heuristics, or single queries.

Scientific question: where (if anywhere) does dynamics beat A* after charging its
own construction cost honestly?

Metrics (per dynamics vs A*):
  * net_vs_astar: ctl_eq_per_q - dyn_eq_per_q (POSITIVE = dynamics wins)
  * advantage_vs_control: fraction of queries where dynamics wins
  * route_stretch: (dyn_cost / ctl_cost) - 1 (0 = optimal, positive = slower)

Result contract: TOP-LEVEL net_vs_astar with CI {lo, hi}, status field,
grants_scientific_authority: false. Terminal vocabulary: SUPPORTED/PARTIAL/
NEGATIVE/CANNOT_CHECK/UNDERPOWERED/ARCHITECTURE_ONLY.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from itertools import product

import sys
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from rakl.navigation_dynamics import (
    DiffusionNavigator,
    PathIntegralNavigator,
    AStarWithGivenHeuristic,
    NavigationProblem,
    NavigationEdge,
    DYNAMICS_STRATEGIES,
)

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "navigation_dynamics.json"


def _random_geometric_problem(rng: random.Random, n: int, k: int, seed_offset: int = 0, heuristic_quality: str = "good"):
    """Generate random geometric graph with configurable heuristic quality.
    
    Args:
        n: number of nodes
        k: each node connects to k nearest neighbors
        seed_offset: for reproducibility
        heuristic_quality: "good" = Euclidean (admissible), "poor" = random (non-admissible)
    """
    rng2 = random.Random(seed_offset)
    points = {f"n{i}": (rng2.random(), rng2.random()) for i in range(n)}
    names = sorted(points)
    
    def dist(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])
    
    edges = []
    for name in names:
        others = sorted(names, key=lambda o: dist(points[name], points[o]))[1 : k + 1]
        for other in others:
            base = dist(points[name], points[other])
            cost = base * (1.0 + rng.random())  # >= straight line
            edges.append(NavigationEdge(name, other, cost))
    
    start, goal = names[0], names[-1]
    
    # Heuristic quality toggle
    if heuristic_quality == "good":
        heuristic = {name: dist(points[name], points[goal]) for name in names}
    else:  # poor heuristic (non-admissible random)
        heuristic = {name: rng.random() for name in names}
    
    return NavigationProblem(f"geo-n{n}-k{k}-{heuristic_quality}", tuple(edges), start, goal, heuristic)


def _run_amortized_experiment(base_problem, dynamics_name, queries, rng):
    """Run amortized experiment: build field once, query many times.
    
    Returns dict with metrics or None if dynamics doesn't support goal fields.
    """
    from rakl.navigation_dynamics import get_navigator
    
    # Create dynamics with appropriate kwargs
    if dynamics_name == "diffusion":
        dynamics = get_navigator(dynamics_name, sweeps=25)
    elif dynamics_name == "path_integral":
        dynamics = get_navigator(dynamics_name, sweeps=25, temperature=0.25)
    else:
        return None  # physarum doesn't support goal fields
    
    control = AStarWithGivenHeuristic()
    
    # Build goal field ONCE
    goal_field = dynamics.build_goal_field(base_problem)
    if goal_field is None:
        return None
    
    results = {
        "dynamics_eq": 0.0,
        "control_eq": 0.0,
        "dynamics_cost": 0.0,
        "control_cost": 0.0,
        "queries_found_dyn": 0,
        "queries_found_ctl": 0,
        "queries_total": len(queries),
        "build_scans": goal_field.build_node_scans,
    }
    
    for start, goal in queries:
        query = NavigationProblem(
            f"q-{start}-to-{goal}",
            base_problem.edges,
            start,
            goal,
            base_problem.heuristic,
        )
        
        dyn_prop = goal_field.propose_from(query)
        ctl_prop = control.propose(query)
        
        # Charge: dynamics = build_cost / queries + walk_cost
        dyn_total = goal_field.build_node_scans / len(queries) + dyn_prop.equivalent_expansions
        ctl_total = ctl_prop.equivalent_expansions
        
        results["dynamics_eq"] += dyn_total
        results["control_eq"] += ctl_total
        
        if dyn_prop.found_route:
            results["queries_found_dyn"] += 1
            results["dynamics_cost"] += dyn_prop.proposed_cost
        if ctl_prop.found_route:
            results["queries_found_ctl"] += 1
            results["control_cost"] += ctl_prop.proposed_cost
    
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


def run_crossover(seed=461, graphs_per_cell=30):
    """Run crossover experiment across full regime grid.
    
    Grid dimensions:
      - Graph size: [12, 24, 48]
      - Heuristic quality: ["good", "poor"]
      - Reuse count: [1, 5, 20]
      - Dynamics: ["diffusion", "path_integral"]
    
    Total cells: 3 × 2 × 3 × 2 = 36 regime cells
    """
    rng = random.Random(seed)
    
    # Crossover grid
    graph_sizes = [12, 24, 48]
    heuristic_qualities = ["good", "poor"]
    reuse_counts = [1, 5, 20]
    
    # Store results per regime cell
    regime_results = defaultdict(lambda: {
        "net_vs_astar": [],
        "advantage_vs_control": [],
        "route_stretch": [],
    })
    
    # Also collect top-level metrics
    all_net_vs_astar = []
    all_advantage = []
    all_stretch = []
    
    graphs_made = 0
    
    for n, hq, reuse, dyn_name in product(graph_sizes, heuristic_qualities, reuse_counts, DYNAMICS_STRATEGIES):
        if dyn_name == "physarum":
            continue  # skip physarum (no goal field support)
        
        cell_key = f"n{n}_{hq}_q{reuse}_{dyn_name}"
        
        for _ in range(graphs_per_cell):
            # Generate base problem
            base = _random_geometric_problem(rng, n=n, k=4, seed_offset=graphs_made, heuristic_quality=hq)
            
            # Verify A* can solve it
            check = AStarWithGivenHeuristic().propose(base)
            if not check.found_route:
                continue
            
            graphs_made += 1
            
            # Generate queries (different starts to same goal)
            queries = []
            nodes = [node for node in base.nodes if node != base.goal]
            for _ in range(reuse):
                if nodes:
                    start = rng.choice(nodes)
                    queries.append((start, base.goal))
            
            if not queries:
                continue
            
            result = _run_amortized_experiment(base, dyn_name, queries, rng)
            if result is None:
                continue
            
            # Per-query metrics
            dyn_eq_per_q = result["dynamics_eq"] / result["queries_total"]
            ctl_eq_per_q = result["control_eq"] / result["queries_total"]
            
            # net_vs_astar: POSITIVE = dynamics wins
            net_vs_astar = ctl_eq_per_q - dyn_eq_per_q
            advantage = 1.0 if dyn_eq_per_q < ctl_eq_per_q else 0.0
            
            # route_stretch: how much slower is dynamics?
            stretch = 0.0
            if result["queries_found_dyn"] > 0 and result["queries_found_ctl"] > 0:
                dyn_avg = result["dynamics_cost"] / result["queries_found_dyn"]
                ctl_avg = result["control_cost"] / result["queries_found_ctl"]
                stretch = (dyn_avg / ctl_avg) - 1.0 if ctl_avg > 0 else 0.0
            
            regime_results[cell_key]["net_vs_astar"].append(net_vs_astar)
            regime_results[cell_key]["advantage_vs_control"].append(advantage)
            regime_results[cell_key]["route_stretch"].append(stretch)
            
            all_net_vs_astar.append(net_vs_astar)
            all_advantage.append(advantage)
            all_stretch.append(stretch)
    
    # Bootstrap CIs
    bs = random.Random(seed + 1)
    
    # Process each regime cell
    regime_output = {}
    for cell_key, metrics in regime_results.items():
        regime_output[cell_key] = {
            "net_vs_astar": _boot(metrics["net_vs_astar"], bs),
            "advantage_vs_control": _boot(metrics["advantage_vs_control"], bs),
            "route_stretch": _boot(metrics["route_stretch"], bs),
        }
    
    # Top-level metrics
    top_level = {
        "schema_version": "orion-navigation-dynamics-v2",
        "seed": seed,
        "graphs_per_cell": graphs_per_cell,
        "graphs_made": graphs_made,
        "claim_boundary": "PREREGISTERED crossover grid (n × heuristic × reuse × dynamics) on random geometric graphs; honest test of goal-field amortization vs A*; grants no scientific authority",
        "grants_scientific_authority": False,
        "crossover_grid": {
            "graph_sizes": graph_sizes,
            "heuristic_qualities": heuristic_qualities,
            "reuse_counts": reuse_counts,
            "dynamics": [d for d in DYNAMICS_STRATEGIES if d != "physarum"],
        },
        "regime_cells": regime_output,
        "net_vs_astar": _boot(all_net_vs_astar, bs),
        "advantage_vs_control": _boot(all_advantage, bs),
        "route_stretch": _boot(all_stretch, bs),
    }
    
    # Determine terminal status
    net = top_level["net_vs_astar"]
    if net is None:
        status = "CANNOT_CHECK"
    elif net["lo"] > 0:
        status = "SUPPORTED"  # dynamics beats A* with CI excluding 0
    elif net["hi"] < 0:
        status = "NEGATIVE"  # dynamics loses to A* with CI excluding 0
    elif 0 in [net["lo"], net["hi"]]:
        status = "PARTIAL"  # CI includes 0 (inconclusive)
    else:
        status = "CANNOT_CHECK"
    
    top_level["status"] = status
    
    return top_level


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=461)
    ap.add_argument("--graphs-per-cell", type=int, default=30)
    a = ap.parse_args()
    res = run_crossover(seed=a.seed, graphs_per_cell=a.graphs_per_cell)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(res, indent=2))
    print(f"WROTE={RESULT.relative_to(HERE.parents[1])}")
    print(f"\n=== CROSSOVER RESULTS ===")
    print(f"Status: {res['status']}")
    print(f"net_vs_astar: {res['net_vs_astar']}")
    print(f"advantage_vs_control: {res['advantage_vs_control']}")
    print(f"route_stretch: {res['route_stretch']}")
    print(f"\nRegime cells: {len(res['regime_cells'])}")
    print(f"AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
