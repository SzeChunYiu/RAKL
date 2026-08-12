"""Hostile worlds for proposal-only summation/limit-order compatibility (#384)."""

from __future__ import annotations

import pytest

from rakl.summation_compatibility import (
    ConvergenceStatus,
    GluingConsumer,
    GluingStatus,
    PermissionStatus,
    SummationCompatibilityWitness,
    WitnessAuditVerdict,
    audit_summation_compatibility,
    build_fail_closed_unknown_witness,
)


def _compatible(**overrides: object) -> SummationCompatibilityWitness:
    base = dict(
        witness_id="W-sum-1",
        atom_id="A-limit-1",
        source_accumulation_method="Lebesgue-integral-monotone-convergence",
        convergence_status=ConvergenceStatus.ABSOLUTE,
        finite_grouping_permitted=PermissionStatus.YES,
        infinite_regrouping_reordering_permitted=PermissionStatus.NO,
        nested_limit_order="sum_then_limit",
        local_block_definition="partial-sum blocks over finite index partitions",
        block_tail_or_convergence_theorem_required="dominated-convergence-tail-bound",
        alternate_summation_equivalence_proof="NOT_APPLICABLE",
        gluing_status=GluingStatus.COMPATIBLE,
        evidence_pointers=("evidence:absolute-convergence-lemma-1",),
        recorded_at_utc="2026-08-12T05:00:00Z",
    )
    base.update(overrides)
    return SummationCompatibilityWitness(**base)  # type: ignore[arg-type]


def test_compatible_witness_grants_gluing_not_theorem() -> None:
    witness = _compatible()
    report = audit_summation_compatibility(
        witness,
        expected_atom_id="A-limit-1",
        consumer=GluingConsumer.LOCAL_TO_GLOBAL_GLUING,
        claimed_witness_hash=witness.witness_canonical_sha256,
    )
    assert report.verdict is WitnessAuditVerdict.GLUING_AUTHORITY_OK
    assert report.grants_gluing_authority is True
    assert report.grants_theorem_authority is False

    theorem = audit_summation_compatibility(
        witness,
        expected_atom_id="A-limit-1",
        consumer=GluingConsumer.THEOREM_AUTHORITY,
    )
    assert theorem.verdict is WitnessAuditVerdict.THEOREM_AUTHORITY_REJECTED
    assert theorem.grants_theorem_authority is False


def test_unknown_fields_fail_closed_and_reject_construction_mismatch() -> None:
    witness = build_fail_closed_unknown_witness(
        witness_id="W-unknown",
        atom_id="A-limit-2",
        source_accumulation_method="unspecified-series-rearrangement",
        recorded_at_utc="2026-08-12T05:01:00Z",
        evidence_pointers=("evidence:missing-convergence-status",),
    )
    assert witness.gluing_status is GluingStatus.FAIL_CLOSED_UNKNOWN
    assert "convergence_status" in witness.unknown_fields

    report = audit_summation_compatibility(
        witness,
        expected_atom_id="A-limit-2",
        consumer=GluingConsumer.ROUTING,
    )
    assert report.verdict is WitnessAuditVerdict.FAIL_CLOSED_UNKNOWN
    assert report.grants_gluing_authority is False

    with pytest.raises(ValueError, match="FAIL_CLOSED_UNKNOWN"):
        _compatible(
            convergence_status=ConvergenceStatus.UNKNOWN,
            gluing_status=GluingStatus.COMPATIBLE,
        )


def test_missing_or_stale_hash_is_unverifiable() -> None:
    missing = audit_summation_compatibility(
        None,
        expected_atom_id="A-limit-1",
        consumer=GluingConsumer.REVIEW,
    )
    assert missing.verdict is WitnessAuditVerdict.WITNESS_UNVERIFIABLE

    witness = _compatible()
    stale = audit_summation_compatibility(
        witness,
        expected_atom_id="A-limit-1",
        consumer=GluingConsumer.CONTRADICTION_DIAGNOSIS,
        claimed_witness_hash="0" * 64,
    )
    assert stale.verdict is WitnessAuditVerdict.WITNESS_UNVERIFIABLE
    assert "claimed_witness_hash_mismatch" in stale.reasons


def test_conditional_requires_condition_and_incompatible_rejects() -> None:
    with pytest.raises(ValueError, match="condition"):
        _compatible(gluing_status=GluingStatus.CONDITIONAL, condition=None)

    conditional = _compatible(
        gluing_status=GluingStatus.CONDITIONAL,
        condition="uniform-integrability-on-blocks",
    )
    ok = audit_summation_compatibility(
        conditional,
        expected_atom_id="A-limit-1",
        consumer=GluingConsumer.LOCAL_TO_GLOBAL_GLUING,
    )
    assert ok.verdict is WitnessAuditVerdict.GLUING_AUTHORITY_OK
    assert ok.grants_gluing_authority is True

    bad = _compatible(gluing_status=GluingStatus.INCOMPATIBLE)
    report = audit_summation_compatibility(
        bad,
        expected_atom_id="A-limit-1",
        consumer=GluingConsumer.LOCAL_TO_GLOBAL_GLUING,
    )
    assert report.verdict is WitnessAuditVerdict.INCOMPATIBLE
    assert report.grants_gluing_authority is False


def test_document_hash_stable_and_authority_claim_fixed() -> None:
    witness = _compatible()
    doc = witness.document()
    assert doc["authority_claim"] == "ROUTING_GLUING_ONLY_NOT_THEOREM"
    assert doc["witness_canonical_sha256"] == witness.witness_canonical_sha256
    with pytest.raises(ValueError, match="authority_claim"):
        _compatible(authority_claim="THEOREM")
