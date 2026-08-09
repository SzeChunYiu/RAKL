from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping


RELEASE_MANIFEST_VERSION = "rakl-release-manifest-v1"
_FULL_SHA1 = re.compile(r"^[0-9a-f]{40}$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _safe_artifact_path(root: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or not relative_path or relative_path in {".", ".."}:
        raise ValueError("artifact path must be a non-empty relative path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("artifact path contains unsafe component")

    root_resolved = root.resolve(strict=True)
    current = root_resolved
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink artifact/path component is not allowed: {relative_path}")
    resolved = current.resolve(strict=True)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("artifact escapes release root") from exc
    if not resolved.is_file():
        raise ValueError(f"artifact is not a regular file: {relative_path}")
    return resolved


class ReleaseManifestVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


@dataclass(frozen=True, order=True)
class ReleaseArtifactSpec:
    role: str
    path: str

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise ValueError("artifact role cannot be empty")
        if not self.path.strip():
            raise ValueError("artifact path cannot be empty")


@dataclass(frozen=True)
class ReleaseArtifactIdentity:
    role: str
    path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ReleaseArtifactIdentity":
        return cls(
            role=str(value["role"]),
            path=str(value["path"]),
            sha256=str(value["sha256"]),
            size_bytes=int(value["size_bytes"]),
        )


@dataclass(frozen=True)
class ReleaseManifest:
    source_revision: str
    artifacts: tuple[ReleaseArtifactIdentity, ...]
    manifest_sha256: str
    manifest_version: str = RELEASE_MANIFEST_VERSION
    authority_scope: str = "ENGINEERING_ARTIFACT_IDENTITY_ONLY"

    def unsigned_dict(self) -> dict[str, object]:
        return {
            "manifest_version": self.manifest_version,
            "source_revision": self.source_revision,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "authority_scope": self.authority_scope,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.unsigned_dict(), "manifest_sha256": self.manifest_sha256}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ReleaseManifest":
        artifacts_value = value.get("artifacts", [])
        if not isinstance(artifacts_value, list):
            raise ValueError("manifest artifacts must be a list")
        return cls(
            source_revision=str(value["source_revision"]),
            artifacts=tuple(ReleaseArtifactIdentity.from_dict(item) for item in artifacts_value),
            manifest_sha256=str(value["manifest_sha256"]),
            manifest_version=str(value.get("manifest_version", RELEASE_MANIFEST_VERSION)),
            authority_scope=str(value.get("authority_scope", "ENGINEERING_ARTIFACT_IDENTITY_ONLY")),
        )

    @property
    def canonical_json(self) -> str:
        return _canonical_bytes(self.to_dict()).decode("utf-8")


@dataclass(frozen=True)
class ReleaseManifestReport:
    verdict: ReleaseManifestVerdict
    issues: tuple[str, ...]
    verified_artifact_count: int
    manifest_sha256: str | None
    authority_scope: str = "ENGINEERING_ARTIFACT_IDENTITY_ONLY"

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict.value,
            "issues": list(self.issues),
            "verified_artifact_count": self.verified_artifact_count,
            "manifest_sha256": self.manifest_sha256,
            "authority_scope": self.authority_scope,
        }


def create_release_manifest(
    root: Path | str,
    *,
    source_revision: str,
    artifacts: Iterable[ReleaseArtifactSpec],
) -> ReleaseManifest:
    if not _FULL_SHA1.fullmatch(source_revision):
        raise ValueError("source_revision must be a full lowercase 40-hex commit SHA")
    root_path = Path(root)
    root_path.resolve(strict=True)
    specs = tuple(sorted(artifacts, key=lambda item: (item.role, item.path)))
    if not specs:
        raise ValueError("release manifest requires at least one artifact")
    keys = [(item.role, item.path) for item in specs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate artifact role/path pair")

    identities: list[ReleaseArtifactIdentity] = []
    for spec in specs:
        resolved = _safe_artifact_path(root_path, spec.path)
        payload = resolved.read_bytes()
        identities.append(
            ReleaseArtifactIdentity(
                role=spec.role,
                path=spec.path,
                sha256=_sha256(payload),
                size_bytes=len(payload),
            )
        )
    unsigned = {
        "manifest_version": RELEASE_MANIFEST_VERSION,
        "source_revision": source_revision,
        "artifacts": [artifact.to_dict() for artifact in identities],
        "authority_scope": "ENGINEERING_ARTIFACT_IDENTITY_ONLY",
    }
    digest = _sha256(_canonical_bytes(unsigned))
    return ReleaseManifest(
        source_revision=source_revision,
        artifacts=tuple(identities),
        manifest_sha256=digest,
    )


def verify_release_manifest(root: Path | str, manifest: ReleaseManifest) -> ReleaseManifestReport:
    issues: list[str] = []
    if manifest.manifest_version != RELEASE_MANIFEST_VERSION:
        issues.append(f"unsupported_manifest_version:{manifest.manifest_version}")
    if not _FULL_SHA1.fullmatch(manifest.source_revision):
        issues.append("invalid_source_revision")
    if manifest.authority_scope != "ENGINEERING_ARTIFACT_IDENTITY_ONLY":
        issues.append("invalid_authority_scope")

    unsigned_digest = _sha256(_canonical_bytes(manifest.unsigned_dict()))
    if unsigned_digest != manifest.manifest_sha256:
        issues.append("manifest_self_digest_mismatch")

    keys = [(item.role, item.path) for item in manifest.artifacts]
    if keys != sorted(keys):
        issues.append("artifact_order_not_canonical")
    if len(keys) != len(set(keys)):
        issues.append("duplicate_artifact_role_path")

    verified = 0
    root_path = Path(root)
    try:
        root_path.resolve(strict=True)
    except OSError:
        return ReleaseManifestReport(
            verdict=ReleaseManifestVerdict.FAILED,
            issues=tuple(sorted(set(issues + ["release_root_missing"]))),
            verified_artifact_count=0,
            manifest_sha256=manifest.manifest_sha256,
        )

    for artifact in manifest.artifacts:
        try:
            resolved = _safe_artifact_path(root_path, artifact.path)
        except (OSError, ValueError) as exc:
            issues.append(f"artifact_unavailable_or_unsafe:{artifact.role}:{artifact.path}:{type(exc).__name__}")
            continue
        payload = resolved.read_bytes()
        actual_digest = _sha256(payload)
        if actual_digest != artifact.sha256:
            issues.append(f"artifact_digest_mismatch:{artifact.role}:{artifact.path}")
            continue
        if len(payload) != artifact.size_bytes:
            issues.append(f"artifact_size_mismatch:{artifact.role}:{artifact.path}")
            continue
        verified += 1

    return ReleaseManifestReport(
        verdict=ReleaseManifestVerdict.VERIFIED if not issues else ReleaseManifestVerdict.FAILED,
        issues=tuple(sorted(set(issues))),
        verified_artifact_count=verified,
        manifest_sha256=manifest.manifest_sha256,
    )
