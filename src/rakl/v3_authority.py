"""Protected, content-addressed authority receipts for RAKL v3.

These objects deliberately separate a caller's assertion from a resolved
attestation.  An ID, enum, ``verified=True`` flag, or an unhashed payload never
grants authority.  Authority-sensitive v3 operations accept only attestations
whose signature, exact subject, exact evidence bytes, evaluator bytes, and
chronology resolve under an externally supplied trust policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import hmac
import json
from typing import Iterable, Tuple


class AttestationPurpose(str, Enum):
    LESSON_VERIFICATION = "LESSON_VERIFICATION"
    LESSON_TRANSFER = "LESSON_TRANSFER"
    LESSON_PROOF = "LESSON_PROOF"
    TOOL_PROJECTION = "TOOL_PROJECTION"
    LOCAL_SECTION_VERIFICATION = "LOCAL_SECTION_VERIFICATION"
    EVOLUTION_ASSURANCE = "EVOLUTION_ASSURANCE"
    GOVERNANCE_PROMOTION = "GOVERNANCE_PROMOTION"
    BENCHMARK_FREEZE = "BENCHMARK_FREEZE"
    BENCHMARK_MATCH = "BENCHMARK_MATCH"


def _parse_time(value: str) -> datetime | None:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class EvidenceArtifact:
    artifact_id: str
    payload: bytes
    payload_sha256: str
    frozen_at: str
    producer_id: str

    def __post_init__(self) -> None:
        if not self.artifact_id or not self.producer_id:
            raise ValueError("evidence artifact requires id and producer")
        if not isinstance(self.payload, bytes):
            raise TypeError("evidence artifact payload must be bytes")
        if not _is_sha256(self.payload_sha256):
            raise ValueError("evidence artifact requires a lowercase SHA-256 digest")
        if _parse_time(self.frozen_at) is None:
            raise ValueError("evidence artifact requires a timezone-aware frozen_at")

    @property
    def content_valid(self) -> bool:
        return hmac.compare_digest(sha256(self.payload).hexdigest(), self.payload_sha256)


@dataclass(frozen=True)
class ProtectedAttestation:
    attestation_id: str
    purpose: AttestationPurpose
    subject_hash: str
    subject_frozen_at: str
    evaluator_artifact_id: str
    evaluator_artifact_sha256: str
    evidence_bindings: Tuple[Tuple[str, str], ...]
    proposer_id: str
    signer_id: str
    issued_at: str
    verdict: str
    signature: str

    def __post_init__(self) -> None:
        if not self.attestation_id or not self.evaluator_artifact_id or not self.proposer_id or not self.signer_id:
            raise ValueError("protected attestation identities cannot be empty")
        if not _is_sha256(self.subject_hash) or not _is_sha256(self.evaluator_artifact_sha256):
            raise ValueError("protected attestation subject/evaluator hashes must be SHA-256")
        if len({item_id for item_id, _ in self.evidence_bindings}) != len(self.evidence_bindings):
            raise ValueError("protected attestation evidence bindings must be unique")
        if any(not _is_sha256(digest) for _, digest in self.evidence_bindings):
            raise ValueError("protected attestation evidence bindings require SHA-256 digests")
        if _parse_time(self.subject_frozen_at) is None or _parse_time(self.issued_at) is None:
            raise ValueError("protected attestation chronology must be timezone-aware")
        if not _is_sha256(self.signature):
            raise ValueError("protected attestation digest must be a SHA-256 value")


def _unsigned_attestation_payload(attestation: ProtectedAttestation) -> dict[str, object]:
    return {
        "attestation_id": attestation.attestation_id,
        "purpose": attestation.purpose.value,
        "subject_hash": attestation.subject_hash,
        "subject_frozen_at": attestation.subject_frozen_at,
        "evaluator_artifact_id": attestation.evaluator_artifact_id,
        "evaluator_artifact_sha256": attestation.evaluator_artifact_sha256,
        "evidence_bindings": [list(item) for item in attestation.evidence_bindings],
        "proposer_id": attestation.proposer_id,
        "signer_id": attestation.signer_id,
        "issued_at": attestation.issued_at,
        "verdict": attestation.verdict,
    }


def issue_protected_attestation(*, signing_key: bytes, **values: object) -> ProtectedAttestation:
    """Construct an attestation proposal for release-manifest review.

    ``signing_key`` is a deprecated compatibility input and creates no authority.
    Resolution requires the exact unsigned digest to be present in the governed
    release manifest; a caller-created key or policy cannot add that entry.
    """

    if not isinstance(signing_key, bytes):
        raise TypeError("signing_key compatibility input must be bytes")
    unsigned = ProtectedAttestation(signature="0" * 64, **values)  # type: ignore[arg-type]
    # Issuance only constructs a proposal. Resolution additionally requires the
    # exact unsigned digest to be present in the release-governed manifest below.
    signature = sha256(canonical_json_bytes(_unsigned_attestation_payload(unsigned))).hexdigest()
    return ProtectedAttestation(signature=signature, **values)  # type: ignore[arg-type]


@dataclass(frozen=True)
class AuthorityTrustPolicy:
    signer_keys: Tuple[Tuple[str, bytes], ...]

    def __post_init__(self) -> None:
        if not self.signer_keys:
            raise ValueError("authority trust policy requires at least one protected signer")
        if len({signer for signer, _ in self.signer_keys}) != len(self.signer_keys):
            raise ValueError("authority trust policy signer ids must be unique")
        if any(not signer or not isinstance(key, bytes) or len(key) < 32 for signer, key in self.signer_keys):
            raise ValueError("authority trust policy signer keys must contain at least 32 bytes")


@dataclass(frozen=True)
class ProtectedAuthorityContext:
    artifacts: Tuple[EvidenceArtifact, ...]
    attestations: Tuple[ProtectedAttestation, ...]
    policy: AuthorityTrustPolicy


@dataclass(frozen=True)
class AttestationResolution:
    valid: bool
    reasons: Tuple[str, ...]
    attestation_id: str | None = None


# Exact attestation payloads approved by this framework release. Adding an entry
# is a governed source change and therefore cannot be done by the runtime caller
# that supplies artifacts/attestations. These initial entries are internal
# assurance fixtures only; deployment roots require a separately reviewed
# manifest update and external evaluator custody.
PROTECTED_ATTESTATION_MANIFEST: dict[str, str] = {
    "verify": "e0642f3afbc68a579aa643c33a7116eba274acc257e5ea3943b8d6887010c6c7",
    "transfer": "b1c18bc4964d761c8c915368ca70e7b32875dc022d6806c1dbfea5f308dd0c3b",
    "tool-projection": "57faa504b675341e2dc5b3b2061a2b38c2fcab820021492c0bf2dcc582db1c9c",
    "section-check": "0a5f192c219636ec22e0dfa362c9a4d30d2c9ba412bcc51970d7966a5d6c6d43",
    "assurance": "3cd740c0ff99026b0a0c4d78e79b0ada6e096e6fc39bfea69fae546c0431df30",
    "governance": "0ecfa661bf7702920fcf977ff741e4f4b9263a284a989dc619ac9311be9cf161",
    "freeze": "c81a942cebfbaeb37f3e8aaa5f86ff83fbe4cb42f6a55241b1526fb4fde22994",
    "match": "b28ec3d25ab5751950d8660cd967e044c5bffe3a1fa28f8a9fad49909d852c89",
}


def resolve_protected_attestation(
    context: ProtectedAuthorityContext | None,
    attestation_id: str | None,
    *,
    purpose: AttestationPurpose,
    subject_hash: str,
    required_artifact_ids: Iterable[str] = (),
    required_artifact_hashes: Iterable[str] = (),
) -> AttestationResolution:
    if context is None or not attestation_id:
        return AttestationResolution(False, ("resolved_protected_attestation_missing",))
    artifact_ids = [item.artifact_id for item in context.artifacts]
    attestation_ids = [item.attestation_id for item in context.attestations]
    if len(set(artifact_ids)) != len(artifact_ids):
        return AttestationResolution(False, ("duplicate_evidence_artifact_id",))
    if len(set(attestation_ids)) != len(attestation_ids):
        return AttestationResolution(False, ("duplicate_protected_attestation_id",))
    artifacts = {item.artifact_id: item for item in context.artifacts}
    attestations = {item.attestation_id: item for item in context.attestations}
    attestation = attestations.get(attestation_id)
    if attestation is None:
        return AttestationResolution(False, (f"protected_attestation_unresolved:{attestation_id}",))
    reasons: list[str] = []
    if attestation.purpose is not purpose:
        reasons.append("protected_attestation_purpose_mismatch")
    if not _is_sha256(subject_hash) or not hmac.compare_digest(attestation.subject_hash, subject_hash):
        reasons.append("protected_attestation_subject_mismatch")
    if attestation.verdict != "PASS":
        reasons.append("protected_attestation_verdict_not_pass")
    if attestation.signer_id == attestation.proposer_id:
        reasons.append("protected_evaluator_not_separate_from_proposer")

    unsigned_digest = sha256(canonical_json_bytes(_unsigned_attestation_payload(attestation))).hexdigest()
    manifest_digest = PROTECTED_ATTESTATION_MANIFEST.get(attestation.attestation_id)
    if manifest_digest is None:
        reasons.append("protected_attestation_not_in_release_manifest")
    elif not hmac.compare_digest(manifest_digest, unsigned_digest):
        reasons.append("protected_attestation_release_manifest_mismatch")
    if not hmac.compare_digest(unsigned_digest, attestation.signature):
        reasons.append("protected_attestation_signature_invalid")

    bound = dict(attestation.evidence_bindings)
    evaluator = artifacts.get(attestation.evaluator_artifact_id)
    if evaluator is None:
        reasons.append("protected_evaluator_artifact_unresolved")
    else:
        if not evaluator.content_valid:
            reasons.append("protected_evaluator_artifact_hash_mismatch")
        if not hmac.compare_digest(evaluator.payload_sha256, attestation.evaluator_artifact_sha256):
            reasons.append("protected_evaluator_artifact_binding_mismatch")
        if evaluator.producer_id != attestation.signer_id:
            reasons.append("protected_evaluator_artifact_wrong_producer")

    issued = _parse_time(attestation.issued_at)
    subject_frozen = _parse_time(attestation.subject_frozen_at)
    if issued is None or subject_frozen is None or subject_frozen > issued:
        reasons.append("protected_attestation_subject_chronology_invalid")

    for artifact_id, digest in attestation.evidence_bindings:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            reasons.append(f"attested_evidence_artifact_unresolved:{artifact_id}")
            continue
        if not artifact.content_valid:
            reasons.append(f"attested_evidence_artifact_hash_mismatch:{artifact_id}")
        if not hmac.compare_digest(artifact.payload_sha256, digest):
            reasons.append(f"attested_evidence_binding_mismatch:{artifact_id}")
        frozen = _parse_time(artifact.frozen_at)
        if issued is None or frozen is None or frozen > issued:
            reasons.append(f"attested_evidence_chronology_invalid:{artifact_id}")

    for artifact_id in required_artifact_ids:
        if artifact_id not in bound:
            reasons.append(f"required_evidence_id_not_attested:{artifact_id}")
    bound_hashes = set(bound.values())
    for digest in required_artifact_hashes:
        if digest not in bound_hashes:
            reasons.append(f"required_evidence_hash_not_attested:{digest}")
    return AttestationResolution(not reasons, tuple(reasons), attestation.attestation_id)
