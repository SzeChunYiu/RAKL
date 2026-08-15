"""Recursive framework audit of the RAKL programme's own persistent negatives.

Runs the merged `rakl.recursive_framework_audit` controller over every record in
the negative-frontier inventory to ask, with the programme's own machinery:
do the persistent negatives localize to the QUESTION being asked, or lower?

Status: retrospective diagnostic, proposal-only. The coordinate mapping is
applied after the outcomes were known, so this is evidence about where to look
next, not a preregistered test, and it mints no authority.

Two honesty constraints are enforced in the output rather than papered over:

1. the source inventory attributes *execution-stage* failure and its vocabulary
   contains no question-level category, so a zero count on QUESTION is a
   CANNOT_CHECK about the question, not evidence that the question is right;
2. every mapping rule is emitted with the result, so the mapping can be
   attacked without re-deriving it.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")

from rakl.recursive_framework_audit import (  # noqa: E402
    AncestorChallenge,
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    decide,
)

INVENTORY = Path("research/negative_frontier_v1/INVENTORY.json")
OUT = Path("research/self_rakl_recursive_question_audit_v1/AUDIT_RESULT.json")

RULES: tuple[tuple[str, AuditCoordinate, str], ...] = (
    (
        "licence/abstention (independence)",
        AuditCoordinate.EVIDENCE,
        "independence cannot be self-supplied; local receipts valid, external trust root absent",
    ),
    (
        "licence/abstention",
        AuditCoordinate.EVALUATOR,
        "an abstention/licence gate outranked the signal gate",
    ),
    ("licence", AuditCoordinate.EVALUATOR, "the verification licence stops below the claim"),
    (
        "instrument-construct (admissibility",
        AuditCoordinate.EVALUATOR,
        "the gate cannot express the effect it gates",
    ),
    (
        "instrument-construct (comparator admissibility)",
        AuditCoordinate.EVALUATOR,
        "the comparator is an oracle, not an admissible weaker parent",
    ),
    (
        "instrument-construct",
        AuditCoordinate.MEASUREMENT,
        "the observation operator measured its own construction, not the target",
    ),
    (
        "capability/benefit",
        AuditCoordinate.EVIDENCE,
        "the mechanic ran; the downstream effect was absent from the evidence",
    ),
    (
        "capability (feature adequacy)",
        AuditCoordinate.MEASUREMENT,
        "extracted features carry insufficient signal -- a measurement-operator gap",
    ),
    (
        "capability",
        AuditCoordinate.EVIDENCE,
        "the subject cannot clear the task threshold, so the effect is unidentifiable",
    ),
    ("hardware", AuditCoordinate.EVIDENCE, "execution environment, not instrument or science"),
    ("power", AuditCoordinate.EVIDENCE, "packet below the registered resolution requirement"),
    (
        "extraction/provenance",
        AuditCoordinate.EVIDENCE,
        "the artifact behind the number does not exist",
    ),
    (
        "extraction/integration",
        AuditCoordinate.INTERFACE,
        "the specification had no executable binding point",
    ),
    (
        "extraction",
        AuditCoordinate.MEASUREMENT,
        "the extraction operator does not recover the target structure",
    ),
    (
        "mapping / allocation-policy",
        AuditCoordinate.DECOMPOSITION,
        "the loss localized to one stage of the decomposition",
    ),
    (
        "mapping",
        AuditCoordinate.FRAMEWORK,
        "surface analogy carried a parent verdict without its preconditions",
    ),
)

UNMAPPED = "UNMAPPED"

# Sub-shapes of the construct-dependence cluster. Each is a way for an
# instrument to read something other than its target.
SHAPES: tuple[tuple[str, str], ...] = (
    ("answer_shares_a_channel_with_the_input", r"alongside the text|family label|identifier leakage|answer-correlated|carried family_id|pre-parsed sibling"),
    ("generator_and_evaluator_share_an_author", r"single-author coupling|generator's own construction|author templated|its author templated"),
    ("gold_is_a_function_of_the_candidate", r"self-grading|share one pure function|entailed by parse success"),
    ("statistic_survives_label_shuffling", r"shuffl"),
    ("comparator_is_an_oracle", r"expressiveness oracle|equal-information generic rule engine"),
    ("gate_cannot_express_the_effect", r"cannot EXPRESS|ceiling below|CAN FAIL"),
    ("registered_arm_unconstructible", r"unconstructible|coverage hole"),
    ("abstention_option_unreachable", r"abstention option unreachable|cannot_assess=false"),
)

# Controls that actually caught a construct defect, i.e. evidence the check
# works when it is run.
CONTROL_EVIDENCE = r"shuffl|scrambl|circularity attack|negative controls"


def classify(attribution: str) -> tuple[str, str]:
    lowered = attribution.lower()
    for needle, coordinate, rationale in RULES:
        if needle.lower() in lowered:
            return coordinate.value, rationale
    return UNMAPPED, "no rule matched; reported rather than forced into a coordinate"


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    records = inventory["records"]

    per_record = []
    for record in records:
        coordinate, rationale = classify(record.get("one_stage_attribution", ""))
        entry = {
            "slug": record["slug"],
            "paper": record["paper"],
            "class": record["class"],
            "coordinate": coordinate,
            "mapping_rationale": rationale,
        }
        if coordinate != UNMAPPED:
            entry["per_record_action"] = decide(
                AuditNode(closure_coordinates_pass=False, material_open_residual=True),
                AuditResidual(plausible_causes=(AuditCoordinate(coordinate),)),
            ).action.value
        per_record.append(entry)

    counts = Counter(e["coordinate"] for e in per_record)

    # --- can the QUESTION coordinate even be checked from this source? -------
    question_pattern = re.compile(
        r"wrong question|question is|reframe|re-frame|framework is wrong|asking the wrong|"
        r"question-level|misframed|wrong target|QoI (is|was) wrong",
        re.I,
    )
    question_language_hits = [
        record["slug"]
        for record in records
        if any(
            question_pattern.search(record.get(field, "") or "")
            for field in ("one_stage_attribution", "core_lever", "what_happened")
        )
    ]
    attribution_stems = sorted(
        {record["one_stage_attribution"].split(".")[0].strip().lower() for record in records}
    )

    # --- construct-dependence cluster ----------------------------------------
    construct_records = [
        record
        for record, entry in zip(records, per_record)
        if entry["coordinate"] in {AuditCoordinate.MEASUREMENT.value, AuditCoordinate.EVALUATOR.value}
    ]
    shape_hits: dict[str, list[str]] = {name: [] for name, _ in SHAPES}
    for record in construct_records:
        blob = " ".join(
            str(record.get(field, "")) for field in ("one_stage_attribution", "what_happened", "core_lever")
        )
        for name, pattern in SHAPES:
            if re.search(pattern, blob, re.I):
                shape_hits[name].append(record["slug"])
    caught_by_control = [
        record["slug"]
        for record in construct_records
        if re.search(
            CONTROL_EVIDENCE,
            " ".join(str(record.get(f, "")) for f in ("what_happened", "core_lever", "one_stage_attribution")),
            re.I,
        )
    ]

    # --- programme-level decision -------------------------------------------
    programme_causes = tuple(AuditCoordinate(c) for c in sorted(counts) if c != UNMAPPED)
    programme_decision = decide(
        AuditNode(closure_coordinates_pass=False, material_open_residual=True),
        AuditResidual(plausible_causes=programme_causes),
    )

    # --- ARN lineage ascent test --------------------------------------------
    arn_slugs = [r["slug"] for r in records if r["slug"].startswith("p2-arn-")]
    arn_challenge = AncestorChallenge(
        ancestor_fiber_id="p2-prose-level-structural-extraction-by-admissible-reducer",
        challenge_evidence_digest="negative-frontier-v1",
        failed_local_repair_families=(
            "v2-deterministic-reducer",
            "v3-instance-paired-reducer",
            "v4-relational-correspondence-reducer",
        ),
        dependent_descendant_ids=tuple(arn_slugs),
        child_fiber_id="p2-arn-extraction",
        residual_id="arn-capability-absent",
        local_causes_tested=(AuditCoordinate.MEASUREMENT, AuditCoordinate.EVIDENCE),
        fresh_evidence_epochs=("arn-external-corpus-v1",),
        parent_coordinate_implicated=AuditCoordinate.FRAMEWORK,
        local_vs_parent_discriminator_id="",
        cost=0,
    )
    arn_decision = decide(
        AuditNode(closure_coordinates_pass=False, material_open_residual=True),
        AuditResidual(
            plausible_causes=(AuditCoordinate.MEASUREMENT,),
            parent_challenge_supported=True,
            distinct_local_repair_families_failed=arn_challenge.distinct_local_repair_families_failed,
        ),
    )

    result = {
        "schema_version": "rakl-self-recursive-question-audit-v1",
        "status": "RETROSPECTIVE_DIAGNOSTIC_PROPOSAL_ONLY",
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "question": (
            "Do the programme's persistent negatives localize to the QUESTION being asked, "
            "or to a lower pursuit coordinate?"
        ),
        "source_inventory": str(INVENTORY),
        "records_audited": len(records),
        "mapping_rules": [
            {"match": needle, "coordinate": coord.value, "rationale": why}
            for needle, coord, why in RULES
        ],
        "coordinate_counts": dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "question_coordinate": {
            "records_mapped_to_QUESTION": counts.get(AuditCoordinate.QUESTION.value, 0),
            "checkable_from_this_source": False,
            "why_not": (
                "The inventory attributes execution-stage failure. Its attribution vocabulary "
                "contains no question-level category, and no record's attribution, lever or "
                "narrative uses question-level language, so a question-level cause could not "
                "have been recorded even if one were present."
            ),
            "question_language_hits": question_language_hits,
            "attribution_vocabulary": attribution_stems,
            "verdict": "CANNOT_CHECK__SOURCE_VOCABULARY_CANNOT_EXPRESS_THE_COORDINATE",
        },
        "programme_level": {
            "plausible_causes": [c.value for c in programme_causes],
            "action": programme_decision.action.value,
            "reasons": list(programme_decision.reasons),
        },
        "construct_dependence_cluster": {
            "records": len(construct_records),
            "share_of_frontier": f"{len(construct_records)}/{len(records)}",
            "shapes": {name: hits for name, hits in shape_hits.items() if hits},
            "unshaped": [
                record["slug"]
                for record in construct_records
                if not any(record["slug"] in hits for hits in shape_hits.values())
            ],
            "caught_by_an_explicit_control": caught_by_control,
            "existing_gate": {
                "module": "src/rakl/instrument_admissibility.py",
                "covers": "oracle-ceiling expressibility: can the instrument express an effect above the MDE",
                "does_not_cover": (
                    "construct independence: whether the instrument reads its target through a "
                    "channel independent of whatever generated or graded it"
                ),
                "callers": ["research/paper3_lift_ceiling_qualification_v1/compute_p3_lift_ceiling_v1.py"],
            },
        },
        "arn_lineage_ascent_test": {
            "ancestor_fiber": arn_challenge.ancestor_fiber_id,
            "distinct_failed_local_repair_families": list(arn_challenge.failed_local_repair_families),
            "frozen_rule_admissible_for_ascent": arn_challenge.admissible_for_ascent,
            "packet_complete": arn_challenge.packet_complete,
            "escalation_admissible": arn_challenge.escalation_admissible,
            "action_under_frozen_chain": arn_decision.action.value,
            "blocking_gap": (
                "no local-vs-parent discriminator is registered: three failed reducer families "
                "show the local level is not responsible, but do not separate parent from child"
            ),
        },
        "per_record": per_record,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"records={len(records)}  unmapped={counts.get(UNMAPPED, 0)}")
    for coordinate, n in result["coordinate_counts"].items():
        print(f"  {coordinate:14s} {n}")
    print(f"QUESTION checkable from this source: False ({len(question_language_hits)} language hits)")
    print(f"programme-level action: {programme_decision.action.value}")
    print(f"construct-dependence cluster: {len(construct_records)}/{len(records)}")
    for name, hits in shape_hits.items():
        if hits:
            print(f"    {name:42s} {len(hits)}")
    print(f"  caught by an explicit control: {len(caught_by_control)}")
    print(f"ARN ascent under frozen chain: {arn_decision.action.value}; escalation admissible: {arn_challenge.escalation_admissible}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
