#!/usr/bin/env python3
"""Six-family cross-family objective transfer sign test.

Computes an honest sign test comparing structurally-informed transfer
(full applicability contract) against a generic no-transfer baseline
(mechanism-only projection).

The six families are: flow, logic, units, state (frozen four) + sched, stat (new).
Each family contributes one sign: +1 if structural transfer reduces
false-accept rate on that family's invalid items.

Output: research/six_family_extension_v1/results/six_family.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import rakl.objective_transfer_benchmark_v2 as V
from rakl.objective_transfer_benchmark_v2 import Decision

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SEED = 20260813
N_PER_CELL = 6


def false_accept_rate(predictions: dict[str, Decision], invalid_ids: list[str]) -> float:
    """False-accept rate: P(predict=ACCEPT | gold=REJECT)."""
    if not invalid_ids:
        return 0.0
    return sum(predictions[i] == Decision.ACCEPT for i in invalid_ids) / len(invalid_ids)


def exact_two_sided_sign_test(n_positive: int, n_negative: int) -> float:
    """Exact two-sided binomial sign test. Ties carry no information."""
    n = n_positive + n_negative
    if n == 0:
        return 1.0
    k = max(n_positive, n_negative)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def run_six_family_sign_test() -> dict:
    """Run the six-family cross-family transfer sign test.
    
    Returns a dict with the sign test results and per-family breakdown.
    """
    # Generate tasks
    tasks = V.generate(seed=SEED, n_per_cell=N_PER_CELL, include_controls=True)
    gold = {t.item_id: V.verify(t).decision for t in tasks}

    # Compute deterministic predictions
    # - mechanism_predict: generic baseline (no obligation structure)
    # - extract: structurally-informed transfer (full contract)
    mechanism = {t.item_id: V.mechanism_predict(t) for t in tasks}
    structural = {t.item_id: V.extract(t).decision for t in tasks}

    # Per-family analysis
    per_family = {}
    signs_positive = {}  # per-family sign for output

    for fam in V.FAMILIES:
        fam_tasks = [t for t in tasks if t.family == fam]
        invalid = [t.item_id for t in fam_tasks if gold[t.item_id] == Decision.REJECT]

        if not invalid:
            # No invalid items for this family - skip
            continue

        mech_fa = false_accept_rate(mechanism, invalid)
        struct_fa = false_accept_rate(structural, invalid)
        delta = mech_fa - struct_fa  # positive = structural reduces false accept

        sign = 1 if delta > 0 else (-1 if delta < 0 else 0)

        per_family[fam] = {
            "n_instances": len(fam_tasks),
            "n_invalid": len(invalid),
            "mechanism_fa": mech_fa,
            "structural_fa": struct_fa,
            "advantage": delta,  # reduction in false-accept rate
            "positive": sign > 0
        }
        signs_positive[fam] = sign

    # Count signs
    pos = sum(1 for s in signs_positive.values() if s > 0)
    neg = sum(1 for s in signs_positive.values() if s < 0)
    ties = sum(1 for s in signs_positive.values() if s == 0)

    # Exact two-sided sign test
    sign_test_p = exact_two_sided_sign_test(pos, neg)

    return {
        "sign_test_p": sign_test_p,
        "all_six_positive": pos == 6,
        "n_positive": pos,
        "n_negative": neg,
        "n_tied": ties,
        "signs_positive": signs_positive,
        "per_family": per_family,
        "grants_scientific_authority": False,
        "status": "DEVELOPMENT_KNOWN_WORLD_SIX_FAMILY_SIGN_INSTRUMENT_ONLY"
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    result = run_six_family_sign_test()
    output_path = RESULTS / "six_family.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wrote {output_path}")
    print(json.dumps({
        "n_positive": result["n_positive"],
        "sign_test_p": result["sign_test_p"],
        "all_six_positive": result["all_six_positive"]
    }, indent=2))


if __name__ == "__main__":
    main()
