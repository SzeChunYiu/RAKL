from rakl.unified_integration_contract import (
    IntegrationReadiness,
    UnifiedMechanicsManifest,
    assess_unified_integration,
)


def _manifest(**changes):
    data = dict(
        manifest_id="m",
        base_commit_hash="base",
        state_commitment_digest="state",
        structural_identity_digest="structure",
        operational_subject_digest="subject",
        geometry_id="geometry",
        quotient_validation_receipt_id="quotient",
        structural_transfer_use_receipt_id="transfer",
        training_assurance_id="training",
        shared_identity_reuse_receipt_id="reuse",
        compilation_proposal_id="proposal",
        fresh_compilation_assurance_id="fresh",
        exact_base_guard_receipt_id="guards",
    )
    data.update(changes)
    return UnifiedMechanicsManifest(**data)


def test_unified_integration_requires_resolution_for_cross_surface_receipts() -> None:
    report = assess_unified_integration(
        _manifest(),
        expected_base_commit_hash="base",
        resolved_receipt_ids=("guards", "quotient", "transfer", "training", "reuse", "fresh"),
        require_geometry=True,
        require_training=True,
        require_shared_identity_reuse=True,
        require_cognitive_compilation=True,
        require_quotient_assurance=True,
        require_transfer_use_assurance=True,
    )
    assert report.verdict is IntegrationReadiness.READY_FOR_INTEGRATION_TEST
    assert not report.grants_authority


def test_unresolved_receipt_fails_closed() -> None:
    report = assess_unified_integration(
        _manifest(),
        expected_base_commit_hash="base",
        resolved_receipt_ids=("guards",),
        require_training=True,
        require_quotient_assurance=True,
    )
    assert report.verdict is IntegrationReadiness.CANNOT_CHECK
    assert any(reason.startswith("unresolved:training_assurance_id") for reason in report.reasons)


def test_base_mismatch_rejects_epoch() -> None:
    report = assess_unified_integration(
        _manifest(),
        expected_base_commit_hash="other",
        resolved_receipt_ids=("guards",),
    )
    assert report.verdict is IntegrationReadiness.REJECT
    assert "base_commit_mismatch" in report.reasons
