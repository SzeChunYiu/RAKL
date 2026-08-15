"""PostgreSQL implementation of the ORION engineering backend protocol.

This module imports cleanly with no driver installed. That is a hard
requirement, not a convenience: the alternative is an ImportError at collection
time, which reads as "the Postgres path is broken" when the truth is "the
Postgres path was never checked".

Every public entry point therefore returns a **typed** result. There is no code
path that quietly does nothing and no code path that reports success without
having reached a server. ``BackendStatus.CANNOT_CHECK`` is the value returned
when the driver, the DSN or the server is missing, and it is never collapsed
into a boolean.

Isolation
---------
The write transaction runs at ``SERIALIZABLE`` with ``run_with_retry`` on
SQLSTATE 40001. See ``engineering_backend`` for why SERIALIZABLE — and not
READ COMMITTED, REPEATABLE READ, or ``FOR UPDATE`` alone — is the faithful
analogue of the reference stores' ``BEGIN IMMEDIATE``.

One behavioural difference is unavoidable and is surfaced in
``BackendCapabilities.conflict_detection_point``: SQLite refuses the second
writer at ``BEGIN``, PostgreSQL refuses it at ``COMMIT``. A caller that retries
only its write statement rather than its whole read/plan/write closure is
correct on SQLite and wrong here.
"""
from __future__ import annotations

import os
import socket
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator, Sequence
from urllib.parse import urlsplit

from .engineering_backend import (
    BackendCapabilities,
    BackendConnection,
    BackendUnavailable,
    ConflictKind,
    ParamStyle,
)

__all__ = [
    "BackendStatus",
    "DriverProbe",
    "PostgresProbe",
    "PostgresBackendResult",
    "DSN_ENVIRONMENT_VARIABLES",
    "probe_driver",
    "resolve_dsn",
    "probe_postgres",
    "try_open_backend",
    "open_backend",
    "PostgresEngineeringBackend",
    "POSTGRES_SERIALIZATION_SQLSTATES",
    "POSTGRES_INTEGRITY_SQLSTATES",
]


# ---------------------------------------------------------------------------
# Driver import. Never raises.
# ---------------------------------------------------------------------------

_psycopg: Any = None
_psycopg_name: str | None = None
_psycopg_version: str | None = None
_import_errors: list[str] = []

try:  # psycopg 3 preferred
    import psycopg as _psycopg3  # type: ignore[import-not-found]
except Exception as _error:  # pragma: no cover - depends on host
    _import_errors.append(f"psycopg:{type(_error).__name__}")
else:  # pragma: no cover - depends on host
    _psycopg = _psycopg3
    _psycopg_name = "psycopg"
    _psycopg_version = getattr(_psycopg3, "__version__", "unknown")

if _psycopg is None:
    try:
        import psycopg2 as _psycopg2  # type: ignore[import-not-found]
    except Exception as _error:  # pragma: no cover - depends on host
        _import_errors.append(f"psycopg2:{type(_error).__name__}")
    else:  # pragma: no cover - depends on host
        _psycopg = _psycopg2
        _psycopg_name = "psycopg2"
        _psycopg_version = getattr(_psycopg2, "__version__", "unknown")

DRIVER_AVAILABLE: bool = _psycopg is not None
DRIVER_NAME: str | None = _psycopg_name

#: Consulted in order. Nothing else is read and no DSN is ever synthesised: a
#: made-up connection string turns "no database configured" into a connection
#: error against someone else's database.
DSN_ENVIRONMENT_VARIABLES: tuple[str, ...] = (
    "ORION_POSTGRES_DSN",
    "ORION_PG_DSN",
    "RAKL_POSTGRES_DSN",
    "DATABASE_URL",
)

#: 40001 serialization_failure, 40P01 deadlock_detected, 40000 transaction_rollback.
POSTGRES_SERIALIZATION_SQLSTATES: frozenset[str] = frozenset({"40001", "40P01", "40000"})
#: 23xxx integrity constraint violation family.
POSTGRES_INTEGRITY_SQLSTATES: frozenset[str] = frozenset(
    {"23000", "23001", "23502", "23503", "23505", "23514", "23P01"}
)
_POSTGRES_UNAVAILABLE_SQLSTATES: frozenset[str] = frozenset(
    {"08000", "08003", "08006", "08001", "08004", "57P01", "57P02", "57P03", "53300"}
)


class BackendStatus(str, Enum):
    """Terminal status of any attempt to obtain a PostgreSQL backend."""

    AVAILABLE = "AVAILABLE"
    #: Driver, DSN or server missing. NOT a failure of the backend under test
    #: and NOT evidence that anything works. Never rendered as pass/fail.
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class DriverProbe:
    available: bool
    driver: str | None
    version: str | None
    import_errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "available": self.available,
            "driver": self.driver,
            "version": self.version,
            "import_errors": list(self.import_errors),
        }


