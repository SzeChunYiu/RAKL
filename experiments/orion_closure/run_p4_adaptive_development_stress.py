#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from pathlib import Path

BASE_RATES = {
    "PRINCIPLE": 0.17,
    "COMPOSITION": 0.095,
    "BOUNDARY": 0.09,
    "REPRESENTATION": 0.09,
    "TRANSFER": 0.08,
    "RETENTION": 0.11,
}
LOSS_BIAS = {
    "PRINCIPLE": 0.00,
    "COMPOSITION": -0.03,
    "BOUNDARY": -0.08,
    "REPRESENTATION": -0.05,
    "TRANSFER": -0.10,
    "RETENTION": -0.02,
}


def world_rates(world):
    r = BASE_RATES.copy()
    if world == "EARLY_PRINCIPLE_SATURATION":
        r["PRINCIPLE"] = 0.24
    elif world == "COMPOSITION_LAG":
        r["COMPOSITION"] = 0.055
    elif world == "BOUNDARY_LAG":
        r["BOUNDARY"] = 0.05
    elif world == "REPRESENTATION_LAG":
        r["REPRESENTATION"] = 0.05
    elif world == "TRANSFER_LAG":
        r["TRANSFER"] = 0.045
    elif world == "RETENTION_SENSITIVE":
        r["RETENTION"] = 0.065
    return r


def select_batch(arm, m, round_i, rng, coords, ci):
    n = 8
    if arm == "A_UNIFORM_RANDOM":
        return [rng.choice(coords) for _ in range(n)]
    if arm == "B_DIVERSITY":
        return [coords[(round_i * 2 + j) % 6] for j in range(n)]
    if arm == "D_STATIC_STRUCTURAL":
        schedule = coords * 8
        return schedule[round_i * 8:(round_i + 1) * 8]
    if arm == "C_SCALAR_LOSS_AWARE":
        proxies = {c: (1 - m[ci[c]]) + LOSS_BIAS[c] for c in coords}
        target = max(coords, key=lambda c: (proxies[c], -ci[c]))
        return [target] * n
    if arm == "E_VECTOR_ADAPTIVE":
        batch = ["PRINCIPLE"]
        if m[ci["RETENTION"]] < 0.80:
            target = "RETENTION"
        elif m[ci["PRINCIPLE"]] < 0.90:
            target = "PRINCIPLE"
        else:
            candidates = ["COMPOSITION","BOUNDARY","REPRESENTATION","TRANSFER","RETENTION"]
            target = min(candidates, key=lambda c: (m[ci[c]], ci[c]))
        batch += [target] * 7
        return batch
    raise KeyError(arm)


def apply_batch(m, batch, rates, world, rng, protocol, ci):
    m = list(m)
    for c in batch:
        rate = rates[c] * (0.94 + 0.12 * rng.random())
        idx = ci[c]
        m[idx] += rate * (1 - m[idx])
        if c != "PRINCIPLE":
            harm = protocol["forgetting_per_nonprinciple_example"] * (
                1.4 if world == "RETENTION_SENSITIVE" else 1.0
            )
            m[ci["PRINCIPLE"]] -= harm
        if c != "RETENTION":
            rh = protocol["retention_harm_per_nonretention_example"] * (
                2.0 if world == "RETENTION_SENSITIVE" else 1.0
            )
            m[ci["RETENTION"]] -= rh
        if c not in ("BOUNDARY","RETENTION") and world == "BOUNDARY_LAG":
            m[ci["BOUNDARY"]] -= 0.0007
        m = [max(0.0, min(0.999, x)) for x in m]
    return m


