"""Migration/import receipts and parity checks for ORION durable-state evolution.

Historical stores remain evidence.  Migration creates new typed import receipts; it
does not rewrite old paths or pretend imported rows were born in the new backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable, Mapping, Tuple

from .engineering_state import canonical_sha256


class ParityVerdict(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MigrationParityReport:
    source_digest: str
    target_digest: str
    verdict: ParityVerdict
    differences: Tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.verdict is ParityVerdict.MATCH


def _canonical_object(value: object) -> object:
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, (tuple, list)):
        return [_canonical_object(item) for item in value]
    return value


def compare_migration_parity(source: object, target: object) -> MigrationParityReport:
    try:
        source_value = _canonical_object(source)
        target_value = _canonical_object(target)
        source_digest = canonical_sha256(source_value)
        target_digest = canonical_sha256(target_value)
    except Exception as error:  # projection failure is not parity
        return MigrationParityReport(
            source_digest="",
            target_digest="",
            verdict=ParityVerdict.CANNOT_CHECK,
            differences=(f"canonicalization_failed:{error.__class__.__name__}",),
        )
    if source_digest == target_digest:
        return MigrationParityReport(source_digest, target_digest, ParityVerdict.MATCH)
    return MigrationParityReport(
        source_digest,
        target_digest,
        ParityVerdict.MISMATCH,
        ("canonical_content_digest_differs",),
    )


@dataclass(frozen=True)
class ImportReceipt:
    import_id: str
    project_id: str
    source_store_kind: str
    source_store_identity: str
    source_head_hash: str
    target_backend_identity: str
    imported_object_ids: Tuple[str, ...]
    parity_digest: str
    created_at_utc: str
    receipt_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "import_id",
            "project_id",
            "source_store_kind",
            "source_store_identity",
            "source_head_hash",
            "target_backend_identity",
            "parity_digest",
            "created_at_utc",
        ):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if len(self.parity_digest) != 64 or any(ch not in "0123456789abcdef" for ch in self.parity_digest):
            raise ValueError("parity_digest must be lowercase SHA-256")
        normalized = self.created_at_utc[:-1] + "+00:00" if self.created_at_utc.endswith("Z") else self.created_at_utc
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError("created_at_utc must be timezone-aware UTC")
        if not self.imported_object_ids:
            raise ValueError("import receipt requires imported objects")
        if len(self.imported_object_ids) != len(set(self.imported_object_ids)):
            raise ValueError("imported object ids must be unique")
        expected = "import-receipt:" + canonical_sha256(self.identity_payload)
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match import content")
        if not self.receipt_id:
            object.__setattr__(self, "receipt_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "import_id": self.import_id,
            "project_id": self.project_id,
            "source_store_kind": self.source_store_kind,
            "source_store_identity": self.source_store_identity,
            "source_head_hash": self.source_head_hash,
            "target_backend_identity": self.target_backend_identity,
            "imported_object_ids": list(self.imported_object_ids),
            "parity_digest": self.parity_digest,
            "created_at_utc": self.created_at_utc,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "receipt_id": self.receipt_id}


def build_import_receipt(
    *,
    import_id: str,
    project_id: str,
    source_store_kind: str,
    source_store_identity: str,
    source_head_hash: str,
    target_backend_identity: str,
    imported_object_ids: Iterable[str],
    parity_report: MigrationParityReport,
    created_at_utc: str,
) -> ImportReceipt:
    if not parity_report.passed:
        raise ValueError("migration import receipt requires MATCH parity")
    return ImportReceipt(
        import_id=import_id,
        project_id=project_id,
        source_store_kind=source_store_kind,
        source_store_identity=source_store_identity,
        source_head_hash=source_head_hash,
        target_backend_identity=target_backend_identity,
        imported_object_ids=tuple(dict.fromkeys(imported_object_ids)),
        parity_digest=parity_report.source_digest,
        created_at_utc=created_at_utc,
    )
