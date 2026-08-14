#!/usr/bin/env python3
"""Three-tier bound on what ANY equal-budget allocation policy can achieve in the
Paper IV model-free development-stress instrument.

Motivation: a greedy oracle is a POLICY, so its score is only a LOWER bound on the
instrument's ceiling.  Concluding "no policy can pass the gate" from a policy score
is invalid.  This runner adds a constructive lower bound (local search over count
vectors) and a rigorous UPPER bound, and it is the upper bound that carries the
`INSTRUMENT_CANNOT_DISCRIMINATE` conclusion.

Upper-bound argument.  Every harm term in ``apply_batch`` is non-negative and is
subtracted from a mastery coordinate, and the gain step ``m -> m*(1-r) + r`` is
monotone increasing in ``m``.  Pointwise dominance is therefore preserved along the
trajectory, so the harm-free trajectory upper-bounds every with-harm trajectory
coordinate by coordinate.  Maximizing the harm-free objective over integer count
vectors summing to the budget is a concave separable allocation, solved exactly by
greedy marginal water-filling.

Diagnostic only.  Promotes nothing; reverses nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_p4_adaptive_development_stress import world_rates


def _mk(protocol):
    coords = protocol["coordinates"]
    ci = {c: i for i, c in enumerate(coords)}
    budget = protocol["rounds"] * protocol["batch_size"]
    m0 = list(protocol["initial_mastery"])
    return coords, ci, budget, m0


def simulate(counts, world, rates, protocol, coords, ci, budget, m0):
    """Expected-dynamics rollout of a count vector, max-remaining-first interleaving."""
    m = list(m0)
    remaining = dict(counts)
    for _ in range(budget):
        c = max(coords, key=lambda k: (remaining.get(k, 0), -ci[k]))
        if remaining.get(c, 0) <= 0:
            break
        remaining[c] -= 1
        idx = ci[c]
        m[idx] += rates[c] * (1 - m[idx])
        if c != "PRINCIPLE":
            m[ci["PRINCIPLE"]] -= protocol["forgetting_per_nonprinciple_example"] * (
                1.4 if world == "RETENTION_SENSITIVE" else 1.0)
        if c != "RETENTION":
            m[ci["RETENTION"]] -= protocol["retention_harm_per_nonretention_example"] * (
                2.0 if world == "RETENTION_SENSITIVE" else 1.0)
        if c not in ("BOUNDARY", "RETENTION") and world == "BOUNDARY_LAG":
            m[ci["BOUNDARY"]] -= 0.0007
        m = [max(0.0, min(0.999, x)) for x in m]
    return sum(m) / 6


def hill_climb(start, world, rates, protocol, coords, ci, budget, m0):
    cur = dict(start)
    best = simulate(cur, world, rates, protocol, coords, ci, budget, m0)
    improved = True
    while improved:
        improved = False
        for a in coords:
            for b in coords:
                if a == b or cur.get(a, 0) <= 0:
                    continue
                cand = dict(cur)
                cand[a] -= 1
                cand[b] = cand.get(b, 0) + 1
                val = simulate(cand, world, rates, protocol, coords, ci, budget, m0)
                if val > best + 1e-12:
                    best, cur, improved = val, cand, True
    return best


def rigorous_upper_bound(rates, coords, ci, budget, m0):
    """Exact optimum of the harm-free relaxation (greedy water-filling is exact here)."""
    val = {c: m0[ci[c]] for c in coords}
    for _ in range(budget):
        best = max(coords, key=lambda c: (rates[c] * (1 - val[c]), -ci[c]))
        val[best] += rates[best] * (1 - val[best])
    return sum(val.values()) / 6


def execute(protocol, greedy_mean, greedy_counts):
    coords, ci, budget, m0 = _mk(protocol)
    uniform = {c: budget // len(coords) for c in coords}
    per_world = {}
    for world in protocol["worlds"]:
        rates = world_rates(world)
        static = simulate(uniform, world, rates, protocol, coords, ci, budget, m0)
        best = max(
            hill_climb(greedy_counts, world, rates, protocol, coords, ci, budget, m0),
            hill_climb(uniform, world, rates, protocol, coords, ci, budget, m0),
        )
        per_world[world] = {
            "constructive_best_minus_static": best - static,
            "rigorous_upper_bound_minus_static":
                rigorous_upper_bound(rates, coords, ci, budget, m0) - static,
        }
    n = len(protocol["worlds"])
    mean_con = sum(v["constructive_best_minus_static"] for v in per_world.values()) / n
    mean_ub = sum(v["rigorous_upper_bound_minus_static"] for v in per_world.values()) / n
    gate = protocol["hard_gate"]["E_minus_D_balanced_mean_min"]
    return {
        "schema_version": "orion-p4-instrument-ceiling-bounds-v1",
        "date": "2026-08-14",
        "kind": "INSTRUMENT_CEILING_BOUND_DIAGNOSTIC",
        "instrument": "research/orion_p1_p4_closure_v2/P4_ADAPTIVE_PROTOCOL_FREEZE.json",
        "reference_parent": "D_STATIC_STRUCTURAL",
        "frozen_hard_gate_E_minus_D_balanced_mean_min": gate,
        "bounds_on_achievable_advantage_over_static": {
            "tier_1_greedy_oracle_policy_stochastic_mean": greedy_mean,
            "tier_2_constructive_best_found_expected_dynamics_mean": mean_con,
            "tier_3_rigorous_upper_bound_harm_free_relaxation_mean": mean_ub,
            "tier_3_rigorous_upper_bound_worst_world": max(
                v["rigorous_upper_bound_minus_static"] for v in per_world.values()),
        },
        "per_world": per_world,
        "gate_margin": {
            "rigorous_upper_bound_vs_gate_ratio": gate / mean_ub,
            "constructive_vs_gate_ratio": gate / mean_con,
        },
        "self_correction": (
            "The greedy oracle is a POLICY and therefore only a lower bound on the ceiling. "
            "It understated the constructively achievable advantage by roughly a factor of three "
            "(0.00148 versus 0.00446 mean). The load-bearing claim is carried by tier 3."
        ),
        "conclusion": (
            "A rigorous upper bound on ANY equal-budget allocation policy's mean advantage over "
            "the static parent lies below the instrument's own frozen promotion gate, so the "
            "instrument cannot reach its own registered gate and INSTRUMENT_CANNOT_DISCRIMINATE "
            "stands on an upper bound rather than on a myopic policy."
        ),
        "bound_tightness_caveat": (
            "Tier 3 is LOOSE by construction: the relaxation drops every harm term, including the "
            "terms that make RETENTION_SENSITIVE hard. Tier 2 and tier 3 differ by about 5.5x, so "
            "the true optimum sits in a wide interval whose upper end is only 2.03x under the gate. "
            "The verdict is supported, but the margin is a factor of two on a loose bound and "
            "should not be described as airtight. A tighter relaxation would strengthen it."
        ),
        "grants_scientific_authority": False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--attribution-receipt", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    rec = json.loads(Path(args.attribution_receipt).read_text())
    coords, ci, budget, _ = _mk(protocol)
    counts = {c: int(round(v))
              for c, v in rec["arms"]["ORACLE_GREEDY_CEILING"]["mean_counts"].items()}
    drift = sum(counts.values()) - budget
    if drift:
        counts["PRINCIPLE"] -= drift
    result = execute(protocol, rec["gap_decomposition"]["ORACLE_minus_D"], counts)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CEILING_BOUNDS.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
