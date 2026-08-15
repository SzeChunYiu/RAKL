"""Narrow database-backend protocol for the ORION engineering stores.

Scope
-----
This module does **not** refactor the existing stores. It extracts, as an
explicit contract, the four things every one of them already requires from its
database, so that a second backend can be held to the same semantics:

1. a *write transaction* that takes its write lock at transaction start, so a
   concurrent writer is refused rather than silently interleaved;
2. a *read connection* that is actually released;
3. a *parameter style* and an insert-if-absent primitive;
4. a *classification of failure* that distinguishes "retry the whole
   read/plan/write" from "an invariant was violated" from "could not check".

The reference stores implement (1) as ``BEGIN IMMEDIATE`` and (4) implicitly by
letting ``sqlite3`` exceptions propagate. Point (4) is the one thing that cannot
be shared verbatim across backends, which is why it is a protocol member.

Isolation
---------
``BEGIN IMMEDIATE`` acquires SQLite's write lock when the transaction opens, so
a second writer fails at ``BEGIN`` rather than at ``COMMIT``. The stores' core
correctness argument depends on that: ``commit_transition`` reads the project
head and then updates it (engineering_store.py:339-384), and the semantic and
evidence batch stores validate a *base revision* read from one table before
writing rows into several others.

The faithful PostgreSQL analogue is therefore ``SERIALIZABLE`` with retry on
SQLSTATE ``40001``:

* ``READ COMMITTED`` is wrong — the head could change between the SELECT and
  the UPDATE, which is exactly the last-writer-wins outcome the CAS exists to
  prevent.
* ``REPEATABLE READ`` blocks the head-CAS write-write case but not the batch
  stores' read/write skew, where the validated row and the written rows live in
  different tables.
* ``SELECT ... FOR UPDATE`` on ``project_heads`` is the literal pessimistic
  equivalent of ``BEGIN IMMEDIATE`` and is a legitimate optimisation for the
  head-CAS path *alone*; it does not cover the batch stores.

``SERIALIZABLE`` is the default this protocol declares, with ``FOR UPDATE``
named as the narrower alternative. Under SERIALIZABLE the conflict surfaces at
COMMIT rather than at BEGIN, so a Postgres implementation MUST retry the whole
read/plan/write closure — replaying only the write would reuse a stale plan.
``run_with_retry`` exists for that and is deliberately not automatic: a caller
that cannot safely replay its plan must not be retried behind its back.

Canonical JSON
--------------
``canonical_dump`` is the encoder used by ``canonical_sha256``
(engineering_state.py:22-30): ``sort_keys=True``, ``separators=(",", ":")``,
``ensure_ascii=False``. Stored payload bytes and identity-hash bytes must agree,
otherwise a byte-for-byte idempotency comparison is comparing against something
other than the object's identity. See ``ENSURE_ASCII_DIVERGENCE``.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Protocol, Sequence, TypeVar, runtime_checkable

__all__ = [
    "BackendError",
    "BackendUnavailable",
    "BackendCapabilities",
    "ConflictKind",
    "ParamStyle",
    "RetryExhausted",
    "EngineeringBackend",
    "BackendConnection",
    "SqliteEngineeringBackend",
    "canonical_dump",
    "run_with_retry",
    "ENSURE_ASCII_DIVERGENCE",
]


# Two shipped stores canonicalise with the interpreter default ensure_ascii=True
# (engineering_atlas_store.py:229, engineering_workflow_workers.py:176) while the
# identity hash and the other three stores use ensure_ascii=False. For any payload
# containing a non-ASCII character the bytes those two stores persist and
# byte-compare are NOT the bytes the content identity was computed over. Recorded
# here rather than silently normalised, because normalising it would change the
# stored bytes of existing rows.
ENSURE_ASCII_DIVERGENCE: tuple[str, ...] = (
    "src/rakl/engineering_atlas_store.py:_dump uses ensure_ascii default (True)",
    "src/rakl/engineering_workflow_workers.py:_dump uses ensure_ascii default (True)",
    "src/rakl/engineering_state.py:_canonical_json_bytes uses ensure_ascii=False",
)


def canonical_dump(value: Mapping[str, object] | Sequence[object] | object) -> str:
    """Canonical JSON text, byte-identical to the identity-hash encoding."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=lambda item: item.value if isinstance(item, Enum) else item,
    )


