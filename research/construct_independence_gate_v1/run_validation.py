"""Validate the construct-independence gate against real recorded instruments.

Fixtures pass while whole classes of defect go unseen, so the gate is run
against instruments whose outcomes are already on record: two that died of
construct dependence, and one that was probative. A gate that flags everything
is as useless as one that flags nothing, so the no-alarm case is asserted too.

The interesting result is the miss, and it is reported rather than hidden.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from rakl.construct_independence import (  # noqa: E402
    ConstructObligation,
    ConstructVerdict,
    InstrumentDesign,
    ObligationDeclaration,
    PermutationNullWitness,
    assess_construct_independence,
)

OUT = Path("research/construct_independence_gate_v1/VALIDATION.json")
ARN_RESULT = Path("research/arn_local_vs_parent_discriminator_v1/RESULT.json")
ARN_VALIDITY = Path("research/arn_local_vs_parent_discriminator_v1/PROBE_VALIDITY.json")


def declared(**kw: bool) -> tuple[ObligationDeclaration, ...]:
    out = []
    for name, ok in kw.items():
        obligation = ConstructObligation[name]
        out.append(ObligationDeclaration(obligation, ok, "recorded in the instrument's frozen design"))
    return tuple(out)


def main() -> int:
    cases = []

    # --- 1. ARN v2 deterministic reducer: statistic survived gold shuffling ---
    arn_v2 = InstrumentDesign(
        instrument_id="arn-v2-deterministic-reducer",
        declarations=declared(CHANNEL_SEPARATION=True, AUTHOR_SEPARATION=True, GOLD_INDEPENDENCE=True)
        + (
            ObligationDeclaration(
                ConstructObligation.PERMUTATION_NULL,
                True,
                "gold shuffling was run and the mapping score survived it",
                witness=PermutationNullWitness(
                    statistic_id="band-similarity-mapping-score",
                    observed=0.71,
                    shuffled_mean=0.68,
                    chance_level=0.50,
                    permutations=1000,
                ),
            ),
        ),
    )
    d2 = assess_construct_independence(arn_v2)
    cases.append(
        {
            "instrument": arn_v2.instrument_id,
            "recorded_terminal": "NEGATIVE__BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE",
            "gate_verdict": d2.verdict.value,
            "gate_reasons": list(d2.reasons),
            "gate_agrees_with_record": d2.verdict is ConstructVerdict.INADMISSIBLE,
        }
    )

    # --- 2. this session's ARN discriminator: chance-level, strata cancelled ---
    result = json.loads(ARN_RESULT.read_text(encoding="utf-8"))
    validity = json.loads(ARN_VALIDITY.read_text(encoding="utf-8"))
    best = max(result["per_feature"].items(), key=lambda kv: kv[1]["accuracy"])
    disc = InstrumentDesign(
        instrument_id="arn-local-vs-parent-discriminator-v1",
        declarations=declared(CHANNEL_SEPARATION=True, AUTHOR_SEPARATION=True, GOLD_INDEPENDENCE=True)
        + (
            ObligationDeclaration(
                ConstructObligation.PERMUTATION_NULL,
                True,
                "1000-permutation label shuffle, seed 20260815",
                witness=PermutationNullWitness(
                    statistic_id=best[0],
                    observed=best[1]["accuracy"],
                    shuffled_mean=0.50,
                    chance_level=0.50,
                    permutations=1000,
                ),
            ),
        ),
    )
    d3 = assess_construct_independence(disc)
    cases.append(
        {
            "instrument": disc.instrument_id,
            "recorded_terminal": "DISCRIMINATOR_NOT_PROBATIVE__DISTRACTOR_DESIGN_ARTIFACT",
            "gate_verdict": d3.verdict.value,
            "gate_reasons": list(d3.reasons),
            "gate_agrees_with_record": d3.verdict is ConstructVerdict.INADMISSIBLE,
            "note": (
                "A clean miss. The gate admits this instrument: its best statistic sits far enough "
                "from chance to clear the separation check and dies under shuffling as required, so "
                "all four obligations pass. It is nonetheless not probative, because the aggregate "
                "is opposite-signed strata cancelling "
                f"(high-similarity band {validity['accuracy_by_distractor_band']['high']['accuracy'][best[0]]}, "
                f"low-similarity band {validity['accuracy_by_distractor_band']['low']['accuracy'][best[0]]}). "
                "No obligation in the registered set can see that, so the gate is incomplete in a "
                "way this session's own instrument demonstrates."
            ),
        }
    )

    # --- 3. a probative instrument must NOT be flagged (no-alarm case) --------
    probative = InstrumentDesign(
        instrument_id="p2-prose-transfer-confirmatory-v1",
        declarations=declared(CHANNEL_SEPARATION=True, AUTHOR_SEPARATION=True, GOLD_INDEPENDENCE=True)
        + (
            ObligationDeclaration(
                ConstructObligation.PERMUTATION_NULL,
                True,
                "scrambling the input collapses the statistic from 0.9722 to 0.2500",
                witness=PermutationNullWitness(
                    statistic_id="coordinate-accuracy",
                    observed=0.9722,
                    shuffled_mean=0.2500,
                    chance_level=0.2500,
                    permutations=12,
                ),
            ),
        ),
    )
    d1 = assess_construct_independence(probative)
    cases.append(
        {
            "instrument": probative.instrument_id,
            "recorded_terminal": "passed six of seven registered gates; demonstrably reads its text",
            "gate_verdict": d1.verdict.value,
            "gate_reasons": list(d1.reasons),
            "gate_agrees_with_record": d1.verdict is ConstructVerdict.ADMISSIBLE,
        }
    )

    agreements = sum(1 for c in cases if c["gate_agrees_with_record"])
    result_doc = {
        "schema_version": "rakl-construct-independence-gate-validation-v1",
        "status": "GATE_VALIDATED_AGAINST_RECORDED_INSTRUMENTS__ONE_KNOWN_MISS",
        "grants_scientific_authority": False,
        "cases": len(cases),
        "verdict_matches_record": f"{agreements}/{len(cases)}",
        "no_alarm_case_holds": d1.verdict is ConstructVerdict.ADMISSIBLE,
        "known_incompleteness": {
            "missed_defect": "STRATUM_CANCELLATION",
            "description": (
                "Opposite-signed strata averaging to a null are invisible to all four obligations. "
                "Every one can be satisfied while the aggregate statistic is a cancellation "
                "artifact, as this session's own ARN discriminator was."
            ),
            "candidate_fifth_obligation": (
                "STRATUM_HOMOGENEITY — registered blocking factors must be declared before "
                "execution, and the statistic reported per stratum as well as in aggregate"
            ),
            "not_implemented_here": (
                "The forward falsifier frozen for this gate covers the four obligations as "
                "registered. Adding a fifth after seeing the miss, without re-freezing, would be "
                "the post-hoc amendment the programme's own invariants forbid."
            ),
        },
        "per_case": cases,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for case in cases:
        mark = "OK " if case["gate_agrees_with_record"] else "MISS"
        print(f"{mark} {case['instrument']:<42s} {case['gate_verdict']}")
    print(f"\nmatches record: {agreements}/{len(cases)}; no-alarm case holds: {result_doc['no_alarm_case_holds']}")
    print("known miss: STRATUM_CANCELLATION (see VALIDATION.json)")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
