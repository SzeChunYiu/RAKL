from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rakl.structural_benchmark import (
    SimilarityQuadrant,
    make_multifamily_cases,
)
from rakl.structural_transfer import assess_transfer
from rakl.structural_types import TransferDecision


RECEIPT_SCHEMA_VERSION = "paper3-structural-benchmark-v1"


def build_receipt(*, subject_sha: str | None = None) -> dict[str, Any]:
    cases = make_multifamily_cases()
    rows: list[dict[str, Any]] = []
    semantic_only_correct = 0
    structural_gate_correct = 0
    hard_case_count = 0

    for case in cases:
        assessment = assess_transfer(case.source, case.target, case.witness)
        structural_prediction = assessment.decision is TransferDecision.LICENSED
        semantic_prediction = case.semantic_similarity_label == "high"
        structural_correct = structural_prediction == case.structural_match_expected
        semantic_correct = semantic_prediction == case.structural_match_expected

        if case.quadrant in {
            SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT,
            SimilarityQuadrant.Q3_HIGH_SEM_LOW_STRUCT,
        }:
            hard_case_count += 1
            semantic_only_correct += int(semantic_correct)
            structural_gate_correct += int(structural_correct)

        rows.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "quadrant": case.quadrant.value,
                "semantic_similarity_label": case.semantic_similarity_label,
                "structural_match_expected": case.structural_match_expected,
                "semantic_only_prediction": semantic_prediction,
                "semantic_only_correct": semantic_correct,
                "structural_gate_decision": assessment.decision.value,
                "structural_gate_correct": structural_correct,
                "structurally_complete": assessment.structurally_complete,
                "reasons": list(assessment.reasons),
                "preserved_relation_count": assessment.preserved_relation_count,
                "required_relation_count": assessment.required_relation_count,
                "preserved_invariant_count": assessment.preserved_invariant_count,
                "required_invariant_count": assessment.required_invariant_count,
                "source_structure_id": case.source.structure_id,
                "target_structure_id": case.target.structure_id,
                "witness_id": case.witness.witness_id,
                "witness_evidence_ids": list(case.witness.evidence_ids),
            }
        )

    q2 = [row for row in rows if row["quadrant"] == SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT.value]
    q3 = [row for row in rows if row["quadrant"] == SimilarityQuadrant.Q3_HIGH_SEM_LOW_STRUCT.value]
    q2_all_licensed = all(row["structural_gate_decision"] == TransferDecision.LICENSED.value for row in q2)
    q3_all_rejected = all(row["structural_gate_decision"] == TransferDecision.REJECTED.value for row in q3)

    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "subject_sha": subject_sha,
        "claim_boundary": (
            "deterministic conformance receipt only; not empirical evidence of cross-domain "
            "generalization, training efficiency, or inference efficiency"
        ),
        "case_count": len(rows),
        "hard_case_count": hard_case_count,
        "families": sorted({case.family for case in cases}),
        "q2_all_licensed": q2_all_licensed,
        "q3_all_rejected": q3_all_rejected,
        "semantic_only_hard_case_accuracy": (
            semantic_only_correct / hard_case_count if hard_case_count else None
        ),
        "structural_gate_hard_case_accuracy": (
            structural_gate_correct / hard_case_count if hard_case_count else None
        ),
        "cheap_mechanism_gate_passed": q2_all_licensed
        and q3_all_rejected
        and structural_gate_correct == hard_case_count,
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--subject-sha")
    args = parser.parse_args()
    receipt = build_receipt(subject_sha=args.subject_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
