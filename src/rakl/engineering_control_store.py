"""Durable authority-neutral projection store for control-plane artifacts.

Incumbent RAKL objects (MetricReceipt, saturation certificates, hard-gate
observations, controller decisions and residual events) remain authoritative under
their existing contracts.  This store only binds their canonical projections to an
exact project snapshot so APIs, observatory views and recovery tooling can query one
consistent engineering state.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Mapping, Tuple

from .engineering_schema_guard import guard_and_initialize_schema
from .engineering_state import canonical_sha256
from .engineering_store import EngineeringIntegrityError


class ControlArtifactKind(str, Enum):
    METRIC_RECEIPT = "METRIC_RECEIPT"
    SATURATION_CERTIFICATE = "SATURATION_CERTIFICATE"
    HARD_GATE = "HARD_GATE"
    CONTROLLER_DECISION = "CONTROLLER_DECISION"
    RESIDUAL_EVENT = "RESIDUAL_EVENT"
    AUTHORITY_PROJECTION = "AUTHORITY_PROJECTION"


@dataclass(frozen=True)
class ControlArtifactProjection:
    project_snapshot_id: str
    kind: ControlArtifactKind
    source_object_id: str
    canonical_payload: Mapping[str, object]
    source_receipt_ids: Tuple[str, ...] = ()
    record_id: str = ""

    def __post_init__(self) -> None:
        if not self.project_snapshot_id.strip() or not self.source_object_id.strip():
            raise ValueError("snapshot and source object identity are required")
        if len(self.source_receipt_ids) != len(set(self.source_receipt_ids)):
            raise ValueError("source receipt ids must be unique")
        expected = "control-record:" + canonical_sha256(self.identity_payload)
        if self.record_id and self.record_id != expected:
            raise ValueError("control record id does not match content")
        if not self.record_id:
            object.__setattr__(self, "record_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "project_snapshot_id": self.project_snapshot_id,
            "kind": self.kind.value,
            "source_object_id": self.source_object_id,
            "canonical_payload": dict(self.canonical_payload),
            "source_receipt_ids": list(self.source_receipt_ids),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "record_id": self.record_id}

    @property
    def grants_scientific_authority(self) -> bool:
        return False



_SCHEMA_SQL = """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS control_projection(
                    record_id TEXT PRIMARY KEY,
                    project_snapshot_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    source_object_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(project_snapshot_id,kind,source_object_id)
                );
                CREATE INDEX IF NOT EXISTS control_projection_snapshot_kind
                    ON control_projection(project_snapshot_id,kind,source_object_id);
                """

class SqliteControlProjectionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _init_schema(self) -> None:
        with closing(self._connect()) as db:
            # H21: verify-or-create. A populated database is checked, never repaired (see engineering_schema_guard).
            guard_and_initialize_schema(
                db, component='engineering_control_store', schema_version='orion-engineering-control-store-v1',
                tables=('control_projection',), create_script=_SCHEMA_SQL,
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
    def _verify_snapshot_if_available(
        db: sqlite3.Connection, project_snapshot_id: str
    ) -> None:
        table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='snapshots'"
        ).fetchone()
        if table is None:
            return
        if db.execute(
            "SELECT 1 FROM snapshots WHERE snapshot_id=?", (project_snapshot_id,)
        ).fetchone() is None:
            raise EngineeringIntegrityError(
                "control projection references unknown project snapshot"
            )

    def record(self, projection: ControlArtifactProjection) -> ControlArtifactProjection:
        with self._tx() as db:
            self._verify_snapshot_if_available(db, projection.project_snapshot_id)
            existing = db.execute(
                """SELECT payload_json FROM control_projection
                   WHERE project_snapshot_id=? AND kind=? AND source_object_id=?""",
                (
                    projection.project_snapshot_id,
                    projection.kind.value,
                    projection.source_object_id,
                ),
            ).fetchone()
            if existing is not None:
                restored = self._from_dict(json.loads(existing["payload_json"]))
                if restored != projection:
                    raise EngineeringIntegrityError(
                        "same snapshot/control coordinate recomputed with different content"
                    )
                return restored
            db.execute(
                "INSERT INTO control_projection VALUES(?,?,?,?,?)",
                (
                    projection.record_id,
                    projection.project_snapshot_id,
                    projection.kind.value,
                    projection.source_object_id,
                    self._dump(projection.to_dict()),
                ),
            )
        return projection

    def records(
        self,
        project_snapshot_id: str,
        *,
        kind: ControlArtifactKind | None = None,
    ) -> Tuple[ControlArtifactProjection, ...]:
        with closing(self._connect()) as db:
            if kind is None:
                rows = db.execute(
                    """SELECT payload_json FROM control_projection
                       WHERE project_snapshot_id=? ORDER BY kind,source_object_id""",
                    (project_snapshot_id,),
                ).fetchall()
            else:
                rows = db.execute(
                    """SELECT payload_json FROM control_projection
                       WHERE project_snapshot_id=? AND kind=? ORDER BY source_object_id""",
                    (project_snapshot_id, kind.value),
                ).fetchall()
        return tuple(self._from_dict(json.loads(row["payload_json"])) for row in rows)

    def control_revision(self, project_snapshot_id: str) -> str:
        records = self.records(project_snapshot_id)
        return "control-revision:" + canonical_sha256(
            {
                "project_snapshot_id": project_snapshot_id,
                "record_ids": [item.record_id for item in records],
            }
        )

    @staticmethod
    def _from_dict(value: Mapping[str, object]) -> ControlArtifactProjection:
        return ControlArtifactProjection(
            project_snapshot_id=str(value["project_snapshot_id"]),
            kind=ControlArtifactKind(str(value["kind"])),
            source_object_id=str(value["source_object_id"]),
            canonical_payload=dict(value.get("canonical_payload", {})),
            source_receipt_ids=tuple(str(item) for item in value.get("source_receipt_ids", ())),
            record_id=str(value.get("record_id", "")),
        )
