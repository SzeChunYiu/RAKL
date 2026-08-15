"""E6 — durable multi-worker workflow: leases, heartbeats, idempotency, crash windows.

The falsifier: "worker death loses logical progress or duplicates an unprotected
side effect without recovery state." Each crash-window test drives one death
and asserts what the second worker sees. Exactly-once across an external effect
is NOT claimed; RECOVERY_REQUIRED is the terminal for the ambiguous window.
"""

from __future__ import annotations

import pytest

from rakl.engineering_workflow import ActivitySpec, ActivityStatus, WorkflowIntegrityError
from rakl.engineering_workflow_workers import ClaimVerdict, SqliteWorkerWorkflowEngine


def spec(activity_id: str = "a1", *, retry_safe: bool = True, external: bool = False, max_attempts: int = 3) -> ActivitySpec:
    return ActivitySpec(activity_id=activity_id, invocation_id="inv-1", input_digest="in-1",
                        retry_safe=retry_safe, external_effect=external, max_attempts=max_attempts)


@pytest.fixture()
def eng(tmp_path) -> SqliteWorkerWorkflowEngine:
    return SqliteWorkerWorkflowEngine(tmp_path / "wf.db")


# --- leases ------------------------------------------------------------------


def test_only_one_worker_holds_an_activity_at_a_time(eng) -> None:
    eng.schedule("w", spec(), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=30)
    b = eng.claim("w", "a1", worker_id="B", now=5, ttl=30)
    assert a.verdict is ClaimVerdict.ACQUIRED
    assert b.verdict is ClaimVerdict.HELD_BY_LIVE_WORKER
    assert "held by 'A'" in b.reason


def test_heartbeat_keeps_a_lease_alive_and_a_stale_token_is_refused(eng) -> None:
    eng.schedule("w", spec(), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=30)
    assert eng.heartbeat(a.lease, now=20) is True
    assert eng.claim("w", "a1", worker_id="B", now=45, ttl=30).verdict is ClaimVerdict.HELD_BY_LIVE_WORKER
    # lease expires at heartbeat 20 + ttl 30 = 50
    b = eng.claim("w", "a1", worker_id="B", now=51, ttl=30)
    assert b.verdict is ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER
    # A's old token no longer holds — A must stop
    assert eng.heartbeat(a.lease, now=52) is False


# --- idempotency -----------------------------------------------------------


def test_duplicate_schedule_delivery_is_a_noop(eng) -> None:
    eng.schedule("w", spec(), idempotency_key="k1")
    eng.schedule("w", spec(), idempotency_key="k1")  # duplicate delivery
    assert eng.activity("w", "a1").attempt_count == 0
    assert sum(1 for e in eng.events("w") if e["kind"] == "ACTIVITY_SCHEDULED") == 1


def test_same_idempotency_key_different_activity_is_a_conflict(eng) -> None:
    eng.schedule("w", spec("a1"), idempotency_key="k1")
    with pytest.raises(WorkflowIntegrityError, match="different activity"):
        eng.schedule("w", spec("a2"), idempotency_key="k1")


def test_a_completed_activity_is_never_reclaimed(eng) -> None:
    eng.schedule("w", spec(), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0)
    assert eng.complete(a.lease, result_digest="r1") is True
    # duplicate completion of the same result: idempotent
    assert eng.complete(a.lease, result_digest="r1") is True
    # a different result for a completed activity: refused
    with pytest.raises(WorkflowIntegrityError, match="different result"):
        eng.complete(a.lease, result_digest="r2")
    late = eng.claim("w", "a1", worker_id="B", now=999)
    assert late.verdict is ClaimVerdict.ALREADY_COMPLETED


