"""Canonical hash helpers for application-side proposal/shadow JSON artifacts.

Framework-improvement ergonomics only (issue #397). Does not grant scientific
authority, does not weaken protected gates, and does not replace TaskEpisode /
Lesson canonical constructors where those already exist.

Applications that hand-serialize shadow/proposal JSON can use this module to:

- emit deterministic canonical JSON bytes;
- hash with the hash field excluded (self-referential documents);
- emit raw 64-hex or ``sha256:``-prefixed digests;
- verify that a document's declared digest matches its payload.
"""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping, MutableMapping, Sequence

from .v3_authority import canonical_json_bytes, canonical_sha256

DEFAULT_HASH_FIELDS: tuple[str, ...] = ("artifact_hash", "content_hash", "receipt_canonical_sha256")


class DigestMode(str, Enum):
    """How digests are formatted for application consumers."""

    RAW = "RAW"
    SHA256_PREFIXED = "SHA256_PREFIXED"


def canonical_bytes(value: object) -> bytes:
    """Return sorted-key, compact, UTF-8 JSON bytes (same contract as v3 authority)."""

    return canonical_json_bytes(value)


def without_hash_fields(
    document: Mapping[str, Any],
    *,
    hash_fields: Sequence[str] = DEFAULT_HASH_FIELDS,
) -> dict[str, Any]:
    """Deep-copy ``document`` with named hash fields removed at the top level."""

    subject: dict[str, Any] = deepcopy(dict(document))
    for field in hash_fields:
        subject.pop(field, None)
    return subject


def format_digest(digest: str, mode: DigestMode = DigestMode.RAW) -> str:
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("digest must be a lowercase 64-character SHA-256 hexdigest")
    if mode is DigestMode.RAW:
        return digest
    if mode is DigestMode.SHA256_PREFIXED:
        return f"sha256:{digest}"
    raise ValueError(f"unsupported digest mode: {mode!r}")


def parse_digest(value: str) -> str:
    """Normalize a raw or ``sha256:``-prefixed digest to lowercase 64-hex."""

    if not isinstance(value, str) or not value:
        raise ValueError("digest value must be a non-empty string")
    digest = value[7:] if value.startswith("sha256:") else value
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("digest must be a lowercase 64-character SHA-256 hexdigest")
    return digest


def hash_document(
    document: Mapping[str, Any],
    *,
    exclude_hash_fields: bool = True,
    hash_fields: Sequence[str] = DEFAULT_HASH_FIELDS,
    mode: DigestMode = DigestMode.RAW,
) -> str:
    """Hash a mapping under the canonical JSON serializer.

    When ``exclude_hash_fields`` is true (default), top-level fields named in
    ``hash_fields`` are omitted before hashing so self-referential digests can
    be filled in after the fact.
    """

    subject: Mapping[str, Any]
    if exclude_hash_fields:
        subject = without_hash_fields(document, hash_fields=hash_fields)
    else:
        subject = document
    return format_digest(canonical_sha256(subject), mode=mode)


def hash_bytes(payload: bytes, *, mode: DigestMode = DigestMode.RAW) -> str:
    return format_digest(sha256(payload).hexdigest(), mode=mode)


def bind_artifact_hash(
    document: Mapping[str, Any],
    *,
    hash_field: str = "artifact_hash",
    mode: DigestMode = DigestMode.RAW,
    extra_exclude_fields: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a shallow-copied document with ``hash_field`` set to the digest.

    Existing constructors for TaskEpisode/Lesson remain authoritative for those
    types; this helper is for application shadow/proposal JSON only.
    """

    exclude = tuple(dict.fromkeys((hash_field, *DEFAULT_HASH_FIELDS, *extra_exclude_fields)))
    digest = hash_document(
        document,
        exclude_hash_fields=True,
        hash_fields=exclude,
        mode=mode,
    )
    bound: dict[str, Any] = dict(document)
    bound[hash_field] = digest
    return bound


def verify_document_hash(
    document: Mapping[str, Any],
    *,
    hash_field: str = "artifact_hash",
    mode: DigestMode | None = None,
    extra_exclude_fields: Sequence[str] = (),
) -> tuple[bool, tuple[str, ...]]:
    """Verify that ``document[hash_field]`` matches the canonical payload digest.

    Returns ``(ok, reasons)``. A matching digest never grants scientific authority.
    """

    reasons: list[str] = []
    if hash_field not in document:
        return False, (f"{hash_field}_missing",)
    declared_raw = document[hash_field]
    if not isinstance(declared_raw, str):
        return False, (f"{hash_field}_not_string",)
    try:
        declared = parse_digest(declared_raw)
    except ValueError:
        return False, (f"{hash_field}_malformed",)

    if mode is None:
        mode = DigestMode.SHA256_PREFIXED if declared_raw.startswith("sha256:") else DigestMode.RAW

    exclude = tuple(dict.fromkeys((hash_field, *DEFAULT_HASH_FIELDS, *extra_exclude_fields)))
    expected = parse_digest(
        hash_document(
            document,
            exclude_hash_fields=True,
            hash_fields=exclude,
            mode=mode,
        )
    )
    if declared != expected:
        reasons.append(f"{hash_field}_mismatch")
    return (not reasons), tuple(reasons)


def assert_stale_hash_fails(
    document: MutableMapping[str, Any],
    *,
    mutate_key: str,
    mutate_value: Any,
    hash_field: str = "artifact_hash",
) -> None:
    """Hostile known-answer: mutate payload after binding and require verify fail-closed."""

    bound = bind_artifact_hash(document, hash_field=hash_field)
    ok, reasons = verify_document_hash(bound, hash_field=hash_field)
    if not ok:
        raise AssertionError(f"freshly bound document must verify; got {reasons}")
    stale = dict(bound)
    stale[mutate_key] = mutate_value
    ok, reasons = verify_document_hash(stale, hash_field=hash_field)
    if ok:
        raise AssertionError("stale hash must fail closed after payload mutation")
    if f"{hash_field}_mismatch" not in reasons:
        raise AssertionError(f"expected mismatch reason; got {reasons}")
