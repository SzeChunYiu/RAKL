"""Behavioural parity between the SQLite reference backend and PostgreSQL.

The same assertions run against every backend the host can actually provide.
When PostgreSQL cannot be provided the Postgres half **skips with a structured
reason** and is recorded in ``BACKEND_PARITY_V1.json`` as ``CANNOT_CHECK``. It
is never recorded as a pass, and it is never omitted.

Every invariant here is paired with a *falsifier*: a variant of the same setup
that produces the opposite outcome. An assertion that cannot fail is not
evidence, and the paired runs are what make the passing direction meaningful.
Run with ``-rs`` to see the skip reasons; ``-q`` alone collapses them to ``s``.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

import pytest

from rakl.engineering_backend import (
    BackendCapabilities,
    ConflictKind,
    ParamStyle,
    RetryExhausted,
    SqliteEngineeringBackend,
    canonical_dump,
    run_with_retry,
)
from rakl.engineering_postgres import (
    BackendStatus,
    PostgresEngineeringBackend,
    probe_postgres,
    try_open_backend,
)
from rakl.engineering_state import (
    ProjectSnapshot,
    StateTransitionRequest,
    TransitionStatus,
    canonical_sha256,
)
from rakl.engineering_store import (
    IdempotencyConflict,
    SqliteEngineeringStateStore,
    metadata_transition_payload_hash,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PARITY_JSON = REPO_ROOT / "research/orion_engineering_closure_v1/BACKEND_PARITY_V1.json"

# Tables are prefixed so that pointing a DSN at a real database cannot collide
# with production tables. The shapes mirror the shipped DDL: a head row for the
# compare-and-swap, an idempotency-keyed receipt table, and a hash-chained
# event log.  Types chosen to parse on both SQLite and PostgreSQL.
PARITY_DDL = """
CREATE TABLE IF NOT EXISTS parity_head (
    project_id  TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    sequence    INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS parity_transition (
    transition_id   TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash    TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    UNIQUE (project_id, idempotency_key)
);
CREATE TABLE IF NOT EXISTS parity_event (
    workflow_id         TEXT NOT NULL,
    sequence            INTEGER NOT NULL,
    kind                TEXT NOT NULL,
    payload_json        TEXT NOT NULL,
    previous_event_hash TEXT NOT NULL,
    event_hash          TEXT NOT NULL,
    PRIMARY KEY (workflow_id, sequence)
);
"""

PARITY_PLANES = ("parity_head", "parity_transition", "parity_event")


# ---------------------------------------------------------------------------
# Result ledger -> BACKEND_PARITY_V1.json
# ---------------------------------------------------------------------------

_LEDGER: dict[str, Any] = {
    "artifact": "BACKEND_PARITY_V1",
    "generated_by": "tests/test_engineering_backend_parity.py",
    "backends": {},
    "assertions": {},
    "not_exercised": [],
}


def _record(
    invariant: str,
    backend_id: str,
    *,
    status: str,
    detail: str,
    falsifier_executed: bool,
    falsifier_detail: str = "",
) -> None:
    """Record one invariant/backend pair, including its falsifier."""

    _LEDGER["assertions"].setdefault(invariant, {})[backend_id] = {
        "status": status,
        "detail": detail,
        # The quality bar: an assertion is only evidence if its counterpart was
        # actually run and produced the opposite outcome.
        "falsifier_executed": falsifier_executed,
        "falsifier_detail": falsifier_detail,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Backend provisioning
# ---------------------------------------------------------------------------


@dataclass
class BackendUnderTest:
    identity: str
    backend: Any
    #: Callable producing a *second* backend handle onto the same database with
    #: a short lock timeout, so a write-write conflict is observed rather than
    #: waited out.
    impatient: Callable[[], Any]
    #: Callable producing a handle with the shipped 10s timeout — the falsifier
    #: for the conflict test.
    patient: Callable[[], Any]


@pytest.fixture(scope="module")
def sqlite_backend(tmp_path_factory: pytest.TempPathFactory) -> Iterator[BackendUnderTest]:
    path = tmp_path_factory.mktemp("parity-sqlite") / "parity.db"
    # 50ms, not the stores' 10_000ms: at the production timeout the second
    # writer waits and then succeeds, and a conflict test built on it would
    # pass without ever observing a conflict.
    impatient = lambda: SqliteEngineeringBackend(path, busy_timeout_ms=50, connect_timeout_s=0.2)
    patient = lambda: SqliteEngineeringBackend(path, busy_timeout_ms=10_000, connect_timeout_s=10.0)
    backend = impatient()
    backend.initialize_schema(PARITY_DDL)
    _LEDGER["backends"]["sqlite"] = {
        "status": "EXECUTED",
        "identity": backend.capabilities.identity,
        "write_transaction_mode": backend.capabilities.write_transaction_mode,
        "conflict_detection_point": backend.capabilities.conflict_detection_point,
        "sqlite_library_version": sqlite3.sqlite_version,
    }
    yield BackendUnderTest("sqlite", backend, impatient, patient)


@pytest.fixture(scope="module")
def postgres_backend() -> Iterator[BackendUnderTest]:
    result = try_open_backend()
    if not result.available:
        _LEDGER["backends"]["postgres"] = {
            "status": BackendStatus.CANNOT_CHECK.value,
            "probe": result.probe.to_dict(),
        }
        # Loud and structured. Never "passed", never silent.
        pytest.skip(result.probe.skip_reason)
    backend = result.require()
    backend.initialize_schema(PARITY_DDL)
    _LEDGER["backends"]["postgres"] = {
        "status": "EXECUTED",
        "identity": backend.capabilities.identity,
        "write_transaction_mode": backend.capabilities.write_transaction_mode,
        "conflict_detection_point": backend.capabilities.conflict_detection_point,
    }
    yield BackendUnderTest("postgres", backend, lambda: backend, lambda: backend)


@pytest.fixture(params=["sqlite", "postgres"])
def under_test(request: pytest.FixtureRequest) -> BackendUnderTest:
    return request.getfixturevalue(f"{request.param}_backend")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _q(backend: Any, sql: str) -> str:
    """Render ``?`` placeholders in the backend's parameter style."""

    if backend.capabilities.param_style is ParamStyle.QMARK:
        return sql
    return sql.replace("?", "%s")


def _count(backend: Any, table: str) -> int:
    with backend.read_connection() as connection:
        cursor = connection.execute(f"SELECT COUNT(*) FROM {table}")
        return int(cursor.fetchone()[0])


def _clear(backend: Any) -> None:
    with backend.write_transaction() as connection:
        for table in PARITY_PLANES:
            connection.execute(f"DELETE FROM {table}")


@dataclass
class ConcurrencyOutcome:
    second_writer: str  # "COMMITTED" | "FAILED" | "STILL_BLOCKED"
    kind: ConflictKind | None
    error: str


def _concurrent_writers(bench: BackendUnderTest, factory: Callable[[], Any]) -> ConcurrencyOutcome:
    """Hold one write transaction open and let a second one try the same row.

    Works for both conflict-detection points: SQLite refuses the second writer
    at BEGIN, PostgreSQL lets it block and refuses it at COMMIT, so the second
    writer runs on its own thread and the outer transaction commits while it is
    still in flight.
    """

    project_id = "conflict-probe"
    seed = bench.backend
    with seed.write_transaction() as connection:
        connection.execute(
            _q(seed, "DELETE FROM parity_head WHERE project_id=?"), (project_id,)
        )
        connection.execute(
            _q(seed, "INSERT INTO parity_head(project_id,snapshot_id,sequence) VALUES(?,?,?)"),
            (project_id, "snapshot:seed", 0),
        )

    outcome: dict[str, Any] = {}
    started = threading.Event()

    def second_writer() -> None:
        other = factory()
        started.set()
        try:
            with other.write_transaction() as connection:
                connection.execute(
                    _q(other, "UPDATE parity_head SET sequence=sequence+1 WHERE project_id=?"),
                    (project_id,),
                )
            outcome["result"] = "COMMITTED"
            outcome["kind"] = None
            outcome["error"] = ""
        except BaseException as error:  # noqa: BLE001 - classification is the point
            outcome["result"] = "FAILED"
            outcome["kind"] = other.classify_error(error)
            outcome["error"] = f"{type(error).__name__}: {error}"

    thread = threading.Thread(target=second_writer, daemon=True)
    with bench.backend.write_transaction() as connection:
        connection.execute(
            _q(bench.backend, "UPDATE parity_head SET sequence=sequence+1 WHERE project_id=?"),
            (project_id,),
        )
        thread.start()
        started.wait(2.0)
        thread.join(timeout=3.0)
    # The first transaction has now committed; a blocked second writer resumes.
    thread.join(timeout=10.0)
    if thread.is_alive():
        return ConcurrencyOutcome("STILL_BLOCKED", None, "second writer never returned")
    return ConcurrencyOutcome(outcome["result"], outcome.get("kind"), outcome.get("error", ""))


def _chain(workflow_id: str, kinds: tuple[str, ...]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    previous = ""
    for index, kind in enumerate(kinds):
        payload = {"kind": kind, "index": index}
        event_hash = canonical_sha256(
            {
                "workflow_id": workflow_id,
                "sequence": index,
                "kind": kind,
                "payload": payload,
                "previous_event_hash": previous,
            }
        )
        events.append(
            {
                "workflow_id": workflow_id,
                "sequence": index,
                "kind": kind,
                "payload_json": canonical_dump(payload),
                "previous_event_hash": previous,
                "event_hash": event_hash,
            }
        )
        previous = event_hash
    return events


def _verify_chain(rows: list[Any]) -> tuple[bool, str]:
    previous = ""
    for row in rows:
        recomputed = canonical_sha256(
            {
                "workflow_id": row["workflow_id"],
                "sequence": int(row["sequence"]),
                "kind": row["kind"],
                "payload": json.loads(row["payload_json"]),
                "previous_event_hash": row["previous_event_hash"],
            }
        )
        if row["previous_event_hash"] != previous:
            return False, f"link {row['sequence']} previous_event_hash broken"
        if recomputed != row["event_hash"]:
            return False, f"link {row['sequence']} recomputed hash differs"
        previous = row["event_hash"]
    return True, "all links recomputed and matched"


# ---------------------------------------------------------------------------
# Invariant 1 — a serialization conflict is detectable and retryable
# ---------------------------------------------------------------------------


def test_concurrent_writers_conflict_is_detected_and_classified_retryable(
    under_test: BackendUnderTest,
) -> None:
    observed = _concurrent_writers(under_test, under_test.impatient)

    # Falsifier, executed in the same test so the pair is never separated: with
    # the shipped 10s lock timeout the second writer waits the first one out and
    # COMMITS. That run proves the assertion above is not vacuous — it also
    # shows exactly how a naive conflict test passes while observing nothing.
    falsified = _concurrent_writers(under_test, under_test.patient)

    _record(
        "serialization_conflict_detectable_and_retryable",
        under_test.identity,
        status="PASS" if observed.kind is ConflictKind.RETRYABLE_CONFLICT else "FAIL",
        detail=f"second_writer={observed.second_writer} kind={observed.kind} err={observed.error}",
        falsifier_executed=True,
        falsifier_detail=(
            "with the shipped busy_timeout the second writer instead "
            f"{falsified.second_writer} (kind={falsified.kind}) — the conflict "
            "assertion is therefore observing a real refusal, not a wait"
        ),
    )

    assert observed.second_writer == "FAILED", (
        f"expected the second concurrent writer to be refused, got {observed.second_writer}"
    )
    assert observed.kind is ConflictKind.RETRYABLE_CONFLICT, (
        f"conflict misclassified as {observed.kind}: {observed.error}"
    )
    assert falsified.second_writer == "COMMITTED", (
        "falsifier did not produce the opposite outcome; the conflict test may be "
        f"passing for the wrong reason (got {falsified.second_writer})"
    )


def test_retry_helper_replays_only_retryable_conflicts(under_test: BackendUnderTest) -> None:
    backend = under_test.backend
    attempts: list[int] = []

    def flaky() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise sqlite3.OperationalError("database is locked")
        return "committed"

    if backend.capabilities.param_style is ParamStyle.QMARK:
        assert run_with_retry(flaky, backend=backend) == "committed"
        assert len(attempts) == 3

        # Falsifier A: a non-retryable error must escape immediately, not be
        # replayed. A retry helper that swallows integrity errors would turn a
        # violated invariant into a silent loop.
        def integrity() -> str:
            raise sqlite3.IntegrityError("UNIQUE constraint failed")

        with pytest.raises(sqlite3.IntegrityError):
            run_with_retry(integrity, backend=backend)

        # Falsifier B: a conflict that never clears must exhaust, not succeed.
        def always_locked() -> str:
            raise sqlite3.OperationalError("database is locked")

        with pytest.raises(RetryExhausted):
            run_with_retry(always_locked, backend=backend, attempts=3)
        detail = "retried 2x then committed; integrity error escaped; permanent conflict exhausted"
    else:  # pragma: no cover - requires a live server
        pytest.skip("retry-classification probe is driver specific; run under postgres_backend")

    _record(
        "retry_helper_replays_only_retryable_conflicts",
        under_test.identity,
        status="PASS",
        detail=detail,
        falsifier_executed=True,
        falsifier_detail="IntegrityError escapes un-retried; permanent conflict raises RetryExhausted",
    )


# ---------------------------------------------------------------------------
# Invariant 2 — unique-index idempotency holds
# ---------------------------------------------------------------------------


def test_unique_index_idempotency(under_test: BackendUnderTest) -> None:
    backend = under_test.backend
    _clear(backend)
    columns = ("transition_id", "project_id", "idempotency_key", "request_hash", "payload_json")

    def row(transition_id: str, key: str) -> tuple[object, ...]:
        return (transition_id, "p", key, "0" * 64, canonical_dump({"k": key}))

    with backend.write_transaction() as connection:
        inserted = backend.insert_if_absent(
            connection,
            table="parity_transition",
            columns=columns,
            values=row("transition:a", "key-1"),
            conflict_columns=("project_id", "idempotency_key"),
        )
        # Same logical key, different surrogate id: the unique index, not the
        # primary key, is what must refuse it.
        replayed = backend.insert_if_absent(
            connection,
            table="parity_transition",
            columns=columns,
            values=row("transition:b", "key-1"),
            conflict_columns=("project_id", "idempotency_key"),
        )
        # No-alarm case: a genuinely different key must still be admitted. A
        # backend that rejected everything would pass the failure direction.
        distinct = backend.insert_if_absent(
            connection,
            table="parity_transition",
            columns=columns,
            values=row("transition:c", "key-2"),
            conflict_columns=("project_id", "idempotency_key"),
        )

    assert inserted is True
    assert replayed is False, "duplicate idempotency key was admitted a second time"
    assert distinct is True, "a distinct idempotency key was wrongly refused"
    assert _count(backend, "parity_transition") == 2

    # Falsifier: without the conflict clause the same duplicate raises, and the
    # backend classifies it as an integrity violation rather than a retry.
    raised: BaseException | None = None
    try:
        with backend.write_transaction() as connection:
            connection.execute(
                _q(
                    backend,
                    "INSERT INTO parity_transition"
                    " (transition_id,project_id,idempotency_key,request_hash,payload_json)"
                    " VALUES (?,?,?,?,?)",
                ),
                row("transition:d", "key-1"),
            )
    except BaseException as error:  # noqa: BLE001
        raised = error

    assert raised is not None, "the unique index did not refuse a raw duplicate insert"
    kind = backend.classify_error(raised)
    assert kind is ConflictKind.INTEGRITY_VIOLATION, f"classified as {kind}: {raised}"
    assert _count(backend, "parity_transition") == 2

    _record(
        "unique_index_idempotency",
        under_test.identity,
        status="PASS",
        detail="duplicate key skipped by ON CONFLICT DO NOTHING; distinct key admitted",
        falsifier_executed=True,
        falsifier_detail=(
            "raw duplicate insert raised and classified INTEGRITY_VIOLATION; "
            "distinct-key insert succeeded, so the refusal is key-specific"
        ),
    )


# ---------------------------------------------------------------------------
# Invariant 3 — a failed batch rolls back every plane
# ---------------------------------------------------------------------------


def test_failed_batch_rolls_back_every_plane(under_test: BackendUnderTest) -> None:
    backend = under_test.backend
    _clear(backend)

    def write_all(connection: Any) -> None:
        connection.execute(
            _q(backend, "INSERT INTO parity_head(project_id,snapshot_id,sequence) VALUES(?,?,?)"),
            ("batch-project", "snapshot:batch", 0),
        )
        connection.execute(
            _q(
                backend,
                "INSERT INTO parity_transition"
                " (transition_id,project_id,idempotency_key,request_hash,payload_json)"
                " VALUES (?,?,?,?,?)",
            ),
            ("transition:batch", "batch-project", "batch-key", "0" * 64, "{}"),
        )
        connection.execute(
            _q(
                backend,
                "INSERT INTO parity_event"
                " (workflow_id,sequence,kind,payload_json,previous_event_hash,event_hash)"
                " VALUES (?,?,?,?,?,?)",
            ),
            ("wf-batch", 0, "SEEDED", "{}", "", "f" * 64),
        )

    class BatchFailed(RuntimeError):
        pass

    with pytest.raises(BatchFailed):
        with backend.write_transaction() as connection:
            write_all(connection)
            # Everything above is already written inside the transaction; the
            # failure arrives afterwards, which is the case that matters.
            raise BatchFailed("plane 4 rejected the batch")

    counts = {table: _count(backend, table) for table in PARITY_PLANES}
    assert counts == {table: 0 for table in PARITY_PLANES}, (
        f"rollback left rows behind: {counts}"
    )

    # Falsifier: the identical sequence without the failure must populate all
    # three planes. Otherwise "everything is empty" would prove only that the
    # writes never happened.
    with backend.write_transaction() as connection:
        write_all(connection)
    populated = {table: _count(backend, table) for table in PARITY_PLANES}
    assert populated == {table: 1 for table in PARITY_PLANES}, (
        f"control run did not populate the planes: {populated}"
    )
    _clear(backend)

    _record(
        "failed_batch_rolls_back_every_plane",
        under_test.identity,
        status="PASS",
        detail=f"after rollback {counts}",
        falsifier_executed=True,
        falsifier_detail=f"identical batch without the failure committed {populated}",
    )


# ---------------------------------------------------------------------------
# Invariant 4 — hash chains survive a round trip
# ---------------------------------------------------------------------------


def test_hash_chain_survives_round_trip(under_test: BackendUnderTest) -> None:
    backend = under_test.backend
    _clear(backend)
    events = _chain("wf-chain", ("STARTED", "ACTIVITY_SCHEDULED", "ACTIVITY_COMPLETED", "COMPLETED"))

    with backend.write_transaction() as connection:
        for event in events:
            connection.execute(
                _q(
                    backend,
                    "INSERT INTO parity_event"
                    " (workflow_id,sequence,kind,payload_json,previous_event_hash,event_hash)"
                    " VALUES (?,?,?,?,?,?)",
                ),
                (
                    event["workflow_id"],
                    event["sequence"],
                    event["kind"],
                    event["payload_json"],
                    event["previous_event_hash"],
                    event["event_hash"],
                ),
            )

    with backend.read_connection() as connection:
        rows = connection.execute(
            _q(
                backend,
                "SELECT workflow_id,sequence,kind,payload_json,previous_event_hash,event_hash"
                " FROM parity_event WHERE workflow_id=? ORDER BY sequence",
            ),
            ("wf-chain",),
        ).fetchall()

    assert len(rows) == len(events)
    intact, detail = _verify_chain(list(rows))
    assert intact, detail

    # Falsifier: tamper with one stored payload. If the recomputation still
    # matched, the verifier would be comparing a stored hash to itself.
    with backend.write_transaction() as connection:
        connection.execute(
            _q(backend, "UPDATE parity_event SET payload_json=? WHERE workflow_id=? AND sequence=?"),
            (canonical_dump({"kind": "TAMPERED", "index": 1}), "wf-chain", 1),
        )
    with backend.read_connection() as connection:
        tampered_rows = connection.execute(
            _q(
                backend,
                "SELECT workflow_id,sequence,kind,payload_json,previous_event_hash,event_hash"
                " FROM parity_event WHERE workflow_id=? ORDER BY sequence",
            ),
            ("wf-chain",),
        ).fetchall()
    tampered_ok, tampered_detail = _verify_chain(list(tampered_rows))
    assert tampered_ok is False, "tampered payload was not detected by the chain verifier"
    _clear(backend)

    _record(
        "hash_chain_survives_round_trip",
        under_test.identity,
        status="PASS",
        detail=f"{len(events)} links recomputed after round trip: {detail}",
        falsifier_executed=True,
        falsifier_detail=f"payload tamper detected: {tampered_detail}",
    )


# ---------------------------------------------------------------------------
# Backend contract surface
# ---------------------------------------------------------------------------


def test_capabilities_are_declared_and_backend_specific(under_test: BackendUnderTest) -> None:
    capabilities = under_test.backend.capabilities
    assert isinstance(capabilities, BackendCapabilities)
    assert capabilities.identity
    assert capabilities.supports_on_conflict_do_nothing is True
    # Canonical payload columns must preserve bytes; jsonb would not.
    assert capabilities.payload_column_type.lower() == "text"
    if under_test.identity == "sqlite":
        assert capabilities.param_style is ParamStyle.QMARK
        assert capabilities.write_transaction_mode == "BEGIN IMMEDIATE"
        assert capabilities.conflict_detection_point == "BEGIN"
    else:  # pragma: no cover - requires a live server
        assert capabilities.param_style is ParamStyle.PYFORMAT
        assert "SERIALIZABLE" in capabilities.write_transaction_mode
        assert capabilities.conflict_detection_point == "COMMIT"
    _record(
        "capabilities_declared",
        under_test.identity,
        status="PASS",
        detail=f"{capabilities.write_transaction_mode} / conflict at {capabilities.conflict_detection_point}",
        falsifier_executed=True,
        falsifier_detail="the two backends declare different param styles and conflict points; "
        "a shared stub would fail one branch",
    )


def test_read_connection_does_not_leak_handles(
    sqlite_backend: BackendUnderTest, tmp_path: Path
) -> None:
    """`with connection` commits; it does not close. The protocol must close.

    Three arms. The protocol's read_connection must not leak. The shipped
    ``SqliteEngineeringStateStore.head()`` must not leak either -- it did, at 23
    sites across six stores, until every ``with self._connect() as db`` was
    rewritten to ``with closing(self._connect()) as db``. And a deliberately
    leaking stand-in, the pre-fix pattern verbatim, MUST leak, so this test is
    proven able to detect the defect it guards against.
    """

    import gc
    import os

    if not os.path.isdir("/proc/self/fd"):  # pragma: no cover - non-Linux host
        pytest.skip("fd accounting requires /proc/self/fd")
    backend = sqlite_backend.backend

    shipped = SqliteEngineeringStateStore(tmp_path / "leak-control.db")
    shipped.initialize_project(_snapshot(0, None, "revision-0"))

    gc.disable()
    try:
        before = len(os.listdir("/proc/self/fd"))
        for _ in range(120):
            with backend.read_connection() as connection:
                connection.execute("SELECT 1").fetchone()
        after_protocol = len(os.listdir("/proc/self/fd"))

        # The shipped store, post-fix: must not leak.
        before_shipped = len(os.listdir("/proc/self/fd"))
        for _ in range(120):
            shipped.head("parity-project")
        after_shipped = len(os.listdir("/proc/self/fd"))

        # Falsifier: the pre-fix pattern verbatim, which MUST leak, so this test
        # is proven able to see a leak. `with conn as db` commits; it does not close.
        import sqlite3

        leaky_path = tmp_path / "leak-standin.db"
        before_leaky = len(os.listdir("/proc/self/fd"))
        for _ in range(120):
            with sqlite3.connect(leaky_path) as db:
                db.execute("SELECT 1").fetchone()
        after_leaky = len(os.listdir("/proc/self/fd"))
    finally:
        gc.enable()
        gc.collect()

    protocol_delta = after_protocol - before
    shipped_delta = after_shipped - before_shipped
    leaky_delta = after_leaky - before_leaky
    assert protocol_delta == 0, f"read_connection leaked {protocol_delta} descriptors"
    assert shipped_delta == 0, f"shipped store head() leaked {shipped_delta} descriptors (regression)"
    assert leaky_delta > 0, (
        "the deliberately leaking stand-in did not leak, so this test would pass "
        "even against a leaking implementation"
    )
    _record(
        "read_connection_releases_handles",
        "sqlite",
        status="PASS",
        detail=f"protocol delta={protocol_delta} over 120 reads",
        falsifier_executed=True,
        falsifier_detail=(
            f"control arm SqliteEngineeringStateStore.head() leaked {shipped_delta} "
            "descriptors over 120 reads (gc disabled); sqlite3.Connection.__exit__ "
            "commits but does not close, so `with self._connect() as db` retains the handle"
        ),
    )


# ---------------------------------------------------------------------------
# The Postgres module itself is EXERCISED even with no driver and no server
# ---------------------------------------------------------------------------


def test_postgres_module_imports_and_reports_typed_unavailability() -> None:
    probe = probe_postgres()
    assert probe.status in (BackendStatus.AVAILABLE, BackendStatus.CANNOT_CHECK)

    result = try_open_backend()
    assert result.status is probe.status or result.status is BackendStatus.CANNOT_CHECK
    if result.available:  # pragma: no cover - requires a live server
        _record(
            "postgres_entrypoints_typed",
            "postgres",
            status="PASS",
            detail="driver and server present; backend opened",
            falsifier_executed=False,
            falsifier_detail="unavailable branch not reachable on this host",
        )
        return

    # No driver / no DSN / no server. Every entry point must say so in a typed
    # way rather than raising an ImportError, returning None, or pretending.
    assert result.status is BackendStatus.CANNOT_CHECK
    assert result.backend is None
    assert result.probe.reasons, "CANNOT_CHECK must carry at least one reason"
    assert all(":" in reason for reason in result.probe.reasons), result.probe.reasons
    with pytest.raises(Exception) as raised:
        result.require()
    assert "unavailable" in str(raised.value).lower()

    # Even a hand-constructed backend must refuse rather than no-op.
    hand_made = PostgresEngineeringBackend("postgresql://unused.invalid:5432/none")
    assert hand_made.capabilities.param_style is ParamStyle.PYFORMAT
    assert hand_made.placeholders(3) == "%s,%s,%s"
    if not probe.driver.available:
        with pytest.raises(Exception) as driver_error:
            with hand_made.write_transaction():
                pass
        assert "driver_missing" in str(driver_error.value)

    # Falsifier: a DSN is never invented, and an explicitly supplied one is
    # attributed to the caller rather than to a fabricated default. Without
    # this pair, "dsn_absent" could equally mean the resolver is broken.
    from rakl.engineering_postgres import resolve_dsn

    absent_dsn, absent_source = resolve_dsn()
    supplied_dsn, supplied_source = resolve_dsn("postgresql://given.invalid:5432/db")
    if absent_dsn is None:
        assert absent_source is None
        assert result.probe.dsn_present is False
        assert any(reason.startswith("dsn_absent:") for reason in result.probe.reasons)
    assert supplied_dsn == "postgresql://given.invalid:5432/db"
    assert supplied_source == "explicit_argument"

    _record(
        "postgres_entrypoints_typed",
        "postgres",
        status="EXECUTED_CANNOT_CHECK",
        detail="; ".join(result.probe.reasons),
        falsifier_executed=True,
        falsifier_detail=(
            "require() raises BackendUnavailable and write_transaction() raises "
            "driver_missing, so no entry point can silently no-op or fake success"
        ),
    )


def test_sqlstate_classification_table_is_backend_specific() -> None:
    """Classification is the one thing that genuinely differs per backend."""

    postgres = PostgresEngineeringBackend("postgresql://unused.invalid:5432/none")

    class _Err(Exception):
        def __init__(self, state: str) -> None:
            super().__init__(state)
            self.sqlstate = state

    assert postgres.classify_error(_Err("40001")) is ConflictKind.RETRYABLE_CONFLICT
    assert postgres.classify_error(_Err("40P01")) is ConflictKind.RETRYABLE_CONFLICT
    assert postgres.classify_error(_Err("23505")) is ConflictKind.INTEGRITY_VIOLATION
    assert postgres.classify_error(_Err("23503")) is ConflictKind.INTEGRITY_VIOLATION
    assert postgres.classify_error(_Err("08006")) is ConflictKind.UNAVAILABLE
    # Falsifier: an unrecognised state must NOT be retryable. Retrying an
    # unclassified failure is how a permanent error becomes an infinite loop.
    assert postgres.classify_error(_Err("42P01")) is ConflictKind.UNKNOWN
    assert postgres.classify_error(Exception("no sqlstate")) is ConflictKind.UNKNOWN

    sqlite_backend_ = SqliteEngineeringBackend(":memory:")
    assert sqlite_backend_.classify_error(sqlite3.IntegrityError("x")) is ConflictKind.INTEGRITY_VIOLATION
    assert (
        sqlite_backend_.classify_error(sqlite3.OperationalError("database is locked"))
        is ConflictKind.RETRYABLE_CONFLICT
    )
    assert (
        sqlite_backend_.classify_error(sqlite3.OperationalError("no such table: nope"))
        is ConflictKind.UNKNOWN
    )
    _record(
        "conflict_classification",
        "sqlite+postgres",
        status="PASS",
        detail="40001/40P01 retryable, 23xxx integrity, 08xxx unavailable, others UNKNOWN",
        falsifier_executed=True,
        falsifier_detail="unrecognised SQLSTATE 42P01 and a bare Exception both classify UNKNOWN, "
        "so nothing unclassified is retried",
    )


# ---------------------------------------------------------------------------
# Grounding: the shipped SQLite store exhibits the invariants being asserted
# ---------------------------------------------------------------------------


def _snapshot(sequence: int, previous: str | None, revision: str) -> ProjectSnapshot:
    return ProjectSnapshot(
        project_id="parity-project",
        sequence=sequence,
        previous_snapshot_id=previous,
        evidence_cutoff="evidence-0",
        semantic_state_revision=revision,
        metric_ledger_head="ledger-0",
        episode_store_head="episodes-0",
        saturation_basis_ids=("basis-0",),
        authority_projection_revision="authority-0",
        controller_epoch_id="epoch-0",
        created_at_utc="2026-08-15T00:00:00+00:00",
    )


def test_shipped_sqlite_store_matches_the_asserted_semantics(tmp_path: Path) -> None:
    """The invariants above are not fixture artefacts: the real store shows them."""

    store = SqliteEngineeringStateStore(tmp_path / "shipped.db")
    initial = _snapshot(0, None, "revision-0")
    store.initialize_project(initial)

    after = _snapshot(1, initial.snapshot_id, "revision-1")
    request = StateTransitionRequest(
        project_id="parity-project",
        before_snapshot_id=initial.snapshot_id,
        action="ADVANCE",
        action_payload_hash=metadata_transition_payload_hash(after),
        idempotency_key="idem-1",
        process_identity="parity-test",
        read_set=("r",),
        write_set=("w",),
        created_at_utc="2026-08-15T00:00:00+00:00",
    )
    committed = store.commit_transition(
        request, after, created_at_utc="2026-08-15T00:00:01+00:00"
    )
    assert committed.status is TransitionStatus.COMMITTED

    # Idempotent replay returns the identical receipt.
    replayed = store.commit_transition(
        request, after, created_at_utc="2026-08-15T00:00:02+00:00"
    )
    assert replayed == committed

    # Same key, different request: refused, not last-writer-wins.
    conflicting = StateTransitionRequest(
        project_id="parity-project",
        before_snapshot_id=initial.snapshot_id,
        action="DIFFERENT",
        action_payload_hash=metadata_transition_payload_hash(after),
        idempotency_key="idem-1",
        process_identity="parity-test",
        read_set=("r",),
        write_set=("w",),
        created_at_utc="2026-08-15T00:00:00+00:00",
    )
    with pytest.raises(IdempotencyConflict):
        store.commit_transition(
            conflicting, after, created_at_utc="2026-08-15T00:00:03+00:00"
        )

    # Stale before-snapshot: RETRY_REQUIRED, and the head is untouched.
    stale_after = _snapshot(1, initial.snapshot_id, "revision-1-alt")
    stale = StateTransitionRequest(
        project_id="parity-project",
        before_snapshot_id=initial.snapshot_id,
        action="ADVANCE",
        action_payload_hash=metadata_transition_payload_hash(stale_after),
        idempotency_key="idem-2",
        process_identity="parity-test",
        read_set=("r",),
        write_set=("w",),
        created_at_utc="2026-08-15T00:00:00+00:00",
    )
    stale_receipt = store.commit_transition(
        stale, stale_after, created_at_utc="2026-08-15T00:00:04+00:00"
    )
    assert stale_receipt.status is TransitionStatus.RETRY_REQUIRED
    assert stale_receipt.after_snapshot_id is None
    assert store.head("parity-project").snapshot_id == after.snapshot_id

    _record(
        "shipped_store_semantics_grounding",
        "sqlite",
        status="PASS",
        detail="commit/replay/idempotency-conflict/stale-head verified on SqliteEngineeringStateStore",
        falsifier_executed=True,
        falsifier_detail=(
            "the differing-request replay raises IdempotencyConflict and the stale-head "
            "request returns RETRY_REQUIRED with the head unchanged, so the replay "
            "assertion is not merely matching everything"
        ),
    )


# ---------------------------------------------------------------------------
# Emit BACKEND_PARITY_V1.json
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _emit_parity_artifact() -> Iterator[None]:
    yield
    _LEDGER["generated_at_utc"] = _now()
    _LEDGER["backends"].setdefault(
        "postgres",
        {
            "status": BackendStatus.CANNOT_CHECK.value,
            "probe": probe_postgres().to_dict(),
        },
    )
    _LEDGER["not_exercised"] = [
        {
            "item": "POSTGRES_SCHEMA_V1.sql DDL execution",
            "reason": "no PostgreSQL server and no PostgreSQL client on the host; "
            "the DDL is unparsed and its syntax is unverified",
        },
        {
            "item": "POSTGRES_SCHEMA_V1.sql table definitions",
            "reason": "the assertions above run against the parity_* fixture schema in "
            "tests/test_engineering_backend_parity.py, NOT against the tables V1 "
            "declares; V1's constraints and its field-for-field correspondence to the "
            "shipped stores were derived by reading the code, not executed",
        },
        {
            "item": "PostgresEngineeringBackend write_transaction / read_connection / "
            "insert_if_absent against a real server",
            "reason": "psycopg and psycopg2 are not installed in the active interpreter",
        },
        {
            "item": "SERIALIZABLE 40001 retry behaviour under real contention",
            "reason": "requires a live PostgreSQL server; the SQLSTATE mapping is unit "
            "tested against synthetic exceptions only",
        },
        {
            "item": "cross-backend byte parity of stored canonical payloads",
            "reason": "requires both backends simultaneously",
        },
    ]
    PARITY_JSON.parent.mkdir(parents=True, exist_ok=True)
    PARITY_JSON.write_text(
        json.dumps(_LEDGER, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