def test_a_worker_without_the_lease_cannot_write_the_receipt(eng) -> None:
    eng.schedule("w", spec(), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    b = eng.claim("w", "a1", worker_id="B", now=20, ttl=10)  # A dead, B reclaims
    assert b.verdict is ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER
    assert eng.complete(a.lease, result_digest="stale") is False  # A's token is dead
    assert eng.complete(b.lease, result_digest="r1") is True


# --- the four crash windows -----------------------------------------------


def test_crash_before_action_is_reclaimable_and_safe(eng) -> None:
    eng.schedule("w", spec(retry_safe=False, external=True), idempotency_key="k1")
    eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    # A dies having done nothing: no effect_started
    b = eng.claim("w", "a1", worker_id="B", now=20, ttl=10)
    assert b.verdict is ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER
    assert eng.activity("w", "a1").attempt_count == 2  # attempts carry across workers


def test_crash_during_retry_safe_action_is_reclaimable(eng) -> None:
    eng.schedule("w", spec(retry_safe=True, external=False), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    eng.mark_effect_started(a.lease)  # A was mid-action
    b = eng.claim("w", "a1", worker_id="B", now=20, ttl=10)
    assert b.verdict is ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER


def test_crash_during_non_retry_safe_action_is_recovery_required(eng) -> None:
    eng.schedule("w", spec(retry_safe=False, external=False), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    eng.mark_effect_started(a.lease)
    b = eng.claim("w", "a1", worker_id="B", now=20, ttl=10)
    assert b.verdict is ClaimVerdict.RECOVERY_REQUIRED
    assert eng.activity("w", "a1").status is ActivityStatus.RECOVERY_REQUIRED
    assert any(e["kind"] == "RECOVERY_REQUIRED" for e in eng.events("w"))


def test_crash_after_external_effect_before_receipt_is_recovery_required_never_retried(eng) -> None:
    """The window nobody can resolve mechanically. Exactly-once is not claimed."""

    eng.schedule("w", spec(retry_safe=True, external=True), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    eng.mark_effect_started(a.lease)  # the effect may or may not have happened
    b = eng.claim("w", "a1", worker_id="B", now=20, ttl=10)
    assert b.verdict is ClaimVerdict.RECOVERY_REQUIRED
    assert "not retried" in b.reason
    # and it stays that way: a third worker gets the same answer, no re-execution
    c = eng.claim("w", "a1", worker_id="C", now=40, ttl=10)
    assert c.verdict is ClaimVerdict.RECOVERY_REQUIRED


def test_crash_after_receipt_before_terminal_reads_the_receipt(eng) -> None:
    eng.schedule("w", spec(external=True), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    eng.mark_effect_started(a.lease)
    eng.complete(a.lease, result_digest="r1")  # receipt written; A dies before anything else
    b = eng.claim("w", "a1", worker_id="B", now=20, ttl=10)
    assert b.verdict is ClaimVerdict.ALREADY_COMPLETED  # reads the receipt, does not re-execute
    assert eng.activity("w", "a1").result_digest == "r1"


def test_max_attempts_binds_across_workers(eng) -> None:
    eng.schedule("w", spec(max_attempts=2), idempotency_key="k1")
    eng.claim("w", "a1", worker_id="A", now=0, ttl=10)
    eng.claim("w", "a1", worker_id="B", now=20, ttl=10)  # attempt 2
    c = eng.claim("w", "a1", worker_id="C", now=40, ttl=10)
    assert c.verdict is ClaimVerdict.RECOVERY_REQUIRED
    assert "max_attempts" in c.reason


# --- history --------------------------------------------------------------


def test_history_is_hash_chained_and_tamper_evident(eng) -> None:
    eng.schedule("w", spec(), idempotency_key="k1")
    a = eng.claim("w", "a1", worker_id="A", now=0)
    eng.complete(a.lease, result_digest="r1")
    assert eng.verify_history("w") is True
    events = eng.events("w")
    assert [e["kind"] for e in events] == ["ACTIVITY_SCHEDULED", "LEASE_ACQUIRED", "ACTIVITY_COMPLETED"]
    for i in range(1, len(events)):
        assert events[i]["previous_event_hash"] == events[i - 1]["event_hash"]
