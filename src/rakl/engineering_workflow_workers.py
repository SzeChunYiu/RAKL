"""E6: durable multi-worker workflow execution.

The reference engine already gives one worker hash-chained history, snapshot
binding, retries and RECOVERY_REQUIRED. What it does not have is a second
worker. This adds what a second worker needs and nothing else:

    lease         exactly one worker holds an activity at a time
    heartbeat     a holder proves it is alive; a silent holder is presumed dead
    reclaim       an expired lease may be taken by another worker
    idempotency   the same logical mutation, delivered twice, executes once

The distributed contract is deliberately weaker than exactly-once, and it says
so. Exactly-once across an external side effect is not achievable without the
effect's own idempotency; what IS achievable is: at most one worker acts under a
lease, a completed activity is never re-executed, and any window in which an
external effect may or may not have happened is RECOVERY_REQUIRED, never
silently retried and never silently completed.

The four crash windows the tests drive:

    before action     lease held, no work done      -> reclaimable, re-run is safe
    during action     lease held, work in progress  -> reclaimable if retry_safe,
                                                       RECOVERY_REQUIRED otherwise
    after effect      effect done, no receipt       -> RECOVERY_REQUIRED, always
    before terminal   receipt written, terminal not -> reclaim reads the receipt,
                                                       does not re-execute

Every state transition is an event on the same hash chain the reference engine
already keeps, so a durable-history backend replays the same log.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator, Mapping

from .engineering_state import canonical_sha256
from .engineering_workflow import (
    ActivitySpec,
    ActivityStatus,
    WorkflowIntegrityError,
)


class LeaseState(str, Enum):
    FREE = "FREE"
    HELD = "HELD"
    EXPIRED = "EXPIRED"


class ClaimVerdict(str, Enum):
    """What happened when a worker tried to take an activity."""

    ACQUIRED = "ACQUIRED"
    HELD_BY_LIVE_WORKER = "HELD_BY_LIVE_WORKER"
    RECLAIMED_FROM_DEAD_WORKER = "RECLAIMED_FROM_DEAD_WORKER"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


@dataclass(frozen=True)
class Lease:
    workflow_id: str
    activity_id: str
    worker_id: str
    lease_token: str
    acquired_at: int
    heartbeat_at: int
    ttl: int

    def alive_at(self, now: int) -> bool:
        return now - self.heartbeat_at < self.ttl


@dataclass(frozen=True)
class ClaimResult:
    verdict: ClaimVerdict
    lease: Lease | None = None
    reason: str = ""


@dataclass(frozen=True)
class WorkerActivityRecord:
    workflow_id: str
    activity_id: str
    status: ActivityStatus
    attempt_count: int
    lease: Lease | None
    effect_started: bool
    result_digest: str | None
    idempotency_key: str


class SqliteWorkerWorkflowEngine:
    """Multi-worker leases, heartbeats and idempotency over a durable event log.

    Time is injected as an integer so tests can drive worker death and lease
    expiry deterministically. A production backend substitutes its clock.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # --- plumbing -----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5.0)
        db.row_factory = sqlite3.Row
        return db

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

    def _init_schema(self) -> None:
        db = self._connect()
        try:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS worker_activities (
                    workflow_id TEXT NOT NULL,
                    activity_id TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    effect_started INTEGER NOT NULL DEFAULT 0,
                    result_digest TEXT,
                    idempotency_key TEXT NOT NULL,
                    PRIMARY KEY (workflow_id, activity_id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ux_worker_activity_idem
                    ON worker_activities (workflow_id, idempotency_key);
                CREATE TABLE IF NOT EXISTS leases (
                    workflow_id TEXT NOT NULL,
                    activity_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    lease_token TEXT NOT NULL,
                    acquired_at INTEGER NOT NULL,
                    heartbeat_at INTEGER NOT NULL,
                    ttl INTEGER NOT NULL,
                    PRIMARY KEY (workflow_id, activity_id)
                );
                CREATE TABLE IF NOT EXISTS worker_events (
                    workflow_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_event_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    PRIMARY KEY (workflow_id, sequence)
                );
                """
            )
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _dump(value: Mapping[str, object]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def _append_event(self, db: sqlite3.Connection, workflow_id: str, kind: str, payload: Mapping[str, object]) -> str:
        row = db.execute(
            "SELECT sequence,event_hash FROM worker_events WHERE workflow_id=? ORDER BY sequence DESC LIMIT 1",
            (workflow_id,),
        ).fetchone()
        sequence = 0 if row is None else row["sequence"] + 1
        previous = "" if row is None else row["event_hash"]
        event_hash = canonical_sha256(
            {"workflow_id": workflow_id, "sequence": sequence, "kind": kind,
             "payload": dict(payload), "previous_event_hash": previous}
        )
        db.execute(
            "INSERT INTO worker_events (workflow_id,sequence,kind,payload_json,previous_event_hash,event_hash) VALUES (?,?,?,?,?,?)",
            (workflow_id, sequence, kind, self._dump(payload), previous, event_hash),
        )
        return event_hash

    def _lease_from_row(self, row: sqlite3.Row | None) -> Lease | None:
        if row is None:
            return None
        return Lease(
            workflow_id=row["workflow_id"], activity_id=row["activity_id"],
            worker_id=row["worker_id"], lease_token=row["lease_token"],
            acquired_at=row["acquired_at"], heartbeat_at=row["heartbeat_at"], ttl=row["ttl"],
        )

    # --- scheduling ---------------------------------------------------------

    def schedule(self, workflow_id: str, spec: ActivitySpec, *, idempotency_key: str) -> None:
        """Register an activity. Re-scheduling the same idempotency key is a no-op."""

        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required for every scheduled activity")
        with self._tx() as db:
            existing = db.execute(
                "SELECT activity_id,spec_json FROM worker_activities WHERE workflow_id=? AND idempotency_key=?",
                (workflow_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["activity_id"] != spec.activity_id or existing["spec_json"] != self._dump(spec.to_dict()):
                    raise WorkflowIntegrityError(
                        "idempotency key already bound to a different activity or spec"
                    )
                return  # duplicate delivery of the same logical schedule: no-op
            db.execute(
                "INSERT INTO worker_activities (workflow_id,activity_id,spec_json,status,idempotency_key) VALUES (?,?,?,?,?)",
                (workflow_id, spec.activity_id, self._dump(spec.to_dict()), ActivityStatus.SCHEDULED.value, idempotency_key),
            )
            self._append_event(db, workflow_id, "ACTIVITY_SCHEDULED",
                               {"activity_id": spec.activity_id, "idempotency_key": idempotency_key})

    # --- leases -------------------------------------------------------------

    def claim(self, workflow_id: str, activity_id: str, *, worker_id: str, now: int, ttl: int = 30) -> ClaimResult:
        """Take the activity under a lease, or learn why not.

        Fail-closed ordering: a completed activity is never re-claimed, an
        activity that may have had an external effect is RECOVERY_REQUIRED, a
        live holder blocks, a dead holder is reclaimed with the attempt count
        preserved so max_attempts still binds across workers.
        """

        with self._tx() as db:
            act = db.execute(
                "SELECT * FROM worker_activities WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone()
            if act is None:
                raise WorkflowIntegrityError(f"unknown activity {activity_id!r}")

            status = ActivityStatus(act["status"])
            if status is ActivityStatus.COMPLETED:
                return ClaimResult(ClaimVerdict.ALREADY_COMPLETED,
                                   reason="activity has a terminal receipt; re-execution refused")
            if status is ActivityStatus.RECOVERY_REQUIRED:
                return ClaimResult(ClaimVerdict.RECOVERY_REQUIRED,
                                   reason="external effect ambiguity; operator recovery required, not a retry")

            spec = ActivitySpec(**{k: v for k, v in json.loads(act["spec_json"]).items()})
            lease = self._lease_from_row(db.execute(
                "SELECT * FROM leases WHERE workflow_id=? AND activity_id=?",
                (workflow_id, activity_id),
            ).fetchone())

            reclaimed = False
            if lease is not None:
                if lease.alive_at(now):
                    return ClaimResult(ClaimVerdict.HELD_BY_LIVE_WORKER, lease,
                                       reason=f"held by {lease.worker_id!r}, heartbeat {now - lease.heartbeat_at}s ago")
                # dead holder. what did it leave behind?
                if act["effect_started"] and spec.external_effect:
                    db.execute("UPDATE worker_activities SET status=? WHERE workflow_id=? AND activity_id=?",
                               (ActivityStatus.RECOVERY_REQUIRED.value, workflow_id, activity_id))
                    db.execute("DELETE FROM leases WHERE workflow_id=? AND activity_id=?", (workflow_id, activity_id))
                    self._append_event(db, workflow_id, "RECOVERY_REQUIRED", {
                        "activity_id": activity_id, "dead_worker": lease.worker_id,
                        "reason": "worker died after starting an external effect and before writing a receipt",
                    })
                    return ClaimResult(ClaimVerdict.RECOVERY_REQUIRED,
                                       reason="dead worker had started an external effect; ambiguity is not retried")
                if act["effect_started"] and not spec.retry_safe:
                    db.execute("UPDATE worker_activities SET status=? WHERE workflow_id=? AND activity_id=?",
                               (ActivityStatus.RECOVERY_REQUIRED.value, workflow_id, activity_id))
                    db.execute("DELETE FROM leases WHERE workflow_id=? AND activity_id=?", (workflow_id, activity_id))
                    self._append_event(db, workflow_id, "RECOVERY_REQUIRED", {
                        "activity_id": activity_id, "dead_worker": lease.worker_id,
                        "reason": "worker died mid-action on a non-retry-safe activity",
                    })
                    return ClaimResult(ClaimVerdict.RECOVERY_REQUIRED,
                                       reason="dead worker was mid-action on a non-retry-safe activity")
                reclaimed = True
                db.execute("DELETE FROM leases WHERE workflow_id=? AND activity_id=?", (workflow_id, activity_id))
                self._append_event(db, workflow_id, "LEASE_RECLAIMED",
                                   {"activity_id": activity_id, "dead_worker": lease.worker_id, "by": worker_id})

            if act["attempt_count"] >= spec.max_attempts:
                return ClaimResult(ClaimVerdict.RECOVERY_REQUIRED,
                                   reason=f"attempt count {act['attempt_count']} reached max_attempts {spec.max_attempts}")

            token = canonical_sha256({"w": workflow_id, "a": activity_id, "worker": worker_id, "t": now,
                                      "n": act["attempt_count"] + 1})
            db.execute(
                "INSERT INTO leases (workflow_id,activity_id,worker_id,lease_token,acquired_at,heartbeat_at,ttl) VALUES (?,?,?,?,?,?,?)",
                (workflow_id, activity_id, worker_id, token, now, now, ttl),
            )
            db.execute(
                "UPDATE worker_activities SET status=?, attempt_count=attempt_count+1, effect_started=0 WHERE workflow_id=? AND activity_id=?",
                (ActivityStatus.RUNNING.value, workflow_id, activity_id),
            )
            self._append_event(db, workflow_id, "LEASE_ACQUIRED",
                               {"activity_id": activity_id, "worker": worker_id, "token": token, "reclaimed": reclaimed})
            new_lease = Lease(workflow_id, activity_id, worker_id, token, now, now, ttl)
            return ClaimResult(
                ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER if reclaimed else ClaimVerdict.ACQUIRED, new_lease
            )

    def heartbeat(self, lease: Lease, *, now: int) -> bool:
        """Extend the lease. False if the token no longer holds — the worker must stop."""

        with self._tx() as db:
            cur = db.execute(
                "UPDATE leases SET heartbeat_at=? WHERE workflow_id=? AND activity_id=? AND lease_token=?",
                (now, lease.workflow_id, lease.activity_id, lease.lease_token),
            )
            return cur.rowcount == 1

    def mark_effect_started(self, lease: Lease) -> None:
        """Record that the external effect is being attempted. Written BEFORE the effect."""

        with self._tx() as db:
            cur = db.execute(
                "UPDATE worker_activities SET effect_started=1 WHERE workflow_id=? AND activity_id=? "
                "AND EXISTS (SELECT 1 FROM leases WHERE workflow_id=? AND activity_id=? AND lease_token=?)",
                (lease.workflow_id, lease.activity_id, lease.workflow_id, lease.activity_id, lease.lease_token),
            )
            if cur.rowcount != 1:
                raise WorkflowIntegrityError("lease no longer held; effect must not start")
            self._append_event(db, lease.workflow_id, "EFFECT_STARTED",
                               {"activity_id": lease.activity_id, "worker": lease.worker_id})

    def complete(self, lease: Lease, *, result_digest: str) -> bool:
        """Write the terminal receipt. Requires the lease; idempotent on the same digest."""

        with self._tx() as db:
            held = db.execute(
                "SELECT 1 FROM leases WHERE workflow_id=? AND activity_id=? AND lease_token=?",
                (lease.workflow_id, lease.activity_id, lease.lease_token),
            ).fetchone()
            act = db.execute(
                "SELECT status,result_digest FROM worker_activities WHERE workflow_id=? AND activity_id=?",
                (lease.workflow_id, lease.activity_id),
            ).fetchone()
            if act["status"] == ActivityStatus.COMPLETED.value:
                if act["result_digest"] != result_digest:
                    raise WorkflowIntegrityError("activity already completed with a different result")
                return True  # duplicate completion of the same result: idempotent
            if held is None:
                return False  # a worker without the lease cannot write the receipt
            db.execute(
                "UPDATE worker_activities SET status=?, result_digest=? WHERE workflow_id=? AND activity_id=?",
                (ActivityStatus.COMPLETED.value, result_digest, lease.workflow_id, lease.activity_id),
            )
            db.execute("DELETE FROM leases WHERE workflow_id=? AND activity_id=?",
                       (lease.workflow_id, lease.activity_id))
            self._append_event(db, lease.workflow_id, "ACTIVITY_COMPLETED",
                               {"activity_id": lease.activity_id, "worker": lease.worker_id, "result_digest": result_digest})
            return True

    # --- reads --------------------------------------------------------------

    def activity(self, workflow_id: str, activity_id: str) -> WorkerActivityRecord:
        db = self._connect()
        try:
            act = db.execute("SELECT * FROM worker_activities WHERE workflow_id=? AND activity_id=?",
                             (workflow_id, activity_id)).fetchone()
            if act is None:
                raise WorkflowIntegrityError(f"unknown activity {activity_id!r}")
            lease = self._lease_from_row(db.execute(
                "SELECT * FROM leases WHERE workflow_id=? AND activity_id=?", (workflow_id, activity_id)
            ).fetchone())
        finally:
            db.close()
        return WorkerActivityRecord(
            workflow_id=workflow_id, activity_id=activity_id, status=ActivityStatus(act["status"]),
            attempt_count=act["attempt_count"], lease=lease, effect_started=bool(act["effect_started"]),
            result_digest=act["result_digest"], idempotency_key=act["idempotency_key"],
        )

    def events(self, workflow_id: str) -> tuple[dict[str, object], ...]:
        db = self._connect()
        try:
            rows = db.execute("SELECT * FROM worker_events WHERE workflow_id=? ORDER BY sequence",
                              (workflow_id,)).fetchall()
        finally:
            db.close()
        return tuple({"sequence": r["sequence"], "kind": r["kind"], "payload": json.loads(r["payload_json"]),
                      "event_hash": r["event_hash"], "previous_event_hash": r["previous_event_hash"]} for r in rows)

    def verify_history(self, workflow_id: str) -> bool:
        """Every event's hash must bind to its predecessor. Tampering breaks the chain."""

        previous = ""
        for e in self.events(workflow_id):
            expected = canonical_sha256({"workflow_id": workflow_id, "sequence": e["sequence"], "kind": e["kind"],
                                         "payload": e["payload"], "previous_event_hash": previous})
            if e["event_hash"] != expected or e["previous_event_hash"] != previous:
                return False
            previous = e["event_hash"]
        return True


__all__ = [
    "ClaimResult",
    "ClaimVerdict",
    "Lease",
    "LeaseState",
    "SqliteWorkerWorkflowEngine",
    "WorkerActivityRecord",
]