@dataclass(frozen=True)
class PostgresProbe:
    """Everything observed about the host's PostgreSQL situation."""

    status: BackendStatus
    driver: DriverProbe
    dsn_source: str | None
    dsn_present: bool
    server_reachable: bool | None
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "driver": self.driver.to_dict(),
            "dsn_source": self.dsn_source,
            "dsn_present": self.dsn_present,
            # None means "not attempted", which is not the same as False.
            "server_reachable": self.server_reachable,
            "reasons": list(self.reasons),
        }

    @property
    def skip_reason(self) -> str:
        return "postgres backend CANNOT_CHECK: " + "; ".join(self.reasons)


@dataclass(frozen=True)
class PostgresBackendResult:
    """Either a usable backend, or a typed statement of why there is none."""

    status: BackendStatus
    probe: PostgresProbe
    backend: "PostgresEngineeringBackend | None" = None

    @property
    def available(self) -> bool:
        return self.status is BackendStatus.AVAILABLE and self.backend is not None

    def require(self) -> "PostgresEngineeringBackend":
        if self.backend is None:
            raise BackendUnavailable("postgres", self.probe.reasons)
        return self.backend

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status.value, "probe": self.probe.to_dict()}


def probe_driver() -> DriverProbe:
    return DriverProbe(
        available=DRIVER_AVAILABLE,
        driver=DRIVER_NAME,
        version=_psycopg_version,
        import_errors=tuple(_import_errors),
    )


def resolve_dsn(explicit: str | None = None) -> tuple[str | None, str | None]:
    """Return ``(dsn, source)``. Reads the environment; invents nothing."""

    if explicit:
        return explicit, "explicit_argument"
    for name in DSN_ENVIRONMENT_VARIABLES:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip(), f"env:{name}"
    return None, None


def _tcp_reachable(dsn: str, timeout: float) -> tuple[bool, str | None]:
    """Best-effort TCP probe so an unreachable server is not reported as a bug.

    A parse failure or a non-TCP DSN yields ``(True, reason)``: this probe may
    only *rule out* a connection, never rule one in on its own.
    """

    try:
        parts = urlsplit(dsn if "://" in dsn else f"postgresql://{dsn}")
        host = parts.hostname
        port = parts.port or 5432
    except Exception as error:  # noqa: BLE001
        return True, f"dsn_unparsed:{type(error).__name__}"
    if not host or host.startswith("/"):
        return True, "non_tcp_or_unix_socket_dsn"
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, None
    except OSError as error:
        return False, f"tcp_connect_failed:{host}:{port}:{error.__class__.__name__}"


def probe_postgres(
    dsn: str | None = None, *, connect_timeout: float = 2.0
) -> PostgresProbe:
    """Determine, without side effects, whether a Postgres backend can be used."""

    driver = probe_driver()
    resolved, source = resolve_dsn(dsn)
    reasons: list[str] = []

    if not driver.available:
        reasons.append(
            "driver_missing:psycopg,psycopg2 not importable in the active interpreter"
        )
    if resolved is None:
        reasons.append(
            "dsn_absent:none of " + ",".join(DSN_ENVIRONMENT_VARIABLES) + " is set"
        )

    server_reachable: bool | None = None
    if resolved is not None:
        server_reachable, detail = _tcp_reachable(resolved, connect_timeout)
        if not server_reachable:
            reasons.append(f"server_unreachable:{detail}")

    if reasons:
        return PostgresProbe(
            status=BackendStatus.CANNOT_CHECK,
            driver=driver,
            dsn_source=source,
            dsn_present=resolved is not None,
            server_reachable=server_reachable,
            reasons=tuple(reasons),
        )
    return PostgresProbe(
        status=BackendStatus.AVAILABLE,
        driver=driver,
        dsn_source=source,
        dsn_present=True,
        server_reachable=server_reachable,
        reasons=(),
    )


def try_open_backend(
    dsn: str | None = None, *, connect_timeout: float = 2.0
) -> PostgresBackendResult:
    """Typed, never-raising entry point. Use this from tests and tooling."""

    probe = probe_postgres(dsn, connect_timeout=connect_timeout)
    if probe.status is not BackendStatus.AVAILABLE:
        return PostgresBackendResult(status=BackendStatus.CANNOT_CHECK, probe=probe)
    resolved, _ = resolve_dsn(dsn)
    assert resolved is not None  # guaranteed by probe.status
    backend = PostgresEngineeringBackend(resolved)
    # A live handshake is the only thing that turns CANNOT_CHECK into AVAILABLE.
    # A reachable TCP port is not a working database.
    try:
        with backend.read_connection() as connection:
            connection.execute("SELECT 1")
    except BackendUnavailable:
        raise
    except Exception as error:  # noqa: BLE001
        failed = PostgresProbe(
            status=BackendStatus.CANNOT_CHECK,
            driver=probe.driver,
            dsn_source=probe.dsn_source,
            dsn_present=True,
            server_reachable=probe.server_reachable,
            reasons=(f"handshake_failed:{type(error).__name__}:{error}",),
        )
        return PostgresBackendResult(status=BackendStatus.CANNOT_CHECK, probe=failed)
    return PostgresBackendResult(
        status=BackendStatus.AVAILABLE, probe=probe, backend=backend
    )


