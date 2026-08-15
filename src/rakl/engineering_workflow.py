"""Durable-history reference workflow engine for ORION engineering closure.

The reference engine demonstrates the failure semantics required from a production
workflow backend.  It does *not* promise exactly-once external effects.  Activities
must declare retry safety; ambiguous completion of a non-retry-safe activity becomes
``RECOVERY_REQUIRED``.  Workflow progress is bound to the epistemic snapshot from
which it was planned.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Mapping, Tuple

from .engineering_state import canonical_sha256


class WorkflowStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


class ActivityStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class WorkflowIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class ActivitySpec:
    activity_id: str
    invocation_id: str
    input_digest: str
    retry_safe: bool
    external_effect: bool
    max_attempts: int = 3

    def __post_init__(self) -> None:
        for name in ("activity_id", "invocation_id", "input_digest"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "activity_id": self.activity_id,
            "invocation_id": self.invocation_id,
            "input_digest": self.input_digest,
            "retry_safe": self.retry_safe,
            "external_effect": self.external_effect,
            "max_attempts": self.max_attempts,
        }


@dataclass(frozen=True)
class WorkflowRecord:
    workflow_id: str
    project_id: str
    project_snapshot_id: str
    status: WorkflowStatus
    head_event_hash: str


@dataclass(frozen=True)
class ActivityRecord:
    workflow_id: str
    spec: ActivitySpec
    status: ActivityStatus
    attempt_count: int
    result_digest: str | None
    last_error: str | None


@dataclass(frozen=True)
class WorkflowEvent:
    workflow_id: str
    sequence: int
    kind: str
    payload: Mapping[str, object]
    previous_event_hash: str
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not self.workflow_id or not self.kind:
            raise ValueError("workflow event identity is required")
        if self.sequence < 0:
            raise ValueError("event sequence cannot be negative")
        expected = canonical_sha256(
            {
                "workflow_id": self.workflow_id,
                "sequence": self.sequence,
                "kind": self.kind,
                "payload": dict(self.payload),
                "previous_event_hash": self.previous_event_hash,
            }
        )
        if self.event_hash and self.event_hash != expected:
            raise ValueError("workflow event hash mismatch")
        if not self.event_hash:
            object.__setattr__(self, "event_hash", expected)

    def to_dict(self) -> dict[str, object]:
        return {
            "workflow_id": self.workflow_id,
            "sequence": self.sequence,
            "kind": self.kind,
            "payload": dict(self.payload),
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
        }


class SqliteReferenceWorkflowEngine:
    """Deterministic local durable-history implementation for tests and development."""

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
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS workflows(
                    workflow_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    project_snapshot_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    next_sequence INTEGER NOT NULL,
                    head_event_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflow_events(
                    workflow_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_event_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    PRIMARY KEY(workflow_id, sequence),
                    UNIQUE(event_hash),
                    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id)
                );
                CREATE TABLE IF NOT EXISTS workflow_activities(
                    workflow_id TEXT NOT NULL,
                    activity_id TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    result_digest TEXT,
                    last_error TEXT,
                    PRIMARY KEY(workflow_id, activity_id),
                    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id)
                );
                """
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
    def _verify_snapshot_binding_if_available(
        db: sqlite3.Connection, project_id: str, project_snapshot_id: str
    ) -> None:
        """Verify snapshot binding when workflow history shares the project DB.

        Standalone workflow-history tests may intentionally use a separate database,
        in which case no snapshot table exists and the history remains a transport
        reference. In the integrated runtime database, a workflow may not bind an
        invented or cross-project snapshot identity.
        """
        table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='snapshots'"
        ).fetchone()
        if table is None:
            return
        row = db.execute(
            "SELECT project_id FROM snapshots WHERE snapshot_id=?",
            (project_snapshot_id,),
        ).fetchone()
        if row is None:
            raise WorkflowIntegrityError("workflow references unknown project snapshot")
        if row["project_id"] != project_id:
            raise WorkflowIntegrityError("workflow snapshot belongs to a different project")

    def _append_event(
        self, db: sqlite3.Connection, workflow_id: str, kind: str, payload: Mapping[str, object]
    ) -> WorkflowEvent:
        row = db.execute(
            "SELECT next_sequence,head_event_hash FROM workflows WHERE workflow_id=?",
            (workflow_id,),
        ).fetchone()
        if row is None:
            raise KeyError(workflow_id)
        event = WorkflowEvent(
            workflow_id=workflow_id,
            sequence=int(row["next_sequence"]),
            kind=kind,
            payload=dict(payload),
            previous_event_hash=str(row["head_event_hash"]),
        )
        db.execute(
            "INSERT INTO workflow_events VALUES(?,?,?,?,?,?)",
            (
                event.workflow_id,
                event.sequence,
                event.kind,
                self._dump(dict(event.payload)),
                event.previous_event_hash,
                event.event_hash,
            ),
        )
        db.execute(
            "UPDATE workflows SET next_sequence=?,head_event_hash=? WHERE workflow_id=?",
            (event.sequence + 1, event.event_hash, workflow_id),
        )
        return event

    def start_workflow(
        self, *, workflow_id: str, project_id: str, project_snapshot_id: str
    ) -> WorkflowRecord:
        if not workflow_id or not project_id or not project_snapshot_id:
            raise ValueError("workflow/project/snapshot identity required")
        with self._tx() as db:
            self._verify_snapshot_binding_if_available(db, project_id, project_snapshot_id)
            existing = db.execute(
                "SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,)
            ).fetchone()
            if existing is not None:
                if (
                    existing["project_id"] != project_id
                    or existing["project_snapshot_id"] != project_snapshot_id
                ):
                    raise WorkflowIntegrityError("workflow id reused with different binding")
                return self.workflow(workflow_id, _db=db)
            db.execute(
                "INSERT INTO workflows VALUES(?,?,?,?,?,?)",
                (workflow_id, project_id, project_snapshot_id, WorkflowStatus.RUNNING.value, 0, ""),
            )
            self._append_event(
                db,
                workflow_id,
                "WORKFLOW_STARTED",
                {"project_id": project_id, "project_snapshot_id": project_snapshot_id},
            )
            return self.workflow(workflow_id, _db=db)

    def workflow(self, workflow_id: str, *, _db: sqlite3.Connection | None = None) -> WorkflowRecord:
        owns = _db is None
        db = self._connect() if owns else _db
        try:
            row = db.execute("SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,)).fetchone()
            if row is None:
                raise KeyError(workflow_id)
            return WorkflowRecord(
                workflow_id=row["workflow_id"],
                project_id=row["project_id"],
                project_snapshot_id=row["project_snapshot_id"],
                status=WorkflowStatus(row["status"]),
                head_event_hash=row["head_event_hash"],
            )
        finally:
            if owns:
                db.close()

    def schedule_activity(self, workflow_id: str, spec: ActivitySpec) -> ActivityRecord:
        with self._tx() as db:
            workflow = self.workflow(workflow_id, _db=db)
            if workflow.status is not WorkflowStatus.RUNNING:
                raise WorkflowIntegrityError("cannot schedule activity on non-running workflow")
            existing = db.execute(
                "SELECT * FROM workflow_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, spec.activity_id),
            ).fetchone()
            if existing is not None:
                restored = self._activity_from_row(existing)
                if restored.spec != spec:
                    raise WorkflowIntegrityError("activity id reused with different specification")
                return restored
            db.execute(
                "INSERT INTO workflow_activities VALUES(?,?,?,?,?,?,?)",
                (
                    workflow_id,
                    spec.activity_id,
                    self._dump(spec.to_dict()),
                    ActivityStatus.SCHEDULED.value,
                    0,
                    None,
                    None,
                ),
            )
            self._append_event(db, workflow_id, "ACTIVITY_SCHEDULED", spec.to_dict())
            return ActivityRecord(workflow_id, spec, ActivityStatus.SCHEDULED, 0, None, None)

    @staticmethod
    def _spec_from_dict(value: Mapping[str, object]) -> ActivitySpec:
        return ActivitySpec(
            activity_id=str(value["activity_id"]),
            invocation_id=str(value["invocation_id"]),
            input_digest=str(value["input_digest"]),
            retry_safe=bool(value["retry_safe"]),
            external_effect=bool(value["external_effect"]),
            max_attempts=int(value["max_attempts"]),
        )

    def _activity_from_row(self, row: sqlite3.Row) -> ActivityRecord:
        return ActivityRecord(
            workflow_id=row["workflow_id"],
            spec=self._spec_from_dict(json.loads(row["spec_json"])),
            status=ActivityStatus(row["status"]),
            attempt_count=int(row["attempt_count"]),
            result_digest=row["result_digest"],
            last_error=row["last_error"],
        )

    def activity(self, workflow_id: str, activity_id: str) -> ActivityRecord:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM workflow_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone()
        if row is None:
            raise KeyError((workflow_id, activity_id))
        return self._activity_from_row(row)

    def begin_activity(self, workflow_id: str, activity_id: str) -> ActivityRecord:
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM workflow_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone()
            if row is None:
                raise KeyError((workflow_id, activity_id))
            activity = self._activity_from_row(row)
            if activity.status is ActivityStatus.COMPLETED:
                return activity
            if activity.status is ActivityStatus.RUNNING:
                # We cannot tell whether a worker is still live from durable history alone.
                # Explicit recovery is required before another attempt is started.
                raise WorkflowIntegrityError("activity already RUNNING; recover before retry")
            if activity.status in {ActivityStatus.FAILED, ActivityStatus.RECOVERY_REQUIRED}:
                raise WorkflowIntegrityError("activity is terminal or recovery-blocked")
            if activity.attempt_count >= activity.spec.max_attempts:
                raise WorkflowIntegrityError("activity attempt limit exhausted")
            attempt = activity.attempt_count + 1
            db.execute(
                "UPDATE workflow_activities SET status=?,attempt_count=?,last_error=NULL WHERE workflow_id=? AND activity_id=?",
                (ActivityStatus.RUNNING.value, attempt, workflow_id, activity_id),
            )
            self._append_event(
                db,
                workflow_id,
                "ACTIVITY_ATTEMPT_STARTED",
                {"activity_id": activity_id, "attempt": attempt},
            )
            return ActivityRecord(
                workflow_id, activity.spec, ActivityStatus.RUNNING, attempt, None, None
            )

    def complete_activity(
        self, workflow_id: str, activity_id: str, *, result_digest: str
    ) -> ActivityRecord:
        if not result_digest:
            raise ValueError("result_digest is required")
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM workflow_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone()
            if row is None:
                raise KeyError((workflow_id, activity_id))
            activity = self._activity_from_row(row)
            if activity.status is ActivityStatus.COMPLETED:
                if activity.result_digest != result_digest:
                    raise WorkflowIntegrityError("completed activity result cannot be rebound")
                return activity
            if activity.status is not ActivityStatus.RUNNING:
                raise WorkflowIntegrityError("only a RUNNING activity may complete")
            db.execute(
                "UPDATE workflow_activities SET status=?,result_digest=? WHERE workflow_id=? AND activity_id=?",
                (ActivityStatus.COMPLETED.value, result_digest, workflow_id, activity_id),
            )
            self._append_event(
                db,
                workflow_id,
                "ACTIVITY_COMPLETED",
                {
                    "activity_id": activity_id,
                    "attempt": activity.attempt_count,
                    "result_digest": result_digest,
                },
            )
            return ActivityRecord(
                workflow_id,
                activity.spec,
                ActivityStatus.COMPLETED,
                activity.attempt_count,
                result_digest,
                None,
            )

    def fail_activity(
        self,
        workflow_id: str,
        activity_id: str,
        *,
        error: str,
        retryable: bool,
    ) -> ActivityRecord:
        if not error:
            raise ValueError("error is required")
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM workflow_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone()
            if row is None:
                raise KeyError((workflow_id, activity_id))
            activity = self._activity_from_row(row)
            if activity.status is not ActivityStatus.RUNNING:
                raise WorkflowIntegrityError("only a RUNNING activity may fail")
            can_retry = (
                retryable
                and activity.spec.retry_safe
                and activity.attempt_count < activity.spec.max_attempts
            )
            next_status = ActivityStatus.SCHEDULED if can_retry else ActivityStatus.FAILED
            db.execute(
                "UPDATE workflow_activities SET status=?,last_error=? WHERE workflow_id=? AND activity_id=?",
                (next_status.value, error, workflow_id, activity_id),
            )
            self._append_event(
                db,
                workflow_id,
                "ACTIVITY_FAILED",
                {
                    "activity_id": activity_id,
                    "attempt": activity.attempt_count,
                    "retryable": retryable,
                    "retry_authorized": can_retry,
                    "error": error,
                },
            )
            return ActivityRecord(
                workflow_id,
                activity.spec,
                next_status,
                activity.attempt_count,
                None,
                error,
            )

    def recover_ambiguous_activity(self, workflow_id: str, activity_id: str) -> ActivityRecord:
        """Resolve a persisted RUNNING attempt after worker loss.

        A retry-safe activity can return to SCHEDULED. A non-retry-safe activity is
        explicitly blocked because an external effect may already have happened.
        """
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM workflow_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone()
            if row is None:
                raise KeyError((workflow_id, activity_id))
            activity = self._activity_from_row(row)
            if activity.status is not ActivityStatus.RUNNING:
                return activity
            if activity.spec.retry_safe and activity.attempt_count < activity.spec.max_attempts:
                next_status = ActivityStatus.SCHEDULED
                kind = "ACTIVITY_AMBIGUOUS_RETRY_AUTHORIZED"
            else:
                next_status = ActivityStatus.RECOVERY_REQUIRED
                kind = "ACTIVITY_AMBIGUOUS_RECOVERY_REQUIRED"
            db.execute(
                "UPDATE workflow_activities SET status=?,last_error=? WHERE workflow_id=? AND activity_id=?",
                (
                    next_status.value,
                    "worker_lost_after_activity_started_without_terminal_result",
                    workflow_id,
                    activity_id,
                ),
            )
            self._append_event(
                db,
                workflow_id,
                kind,
                {"activity_id": activity_id, "attempt": activity.attempt_count},
            )
            if next_status is ActivityStatus.RECOVERY_REQUIRED:
                db.execute(
                    "UPDATE workflows SET status=? WHERE workflow_id=?",
                    (WorkflowStatus.RECOVERY_REQUIRED.value, workflow_id),
                )
            return ActivityRecord(
                workflow_id,
                activity.spec,
                next_status,
                activity.attempt_count,
                None,
                "worker_lost_after_activity_started_without_terminal_result",
            )

    def check_snapshot_freshness(
        self, workflow_id: str, *, current_project_snapshot_id: str
    ) -> WorkflowStatus:
        workflow = self.workflow(workflow_id)
        if workflow.project_snapshot_id != current_project_snapshot_id:
            return WorkflowStatus.CANNOT_CHECK
        return workflow.status

    def complete_workflow(self, workflow_id: str) -> WorkflowRecord:
        with self._tx() as db:
            workflow = self.workflow(workflow_id, _db=db)
            if workflow.status is not WorkflowStatus.RUNNING:
                return workflow
            rows = db.execute(
                "SELECT status FROM workflow_activities WHERE workflow_id=?", (workflow_id,)
            ).fetchall()
            if any(ActivityStatus(row["status"]) is not ActivityStatus.COMPLETED for row in rows):
                raise WorkflowIntegrityError("workflow has incomplete activities")
            db.execute(
                "UPDATE workflows SET status=? WHERE workflow_id=?",
                (WorkflowStatus.COMPLETED.value, workflow_id),
            )
            self._append_event(db, workflow_id, "WORKFLOW_COMPLETED", {})
            return self.workflow(workflow_id, _db=db)

    def events(self, workflow_id: str) -> Tuple[WorkflowEvent, ...]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM workflow_events WHERE workflow_id=? ORDER BY sequence",
                (workflow_id,),
            ).fetchall()
        return tuple(
            WorkflowEvent(
                workflow_id=row["workflow_id"],
                sequence=int(row["sequence"]),
                kind=row["kind"],
                payload=json.loads(row["payload_json"]),
                previous_event_hash=row["previous_event_hash"],
                event_hash=row["event_hash"],
            )
            for row in rows
        )

    def verify_history(
        self, workflow_id: str, *, expected_head_hash: str | None = None
    ) -> bool:
        """Verify the internal chain and, optionally, an externally sealed head.

        An internally valid shorter history cannot prove that no tail records were
        lost.  Callers resuming from a previously sealed workflow head should pass
        ``expected_head_hash`` so tail truncation is detectable rather than silently
        accepted.
        """
        try:
            events = self.events(workflow_id)
        except (ValueError, json.JSONDecodeError):
            return False
        previous = ""
        for expected_sequence, event in enumerate(events):
            if event.sequence != expected_sequence or event.previous_event_hash != previous:
                return False
            previous = event.event_hash
        try:
            workflow = self.workflow(workflow_id)
        except KeyError:
            return False
        if workflow.head_event_hash != previous:
            return False
        if expected_head_hash is not None and expected_head_hash != previous:
            return False
        return True
