"""Exact-byte blob storage adapters for ORION engineering closure.

The blob plane is deliberately weaker than epistemic authority: a verified SHA-256
only establishes byte identity/integrity.  It cannot promote evidence, claims, or
lessons.  Compression, encryption and tiering may vary by backend as long as the
logical raw-byte digest remains stable.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import tempfile
from typing import Mapping

from .engineering_store import BlobStore, EngineeringIntegrityError


def _sha256(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _valid_digest(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


@dataclass(frozen=True)
class BlobStat:
    digest: str
    raw_bytes: int
    backend: str
    location: str

    def to_dict(self) -> dict[str, object]:
        return {
            "digest": self.digest,
            "raw_bytes": self.raw_bytes,
            "backend": self.backend,
            "location": self.location,
        }


class LocalFilesystemBlobStore(BlobStore):
    """Reference local content-addressed store with verified, atomic writes."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str) -> Path:
        if not _valid_digest(digest):
            raise ValueError("digest must be lowercase SHA-256")
        return self.root / digest[:2] / digest

    def put_if_absent(self, payload: bytes) -> str:
        digest = _sha256(payload)
        target = self._path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = target.read_bytes()
            if _sha256(existing) != digest:
                raise EngineeringIntegrityError(
                    f"existing blob failed digest verification:{digest}"
                )
            return digest

        fd, temp_name = tempfile.mkstemp(prefix=".orion-blob-", dir=target.parent)
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            # Another process may have installed the same content while this writer
            # was flushing.  Verify rather than overwrite an existing object.
            if target.exists():
                existing = target.read_bytes()
                if _sha256(existing) != digest:
                    raise EngineeringIntegrityError(
                        f"concurrent blob failed digest verification:{digest}"
                    )
            else:
                os.replace(temp, target)
            return digest
        finally:
            if temp.exists():
                temp.unlink()

    def get_verified(self, digest: str) -> bytes:
        path = self._path(digest)
        if not path.exists():
            raise KeyError(digest)
        payload = path.read_bytes()
        actual = _sha256(payload)
        if actual != digest:
            raise EngineeringIntegrityError(
                f"blob digest mismatch:expected={digest}:actual={actual}"
            )
        return payload

    def exists_verified(self, digest: str) -> bool:
        try:
            self.get_verified(digest)
        except (KeyError, EngineeringIntegrityError):
            return False
        return True

    def stat(self, digest: str) -> Mapping[str, object]:
        payload = self.get_verified(digest)
        path = self._path(digest)
        return BlobStat(
            digest=digest,
            raw_bytes=len(payload),
            backend="LOCAL_FILESYSTEM_REFERENCE",
            location=str(path),
        ).to_dict()


class CanonicalPayloadStoreAdapter(BlobStore):
    """Adapter over the incumbent ``project_runtime.CanonicalPayloadStore`` API.

    The adapter is duck-typed on purpose so the engineering layer can land before
    the package refactor.  It preserves incumbent methods rather than duplicating
    object bytes or inventing a new evidence authority.
    """

    def __init__(self, incumbent_store: object) -> None:
        for method in ("put_bytes", "read_bytes", "verify", "path_for"):
            if not callable(getattr(incumbent_store, method, None)):
                raise TypeError(f"incumbent payload store lacks required method:{method}")
        self._store = incumbent_store

    def put_if_absent(self, payload: bytes) -> str:
        stored = self._store.put_bytes(payload)
        digest = str(getattr(stored, "sha256"))
        if not _valid_digest(digest):
            raise EngineeringIntegrityError("incumbent payload store returned invalid digest")
        return digest

    def get_verified(self, digest: str) -> bytes:
        payload = bytes(self._store.read_bytes(digest))
        if _sha256(payload) != digest:
            raise EngineeringIntegrityError("incumbent payload read violated SHA-256 identity")
        return payload

    def exists_verified(self, digest: str) -> bool:
        return bool(self._store.verify(digest))

    def stat(self, digest: str) -> Mapping[str, object]:
        payload = self.get_verified(digest)
        return BlobStat(
            digest=digest,
            raw_bytes=len(payload),
            backend="INCUMBENT_CANONICAL_PAYLOAD_STORE",
            location=str(self._store.path_for(digest)),
        ).to_dict()