class BackendError(RuntimeError):
    """Any typed failure raised by a backend implementation."""


class BackendUnavailable(BackendError):
    """The backend cannot be used at all: no driver, no server, no credentials.

    Distinct from every other error on purpose. "Could not check" is never the
    same claim as "checked and fine", and a caller must be able to tell them
    apart without string matching.
    """

    def __init__(self, backend: str, reasons: Sequence[str]) -> None:
        self.backend = backend
        self.reasons: tuple[str, ...] = tuple(reasons)
        super().__init__(f"{backend} backend unavailable: " + "; ".join(self.reasons))


class RetryExhausted(BackendError):
    """A retryable conflict kept recurring; the caller must not assume success."""


class ConflictKind(str, Enum):
    """How a backend failure should be acted on."""

    NONE = "NONE"
    #: Serialization/lock conflict. The whole read/plan/write closure may be
    #: replayed. SQLite: "database is locked"/"database is table is locked".
    #: PostgreSQL: SQLSTATE 40001 (serialization_failure), 40P01 (deadlock).
    RETRYABLE_CONFLICT = "RETRYABLE_CONFLICT"
    #: A declared invariant was violated (unique/foreign key/check). Replaying
    #: changes nothing; this is the signal idempotency logic reads.
    INTEGRITY_VIOLATION = "INTEGRITY_VIOLATION"
    #: Connection/driver/server level. Neither success nor a proven violation.
    UNAVAILABLE = "UNAVAILABLE"
    #: Classified as nothing else. Never treat as retryable.
    UNKNOWN = "UNKNOWN"


class ParamStyle(str, Enum):
    QMARK = "qmark"       # sqlite3: ... WHERE a=?
    PYFORMAT = "pyformat"  # psycopg/psycopg2: ... WHERE a=%s


@dataclass(frozen=True)
class BackendCapabilities:
    """What a concrete backend promises. Compared directly in parity tests."""

    identity: str
    param_style: ParamStyle
    #: Human-readable statement of how the write transaction obtains isolation.
    write_transaction_mode: str
    #: Where a write-write conflict becomes visible: "BEGIN" (pessimistic,
    #: SQLite BEGIN IMMEDIATE) or "COMMIT" (optimistic, PostgreSQL SERIALIZABLE).
    conflict_detection_point: str
    #: SQL type used for canonical payload columns. Must preserve bytes; see
    #: POSTGRES_SCHEMA_V1.sql on why this is not jsonb.
    payload_column_type: str
    supports_on_conflict_do_nothing: bool


@runtime_checkable
class BackendConnection(Protocol):
    """The only connection surface the stores use."""

    def execute(self, sql: str, parameters: Sequence[object] = ()) -> Any: ...


@runtime_checkable
class EngineeringBackend(Protocol):
    """Everything the ORION stores need from a database, and nothing more."""

    @property
    def capabilities(self) -> BackendCapabilities: ...

    def initialize_schema(self, script: str) -> None:
        """Apply DDL. Must be safe to call repeatedly."""

    def write_transaction(self) -> Any:
        """Context manager: open with write isolation, commit, always release.

        On any exception the transaction rolls back and the exception
        propagates. The connection is closed in a ``finally`` — a rollback that
        leaks the handle is not a rollback a long-lived process can rely on.
        """

    def read_connection(self) -> Any:
        """Context manager for a read-only connection that is actually closed."""

    def classify_error(self, error: BaseException) -> ConflictKind:
        """Map a driver exception onto the action the caller should take."""

    def insert_if_absent(
        self,
        connection: BackendConnection,
        *,
        table: str,
        columns: Sequence[str],
        values: Sequence[object],
        conflict_columns: Sequence[str],
    ) -> bool:
        """Insert a row unless one already exists on ``conflict_columns``.

        Returns True when the row was inserted, False when it was already there.
        This is the primitive behind every "replay returns the prior object"
        path in the stores; the store still re-reads and compares the existing
        row, because *identical key* is not *identical content*.
        """

    def placeholders(self, count: int) -> str:
        """Comma-separated placeholders in this backend's parameter style."""


T = TypeVar("T")


