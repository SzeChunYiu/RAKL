"""Development hostile gluing worlds for quantifier-scope compatibility (#459).

Worlds are fresh and untouched — they are inspired by historical quantifier
failure families (point/global, time/supremum, sequence/limit, norm/quantifier)
but do not replay a motivating application case as confirmatory evidence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rakl.quantifier_compatibility import (
    GluingConsumer,
    GluingStatus,
    PermissionStatus,
    QuantifierCompatibilityWitness,
    ScopeAlignment,
    WitnessAuditVerdict,
    audit_quantifier_compatibility,
    build_fail_closed_unknown_witness,
)

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def _witness(**overrides: object) -> QuantifierCompatibilityWitness:
    base = dict(
        witness_id="W-quant-1",
        atom_id="A-scope-1",
        source_claim_scope="local-section energy bound on chart U",
        point_global_scope=ScopeAlignment.ALIGNED,
        time_supremum_scope=ScopeAlignment.ALIGNED,
        sequence_limit_scope=ScopeAlignment.ALIGNED,
        norm_quantifier_scope=ScopeAlignment.ALIGNED,
        point_global_substitution_permitted=PermissionStatus.NO,
        time_supremum_substitution_permitted=PermissionStatus.NO,
        sequence_limit_substitution_permitted=PermissionStatus.NO,
        norm_quantifier_substitution_permitted=PermissionStatus.NO,
        required_scope_witness="NOT_APPLICABLE",
        gluing_status=GluingStatus.COMPATIBLE,
        evidence_pointers=("evidence:aligned-local-sections-1",),
        recorded_at_utc="2026-08-12T06:00:00Z",
    )
    base.update(overrides)
    return QuantifierCompatibilityWitness(**base)  # type: ignore[arg-type]


def test_gw_quant_1_aligned_scopes_grant_gluing_not_theorem() -> None:
    witness = _witness()
    report = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-1",
        consumer=GluingConsumer.LOCAL_TO_GLOBAL_GLUING,
        claimed_witness_hash=witness.witness_canonical_sha256,
    )
    assert report.verdict is WitnessAuditVerdict.GLUING_AUTHORITY_OK
    assert report.grants_gluing_authority is True
    assert report.grants_theorem_authority is False

    theorem = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-1",
        consumer=GluingConsumer.THEOREM_AUTHORITY,
    )
    assert theorem.verdict is WitnessAuditVerdict.THEOREM_AUTHORITY_REJECTED


def test_gw_quant_2_point_global_misalignment_rejects_gluing() -> None:
    witness = _witness(
        witness_id="W-quant-2",
        atom_id="A-scope-2",
        source_claim_scope="pointwise chart bound glued as global statement",
        point_global_scope=ScopeAlignment.MISALIGNED,
        gluing_status=GluingStatus.INCOMPATIBLE,
        evidence_pointers=("evidence:point-global-substitution-without-bridge",),
    )
    report = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-2",
        consumer=GluingConsumer.ROUTING,
    )
    assert report.verdict is WitnessAuditVerdict.INCOMPATIBLE
    assert report.grants_gluing_authority is False
    assert "point_global_scope:point_global_substitution_permitted" in witness.misaligned_axes_without_substitution


def test_gw_quant_3_time_supremum_misalignment_rejects_compatible_construction() -> None:
    with pytest.raises(ValueError, match="misaligned scope axes"):
        _witness(
            witness_id="W-quant-3",
            atom_id="A-scope-3",
            source_claim_scope="local-in-time bound promoted to supreme norm",
            time_supremum_scope=ScopeAlignment.MISALIGNED,
            gluing_status=GluingStatus.COMPATIBLE,
        )


def test_gw_quant_4b_conditional_with_substitution_no_rejects_construction() -> None:
    with pytest.raises(ValueError, match="CONDITIONAL gluing requires substitution permission YES"):
        _witness(
            witness_id="W-quant-4b",
            atom_id="A-scope-4b",
            source_claim_scope="pointwise bound promoted globally",
            point_global_scope=ScopeAlignment.MISALIGNED,
            point_global_substitution_permitted=PermissionStatus.NO,
            gluing_status=GluingStatus.CONDITIONAL,
            condition="some-nonempty-condition",
            evidence_pointers=("evidence:test",),
        )


def test_gw_quant_4c_conditional_not_applicable_bridge_rejects_construction() -> None:
    with pytest.raises(ValueError, match="explicit scope-bridge witness"):
        _witness(
            witness_id="W-quant-4c",
            atom_id="A-scope-4c",
            source_claim_scope="pointwise bound promoted globally",
            point_global_scope=ScopeAlignment.MISALIGNED,
            point_global_substitution_permitted=PermissionStatus.YES,
            required_scope_witness="NOT_APPLICABLE",
            gluing_status=GluingStatus.CONDITIONAL,
            condition="some-nonempty-condition",
            evidence_pointers=("evidence:test",),
        )


def test_gw_quant_4_sequence_limit_conditional_with_uniform_bound() -> None:
    witness = _witness(
        witness_id="W-quant-4",
        atom_id="A-scope-4",
        source_claim_scope="finite-sequence convergence glued to limit conclusion",
        sequence_limit_scope=ScopeAlignment.MISALIGNED,
        sequence_limit_substitution_permitted=PermissionStatus.YES,
        required_scope_witness="uniform-convergence-bridge-lemma-4",
        gluing_status=GluingStatus.CONDITIONAL,
        condition="uniform-bound-on-partial-sums",
        evidence_pointers=("evidence:sequence-limit-conditional-bridge",),
    )
    report = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-4",
        consumer=GluingConsumer.CONTRADICTION_DIAGNOSIS,
    )
    assert report.verdict is WitnessAuditVerdict.GLUING_AUTHORITY_OK
    assert report.grants_gluing_authority is True


def test_gw_quant_5_norm_quantifier_misalignment_incompatible() -> None:
    witness = _witness(
        witness_id="W-quant-5",
        atom_id="A-scope-5",
        source_claim_scope="L2 norm bound substituted for uniform quantifier statement",
        norm_quantifier_scope=ScopeAlignment.MISALIGNED,
        gluing_status=GluingStatus.INCOMPATIBLE,
        evidence_pointers=("evidence:norm-quantifier-scope-leak",),
    )
    report = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-5",
        consumer=GluingConsumer.LOCAL_TO_GLOBAL_GLUING,
    )
    assert report.verdict is WitnessAuditVerdict.INCOMPATIBLE


def test_gw_quant_6_unknown_fields_fail_closed() -> None:
    witness = build_fail_closed_unknown_witness(
        witness_id="W-quant-6",
        atom_id="A-scope-6",
        source_claim_scope="unspecified quantifier scope on glued sections",
        recorded_at_utc="2026-08-12T06:05:00Z",
        evidence_pointers=("evidence:missing-scope-status",),
    )
    assert witness.gluing_status is GluingStatus.FAIL_CLOSED_UNKNOWN
    assert "point_global_scope" in witness.unknown_fields

    report = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-6",
        consumer=GluingConsumer.REVIEW,
    )
    assert report.verdict is WitnessAuditVerdict.FAIL_CLOSED_UNKNOWN
    assert report.grants_gluing_authority is False


def test_missing_or_stale_hash_is_unverifiable() -> None:
    missing = audit_quantifier_compatibility(
        None,
        expected_atom_id="A-scope-1",
        consumer=GluingConsumer.REVIEW,
    )
    assert missing.verdict is WitnessAuditVerdict.WITNESS_UNVERIFIABLE

    witness = _witness()
    stale = audit_quantifier_compatibility(
        witness,
        expected_atom_id="A-scope-1",
        consumer=GluingConsumer.REVIEW,
        claimed_witness_hash="0" * 64,
    )
    assert stale.verdict is WitnessAuditVerdict.WITNESS_UNVERIFIABLE
    assert "claimed_witness_hash_mismatch" in stale.reasons


def test_document_hash_stable_and_separate_from_summation_surface() -> None:
    witness = _witness()
    doc = witness.document()
    assert doc["authority_claim"] == "ROUTING_GLUING_ONLY_NOT_THEOREM"
    assert doc["schema_version"] == "quantifier-compatibility-witness-v1"
    assert doc["witness_canonical_sha256"] == witness.witness_canonical_sha256
    with pytest.raises(ValueError, match="authority_claim"):
        _witness(authority_claim="THEOREM")


def test_witness_document_validates_against_schema() -> None:
    import json

    import jsonschema

    schema = json.loads((SCHEMAS / "quantifier-compatibility-witness-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(_witness().document(), schema)