def open_backend(dsn: str | None = None) -> "PostgresEngineeringBackend":
    """Raising variant for call sites that must not proceed without a database."""

    return try_open_backend(dsn).require()


def _sqlstate(error: BaseException) -> str | None:
    state = getattr(error, "sqlstate", None)
    if state:
        return str(state)
    diag = getattr(error, "diag", None)
    state = getattr(diag, "sqlstate", None) if diag is not None else None
    if state:
        return str(state)
    # psycopg2 exposes it as pgcode.
    code = getattr(error, "pgcode", None)
    return str(code) if code else None


class PostgresEngineeringBackend:
    """The engineering backend protocol over psycopg/psycopg2.

    Constructing this object does not connect. Every method that needs the
    driver raises ``BackendUnavailable`` when it is missing, so an instance
    obtained by some path other than :func:`try_open_backend` still cannot
    produce a fake success.
    """

    def __init__(self, dsn: str, *, statement_timeout_ms: int | None = None) -> None:
        if not dsn or not dsn.strip():
            raise ValueError("dsn is required; this backend never synthesises one")
        self.dsn = dsn.strip()
        self.statement_timeout_ms = statement_timeout_ms

    # -- availability -----------------------------------------------------

    def _require_driver(self) -> Any:
        if _psycopg is None:
            raise BackendUnavailable(
                "postgres",
                (
                    "driver_missing:psycopg,psycopg2 not importable",
                    *(_import_errors or ()),
                ),
            )
        return _psycopg

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            identity=f"postgres:{_redact(self.dsn)}",
            param_style=ParamStyle.PYFORMAT,
            write_transaction_mode="SERIALIZABLE (retry on SQLSTATE 40001)",
            # The single behavioural difference from SQLite that callers must
            # know about: the conflict lands at COMMIT, not at BEGIN.
            conflict_detection_point="COMMIT",
            payload_column_type="text",
            supports_on_conflict_do_nothing=True,
        )

    # -- plumbing ---------------------------------------------------------

    def _connect(self) -> Any:
        driver = self._require_driver()
        connection = driver.connect(self.dsn)
        if self.statement_timeout_ms is not None:
            connection.cursor().execute(
                f"SET statement_timeout = {int(self.statement_timeout_ms)}"
            )
        return connection

    def initialize_schema(self, script: str) -> None:
        self._require_driver()
        with self.write_transaction() as connection:
            connection.execute(script)

    @contextmanager
    def write_transaction(self) -> Iterator[BackendConnection]:
        self._require_driver()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute("BEGIN ISOLATION LEVEL SERIALIZABLE")
            yield _CursorConnection(cursor)
            connection.commit()
        except BaseException:
            try:
                connection.rollback()
            except Exception:  # noqa: BLE001 - rollback failure must not mask the cause
                pass
            raise
        finally:
            try:
                connection.close()
            except Exception:  # noqa: BLE001
                pass

    @contextmanager
    def read_connection(self) -> Iterator[BackendConnection]:
        self._require_driver()
        connection = self._connect()
        try:
            yield _CursorConnection(connection.cursor())
        finally:
            try:
                connection.close()
            except Exception:  # noqa: BLE001
                pass

    # -- contract ---------------------------------------------------------

    def classify_error(self, error: BaseException) -> ConflictKind:
        if isinstance(error, BackendUnavailable):
            return ConflictKind.UNAVAILABLE
        state = _sqlstate(error)
        if state is None:
            return ConflictKind.UNKNOWN
        if state in POSTGRES_SERIALIZATION_SQLSTATES:
            return ConflictKind.RETRYABLE_CONFLICT
        if state in POSTGRES_INTEGRITY_SQLSTATES:
            return ConflictKind.INTEGRITY_VIOLATION
        if state in _POSTGRES_UNAVAILABLE_SQLSTATES or state.startswith("08"):
            return ConflictKind.UNAVAILABLE
        return ConflictKind.UNKNOWN

    def placeholders(self, count: int) -> str:
        if count < 1:
            raise ValueError("count must be >= 1")
        return ",".join("%s" for _ in range(count))

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


class _CursorConnection:
    """Adapts a DB-API cursor to the ``BackendConnection`` execute-returns-cursor
    shape that ``sqlite3.Connection`` provides natively."""

    __slots__ = ("_cursor",)

    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    def execute(self, sql: str, parameters: Sequence[object] = ()) -> Any:
        self._cursor.execute(sql, tuple(parameters) if parameters else None)
        return self._cursor

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)


def _redact(dsn: str) -> str:
    """Strip credentials so a DSN can appear in a capabilities string or report."""

    try:
        parts = urlsplit(dsn if "://" in dsn else f"postgresql://{dsn}")
    except Exception:  # noqa: BLE001
        return "<unparsed-dsn>"
    host = parts.hostname or "<host>"
    port = parts.port or 5432
    database = (parts.path or "/").lstrip("/") or "<db>"
    return f"{host}:{port}/{database}"
