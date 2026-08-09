from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Tuple


class AttestationVerdict(str, Enum):
    VERIFIED_PROPOSAL_ONLY = "VERIFIED_PROPOSAL_ONLY"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class RuntimeAttestation:
    verdict: AttestationVerdict
    reasons: Tuple[str, ...]
    executable_path: str
    executable_sha256: str | None
    environment_fingerprint_sha256: str | None
    python_version: str
    platform_identity: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion(self) -> bool:
        return False


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def environment_fingerprint(
    environment: Mapping[str, str],
    *,
    allowed_names: Tuple[str, ...],
) -> tuple[AttestationVerdict, str | None, Tuple[str, ...]]:
    """Hash declared environment values without storing raw secret values."""
    allowed = tuple(sorted(allowed_names))
    if len(set(allowed)) != len(allowed):
        return AttestationVerdict.REJECT, None, ("duplicate_allowed_environment_name",)
    supplied = set(environment)
    expected = set(allowed)
    if supplied - expected:
        return AttestationVerdict.REJECT, None, ("undeclared_environment_variable_present",)
    if expected - supplied:
        return AttestationVerdict.CANNOT_CHECK, None, ("declared_environment_variable_missing",)
    payload = [
        [name, _sha256_bytes(str(environment[name]).encode("utf-8"))]
        for name in allowed
    ]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return AttestationVerdict.VERIFIED_PROPOSAL_ONLY, _sha256_bytes(canonical), (
        "environment_names_and_value_digests_bound_without_disclosing_values",
    )


def attest_runtime(
    executable_path: str | Path,
    *,
    expected_executable_sha256: str | None = None,
    environment: Mapping[str, str] | None = None,
    allowed_environment_names: Tuple[str, ...] = (),
) -> RuntimeAttestation:
    path = Path(executable_path)
    reasons: list[str] = []

    if not path.is_absolute():
        return RuntimeAttestation(
            AttestationVerdict.REJECT,
            ("executable_path_must_be_absolute",),
            str(path),
            None,
            None,
            sys.version.split()[0],
            platform.platform(),
        )
    if not path.exists() or not path.is_file():
        return RuntimeAttestation(
            AttestationVerdict.CANNOT_CHECK,
            ("executable_artifact_unavailable",),
            str(path),
            None,
            None,
            sys.version.split()[0],
            platform.platform(),
        )

    try:
        executable_hash = _sha256_bytes(path.read_bytes())
    except OSError:
        return RuntimeAttestation(
            AttestationVerdict.CANNOT_CHECK,
            ("executable_artifact_unreadable",),
            str(path),
            None,
            None,
            sys.version.split()[0],
            platform.platform(),
        )

    if expected_executable_sha256 is not None:
        if len(expected_executable_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in expected_executable_sha256):
            return RuntimeAttestation(
                AttestationVerdict.REJECT,
                ("expected_executable_sha256_invalid",),
                str(path),
                executable_hash,
                None,
                sys.version.split()[0],
                platform.platform(),
            )
        if executable_hash != expected_executable_sha256:
            return RuntimeAttestation(
                AttestationVerdict.REJECT,
                ("executable_sha256_mismatch",),
                str(path),
                executable_hash,
                None,
                sys.version.split()[0],
                platform.platform(),
            )
        reasons.append("executable_sha256_matches_expected")

    env = dict(environment or {})
    env_verdict, env_hash, env_reasons = environment_fingerprint(
        env,
        allowed_names=allowed_environment_names,
    )
    reasons.extend(env_reasons)
    if env_verdict is AttestationVerdict.REJECT:
        return RuntimeAttestation(
            AttestationVerdict.REJECT,
            tuple(reasons),
            str(path),
            executable_hash,
            env_hash,
            sys.version.split()[0],
            platform.platform(),
        )
    if env_verdict is AttestationVerdict.CANNOT_CHECK:
        return RuntimeAttestation(
            AttestationVerdict.CANNOT_CHECK,
            tuple(reasons),
            str(path),
            executable_hash,
            env_hash,
            sys.version.split()[0],
            platform.platform(),
        )

    reasons.extend(
        (
            "runtime_artifact_observed",
            "platform_and_python_identity_recorded",
            "attestation_is_reproducibility_evidence_not_scientific_truth",
        )
    )
    return RuntimeAttestation(
        AttestationVerdict.VERIFIED_PROPOSAL_ONLY,
        tuple(reasons),
        str(path),
        executable_hash,
        env_hash,
        sys.version.split()[0],
        platform.platform(),
    )
