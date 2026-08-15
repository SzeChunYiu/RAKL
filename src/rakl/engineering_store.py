"""Transactional reference metadata store for ORION engineering contracts.

SQLite is used only as a deterministic local/reference backend.  The production
backend described by the engineering-closure packet is expected to provide the
same observable semantics on a database with production concurrency/HA support
(e.g. serializable PostgreSQL transactions).  No database row grants RAKL
scientific or promotion authority.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Mapping, Protocol, runtime_checkable

from .engineering_state import (
    EpistemicStatus,
    ProjectSnapshot,
    StateTransitionReceipt,
    StateTransitionRequest,
    TransitionStatus,
)




@runtime_checkable
class BlobStore(Protocol):
    """Production-neutral exact-byte storage contract.

    Implementations must preserve SHA-256 identity over the raw logical bytes;
    compression, encryption or storage tiering are physical concerns only.
    """

    def put_if_absent(self, payload: bytes) -> str: ...

    def get_verified(self, digest: str) -> bytes: ...

    def exists_verified(self, digest: str) -> bool: ...

    def stat(self, digest: str) -> Mapping[str, object]: ...


@runtime_checkable
class EngineeringStateRepository(Protocol):
    """Minimum metadata semantics required by controller/service code."""

    def initialize_project(self, snapshot: ProjectSnapshot) -> ProjectSnapshot: ...

    def head(self, project_id: str) -> ProjectSnapshot: ...

    def get_snapshot(self, snapshot_id: str) -> ProjectSnapshot: ...

    def record_epistemic_status(self, status: EpistemicStatus) -> EpistemicStatus: ...

    def latest_epistemic_status(
        self, *, project_snapshot_id: str, target_id: str, fiber_id: str
    ) -> EpistemicStatus | None: ...

    def transition_receipt(
        self, project_id: str, idempotency_key: str
    ) -> StateTransitionReceipt | None: ...

    def commit_transition(
        self, request: StateTransitionRequest, after_snapshot: ProjectSnapshot, **kwargs: object
    ) -> StateTransitionReceipt: ...

    def record_noncommitted_transition(
        self, request: StateTransitionRequest, *, status: TransitionStatus, reasons: tuple[str, ...], created_at_utc: str
    ) -> StateTransitionReceipt: ...


class EngineeringStoreError(RuntimeError):
    pass


class EngineeringIntegrityError(EngineeringStoreError):
    pass


class IdempotencyConflict(EngineeringStoreError):
    pass


class ProjectNotInitialized(EngineeringStoreError):
    pass


class SqliteEngineeringStateStore:
    """Reference transactional store with snapshot CAS and idempotent transitions.

    Properties intentionally tested here:

    * one authoritative project head;
    * immutable content-identified snapshots/statuses/receipts;
    * idempotency-key replay returns the exact prior receipt;
    * reuse of an idempotency key with a different request is rejected;
    * a transition based on a stale snapshot returns RETRY_REQUIRED rather than
      silently applying last-writer-wins;
    * committed transitions atomically install the next snapshot and receipt.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    previous_snapshot_id TEXT,
                    payload_json TEXT NOT NULL,
                    UNIQUE(project_id, sequence),
                    FOREIGN KEY(previous_snapshot_id) REFERENCES snapshots(snapshot_id)
                );
                CREATE TABLE IF NOT EXISTS project_heads (
                    project_id TEXT PRIMARY KEY,
                    snapshot_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    FOREIGN KEY(snapshot_id) REFERENCES snapshots(snapshot_id)
                );
                CREATE TABLE IF NOT EXISTS epistemic_statuses (
                    status_id TEXT PRIMARY KEY,
                    project_snapshot_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    fiber_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(project_snapshot_id) REFERENCES snapshots(snapshot_id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS epistemic_status_unique_coordinates
                    ON epistemic_statuses(project_snapshot_id, target_id, fiber_id);
                CREATE TABLE IF NOT EXISTS transitions (
                    transition_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    before_snapshot_id TEXT NOT NULL,
                    after_snapshot_id TEXT,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(project_id, idempotency_key),
                    FOREIGN KEY(before_snapshot_id) REFERENCES snapshots(snapshot_id),
                    FOREIGN KEY(after_snapshot_id) REFERENCES snapshots(snapshot_id)
                );
                """
            )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
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

    def initialize_project(self, snapshot: ProjectSnapshot) -> ProjectSnapshot:
        if snapshot.sequence != 0:
            raise ValueError("initial project snapshot must have sequence 0")
        with self._transaction() as db:
            existing = db.execute(
                "SELECT payload_json FROM snapshots WHERE snapshot_id=?",
                (snapshot.snapshot_id,),
            ).fetchone()
            if existing is not None:
                restored = ProjectSnapshot.from_dict(json.loads(existing["payload_json"]))
                if restored != snapshot:
                    raise EngineeringIntegrityError("snapshot id collision or stored snapshot corruption")
                head = db.execute(
                    "SELECT snapshot_id FROM project_heads WHERE project_id=?",
                    (snapshot.project_id,),
                ).fetchone()
                if head is None or head["snapshot_id"] != snapshot.snapshot_id:
                    raise EngineeringIntegrityError("initial snapshot exists but project head disagrees")
                return restored
            if db.execute(
                "SELECT 1 FROM project_heads WHERE project_id=?", (snapshot.project_id,)
            ).fetchone() is not None:
                raise EngineeringStoreError("project already initialized with another snapshot")
            db.execute(
                "INSERT INTO snapshots(snapshot_id,project_id,sequence,previous_snapshot_id,payload_json) VALUES(?,?,?,?,?)",
                (
                    snapshot.snapshot_id,
                    snapshot.project_id,
                    snapshot.sequence,
                    snapshot.previous_snapshot_id,
                    self._dump(snapshot.to_dict()),
                ),
            )
            db.execute(
                "INSERT INTO project_heads(project_id,snapshot_id,sequence) VALUES(?,?,?)",
                (snapshot.project_id, snapshot.snapshot_id, snapshot.sequence),
            )
        return snapshot

    def head(self, project_id: str) -> ProjectSnapshot:
        with self._connect() as db:
            row = db.execute(
                """SELECT s.payload_json FROM project_heads h
                   JOIN snapshots s ON s.snapshot_id=h.snapshot_id
                   WHERE h.project_id=?""",
                (project_id,),
            ).fetchone()
        if row is None:
            raise ProjectNotInitialized(project_id)
        return ProjectSnapshot.from_dict(json.loads(row["payload_json"]))

    def get_snapshot(self, snapshot_id: str) -> ProjectSnapshot:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload_json FROM snapshots WHERE snapshot_id=?", (snapshot_id,)
            ).fetchone()
        if row is None:
            raise KeyError(snapshot_id)
        return ProjectSnapshot.from_dict(json.loads(row["payload_json"]))

    def _require_project_snapshot(self, project_id: str, snapshot_id: str) -> ProjectSnapshot:
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot.project_id != project_id:
            raise EngineeringIntegrityError(
                "transition snapshot belongs to a different project"
            )
        return snapshot

    def record_epistemic_status(self, status: EpistemicStatus) -> EpistemicStatus:
        # Verify the bound snapshot exists before admitting the read model.
        self.get_snapshot(status.project_snapshot_id)
        payload = self._dump(status.to_dict())
        with self._transaction() as db:
            # One snapshot/target/fibre has exactly one canonical status. If the same
            # coordinates produce a different status, some supposedly snapshot-bound
            # input changed without creating a new snapshot. Fail closed rather than
            # letting UI/controller consumers race over insertion order.
            coordinate = db.execute(
                """SELECT payload_json FROM epistemic_statuses
                   WHERE project_snapshot_id=? AND target_id=? AND fiber_id=?""",
                (status.project_snapshot_id, status.target_id, status.fiber_id),
            ).fetchone()
            if coordinate is not None:
                restored = EpistemicStatus.from_dict(json.loads(coordinate["payload_json"]))
                if restored != status:
                    raise EngineeringIntegrityError(
                        "snapshot/target/fiber already bound to a different EpistemicStatus"
                    )
                return restored
            existing = db.execute(
                "SELECT payload_json FROM epistemic_statuses WHERE status_id=?", (status.status_id,)
            ).fetchone()
            if existing is not None:
                restored = EpistemicStatus.from_dict(json.loads(existing["payload_json"]))
                if restored != status:
                    raise EngineeringIntegrityError("status id collision or stored status corruption")
                return restored
            db.execute(
                "INSERT INTO epistemic_statuses(status_id,project_snapshot_id,target_id,fiber_id,payload_json) VALUES(?,?,?,?,?)",
                (
                    status.status_id,
                    status.project_snapshot_id,
                    status.target_id,
                    status.fiber_id,
                    payload,
                ),
            )
        return status

    def latest_epistemic_status(
        self,
        *,
        project_snapshot_id: str,
        target_id: str,
        fiber_id: str,
    ) -> EpistemicStatus | None:
        with self._connect() as db:
            row = db.execute(
                """SELECT payload_json FROM epistemic_statuses
                   WHERE project_snapshot_id=? AND target_id=? AND fiber_id=?
                   LIMIT 1""",
                (project_snapshot_id, target_id, fiber_id),
            ).fetchone()
        return None if row is None else EpistemicStatus.from_dict(json.loads(row["payload_json"]))

    def transition_receipt(self, project_id: str, idempotency_key: str) -> StateTransitionReceipt | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload_json FROM transitions WHERE project_id=? AND idempotency_key=?",
                (project_id, idempotency_key),
            ).fetchone()
        return None if row is None else StateTransitionReceipt.from_dict(json.loads(row["payload_json"]))

    def commit_transition(
        self,
        request: StateTransitionRequest,
        after_snapshot: ProjectSnapshot,
        *,
        produced_artifact_ids: tuple[str, ...] = (),
        metric_receipt_ids: tuple[str, ...] = (),
        residual_ids: tuple[str, ...] = (),
        created_at_utc: str,
    ) -> StateTransitionReceipt:
        if request.project_id != after_snapshot.project_id:
            raise ValueError("transition request and after snapshot project differ")
        self._require_project_snapshot(request.project_id, request.before_snapshot_id)

        with self._transaction() as db:
            replay = db.execute(
                "SELECT request_hash,payload_json FROM transitions WHERE project_id=? AND idempotency_key=?",
                (request.project_id, request.idempotency_key),
            ).fetchone()
            if replay is not None:
                if replay["request_hash"] != request.request_hash:
                    raise IdempotencyConflict(
                        "idempotency key already bound to a different transition request"
                    )
                return StateTransitionReceipt.from_dict(json.loads(replay["payload_json"]))

            head = db.execute(
                "SELECT snapshot_id,sequence FROM project_heads WHERE project_id=?",
                (request.project_id,),
            ).fetchone()
            if head is None:
                raise ProjectNotInitialized(request.project_id)

            if head["snapshot_id"] != request.before_snapshot_id:
                receipt = StateTransitionReceipt(
                    project_id=request.project_id,
                    before_snapshot_id=request.before_snapshot_id,
                    after_snapshot_id=None,
                    action=request.action,
                    action_payload_hash=request.action_payload_hash,
                    idempotency_key=request.idempotency_key,
                    request_hash=request.request_hash,
                    process_identity=request.process_identity,
                    read_set=request.read_set,
                    write_set=request.write_set,
                    produced_artifact_ids=(),
                    metric_receipt_ids=(),
                    residual_ids=(),
                    status=TransitionStatus.RETRY_REQUIRED,
                    reasons=("stale_before_snapshot_replan_on_current_head",),
                    created_at_utc=created_at_utc,
                )
                db.execute(
                    "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                    (
                        receipt.transition_id,
                        receipt.project_id,
                        receipt.idempotency_key,
                        receipt.request_hash,
                        receipt.before_snapshot_id,
                        receipt.after_snapshot_id,
                        receipt.status.value,
                        self._dump(receipt.to_dict()),
                    ),
                )
                return receipt

            if after_snapshot.previous_snapshot_id != request.before_snapshot_id:
                raise ValueError("after snapshot must point to transition before snapshot")
            if after_snapshot.sequence != int(head["sequence"]) + 1:
                raise ValueError("after snapshot sequence must advance project head exactly once")

            db.execute(
                "INSERT INTO snapshots(snapshot_id,project_id,sequence,previous_snapshot_id,payload_json) VALUES(?,?,?,?,?)",
                (
                    after_snapshot.snapshot_id,
                    after_snapshot.project_id,
                    after_snapshot.sequence,
                    after_snapshot.previous_snapshot_id,
                    self._dump(after_snapshot.to_dict()),
                ),
            )
            db.execute(
                "UPDATE project_heads SET snapshot_id=?,sequence=? WHERE project_id=?",
                (after_snapshot.snapshot_id, after_snapshot.sequence, after_snapshot.project_id),
            )
            receipt = StateTransitionReceipt(
                project_id=request.project_id,
                before_snapshot_id=request.before_snapshot_id,
                after_snapshot_id=after_snapshot.snapshot_id,
                action=request.action,
                action_payload_hash=request.action_payload_hash,
                idempotency_key=request.idempotency_key,
                request_hash=request.request_hash,
                process_identity=request.process_identity,
                read_set=request.read_set,
                write_set=request.write_set,
                produced_artifact_ids=produced_artifact_ids,
                metric_receipt_ids=metric_receipt_ids,
                residual_ids=residual_ids,
                status=TransitionStatus.COMMITTED,
                reasons=("snapshot_compare_and_swap_committed",),
                created_at_utc=created_at_utc,
            )
            db.execute(
                "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                (
                    receipt.transition_id,
                    receipt.project_id,
                    receipt.idempotency_key,
                    receipt.request_hash,
                    receipt.before_snapshot_id,
                    receipt.after_snapshot_id,
                    receipt.status.value,
                    self._dump(receipt.to_dict()),
                ),
            )
            return receipt

    def record_noncommitted_transition(
        self,
        request: StateTransitionRequest,
        *,
        status: TransitionStatus,
        reasons: tuple[str, ...],
        created_at_utc: str,
    ) -> StateTransitionReceipt:
        if status is TransitionStatus.COMMITTED:
            raise ValueError("use commit_transition for COMMITTED outcomes")
        # Ensure the request names a historical snapshot of this exact project.
        self._require_project_snapshot(request.project_id, request.before_snapshot_id)
        receipt = StateTransitionReceipt(
            project_id=request.project_id,
            before_snapshot_id=request.before_snapshot_id,
            after_snapshot_id=None,
            action=request.action,
            action_payload_hash=request.action_payload_hash,
            idempotency_key=request.idempotency_key,
            request_hash=request.request_hash,
            process_identity=request.process_identity,
            read_set=request.read_set,
            write_set=request.write_set,
            produced_artifact_ids=(),
            metric_receipt_ids=(),
            residual_ids=(),
            status=status,
            reasons=reasons,
            created_at_utc=created_at_utc,
        )
        with self._transaction() as db:
            replay = db.execute(
                "SELECT request_hash,payload_json FROM transitions WHERE project_id=? AND idempotency_key=?",
                (request.project_id, request.idempotency_key),
            ).fetchone()
            if replay is not None:
                if replay["request_hash"] != request.request_hash:
                    raise IdempotencyConflict(
                        "idempotency key already bound to a different transition request"
                    )
                return StateTransitionReceipt.from_dict(json.loads(replay["payload_json"]))
            db.execute(
                "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                (
                    receipt.transition_id,
                    receipt.project_id,
                    receipt.idempotency_key,
                    receipt.request_hash,
                    receipt.before_snapshot_id,
                    receipt.after_snapshot_id,
                    receipt.status.value,
                    self._dump(receipt.to_dict()),
                ),
            )
        return receipt
