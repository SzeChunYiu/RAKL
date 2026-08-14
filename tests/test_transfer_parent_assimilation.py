from rakl.transfer_parent_assimilation import (
    FormalParentDisposition,
    FormalParentResult,
    TransferVerdict,
    arbitrate_transfer,
)

SUBJECT = "a" * 64
DERIVATION = "b" * 64


def _parent(disposition, **updates):
    values = dict(
        method_id="bareinboim-pearl-sid-family",
        method_version="transportability-parent-boundary-v1",
        subject_sha256=SUBJECT,
        disposition=disposition,
        derivation_sha256=DERIVATION if disposition in {FormalParentDisposition.LICENSED, FormalParentDisposition.REJECTED} else None,
    )
    values.update(updates)
    return FormalParentResult(**values)


def test_formal_rejection_cannot_be_overridden_by_orion_license():
    result = arbitrate_transfer(
        _parent(FormalParentDisposition.REJECTED),
        TransferVerdict.LICENSED,
        expected_subject_sha256=SUBJECT,
    )
    assert result.verdict is TransferVerdict.REJECTED
    assert result.authority_source == "FORMAL_PARENT"
    assert not result.orion_residual_eligible
    assert not result.grants_scientific_authority


def test_formal_license_cannot_be_overridden_by_orion_rejection():
    result = arbitrate_transfer(
        _parent(FormalParentDisposition.LICENSED),
        TransferVerdict.REJECTED,
        expected_subject_sha256=SUBJECT,
    )
    assert result.verdict is TransferVerdict.LICENSED
    assert result.authority_source == "FORMAL_PARENT"
    assert not result.orion_residual_eligible


def test_formal_cannot_check_fails_closed_even_when_orion_would_license():
    result = arbitrate_transfer(
        _parent(FormalParentDisposition.CANNOT_CHECK),
        TransferVerdict.LICENSED,
        expected_subject_sha256=SUBJECT,
    )
    assert result.verdict is TransferVerdict.CANNOT_CHECK
    assert result.authority_source == "FORMAL_PARENT"
    assert not result.orion_residual_eligible


def test_out_of_scope_is_the_only_path_to_orion_residual():
    for verdict in TransferVerdict:
        result = arbitrate_transfer(
            _parent(FormalParentDisposition.OUT_OF_SCOPE),
            verdict,
            expected_subject_sha256=SUBJECT,
        )
        assert result.verdict is verdict
        assert result.authority_source == "ORION_OUTSIDE_FORMAL_PARENT_SCOPE"
        assert result.orion_residual_eligible
        assert not result.grants_scientific_authority


def test_stale_subject_fails_closed_before_arbitration():
    result = arbitrate_transfer(
        _parent(FormalParentDisposition.LICENSED, subject_sha256="c" * 64),
        TransferVerdict.LICENSED,
        expected_subject_sha256=SUBJECT,
    )
    assert result.verdict is TransferVerdict.CANNOT_CHECK
    assert result.authority_source == "BOUNDARY_VALIDATION_FAILURE"
    assert "formal_parent_subject_mismatch" in result.reasons


def test_decisive_parent_without_derivation_digest_fails_closed():
    result = arbitrate_transfer(
        _parent(FormalParentDisposition.REJECTED, derivation_sha256=None),
        TransferVerdict.REJECTED,
        expected_subject_sha256=SUBJECT,
    )
    assert result.verdict is TransferVerdict.CANNOT_CHECK
    assert "formal_parent_decisive_result_missing_derivation_digest" in result.reasons


def test_wrong_parent_identity_or_version_fails_closed():
    bad_id = arbitrate_transfer(
        _parent(FormalParentDisposition.LICENSED, method_id="orion-renamed-parent"),
        TransferVerdict.LICENSED,
        expected_subject_sha256=SUBJECT,
    )
    assert bad_id.verdict is TransferVerdict.CANNOT_CHECK
    assert "formal_parent_method_id_mismatch" in bad_id.reasons

    bad_version = arbitrate_transfer(
        _parent(FormalParentDisposition.LICENSED, method_version="posthoc-v2"),
        TransferVerdict.LICENSED,
        expected_subject_sha256=SUBJECT,
    )
    assert bad_version.verdict is TransferVerdict.CANNOT_CHECK
    assert "formal_parent_method_version_mismatch" in bad_version.reasons


def test_malformed_hashes_fail_closed():
    result = arbitrate_transfer(
        _parent(FormalParentDisposition.LICENSED, subject_sha256="not-a-hash", derivation_sha256="also-bad"),
        TransferVerdict.LICENSED,
        expected_subject_sha256="bad",
    )
    assert result.verdict is TransferVerdict.CANNOT_CHECK
    assert result.authority_source == "BOUNDARY_VALIDATION_FAILURE"
    assert "expected_subject_sha256_invalid" in result.reasons
    assert "formal_parent_subject_sha256_invalid" in result.reasons
    assert "formal_parent_decisive_result_missing_derivation_digest" in result.reasons
