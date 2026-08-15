"""Runtime/build identity binding for ORION engineering release provenance.

A successful verification binds executable bytes to declared build/source coordinates.
It is infrastructure provenance only and grants no scientific or promotion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Mapping

from .engineering_state import canonical_sha256


class ArtifactVerificationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class RuntimeArtifactIdentity:
    artifact_name: str
    artifact_sha256: str
    source_revision: str
    builder_id: str
    build_type: str
    provenance_id: str
    image_digest: str | None = None
    environment_manifest_digest: str | None = None
    identity_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "artifact_name",
            "artifact_sha256",
            "source_revision",
            "builder_id",
            "build_type",
            "provenance_id",
        ):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if len(self.artifact_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.artifact_sha256):
            raise ValueError("artifact_sha256 must be lowercase SHA-256")
        if self.image_digest is not None:
            if not self.image_digest.startswith("sha256:"):
                raise ValueError("image_digest must be digest-pinned")
            digest = self.image_digest.removeprefix("sha256:")
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ValueError("image_digest must contain a lowercase SHA-256 digest")
        expected = "runtime-artifact:" + canonical_sha256(self.identity_payload)
        if self.identity_id and self.identity_id != expected:
            raise ValueError("runtime artifact identity mismatch")
        if not self.identity_id:
            object.__setattr__(self, "identity_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "artifact_name": self.artifact_name,
            "artifact_sha256": self.artifact_sha256,
            "source_revision": self.source_revision,
            "builder_id": self.builder_id,
            "build_type": self.build_type,
            "provenance_id": self.provenance_id,
            "image_digest": self.image_digest,
            "environment_manifest_digest": self.environment_manifest_digest,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "identity_id": self.identity_id}

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ArtifactVerification:
    verdict: ArtifactVerificationVerdict
    identity_id: str
    reason: str


def verify_runtime_artifact(
    identity: RuntimeArtifactIdentity,
    artifact_bytes: bytes | None,
) -> ArtifactVerification:
    if artifact_bytes is None:
        return ArtifactVerification(
            ArtifactVerificationVerdict.CANNOT_CHECK,
            identity.identity_id,
            "artifact_bytes_unavailable",
        )
    actual = sha256(artifact_bytes).hexdigest()
    if actual != identity.artifact_sha256:
        return ArtifactVerification(
            ArtifactVerificationVerdict.MISMATCH,
            identity.identity_id,
            f"artifact_digest_mismatch:{actual}",
        )
    return ArtifactVerification(
        ArtifactVerificationVerdict.VERIFIED,
        identity.identity_id,
        "artifact_bytes_match_declared_build_identity",
    )