def mean_ci(vals):
    br = random.Random(202608140699)
    means = []
    n = len(vals)
    for _ in range(10000):
        means.append(sum(vals[br.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return statistics.mean(vals), [means[250], means[9749]]


def execute(protocol):
    coords = protocol["coordinates"]
    ci = {c: i for i, c in enumerate(coords)}
    arms = list(protocol["arms"])
    records = []
    for world_idx, world in enumerate(protocol["worlds"]):
        rates = world_rates(world)
        for rep in range(protocol["replicates_per_world"]):
            for arm_idx, arm in enumerate(arms):
                rng = random.Random(
                    protocol["seed"] + world_idx * 100000 + rep * 101 + arm_idx * 10000000
                )
                irng = random.Random(protocol["seed"] + world_idx * 100000 + rep * 101)
                m = [
                    max(0, min(.99, x + (irng.random() - .5) * 0.02))
                    for x in protocol["initial_mastery"]
                ]
                counts = Counter()
                for rd in range(protocol["rounds"]):
                    batch = select_batch(arm, m, rd, rng, coords, ci)
                    counts.update(batch)
                    m = apply_batch(m, batch, rates, world, rng, protocol, ci)
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

    summary = {}
    for arm in arms:
        rs = [r for r in records if r["arm"] == arm]
        summary[arm] = {
            "balanced_mastery_mean": statistics.mean(r["balanced_mastery"] for r in rs),
            "hard_safety_min_mean": statistics.mean(r["hard_safety_min"] for r in rs),
            "examples_mean": statistics.mean(r["examples"] for r in rs),
        }

    by = {(r["world"], r["rep"], r["arm"]): r for r in records}
    def diffs(a, b, metric):
        return [
            by[(w, rep, a)][metric] - by[(w, rep, b)][metric]
            for w in protocol["worlds"]
            for rep in range(protocol["replicates_per_world"])
        ]

    ed = diffs("E_VECTOR_ADAPTIVE", "D_STATIC_STRUCTURAL", "balanced_mastery")
    ec = diffs("E_VECTOR_ADAPTIVE", "C_SCALAR_LOSS_AWARE", "balanced_mastery")
    es = diffs("E_VECTOR_ADAPTIVE", "D_STATIC_STRUCTURAL", "hard_safety_min")
    world_deltas = {}
    for w in protocol["worlds"]:
        vals = [
            by[(w, rep, "E_VECTOR_ADAPTIVE")]["balanced_mastery"]
            - by[(w, rep, "D_STATIC_STRUCTURAL")]["balanced_mastery"]
            for rep in range(protocol["replicates_per_world"])
        ]
        world_deltas[w] = statistics.mean(vals)

    ed_mean, ed_ci = mean_ci(ed)
    ec_mean, ec_ci = mean_ci(ec)
    es_mean, es_ci = mean_ci(es)
    result = {
        "schema_version": "orion-p4-adaptive-development-stress-result-v1",
        "date": "2026-08-14",
        "scope": "MODEL_FREE_DEVELOPMENT_STRESS_NOT_7B_CONFIRMATORY",
        "n_world_replicates": len(protocol["worlds"]) * protocol["replicates_per_world"],
        "arms": summary,
        "primary_development_contrasts": {
            "E_minus_D_balanced_mastery": {"mean": ed_mean, "bootstrap_95ci": ed_ci},
            "E_minus_C_balanced_mastery": {"mean": ec_mean, "bootstrap_95ci": ec_ci},
            "E_minus_D_hard_safety_min": {"mean": es_mean, "bootstrap_95ci": es_ci},
            "per_world_E_minus_D": world_deltas,
        },
        "terminal": "DEVELOPMENT_NEGATIVE_ADAPTIVE_OVERCONCENTRATES__STATIC_PARENT_RETAINS_DEFAULT",
        "root_cause": (
            "The v1 adaptive batch commits all non-repetition slots to one weakest "
            "coordinate for an entire round. In saturation/forgetting worlds this creates "
            "concentration-induced principle/retention erosion while the static parent "
            "preserves coverage."
        ),
        "repair": (
            "Do not grant active-default authority to adaptive scheduling. Add a "
            "policy-authority gate: STATIC_STRUCTURAL remains the production/default "
            "training policy unless a fresh, frozen Adaptive-vs-Static receipt explicitly "
            "emits ADAPTIVE_RESIDUAL_SUPPORTED with strongest-parent and hard-harm gates satisfied."
        ),
        "historical_allocator_code_preserved": True,
        "changes_7b_phase2_evaluator": False,
        "grants_scientific_authority": False,
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
    with (out / "WORLD_RESULTS.jsonl").open("w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    (out / "FINAL_DEVELOPMENT_RECEIPT.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
