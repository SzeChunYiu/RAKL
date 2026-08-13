#!/usr/bin/env python3
"""#537 NAVIGATION DYNAMICS SUCCESSOR: amortized/dynamic phase diagram.

PREREGISTRATION (GitHub issue #537): the historical navigation-dynamics study (#519)
returned NEGATIVE -- the diffusion / path-integral dynamics lost to A* on single-shot
and lightly-reused worlds, because their relaxation sweeps are charged honestly (one
sweep = |V| node scans) and A* with a consistent heuristic is near-frugal, AND the
study never built the strongest amortized parent: A* guided by the EXACT reverse-
Dijkstra cost-to-go field. This successor closes both gaps:

  1. It builds the parents the historical study lacked -- exact reverse-Dijkstra
     field (the tightest admissible heuristic), ALT landmarks, and an incrementally
     repaired exact shortest-path tree -- so "A* guided by the exact field" is the
     strongest parent any amortized/dynamic mechanic must beat.
  2. It redesigns the dynamics mechanic as an ADMISSIBLE approximate field (soft-min
     Bellman backups seeded at the trivial lower bound 0, so partial convergence is
     always <= exact) maintained by LOCAL repair under edge updates, guiding A*.

Hypothesis: the exact field strictly dominates the approximate field on TOTAL node
scans in the static regime (cheaper build + tighter heuristic). The only conceivable
win for the approximate field is a dynamic regime with many LOCALIZED updates, where
its capped local repair could beat an exact rebuild -- but the incrementally repaired
EXACT field is also local. This script measures it honestly across a phase diagram
and reports POSITIVE only if the successor beats the strongest applicable parent with
a CI excluding zero and the optimality gate intact.

Cost meter (identical to rakl.navigation_dynamics): one search expansion = one node
scan; one relaxation sweep over |V| nodes = |V| node scans. Field build + every repair
+ every query are charged in this single unit, so no method wins by accounting fiction.
Optimality is a HARD GATE vs the exact shortest path (the oracle): a candidate that
ever returns a suboptimal route cannot win even if it is cheaper.

Result contract: top-level net_vs_strong_parent + net_vs_astar with bootstrap CIs
{mean, lo, hi, n}; status; COMPLETE EFFICIENCY telemetry (sample, seed,
measured_quantity via states_expanded, cost_model/stage_costs block); regime_analysis
for crossover detection (#543). grants_scientific_authority: false everywhere.
Terminal vocabulary: SUPPORTED/PARTIAL/NEGATIVE/CANNOT_CHECK/UNDERPOWERED.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rakl.navigation_dynamics import NavigationProblem, NavigationEdge
from rakl.navigation_successor import (
    ReverseDijkstraField,
    ALTField,
    IncrementalExactField,
    ApproximateIncrementalField,
    build_reverse_dijkstra,
    field_guided_astar,
    oracle_route_cost,
)

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results" / "navigation_dynamics_successor.json"

STRONG_FIELD_PARENTS = ("astar_exact_field", "astar_exact_incremental")
ALL_PARENTS = ("astar", "astar_exact_field", "astar_exact_incremental", "astar_alt")
SUCCESSOR = "coop_field_guided"


# --------------------------------------------------------------------------- #
# geometric graph generator (Euclidean heuristic is consistent -> admissible)
# --------------------------------------------------------------------------- #
def _geometric_graph(rng: random.Random, n: int, k: int):
    """k-nearest-neighbour geometric graph. edge cost = base*(1+r) >= base = Euclidean,
    so the Euclidean distance to goal is a CONSISTENT (hence admissible) heuristic by
    the triangle inequality -- the same 'good' control the historical study used."""
    pts = {f"n{i}": (rng.random(), rng.random()) for i in range(n)}
    names = sorted(pts)

    def dist(a, b):
        return math.hypot(pts[a][0] - pts[b][0], pts[a][1] - pts[b][1])

    edges = []
    for a in names:
        others = sorted(names, key=lambda o: dist(a, o))[1 : k + 1]
        for b in others:
            base = dist(a, b)
            edges.append(NavigationEdge(a, b, base * (1.0 + rng.random())))
    goal = names[-1]
    eucl = {a: dist(a, goal) for a in names}
    # Euclidean base distance per edge: updates are clamped to >= base so the
    # Euclidean heuristic stays ADMISSIBLE (cost >= ||u-v||) under decreases.
    base_of = [dist(e.source, e.target) for e in edges]
    return names, edges, base_of, eucl, goal


def _reachable_start(names, edges, goal, rng, base_costs):
    """Pick a start that can reach the goal (finite oracle)."""
    probe = NavigationProblem("probe", tuple(edges), names[0], goal, {})
    order = list(names)
    rng.shuffle(order)
    for s in order:
        if s == goal:
            continue
        p = NavigationProblem("probe", tuple(edges), s, goal, {})
        if math.isfinite(oracle_route_cost(p)):
            return s
    return names[0]


# --------------------------------------------------------------------------- #
# one workload: build + interleaved (update, query-batch); returns per-method totals
# --------------------------------------------------------------------------- #
def run_workload(seed: int, n: int, q_total: int, u_count: int, locality: str):
    """Run one amortized/dynamic workload; return (stage_costs, oracle_ok, start_reachable).

    stage_costs[method] = {build, updates, queries, total, states_expanded}.
    Every method sees the SAME graph states and the SAME query starts.
    """
    rng = random.Random(seed)
    names, edges, base_of, eucl, goal = _geometric_graph(rng, n, k=3)
    base = list(edges)  # mutable copy; updates perturb entries in place

    def problem_with_start(start):
        return NavigationProblem(f"w{seed}", tuple(base), start, goal, {})

    start = _reachable_start(names, base, goal, rng, base)

    # schedule: distribute q_total queries across u_count+1 rounds; updates between rounds
    rounds = u_count + 1
    per_round = max(1, q_total // rounds)
    # choose update edges: 'local' = a tight cluster of nodes; 'scattered' = random
    hot = set(rng.sample(names, min(4, n)))
    inc_edges = [i for i, e in enumerate(base) if e.source in hot or e.target in hot]

    # ---- prepare field-based objects (built once on the initial graph) ----
    p0 = problem_with_start(start)
    exact_rebuild_field = ReverseDijkstraField(p0)            # rebuilt per update
    exact_inc_field = IncrementalExactField(p0)               # repaired per update
    alt_field = ALTField(p0, n_landmarks=4, rng=random.Random(seed ^ 0xA17))  # rebuilt per update
    apx_field = ApproximateIncrementalField(
        p0, build_sweeps=3, repair_sweeps=2, repair_radius=3, temperature=0.5
    )

    # ---- stage cost accumulators (node scans) ----
    sc = {m: {"build": 0, "updates": 0, "queries": 0, "total": 0} for m in ALL_PARENTS + (SUCCESSOR,)}
    sc["astar"]["build"] = 0
    sc["astar_exact_field"]["build"] = exact_rebuild_field.total_build_scans
    sc["astar_exact_incremental"]["build"] = exact_inc_field.total_build_scans
    sc["astar_alt"]["build"] = alt_field.total_build_scans
    sc[SUCCESSOR]["build"] = apx_field.total_build_scans

    oracle_ok = True
    n_checks = 0

    def do_queries(prob):
        nonlocal oracle_ok, n_checks
        # query starts: spread across nodes for amortization
        starts = [names[(start_idx * 7919) % n] for start_idx in range(per_round)]
        for s in starts:
            if s == goal:
                continue
            qp = NavigationProblem(f"q{seed}", tuple(prob.edges), s, goal, {})
            orc = oracle_route_cost(qp)
            if not math.isfinite(orc):
                continue
            n_checks += 1
            # astar (Euclidean baseline)
            r, c = field_guided_astar(qp, eucl)
            if r is None or abs(qp.validate_route(r) - orc) > 1e-9:
                oracle_ok = False
            sc["astar"]["queries"] += c
            # exact rebuild field (values are exact for current graph only if rebuilt; we
            # rebuild on updates, so between updates the field matches the current graph)
            r, c = field_guided_astar(qp, exact_rebuild_field.values)
            if r is None or abs(qp.validate_route(r) - orc) > 1e-9:
                oracle_ok = False
            sc["astar_exact_field"]["queries"] += c
            # exact incremental field
            r, c = field_guided_astar(qp, exact_inc_field.values)
            if r is None or abs(qp.validate_route(r) - orc) > 1e-9:
                oracle_ok = False
            sc["astar_exact_incremental"]["queries"] += c
            # alt field
            r, c = field_guided_astar(qp, alt_field.values)
            if r is None or abs(qp.validate_route(r) - orc) > 1e-9:
                oracle_ok = False
            sc["astar_alt"]["queries"] += c
            # successor approximate field
            r, c = field_guided_astar(qp, apx_field.values)
            if r is None or abs(qp.validate_route(r) - orc) > 1e-9:
                oracle_ok = False
            sc[SUCCESSOR]["queries"] += c

    # round 0 queries (on initial graph)
    do_queries(p0)

    # interleaved updates + queries
    for u in range(u_count):
        # pick an edge to perturb
        if locality == "local" and inc_edges:
            idx = rng.choice(inc_edges)
        else:
            idx = rng.randrange(len(base))
        e = base[idx]
        factor = 0.5 if (u % 2 == 0) else 2.0  # mixed decrease / increase
        bdist = base_of[idx]
        nc = max(bdist, round(e.cost * factor, 4))  # >= Euclidean base -> Euclidean h admissible
        base[idx] = NavigationEdge(e.source, e.target, nc)
        p_new = problem_with_start(start)

        # astar: pays nothing for updates (re-searches at query time)
        # exact rebuild: rebuild from scratch
        exact_rebuild_field = ReverseDijkstraField(p_new)
        sc["astar_exact_field"]["updates"] += exact_rebuild_field.total_build_scans
        # exact incremental: repair
        exact_inc_field.refresh_problem(p_new)
        sc["astar_exact_incremental"]["updates"] += exact_inc_field.apply_change((base[idx],))
        # alt rebuild
        alt_field = ALTField(p_new, n_landmarks=4, rng=random.Random(seed ^ 0xA17))
        sc["astar_alt"]["updates"] += alt_field.total_build_scans
        # successor local repair
        apx_field.refresh_problem(p_new)
        sc[SUCCESSOR]["updates"] += apx_field.apply_change((base[idx],))

        do_queries(p_new)

    for m in sc:
        sc[m]["total"] = sc[m]["build"] + sc[m]["updates"] + sc[m]["queries"]
        sc[m]["states_expanded"] = sc[m]["total"]
    return sc, oracle_ok, n_checks


# --------------------------------------------------------------------------- #
# bootstrap CI (percentile, B resamples)
# --------------------------------------------------------------------------- #
def _boot(values, B=5000):
    if not values:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    rng = random.Random(12345)
    n = len(values)
    means = []
    for _ in range(B):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * B)]
    hi = means[min(B - 1, int(0.975 * B))]
    return {"mean": sum(values) / n, "lo": lo, "hi": hi, "n": n}


def _ci_excludes_zero(ci):
    return ci["lo"] > 0.0 or ci["hi"] < 0.0


# --------------------------------------------------------------------------- #
# main: phase diagram -> result JSON with COMPLETE telemetry
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=12)
    ap.add_argument("--baseseed", type=int, default=537)
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()

    Ns = (16, 32, 64)
    Qs = (1, 8, 32)
    Us = (0, 4, 16)
    localities = ("scattered", "local")

    pooled_nsp = []   # net vs strongest field parent
    pooled_nastar = []
    cell_records = {}
    oracle_violations = 0
    total_workloads = 0
    graphs_made = 0

    for N in Ns:
        for Q in Qs:
            for U in Us:
                for loc in localities:
                    cell_key = f"N{N}_Q{Q}_U{U}_{loc}"
                    nets_sp = []
                    nets_astar = []
                    for r in range(args.replicates):
                        seed = (args.baseseed * 1000003) ^ (N * 73856093) ^ (Q * 19349663) ^ (U * 83492791) ^ (hash(loc) & 0xFFFF) ^ (r * 2654435761)
                        seed &= 0x7FFFFFFF
                        sc, ok, nchecks = run_workload(seed, N, Q, U, loc)
                        if not ok:
                            oracle_violations += 1
                        total_workloads += 1
                        graphs_made += 1
                        # strongest field parent = cheaper of the two exact-field totals
                        strong_total = min(sc["astar_exact_field"]["total"],
                                           sc["astar_exact_incremental"]["total"])
                        sp = strong_total - sc[SUCCESSOR]["total"]
                        na = sc["astar"]["total"] - sc[SUCCESSOR]["total"]
                        nets_sp.append(sp)
                        nets_astar.append(na)
                        pooled_nsp.append(sp)
                        pooled_nastar.append(na)
                    ci_sp = _boot(nets_sp, args.bootstrap)
                    ci_na = _boot(nets_astar, args.bootstrap)
                    cell_records[cell_key] = {
                        "axes": {"N": N, "Q": Q, "U": U, "locality": loc},
                        "net_vs_strong_parent": ci_sp,
                        "net_vs_astar": ci_na,
                    }

    top_sp = _boot(pooled_nsp, args.bootstrap)
    top_na = _boot(pooled_nastar, args.bootstrap)

    # ---- regime_analysis (#543 crossover): positive vs negative cells ----
    pos_cells = [c["axes"] | {"cell": k} for k, c in cell_records.items()
                 if c["net_vs_strong_parent"]["lo"] > 0.0]
    neg_cells = [c["axes"] | {"cell": k} for k, c in cell_records.items()
                 if c["net_vs_strong_parent"]["hi"] < 0.0]
    pos_vals = [c["net_vs_strong_parent"]["mean"] for c in cell_records.values()
                if c["net_vs_strong_parent"]["lo"] > 0.0]
    neg_vals = [c["net_vs_strong_parent"]["mean"] for c in cell_records.values()
                if c["net_vs_strong_parent"]["hi"] < 0.0]
    pos_ci = _boot(pos_vals, args.bootstrap) if pos_vals else {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    neg_ci = _boot(neg_vals, args.bootstrap) if neg_vals else {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    regime_analysis = {
        "positive_subset": {
            "cells": [{k: v for k, v in c.items() if isinstance(v, (int, float))} for c in pos_cells],
            "net_saving_mean": pos_ci["mean"],
            "net_saving_ci95": [pos_ci["lo"], pos_ci["hi"]],
            "n": pos_ci["n"],
        },
        "negative_subset": {
            "cells": [{k: v for k, v in c.items() if isinstance(v, (int, float))} for c in neg_cells],
            "net_saving_mean": neg_ci["mean"],
            "net_saving_ci95": [neg_ci["lo"], neg_ci["hi"]],
            "n": neg_ci["n"],
        },
    }

    # ---- verdict (honest): POSITIVE only if pooled net > 0 AND CI excludes zero ----
    optimality_gate = (oracle_violations == 0)
    if (top_sp["mean"] > 0 and top_sp["lo"] > 0 and optimality_gate and
            not (pos_cells and neg_cells)):
        status = "SUPPORTED"
    elif pos_cells and neg_cells and optimality_gate:
        # genuine crossover: successor wins some regimes, loses others
        status = "PARTIAL"
    elif optimality_gate and top_sp["mean"] <= 0 and top_sp["hi"] < 0:
        status = "NEGATIVE"
    elif not optimality_gate:
        status = "CANNOT_CHECK"
    else:
        status = "NEGATIVE"

    # ---- representative stage-cost snapshot (median cell) for the cost_model block ----
    # one concrete workload's stage costs, so cost_model is real (not fabricated)
    demo_sc, demo_ok, demo_n = run_workload(args.baseseed, 32, 8, 4, "local")
    cost_model = {
        "meter": "node_scans (1 search expansion = 1 scan; 1 relaxation sweep over |V| = |V| scans)",
        "charged_stages": ["build", "updates", "queries"],
        "sign_convention": "net = parent_total - successor_total; POSITIVE = successor wins",
        "methods": {m: {k: v for k, v in s.items()} for m, s in demo_sc.items()},
    }

    out = {
        "schema_version": "orion-navigation-dynamics-successor-v1",
        "issue": "#537",
        "seed": args.baseseed,
        "replicates_per_cell": args.replicates,
        "bootstrap_samples": args.bootstrap,
        "graphs_made": graphs_made,
        "n": graphs_made,
        "independent_unit": "workload (one graph instance across its full query+update schedule)",
        "measured_quantity": "node_scans (build + updates + queries), reported per-method as states_expanded",
        "claim_boundary": (
            "PREREGISTERED phase diagram (graph_size x query_count x update_count x locality) "
            "on random geometric graphs; honest test of whether an admissible approximate "
            "cost-to-go field, maintained by local repair, beats the strongest amortized "
            "parent (A* guided by the exact reverse-Dijkstra field / its incremental repair) "
            "on TOTAL node scans with all build+update+query costs charged. Grants no "
            "scientific authority."
        ),
        "grants_scientific_authority": False,
        "crossover_grid": {
            "graph_sizes": list(Ns),
            "query_counts": list(Qs),
            "update_counts": list(Us),
            "localities": list(localities),
            "update_type": "mixed (alternating decrease/increase)",
        },
        "methods": {
            "astar": "plain A* with the consistent Euclidean heuristic; no preprocessing (historical STRONG_CONTROL)",
            "astar_exact_field": "A* guided by the EXACT reverse-Dijkstra field; rebuilt from scratch each update",
            "astar_exact_incremental": "A* guided by the exact field maintained by Ramalingam-style incremental repair",
            "astar_alt": "A* guided by the ALT landmark lower bound; rebuilt each update",
            "coop_field_guided": "SUCCESSOR: A* guided by the admissible soft-min approximate field, local repair per update",
        },
        "strongest_parent_rule": "min(astar_exact_field.total, astar_exact_incremental.total) per workload",
        "regime_cells": cell_records,
        "net_vs_strong_parent": top_sp,
        "net_vs_astar": top_na,
        "regime_analysis": regime_analysis,
        "optimality_gate": {
            "passed": optimality_gate,
            "oracle": "exact_shortest_route (unregistered, all-pairs exact)",
            "n_queries_checked": demo_n,
            "n_violations": oracle_violations,
            "note": "every query route cost == oracle to 1e-9; a suboptimal route cannot win",
        },
        "cost_model": cost_model,
        "admissibility_argument": (
            "The approximate field is a soft-min Bellman backup seeded at 0 (a valid lower "
            "bound since true cost >= 0). With V_j <= exact_j for all j, V_i = -T log sum_j "
            "exp(-(L_ij+V_j)/T) <= min_j (L_ij+V_j) <= min_j (L_ij+exact_j) = exact_i, so the "
            "induction holds from the first sweep: EVERY sweep count is admissible, and A* "
            "guided by it stays optimal. Local repair seeds from current admissible values "
            "and only lowers them, so admissibility is preserved under updates."
        ),
        "status": status,
        "telemetry_class": "EFFICIENCY",
    }

    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(out, indent=2))
    print(f"wrote {RESULT}")
    print(f"status={status}  net_vs_strong_parent={top_sp}  net_vs_astar={top_na}")
    print(f"optimality_gate={'PASS' if optimality_gate else 'FAIL'} "
          f"(violations={oracle_violations})  workloads={total_workloads} graphs_made={graphs_made}")
    print(f"positive_cells={len(pos_cells)} negative_cells={len(neg_cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
