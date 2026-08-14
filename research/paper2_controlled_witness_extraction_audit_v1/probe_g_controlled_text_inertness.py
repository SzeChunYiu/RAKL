#!/usr/bin/env python3
"""Probe G applied to the controlled-witness-extraction instrument.

AUXILIARY_DIAGNOSTIC_ONLY. Not part of the frozen registration of
`research/paper2_controlled_witness_extraction_v1/`. Modifies nothing frozen.

`research/paper2_controlled_witness_extraction_v1/FINAL_RECEIPT.json` reports
`full_controlled_extractor.exact_decision = 1.0` under the terminal
`PROMOTE_CONDITIONALLY_CONTROLLED_TEXT_STRUCTURAL_WITNESS_EXTRACTION`, scoped
`CONTROLLED_SCIENTIFIC_PROSE_OVER_EXISTING_SIX_EXACT_VERIFIER_FAMILIES`.

Probe G (already decisive against the six-family robustness packet) asks the
same question here: does the candidate-visible *text* carry any of the signal
that the reported score measures?

Four registered measurements, each falsifiable:

  T1 text inertness   — replace every `source_text` / `target_text` with noise
                        before rendering; recompute gold and the full arm. If
                        both are unchanged the natural-language surface is inert.
  T2 round-trip       — is `extract_controlled_task(render_controlled_task(t))`
                        byte-identical to `t.public`? If yes, the "extraction"
                        step is a serialization inverse, and `exact_decision`
                        is entailed by parse success rather than measured.
  T3 clean baselines  — always_reject / always_accept / always_cannot_check on
                        the same items (selectivity is not edge).
  T4 shuffle null     — equal-n null pairing each item's text surface with a
                        different item's gold, destroying only the
                        text<->answer binding.

T1 and T2 are two-sided: this probe reports NOT_INERT / NOT_A_ROUND_TRIP just
as readily as the reverse, and the outcome is decided by execution.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import replace
from pathlib import Path

from rakl.controlled_witness_extraction import (
    controlled_span_manifest,
    extract_controlled_task,
    render_controlled_task,
)
from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_benchmark_v2 import generate, verify

HERE = Path(__file__).resolve().parent
PROTOCOL = (
    HERE.parent / "paper2_controlled_witness_extraction_v1" / "PROTOCOL.json"
)

NOISE_WORDS = ("zqx", "vpl", "mtr", "kbd", "wfn", "hgs", "yjc", "roa", "ludo", "esk")


def _noise(rng: random.Random) -> str:
    return " ".join(rng.choice(NOISE_WORDS) for _ in range(8))


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _predict_from_text(task, variant: int) -> Decision:
    """Byte-for-byte the arm used by experiments/paper2/run_controlled_witness_extraction_v1.py."""
    text = render_controlled_task(task, variant=variant)
    expected = dict(controlled_span_manifest(text))
    parsed = extract_controlled_task(text, expected_span_sha256=expected)
    if not parsed.complete or parsed.task is None:
        return Decision.CANNOT_CHECK
    try:
        return verify(parsed.task).decision
    except (KeyError, TypeError, ValueError):
        return Decision.CANNOT_CHECK


def _gold(task) -> Decision:
    try:
        return verify(task).decision
    except (KeyError, TypeError, ValueError):
        return Decision.CANNOT_CHECK


def _score(golds, preds) -> dict[str, float]:
    n = len(golds)
    exact = sum(g is p for g, p in zip(golds, preds)) / n
    valid = [i for i, g in enumerate(golds) if g is Decision.ACCEPT]
    invalid = [i for i, g in enumerate(golds) if g is Decision.REJECT]
    unknown = [i for i, g in enumerate(golds) if g is Decision.CANNOT_CHECK]
    return {
        "exact_decision": exact,
        "valid_accept": (
            sum(preds[i] is Decision.ACCEPT for i in valid) / len(valid) if valid else float("nan")
        ),
        "invalid_false_accept": (
            sum(preds[i] is Decision.ACCEPT for i in invalid) / len(invalid)
            if invalid
            else float("nan")
        ),
        "cannot_check_recall": (
            sum(preds[i] is Decision.CANNOT_CHECK for i in unknown) / len(unknown)
            if unknown
            else float("nan")
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "results"))
    ap.add_argument("--null-reps", type=int, default=200)
    args = ap.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    protocol = json.loads(PROTOCOL.read_text())
    seed = int(protocol["fresh_seed"])
    n_per_cell = int(protocol["n_per_cell"])
    variants = int(protocol["text_variants_per_case"])

    base_tasks = generate(seed, n_per_cell)
    rng = random.Random(20260814)

    # ---- T1: text inertness -------------------------------------------------
    scrambled = [
        replace(t, source_text=_noise(rng), target_text=_noise(rng)) for t in base_tasks
    ]
    gold_same = sum(_gold(a) is _gold(b) for a, b in zip(base_tasks, scrambled))

    arm_same = 0
    arm_total = 0
    for variant in range(variants):
        for a, b in zip(base_tasks, scrambled):
            arm_same += _predict_from_text(a, variant) is _predict_from_text(b, variant)
            arm_total += 1

    # Does the rendered surface actually change when the text is scrambled?
    # (Guards against "unchanged because the scramble never reached the text".)
    surface_changed = sum(
        render_controlled_task(a, variant=0) != render_controlled_task(b, variant=0)
        for a, b in zip(base_tasks, scrambled)
    )

    # ---- T2: is the extractor a serialization inverse? ----------------------
    roundtrip_identical = 0
    parse_complete = 0
    rt_total = 0
    for variant in range(variants):
        for t in base_tasks:
            text = render_controlled_task(t, variant=variant)
            expected = dict(controlled_span_manifest(text))
            parsed = extract_controlled_task(text, expected_span_sha256=expected)
            rt_total += 1
            if parsed.complete and parsed.task is not None:
                parse_complete += 1
                if _canon(parsed.task.public) == _canon(t.public):
                    roundtrip_identical += 1

    # ---- headline arm reproduction -----------------------------------------
    golds: list[Decision] = []
    preds: list[Decision] = []
    for variant in range(variants):
        for t in base_tasks:
            golds.append(_gold(t))
            preds.append(_predict_from_text(t, variant))
    full_arm = _score(golds, preds)

    # ---- T3: clean trivial baselines ---------------------------------------
    baselines = {
        "always_reject": [Decision.REJECT] * len(golds),
        "always_accept": [Decision.ACCEPT] * len(golds),
        "always_cannot_check": [Decision.CANNOT_CHECK] * len(golds),
    }
    baseline_scores = {name: _score(golds, arm) for name, arm in baselines.items()}

    # ---- T4: shuffle equal-n null ------------------------------------------
    # Destroy only the text<->answer binding: score each item's prediction
    # against a permuted gold vector of the same marginal distribution.
    null_rng = random.Random(4242)
    null_exact: list[float] = []
    for _ in range(args.null_reps):
        permuted = golds[:]
        null_rng.shuffle(permuted)
        null_exact.append(sum(g is p for g, p in zip(permuted, preds)) / len(preds))
    null_exact.sort()
    lo = null_exact[int(0.025 * len(null_exact))]
    hi = null_exact[min(len(null_exact) - 1, int(0.975 * len(null_exact)))]
    null_mean = sum(null_exact) / len(null_exact)

    text_is_inert = gold_same == len(base_tasks) and arm_same == arm_total
    is_round_trip = roundtrip_identical == rt_total

    report = {
        "schema": "paper2-controlled-witness-audit-probe-g-v1",
        "status": "AUXILIARY_DIAGNOSTIC_ONLY__NOT_PART_OF_FROZEN_REGISTRATION",
        "grants_scientific_authority": False,
        "subject": {
            "protocol": str(PROTOCOL.relative_to(HERE.parents[1])),
            "fresh_seed": seed,
            "n_per_cell": n_per_cell,
            "text_variants_per_case": variants,
            "n_base_tasks": len(base_tasks),
            "n_text_surfaces": rt_total,
        },
        "gold_counts": dict(Counter(g.value for g in golds)),
        "reproduced_full_arm": full_arm,
        "t1_text_inertness": {
            "rendered_surface_changed_by_scramble": f"{surface_changed}/{len(base_tasks)}",
            "gold_unchanged_after_text_scramble": f"{gold_same}/{len(base_tasks)}",
            "full_arm_unchanged_after_text_scramble": f"{arm_same}/{arm_total}",
            "natural_language_surface_is_inert": text_is_inert,
        },
        "t2_serialization_inverse": {
            "parse_complete": f"{parse_complete}/{rt_total}",
            "public_recovered_byte_identical": f"{roundtrip_identical}/{rt_total}",
            "extractor_is_serialization_inverse": is_round_trip,
        },
        "t3_clean_trivial_baselines": baseline_scores,
        "t4_shuffle_equal_n_null": {
            "reps": args.null_reps,
            "null_mean_exact": null_mean,
            "null_95": [lo, hi],
            "observed_exact": full_arm["exact_decision"],
        },
        "interpretation": (
            "If T1 shows gold and the full arm unchanged under text scramble while the "
            "rendered surface did change, the candidate-visible natural-language surface "
            "carries none of the measured signal. If T2 shows task.public recovered "
            "byte-identically, the 'extraction' step is the inverse of the renderer's "
            "json.dumps, so exact_decision=1.0 is entailed by parse success and is a "
            "measure of serialization fidelity, not of structural witness extraction "
            "from prose. The registered mutation panel (drop_semantic_field x10) remains "
            "a valid test of fail-closed parser behaviour under field omission; it is not "
            "a test of extraction."
        ),
    }

    path = outdir / "PROBE_G_CONTROLLED_TEXT_INERTNESS.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("t1_text_inertness", "t2_serialization_inverse")}, indent=2))
    print(json.dumps(report["t4_shuffle_equal_n_null"], indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
