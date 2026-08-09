from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from rakl.artifact_attestation import (
    AttestationVerdict,
    attest_runtime,
    environment_fingerprint,
)


def test_runtime_attestation_binds_executable_and_environment_without_raw_values():
    path = Path(sys.executable).resolve()
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    report = attest_runtime(
        path,
        expected_executable_sha256=expected,
        environment={"API_TOKEN": "secret-value"},
        allowed_environment_names=("API_TOKEN",),
    )
    assert report.verdict is AttestationVerdict.VERIFIED_PROPOSAL_ONLY
    assert report.executable_sha256 == expected
    assert report.environment_fingerprint_sha256 is not None
    assert "secret-value" not in repr(report)


def test_runtime_attestation_rejects_executable_hash_mismatch():
    path = Path(sys.executable).resolve()
    report = attest_runtime(
        path,
        expected_executable_sha256="0" * 64,
        environment={},
        allowed_environment_names=(),
    )
    assert report.verdict is AttestationVerdict.REJECT
    assert "executable_sha256_mismatch" in report.reasons


def test_environment_attestation_fails_closed_on_missing_declared_value():
    verdict, digest, reasons = environment_fingerprint({}, allowed_names=("TOKEN",))
    assert verdict is AttestationVerdict.CANNOT_CHECK
    assert digest is None
    assert "declared_environment_variable_missing" in reasons