def run_with_retry(
    operation: Callable[[], T],
    *,
    backend: EngineeringBackend,
    attempts: int = 5,
) -> T:
    """Replay a whole read/plan/write closure while it hits retryable conflicts.

    ``operation`` must be the complete closure, not just the write: under
    SERIALIZABLE the conflict is only reported at COMMIT, so re-issuing the
    write alone would commit a plan formed against a snapshot the database has
    already rejected.
    """

    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            return operation()
        except BaseException as error:  # noqa: BLE001 - classified immediately
            if backend.classify_error(error) is not ConflictKind.RETRYABLE_CONFLICT:
                raise
            last = error
    raise RetryExhausted(
        f"{attempts} attempts all ended in a retryable conflict; "
        f"last={type(last).__name__}: {last}"
    ) from last


class SqliteEngineeringBackend:
    """SQLite implementation whose semantics the shipped stores already match.

    ``busy_timeout_ms`` is a constructor argument rather than a constant because
    the reference stores use 10 000 ms, and a conflict test run against a
    10-second timeout does not observe a conflict — it observes a wait followed
    by success, and passes while proving nothing.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        busy_timeout_ms: int = 10_000,
        connect_timeout_s: float = 10.0,
        foreign_keys: bool = True,
    ) -> None:
        self.path = str(path)
        parent = Path(self.path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_ms = int(busy_timeout_ms)
        self.connect_timeout_s = float(connect_timeout_s)
        self.foreign_keys = bool(foreign_keys)

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            identity=f"sqlite:{self.path}",
            param_style=ParamStyle.QMARK,
            write_transaction_mode="BEGIN IMMEDIATE",
            conflict_detection_point="BEGIN",
            payload_column_type="TEXT",
            supports_on_conflict_do_nothing=True,
        )

    # -- plumbing ---------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        # isolation_level=None disables the driver's implicit BEGIN, which is
        # what makes the explicit BEGIN IMMEDIATE below legal. With the default
        # legacy mode, any DML issued before BEGIN IMMEDIATE on the same
        # connection raises "cannot start a transaction within a transaction".
        connection = sqlite3.connect(
            self.path, timeout=self.connect_timeout_s, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        if self.foreign_keys:
            connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        return connection

    def initialize_schema(self, script: str) -> None:
        connection = self._connect()
        try:
            connection.executescript(script)
        finally:
            connection.close()

    @contextmanager
    def write_transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            connection.close()

    @contextmanager
    def read_connection(self) -> Iterator[sqlite3.Connection]:
        # sqlite3.Connection.__exit__ commits or rolls back; it does NOT close.
        # `with self._connect() as db` therefore leaks a handle per call, which
        # is why this returns a closing context manager instead.
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    # -- contract ---------------------------------------------------------

    def classify_error(self, error: BaseException) -> ConflictKind:
        if isinstance(error, sqlite3.IntegrityError):
            return ConflictKind.INTEGRITY_VIOLATION
        if isinstance(error, sqlite3.OperationalError):
            message = str(error).lower()
            if "locked" in message or "busy" in message:
                return ConflictKind.RETRYABLE_CONFLICT
            if "unable to open database" in message or "disk i/o" in message:
                return ConflictKind.UNAVAILABLE
            return ConflictKind.UNKNOWN
        if isinstance(error, BackendUnavailable):
            return ConflictKind.UNAVAILABLE
        return ConflictKind.UNKNOWN

    def placeholders(self, count: int) -> str:
        if count < 1:
            raise ValueError("count must be >= 1")
        return ",".join("?" for _ in range(count))

    def insert_if_absent(
        self,
        connection: BackendConnection,
        *,
        table: str,
        columns: Sequence[str],
        values: Sequence[object],
        conflict_columns: Sequence[str],
    ) -> bool:
        if len(columns) != len(values):
            raise ValueError("columns and values must have equal length")
        if not conflict_columns:
            raise ValueError("conflict_columns is required; a blind insert is not an upsert")
        missing = [c for c in conflict_columns if c not in columns]
        if missing:
            raise ValueError(f"conflict columns not present in insert: {missing}")
        sql = (
            f"INSERT INTO {table} ({','.join(columns)}) "
            f"VALUES ({self.placeholders(len(values))}) "
            f"ON CONFLICT ({','.join(conflict_columns)}) DO NOTHING"
        )
        cursor = connection.execute(sql, tuple(values))
        return bool(getattr(cursor, "rowcount", 0))
