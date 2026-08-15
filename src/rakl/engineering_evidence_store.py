"""Snapshot-versioned evidence metadata for the ORION engineering reference backend.

Exact evidence bytes live in a :class:`BlobStore` under raw SHA-256 identity.  This
module stores only immutable logical/provenance bindings and a deterministic evidence
revision.  As with semantic state, the after-snapshot id is durable commit metadata,
not part of the record content hash, avoiding snapshot/content identity cycles.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator, Mapping, Tuple

from .engineering_schema_guard import guard_and_initialize_schema
from .engineering_state import canonical_sha256
from .engineering_store import EngineeringIntegrityError


def _require_digest(value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("payload_sha256 must be lowercase SHA-256")


@dataclass(frozen=True)
class EvidenceRecord:
    project_id: str
    logical_record_id: str
    payload_sha256: str
    source_identity: str
    source_version: str | None
    provenance_payload: Mapping[str, object]
    created_sequence: int
    evidence_id: str = ""

    def __post_init__(self) -> None:
        for name in ("project_id", "logical_record_id", "source_identity"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        _require_digest(self.payload_sha256)
        if self.created_sequence < 0:
            raise ValueError("created_sequence cannot be negative")
        expected = "evidence-record:" + canonical_sha256(self.identity_payload)
        if self.evidence_id and self.evidence_id != expected:
            raise ValueError("evidence_id does not match content")
        if not self.evidence_id:
            object.__setattr__(self, "evidence_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "project_id": self.project_id,
            "logical_record_id": self.logical_record_id,
            "payload_sha256": self.payload_sha256,
            "source_identity": self.source_identity,
            "source_version": self.source_version,
            "provenance_payload": dict(self.provenance_payload),
            "created_sequence": self.created_sequence,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "evidence_id": self.evidence_id}


@dataclass(frozen=True)
class EvidenceMutationBatch:
    project_id: str
    sequence: int
    base_evidence_revision: str
    records: Tuple[EvidenceRecord, ...]
    batch_id: str = ""

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.base_evidence_revision.strip():
            raise ValueError("evidence batch requires project and base revision")
        if self.sequence < 1:
            raise ValueError("reference evidence mutation sequence must be >= 1")
        if not self.records:
            raise ValueError("evidence batch requires at least one record")
        logical_ids = [item.logical_record_id for item in self.records]
        if len(logical_ids) != len(set(logical_ids)):
            raise ValueError("evidence batch logical record ids must be unique")
        for item in self.records:
            if item.project_id != self.project_id:
                raise ValueError("evidence batch record belongs to another project")
            if item.created_sequence != self.sequence:
                raise ValueError("evidence record sequence must equal batch sequence")
        expected = "evidence-batch:" + canonical_sha256(self.identity_payload)
        if self.batch_id and self.batch_id != expected:
            raise ValueError("evidence batch id does not match content")
        if not self.batch_id:
            object.__setattr__(self, "batch_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "project_id": self.project_id,
            "sequence": self.sequence,
            "base_evidence_revision": self.base_evidence_revision,
            "records": [item.to_dict() for item in self.records],
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "batch_id": self.batch_id}


@dataclass(frozen=True)
class EvidenceBatchCommit:
    batch_id: str
    committed_snapshot_id: str
    evidence_revision: str



_SCHEMA_SQL = """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS engineering_evidence_records(
                    evidence_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    logical_record_id TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_snapshot_id TEXT NOT NULL,
                    created_sequence INTEGER NOT NULL CHECK(created_sequence >= 0),
                    payload_json TEXT NOT NULL,
                    UNIQUE(project_id, logical_record_id)
                );
                CREATE INDEX IF NOT EXISTS engineering_evidence_by_project_sequence
                    ON engineering_evidence_records(project_id, created_sequence, logical_record_id);
                CREATE TABLE IF NOT EXISTS engineering_evidence_batch_commits(
                    batch_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    committed_snapshot_id TEXT NOT NULL,
                    evidence_revision TEXT NOT NULL,
                    batch_json TEXT NOT NULL
                );
                """

class SqliteEvidenceMetadataStore:
    """Append-only logical evidence metadata with preview/commit semantics."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _init_schema(self) -> None:
        with closing(self._connect()) as db:
            # H21: verify-or-create. A populated database is checked, never repaired (see engineering_schema_guard).
            guard_and_initialize_schema(
                db, component='engineering_evidence_store', schema_version='orion-engineering-evidence-store-v1',
                tables=('engineering_evidence_records', 'engineering_evidence_batch_commits'), create_script=_SCHEMA_SQL,
            )

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.execute("COMMIT")
        except Exception:
            try:
                db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            db.close()

    @staticmethod
    def _dump(value: Mapping[str, object]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _from_dict(value: Mapping[str, object]) -> EvidenceRecord:
        return EvidenceRecord(
            project_id=str(value["project_id"]),
            logical_record_id=str(value["logical_record_id"]),
            payload_sha256=str(value["payload_sha256"]),
            source_identity=str(value["source_identity"]),
            source_version=(None if value.get("source_version") is None else str(value["source_version"])),
            provenance_payload=dict(value.get("provenance_payload", {})),
            created_sequence=int(value["created_sequence"]),
            evidence_id=str(value.get("evidence_id", "")),
        )

    def _records_at_db(
        self, db: sqlite3.Connection, project_id: str, sequence: int
    ) -> Tuple[EvidenceRecord, ...]:
        rows = db.execute(
            """SELECT payload_json FROM engineering_evidence_records
               WHERE project_id=? AND created_sequence <= ? ORDER BY logical_record_id""",
            (project_id, sequence),
        ).fetchall()
        return tuple(self._from_dict(json.loads(row["payload_json"])) for row in rows)

    def records_at(self, project_id: str, sequence: int) -> Tuple[EvidenceRecord, ...]:
        with closing(self._connect()) as db:
            return self._records_at_db(db, project_id, sequence)

    @staticmethod
    def _revision_for(project_id: str, records: Iterable[EvidenceRecord]) -> str:
        return "evidence-revision:" + canonical_sha256(
            {
                "project_id": project_id,
                "evidence_ids": [
                    item.evidence_id for item in sorted(records, key=lambda item: item.logical_record_id)
                ],
            }
        )

    def evidence_revision(self, project_id: str, sequence: int) -> str:
        return self._revision_for(project_id, self.records_at(project_id, sequence))

    def _preview_batch_revision_db(
        self, db: sqlite3.Connection, batch: EvidenceMutationBatch
    ) -> str:
        base = self._revision_for(
            batch.project_id,
            self._records_at_db(db, batch.project_id, batch.sequence - 1),
        )
        if base != batch.base_evidence_revision:
            raise EngineeringIntegrityError("evidence batch base revision is stale")
        existing = {
            item.logical_record_id: item
            for item in self._records_at_db(db, batch.project_id, batch.sequence - 1)
        }
        for record in batch.records:
            previous = existing.get(record.logical_record_id)
            if previous is not None and previous != record:
                raise EngineeringIntegrityError("logical evidence record id cannot be rebound")
            existing[record.logical_record_id] = record
        return self._revision_for(batch.project_id, existing.values())

    def preview_batch_revision(self, batch: EvidenceMutationBatch) -> str:
        with closing(self._connect()) as db:
            return self._preview_batch_revision_db(db, batch)

    def _commit_batch_db(
        self,
        db: sqlite3.Connection,
        batch: EvidenceMutationBatch,
        *,
        committed_snapshot_id: str,
        expected_evidence_revision: str,
    ) -> EvidenceBatchCommit:
        preview = self._preview_batch_revision_db(db, batch)
        if preview != expected_evidence_revision:
            raise EngineeringIntegrityError("evidence preview does not match after snapshot cutoff")
        existing_commit = db.execute(
            """SELECT project_id,committed_snapshot_id,evidence_revision,batch_json
               FROM engineering_evidence_batch_commits WHERE batch_id=?""",
            (batch.batch_id,),
        ).fetchone()
        if existing_commit is not None:
            if (
                existing_commit["project_id"] != batch.project_id
                or existing_commit["committed_snapshot_id"] != committed_snapshot_id
                or existing_commit["evidence_revision"] != expected_evidence_revision
                or json.loads(existing_commit["batch_json"]) != batch.to_dict()
            ):
                raise EngineeringIntegrityError("evidence batch id already committed differently")
            return EvidenceBatchCommit(batch.batch_id, committed_snapshot_id, expected_evidence_revision)
        for record in batch.records:
            row = db.execute(
                """SELECT payload_json FROM engineering_evidence_records
                   WHERE project_id=? AND logical_record_id=?""",
                (record.project_id, record.logical_record_id),
            ).fetchone()
            if row is not None:
                restored = self._from_dict(json.loads(row["payload_json"]))
                if restored != record:
                    raise EngineeringIntegrityError("logical evidence record id already bound differently")
                continue
            db.execute(
                "INSERT INTO engineering_evidence_records VALUES(?,?,?,?,?,?,?)",
                (
                    record.evidence_id,
                    record.project_id,
                    record.logical_record_id,
                    record.payload_sha256,
                    committed_snapshot_id,
                    record.created_sequence,
                    self._dump(record.to_dict()),
                ),
            )
        actual = self._revision_for(
            batch.project_id,
            self._records_at_db(db, batch.project_id, batch.sequence),
        )
        if actual != expected_evidence_revision:
            raise EngineeringIntegrityError("committed evidence revision diverged from preview")
        db.execute(
            "INSERT INTO engineering_evidence_batch_commits VALUES(?,?,?,?,?,?)",
            (
                batch.batch_id,
                batch.project_id,
                batch.sequence,
                committed_snapshot_id,
                actual,
                self._dump(batch.to_dict()),
            ),
        )
        return EvidenceBatchCommit(batch.batch_id, committed_snapshot_id, actual)

    def batch_commit(self, batch_id: str) -> EvidenceBatchCommit | None:
        with closing(self._connect()) as db:
            row = db.execute(
                """SELECT committed_snapshot_id,evidence_revision
                   FROM engineering_evidence_batch_commits WHERE batch_id=?""",
                (batch_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceBatchCommit(batch_id, row["committed_snapshot_id"], row["evidence_revision"])
