#!/usr/bin/env python3
"""Failure-attribution decomposition of the preserved Paper IV adaptive-v1 development negative.

This runner does NOT define new world dynamics.  It imports ``world_rates``,
``apply_batch`` and ``mean_ci`` unchanged from
``run_p4_adaptive_development_stress.py`` so that the frozen parent arms
``D_STATIC_STRUCTURAL`` and ``E_VECTOR_ADAPTIVE`` reproduce exactly and every
contrast is paired against the exact preserved negative.

It is a diagnostic.  It cannot promote a mechanic, cannot emit
``ADAPTIVE_RESIDUAL_SUPPORTED``, and cannot alter any existing freeze or
receipt.  See ``research/paper4_allocator_attribution_v1/ATTRIBUTION_DIAGNOSTIC_PROTOCOL.json``.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from run_p4_adaptive_development_stress import (  # noqa: E402
    apply_batch,
    mean_ci,
    select_batch as parent_select_batch,
    world_rates,
)

NON_PRINCIPLE = ["COMPOSITION", "BOUNDARY", "REPRESENTATION", "TRANSFER", "RETENTION"]
PRINCIPLE_CAP = 8  # exactly D_STATIC_STRUCTURAL's per-coordinate share
DECONCENTRATION_SHARES = (2, 2, 1, 1, 1)  # sums to the 7 non-floor slots

ARMS = (
    "D_STATIC_STRUCTURAL",
    "E_VECTOR_ADAPTIVE",
    "X1_GUARDRAIL_AS_CONSTRAINT",
    "X2_DECONCENTRATE",
    "X3_BOTH_LEVERS",
    "ORACLE_GREEDY_CEILING",
)


def _argmin_non_principle(m, ci):
    return min(NON_PRINCIPLE, key=lambda c: (m[ci[c]], ci[c]))


def _apply_principle_cap(batch, m, ci, principle_used):
    """Treat PRINCIPLE as a hard constraint rather than a budget-consuming target."""
    out = []
    used = principle_used
    for slot in batch:
        if slot == "PRINCIPLE" and used >= PRINCIPLE_CAP:
            out.append(_argmin_non_principle(m, ci))
        else:
            if slot == "PRINCIPLE":
                used += 1
            out.append(slot)
    return out


def _v1_target(m, ci):
    if m[ci["RETENTION"]] < 0.80:
        return "RETENTION", True
    if m[ci["PRINCIPLE"]] < 0.90:
        return "PRINCIPLE", True
    return _argmin_non_principle(m, ci), False


def _deconcentrated_batch(m, ci):
    batch = ["PRINCIPLE"]
    target, is_guardrail_repair = _v1_target(m, ci)
    if is_guardrail_repair:
        # Guard-rail repair keeps v1 semantics exactly; only the ordinary
        # structural-target path is deconcentrated.
        batch += [target] * 7
        return batch
    order = sorted(NON_PRINCIPLE, key=lambda c: (m[ci[c]], ci[c]))
    for coord, share in zip(order, DECONCENTRATION_SHARES):
        batch += [coord] * share
    return batch


def _oracle_expected_delta(coord, m, rates, world, protocol, ci):
    """Exact expected immediate change in balanced_mastery from one example."""
    idx = ci[coord]
    delta = rates[coord] * (1 - m[idx])
    if coord != "PRINCIPLE":
        delta -= protocol["forgetting_per_nonprinciple_example"] * (
            1.4 if world == "RETENTION_SENSITIVE" else 1.0
        )
    if coord != "RETENTION":
        delta -= protocol["retention_harm_per_nonretention_example"] * (
            2.0 if world == "RETENTION_SENSITIVE" else 1.0
        )
    if coord not in ("BOUNDARY", "RETENTION") and world == "BOUNDARY_LAG":
        delta -= 0.0007
    return delta


def run_arm(arm, m0, rates, world, rng, coords, ci, protocol):
    m = list(m0)
    counts = Counter()

    if arm == "ORACLE_GREEDY_CEILING":
        for _ in range(protocol["rounds"] * protocol["batch_size"]):
            best = max(
                coords,
                key=lambda c: (_oracle_expected_delta(c, m, rates, world, protocol, ci), -ci[c]),
            )
            counts[best] += 1
            m = apply_batch(m, [best], rates, world, rng, protocol, ci)
        return m, counts

    principle_used = 0
    for rd in range(protocol["rounds"]):
        if arm in ("D_STATIC_STRUCTURAL", "E_VECTOR_ADAPTIVE"):
            batch = parent_select_batch(arm, m, rd, rng, coords, ci)
        elif arm == "X1_GUARDRAIL_AS_CONSTRAINT":
            batch = _apply_principle_cap(
                parent_select_batch("E_VECTOR_ADAPTIVE", m, rd, rng, coords, ci),
                m,
                ci,
                principle_used,
            )
        elif arm == "X2_DECONCENTRATE":
            batch = _deconcentrated_batch(m, ci)
        elif arm == "X3_BOTH_LEVERS":
            batch = _apply_principle_cap(_deconcentrated_batch(m, ci), m, ci, principle_used)
        else:
            raise KeyError(arm)
        principle_used += sum(1 for c in batch if c == "PRINCIPLE")
        counts.update(batch)
        m = apply_batch(m, batch, rates, world, rng, protocol, ci)
    return m, counts


def execute(protocol):
    coords = protocol["coordinates"]
    ci = {c: i for i, c in enumerate(coords)}
    records = []
    for world_idx, world in enumerate(protocol["worlds"]):
        rates = world_rates(world)
        for rep in range(protocol["replicates_per_world"]):
            for arm_idx, arm in enumerate(ARMS):
                # D and E must consume the identical rng stream as the parent
                # runner, whose arm order is list(protocol["arms"]).
                parent_arms = list(protocol["arms"])
                stream_idx = parent_arms.index(arm) if arm in parent_arms else 100 + arm_idx
                rng = random.Random(
                    protocol["seed"] + world_idx * 100000 + rep * 101 + stream_idx * 10000000
                )
                irng = random.Random(protocol["seed"] + world_idx * 100000 + rep * 101)
                m0 = [
                    max(0, min(.99, x + (irng.random() - .5) * 0.02))
                    for x in protocol["initial_mastery"]
                ]
                m, counts = run_arm(arm, m0, rates, world, rng, coords, ci, protocol)
                records.append(
                    {
                        "world": world,
                        "rep": rep,
                        "arm": arm,
                        "mastery": dict(zip(coords, m)),
                        "balanced_mastery": sum(m) / 6,
                        "hard_safety_min": min(
                            m[ci["PRINCIPLE"]], m[ci["BOUNDARY"]], m[ci["RETENTION"]]
                        ),
                        "counts": dict(counts),
                        "examples": sum(counts.values()),
                    }
                )

    by = {(r["world"], r["rep"], r["arm"]): r for r in records}

    def diffs(a, b, metric):
        return [
            by[(w, rep, a)][metric] - by[(w, rep, b)][metric]
            for w in protocol["worlds"]
            for rep in range(protocol["replicates_per_world"])
        ]

    summary = {}
    for arm in ARMS:
        rs = [r for r in records if r["arm"] == arm]
        entry = {
            "balanced_mastery_mean": statistics.mean(r["balanced_mastery"] for r in rs),
            "hard_safety_min_mean": statistics.mean(r["hard_safety_min"] for r in rs),
            "examples_mean": statistics.mean(r["examples"] for r in rs),
            "mean_counts": {
                c: statistics.mean(r["counts"].get(c, 0) for r in rs) for c in coords
            },
        }
        if arm != "D_STATIC_STRUCTURAL":
            mean_b, ci_b = mean_ci(diffs(arm, "D_STATIC_STRUCTURAL", "balanced_mastery"))
            mean_s, ci_s = mean_ci(diffs(arm, "D_STATIC_STRUCTURAL", "hard_safety_min"))
            entry["minus_D_balanced_mastery"] = {"mean": mean_b, "bootstrap_95ci": ci_b}
            entry["minus_D_hard_safety_min"] = {"mean": mean_s, "bootstrap_95ci": ci_s}
        summary[arm] = entry

    e_gap = summary["E_VECTOR_ADAPTIVE"]["minus_D_balanced_mastery"]["mean"]
    x1_gap = summary["X1_GUARDRAIL_AS_CONSTRAINT"]["minus_D_balanced_mastery"]["mean"]
    x2_gap = summary["X2_DECONCENTRATE"]["minus_D_balanced_mastery"]["mean"]
    oracle_gap = summary["ORACLE_GREEDY_CEILING"]["minus_D_balanced_mastery"]["mean"]

    e_counts_by_world = {}
    for w in protocol["worlds"]:
        rs = [r for r in records if r["arm"] == "E_VECTOR_ADAPTIVE" and r["world"] == w]
        e_counts_by_world[w] = {
            c: statistics.mean(r["counts"].get(c, 0) for r in rs) for c in coords
        }
    signatures = Counter(
        json.dumps({k: round(v, 6) for k, v in row.items()}, sort_keys=True)
        for row in e_counts_by_world.values()
    )
    max_identical_worlds = max(signatures.values())

    p1 = (x1_gap - e_gap) >= 0.010
    p2 = abs(x2_gap - e_gap) < 0.005
    p3 = oracle_gap < 0.05
    p4 = max_identical_worlds >= 5 and abs(
        summary["E_VECTOR_ADAPTIVE"]["mean_counts"]["PRINCIPLE"] - 13
    ) < 1e-9

    if p1 and p2:
        attribution = "ATTRIBUTION_GUARDRAIL_BUDGET_CAPTURE"
    elif (not p1) and (not p2):
        attribution = "ATTRIBUTION_CONCENTRATION"
    else:
        attribution = "ATTRIBUTION_MIXED"

    result = {
        "schema_version": "orion-p4-allocator-attribution-diagnostic-result-v1",
        "date": "2026-08-14",
        "kind": "FAILURE_ATTRIBUTION_DIAGNOSTIC",
        "protocol": "research/paper4_allocator_attribution_v1/ATTRIBUTION_DIAGNOSTIC_PROTOCOL.json",
        "n_world_replicates": len(protocol["worlds"]) * protocol["replicates_per_world"],
        "arms": summary,
        "gap_decomposition": {
            "E_minus_D": e_gap,
            "X1_minus_D": x1_gap,
            "X2_minus_D": x2_gap,
            "X3_minus_D": summary["X3_BOTH_LEVERS"]["minus_D_balanced_mastery"]["mean"],
            "ORACLE_minus_D": oracle_gap,
            "budget_capture_lever_effect": x1_gap - e_gap,
            "concentration_lever_effect": x2_gap - e_gap,
            "fraction_of_gap_closed_by_budget_capture_lever": (x1_gap - e_gap) / abs(e_gap),
            "fraction_of_gap_closed_by_concentration_lever": (x2_gap - e_gap) / abs(e_gap),
        },
        "E_realized_counts_by_world": e_counts_by_world,
        "predictions": {
            "P1_budget_capture_is_dominant": p1,
            "P2_concentration_is_not_dominant": p2,
            "P3_instrument_ceiling_below_its_own_gate": p3,
            "P4_world_invariant_allocation": p4,
        },
        "attribution_terminal": attribution,
        "instrument_terminal": (
            "INSTRUMENT_CANNOT_DISCRIMINATE" if p3 else "INSTRUMENT_CAN_DISCRIMINATE"
        ),
        "frozen_parent_hard_gate_E_minus_D_min": 0.05,
        "grants_scientific_authority": False,
        "can_promote_a_mechanic": False,
        "changes_7b_phase2_evaluator": False,
        "reverses_parent_negative": False,
    }
    return records, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    records, result = execute(protocol)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "ATTRIBUTION_WORLD_RESULTS.jsonl").open("w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    (out / "ATTRIBUTION_RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["gap_decomposition"], indent=2))
    print(json.dumps(result["predictions"], indent=2))
    print(result["attribution_terminal"], "/", result["instrument_terminal"])


if __name__ == "__main__":
    main()
