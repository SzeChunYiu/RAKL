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


def build_structural_transfer_use_receipt(
    *,
    resolved_witness_evidence_ids: frozenset[str] = frozenset(),
    resolved_preservation_receipt_ids: frozenset[str] = frozenset(),
    subject_sha: str | None = None,
) -> dict[str, Any]:
    """Build a use-site transfer receipt exercising ``assess_transfer_for_use``.

    The base conformance receipt (``build_receipt``) runs ``assess_transfer``,
    which licenses a transfer on relation/invariant/boundary preservation but
    does not make a witness's explicit ``non_preserved_properties`` load-bearing
    at the consumer.  This builder is the production wiring point for the
    use-site contract: for every benchmark case whose downstream use depends on
    the source invariants, the transfer must additionally pass
    ``assess_transfer_for_use`` with each required property backed by a resolved
    preservation receipt and each declared loss explicitly acknowledged.

    The caller's assurance layer supplies the resolved witness-evidence and
    preservation-receipt identity sets; unresolved evidence/receipts fail closed
    to CANNOT_CHECK.  Grants no scientific authority.
    """
    from rakl.structural_transfer_use import (
        StructuralTransferUseContract,
        TransferUseVerdict,
        assess_transfer_for_use,
    )

    cases = make_multifamily_cases()
    rows: list[dict[str, Any]] = []
    for case in cases:
        required = frozenset(case.source.invariants)
        accepted_losses = frozenset(case.witness.non_preserved_properties)
        preservation_receipts = tuple(
            (prop, f"preservation-receipt:{case.case_id}:{prop}") for prop in sorted(required)
        )
        use = StructuralTransferUseContract(
            use_id=f"{case.case_id}:use",
            qoi=case.source.qoi,
            required_properties=required,
            accepted_non_preserved_properties=accepted_losses,
            property_preservation_receipts=preservation_receipts,
        )
        assessment = assess_transfer_for_use(
            case.source,
            case.target,
            case.witness,
            use,
            resolved_witness_evidence_ids=resolved_witness_evidence_ids,
            resolved_preservation_receipt_ids=resolved_preservation_receipt_ids,
        )
        rows.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "use_id": use.use_id,
                "qoi": use.qoi,
                "required_properties": sorted(use.required_properties),
                "accepted_non_preserved_properties": sorted(use.accepted_non_preserved_properties),
                "base_decision": assessment.base_decision.value,
                "use_verdict": assessment.verdict.value,
                "reasons": list(assessment.reasons),
                "witness_id": case.witness.witness_id,
                "witness_evidence_ids": list(case.witness.evidence_ids),
            }
        )

    licensed = sum(1 for row in rows if row["use_verdict"] == TransferUseVerdict.LICENSED_FOR_USE.value)
    return {
        "schema_version": "paper3-structural-transfer-use-v1",
        "subject_sha": subject_sha,
        "claim_boundary": (
            "use-site transfer conformance receipt only; the use gate is load-bearing on "
            "non_preserved_properties and resolved preservation receipts, and grants no "
            "scientific or cross-domain-generalization authority"
        ),
        "case_count": len(rows),
        "licensed_for_use_count": licensed,
        "resolved_witness_evidence_count": len(resolved_witness_evidence_ids),
        "resolved_preservation_receipt_count": len(resolved_preservation_receipt_ids),
        "cases": rows,
    }
