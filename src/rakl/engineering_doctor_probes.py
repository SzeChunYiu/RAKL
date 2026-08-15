"""E20 — the real operator doctor probes.

`engineering_ops.OperatorDoctor` is a harness: it holds callables, catches their
exceptions and renders them. It ships with no probes, so nothing it renders has
yet inspected anything. This module supplies probes that genuinely open the live
subsystems — the sqlite databases, the content-addressed object store, the
rebuildable index, the worker lease table, the stored status record, the backup
manifest, the migration parity projection, the build provenance record and the
secret store — and reports what it found.

The discrimination rule, which is the whole point of the fibre and is asserted
row by row in ``tests/test_engineering_doctor_probes.py``:

    target absent / unreachable / unreadable / handle not supplied  -> CANNOT_CHECK
    target present, inspected, inspection says broken               -> FAIL
    target present, inspected, healthy but outside a threshold      -> DEGRADED
    target present, inspected, inside every threshold               -> OK

So a *corrupt* database is FAIL and a *missing* database is CANNOT_CHECK. "Could
not check" is never reported as "checked and fine", because an operator who
cannot tell those apart is exactly the failure E20 names.

Two hazards this module is built around:

  * ``sqlite3.connect(path)`` CREATES a missing database file, and
    ``PRAGMA integrity_check`` on the empty file it just created returns ``ok``.
    A naive probe therefore returns OK for a database that does not exist. Every
    database read here goes through ``_open_readonly``, which uses
    ``file:...?mode=ro`` and is preceded by an existence check, and the tests
    assert both the CANNOT_CHECK verdict and that no file was created.
  * A diagnostic that mutates is a hazard in its own right. No probe here writes,
    migrates, rebuilds or repairs anything.

Time is injected as an integer (``ProbeContext.now``), matching
`engineering_workflow_workers`, so lease expiry and backup staleness are driven
deterministically. ``now=None`` means no clock was supplied: every time-dependent
judgement is then CANNOT_CHECK rather than assumed fresh.

NOT claimed here: that a probe passing locally proves a production subsystem is
healthy. The probes inspect whatever handles the caller wires in. What is claimed
is that an unwired, unreachable or unreadable subsystem can never be rendered OK.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .engineering_migration import ParityVerdict, compare_migration_parity
from .engineering_ops import (
    BackupManifest,
    BuildProvenance,
    OperatorDoctor,
    ProbeResult,
    ProbeStatus,
    ProvenanceVerdict,
    RestoreVerdict,
    project_observatory,
    verify_restore,
)
from .engineering_workflow import ActivityStatus
from .project_runtime import CanonicalPayloadStore, PayloadIntegrityError

# Severity for operator triage. FAIL dominates: a confirmed broken subsystem must
# not be masked by an unavailable one. CANNOT_CHECK outranks DEGRADED because
# being blind is worse than being slow.
_SEVERITY: dict[ProbeStatus, int] = {
    ProbeStatus.OK: 0,
    ProbeStatus.DEGRADED: 1,
    ProbeStatus.CANNOT_CHECK: 2,
    ProbeStatus.FAIL: 3,
}

_FRESHNESS_OK = frozenset({"FRESH", "CURRENT"})
_FRESHNESS_DEGRADED = frozenset({"STALE", "DEGRADED", "AGING"})
_GATE_FAILED = frozenset({"FAIL", "FAILED", "BLOCKED", "VIOLATED"})
_GATE_PASSED = frozenset({"PASS", "PASSED", "OK", "SATISFIED"})


@dataclass(frozen=True)
class ProbeContext:
    """Handles the operator wires in. Every field is optional on purpose.

    An empty context is a legitimate input: it is the state of an operator who
    has wired nothing, and it must produce all-CANNOT_CHECK, never all-OK. That
    is the cheapest direct test of this module's one non-negotiable rule.
    """

    now: int | None = None

    # database reachability + integrity
    database_path: Path | None = None
    database_expected_tables: tuple[str, ...] = ()

    # content-addressed object store
    object_store_root: Path | None = None
    expected_object_digests: tuple[str, ...] = ()

    # rebuildable index over the canonical semantic store
    semantic_store: object | None = None
    semantic_index: object | None = None
    semantic_sequence: int = 0

    # durable multi-worker workflow engine
    workflow_db_path: Path | None = None
    lease_expiry_grace_seconds: int = 0

    # stored EpistemicStatus record (read, never recomputed)
    stored_status: Mapping[str, object] | None = None

    # backup / restore
    backup_manifest: BackupManifest | None = None
    backup_restore_root: Path | None = None
    backup_max_age_seconds: int = 86_400

    # migration parity
    migration_source: object | None = None
    migration_target: object | None = None

    # build provenance
    provenance: BuildProvenance | None = None
    artifact_bytes: bytes | None = None

    # secrets
    secret_store: object | None = None
    required_secret_names: tuple[str, ...] = ()


def _open_readonly(path: Path) -> sqlite3.Connection:
    """Open an existing database without ever creating one.

    ``sqlite3.connect(path)`` on a missing path creates an empty database whose
    integrity check passes. Read-only URI mode raises instead, which is the only
    behaviour compatible with "a probe that cannot run returns CANNOT_CHECK".
    """

    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _parse_utc(value: str) -> int:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def _table_names(db: sqlite3.Connection) -> set[str]:
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


# --- database ---------------------------------------------------------------


def probe_database(ctx: ProbeContext) -> ProbeResult:
    """Reachability plus `PRAGMA integrity_check` plus declared-schema presence."""

    name = "database"
    if ctx.database_path is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no database path supplied")
    path = Path(ctx.database_path)
    if not path.is_file():
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"no database file at {path}")
    try:
        db = _open_readonly(path)
    except sqlite3.OperationalError as exc:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"unreachable read-only: {exc}")
    try:
        try:
            rows = db.execute("PRAGMA integrity_check").fetchall()
        except sqlite3.OperationalError as exc:
            # cannot read it (locked, permissions, i/o) — not evidence of health
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"integrity check unavailable: {exc}")
        except sqlite3.DatabaseError as exc:
            # "file is not a database" / "database disk image is malformed"
            return ProbeResult(name, ProbeStatus.FAIL, f"integrity check refused: {exc}")
        findings = [str(row[0]) for row in rows]
        if findings != ["ok"]:
            return ProbeResult(name, ProbeStatus.FAIL, "integrity_check: " + "; ".join(findings[:3]))
        if ctx.database_expected_tables:
            try:
                present = _table_names(db)
            except sqlite3.DatabaseError as exc:
                return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"schema unreadable: {exc}")
            missing = sorted(set(ctx.database_expected_tables) - present)
            if missing:
                return ProbeResult(name, ProbeStatus.FAIL, f"declared tables absent: {missing}")
        return ProbeResult(
            name,
            ProbeStatus.OK,
            f"integrity_check=ok, {len(ctx.database_expected_tables)} declared tables present, {path}",
        )
    finally:
        db.close()


# --- object store -----------------------------------------------------------


def probe_object_store(ctx: ProbeContext) -> ProbeResult:
    """Every declared object must still read back at its own digest."""

    name = "object_store"
    if ctx.object_store_root is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no object store root supplied")
    root = Path(ctx.object_store_root)
    if not root.is_dir():
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"no object store at {root}")
    if not ctx.expected_object_digests:
        return ProbeResult(
            name, ProbeStatus.CANNOT_CHECK, "no expected object digests declared; presence of a directory is not integrity"
        )
    store = CanonicalPayloadStore(root)
    missing: list[str] = []
    corrupt: list[str] = []
    unparseable: list[str] = []
    for digest in ctx.expected_object_digests:
        try:
            store.read_bytes(digest)
        except KeyError:
            missing.append(digest)
        except PayloadIntegrityError:
            corrupt.append(digest)
        except ValueError:
            unparseable.append(digest)
        except OSError as exc:
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"object store unreadable: {exc}")
    if corrupt or missing:
        return ProbeResult(
            name,
            ProbeStatus.FAIL,
            f"corrupt={sorted(corrupt)[:3]} missing={sorted(missing)[:3]} of {len(ctx.expected_object_digests)} declared",
        )
    if unparseable:
        return ProbeResult(
            name, ProbeStatus.CANNOT_CHECK, f"malformed declared digests, not checkable: {sorted(unparseable)[:3]}"
        )
    return ProbeResult(
        name,
        ProbeStatus.OK,
        f"{len(ctx.expected_object_digests)} declared objects verified, {store.object_count()} stored",
    )


# --- index ------------------------------------------------------------------


def probe_index(ctx: ProbeContext) -> ProbeResult:
    """Index lag: the built projection's revision against the canonical revision.

    The index is disposable and grants no authority, so a lagging index is
    DEGRADED, not FAIL. An index that was never built is CANNOT_CHECK — it has
    no revision to compare, and reporting OK for it would be reporting on a
    projection nobody made.
    """

    name = "index"
    if ctx.semantic_store is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no semantic store supplied")
    if ctx.semantic_index is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no index supplied")
    snapshot = getattr(ctx.semantic_index, "snapshot", None)
    if snapshot is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "index has never been built; nothing to compare")
    revision_of = getattr(ctx.semantic_store, "semantic_revision", None)
    if not callable(revision_of):
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "semantic store exposes no semantic_revision")
    try:
        canonical = revision_of(ctx.semantic_sequence)
    except Exception as exc:  # noqa: BLE001 — an unreadable store did not check
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"canonical revision unavailable: {type(exc).__name__}: {exc}")
    indexed = getattr(snapshot, "semantic_revision", None)
    if not indexed:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "index snapshot carries no revision")
    if indexed != canonical:
        return ProbeResult(
            name,
            ProbeStatus.DEGRADED,
            f"index lag at sequence {ctx.semantic_sequence}: indexed={indexed} canonical={canonical}",
        )
    atoms = getattr(snapshot, "indexed_atoms", ())
    return ProbeResult(name, ProbeStatus.OK, f"index current at sequence {ctx.semantic_sequence}, {len(atoms)} atoms")


# --- workflow workers -------------------------------------------------------


def probe_workflow_workers(ctx: ProbeContext) -> ProbeResult:
    """RECOVERY_REQUIRED runs are FAIL; expired leases are DEGRADED.

    RECOVERY_REQUIRED is the engine's typed statement that an external effect may
    or may not have happened. That is an operator obligation, not a transient, so
    it outranks a stuck lease — a lease whose holder went silent is reclaimable
    by design.

    The engine exposes no enumeration API (``activity()`` needs an id you already
    know), so this reads its tables read-only rather than adding a method to a
    module this fibre does not own.
    """

    name = "workflow_workers"
    if ctx.workflow_db_path is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no workflow database path supplied")
    path = Path(ctx.workflow_db_path)
    if not path.is_file():
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"no workflow database at {path}")
    try:
        db = _open_readonly(path)
    except sqlite3.OperationalError as exc:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"unreachable read-only: {exc}")
    try:
        try:
            tables = _table_names(db)
        except sqlite3.DatabaseError as exc:
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"schema unreadable: {exc}")
        if not {"worker_activities", "leases"} <= tables:
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "not a worker workflow database (tables absent)")
        try:
            recovery = db.execute(
                "SELECT workflow_id,activity_id FROM worker_activities WHERE status=? ORDER BY activity_id",
                (ActivityStatus.RECOVERY_REQUIRED.value,),
            ).fetchall()
            leases = db.execute("SELECT activity_id,worker_id,heartbeat_at,ttl FROM leases").fetchall()
        except sqlite3.DatabaseError as exc:
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"workflow tables unreadable: {exc}")
    finally:
        db.close()

    if recovery:
        listed = ", ".join(f"{row[0]}/{row[1]}" for row in recovery[:3])
        return ProbeResult(
            name, ProbeStatus.FAIL, f"{len(recovery)} activities in RECOVERY_REQUIRED: {listed}"
        )
    if ctx.now is None:
        return ProbeResult(
            name,
            ProbeStatus.CANNOT_CHECK,
            f"no RECOVERY_REQUIRED activities, but lease liveness needs an injected clock ({len(leases)} leases held)",
        )
    # matches Lease.alive_at: alive iff now - heartbeat_at < ttl
    expired = [
        row for row in leases if (ctx.now - int(row[2])) >= (int(row[3]) + ctx.lease_expiry_grace_seconds)
    ]
    if expired:
        listed = ", ".join(f"{row[0]}@{row[1]}" for row in expired[:3])
        return ProbeResult(
            name, ProbeStatus.DEGRADED, f"{len(expired)}/{len(leases)} leases expired and reclaimable: {listed}"
        )
    return ProbeResult(name, ProbeStatus.OK, f"no RECOVERY_REQUIRED activities, {len(leases)} live leases")


# --- stored status / saturation freshness -----------------------------------


def probe_status_freshness(ctx: ProbeContext) -> ProbeResult:
    """Read the stored status through the E11 read model. Compute nothing.

    The read model's invariant is that it derives no epistemic value; this probe
    inherits it. It maps *stored* strings to a probe status and reports an
    unrecognised stored freshness as CANNOT_CHECK rather than guessing which side
    of the line it falls on.
    """

    name = "status_freshness"
    if ctx.stored_status is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no stored status record supplied")
    view = project_observatory(ctx.stored_status)
    failed = sorted(k for k, v in view.hard_gates.items() if str(v).upper() in _GATE_FAILED)
    if failed:
        return ProbeResult(name, ProbeStatus.FAIL, f"stored hard gates failing: {failed}")
    unknown_gates = sorted(
        k for k, v in view.hard_gates.items() if str(v).upper() not in _GATE_PASSED | _GATE_FAILED
    )
    freshness = str(view.freshness).upper()
    if freshness in _FRESHNESS_OK:
        if unknown_gates:
            return ProbeResult(
                name, ProbeStatus.CANNOT_CHECK, f"stored gate verdicts not interpretable: {unknown_gates}"
            )
        return ProbeResult(
            name,
            ProbeStatus.OK,
            f"stored freshness={view.freshness}, gates={dict(view.hard_gates)}, axes={dict(view.saturation_axes)}",
        )
    if freshness in _FRESHNESS_DEGRADED:
        return ProbeResult(name, ProbeStatus.DEGRADED, f"stored freshness={view.freshness} (status_id={view.status_id})")
    return ProbeResult(
        name, ProbeStatus.CANNOT_CHECK, f"stored freshness {view.freshness!r} is absent or not interpretable"
    )


# --- backup -----------------------------------------------------------------


def probe_backup(ctx: ProbeContext) -> ProbeResult:
    """A backup is healthy only if it names files, restores byte-exact and is recent."""

    name = "backup"
    manifest = ctx.backup_manifest
    if manifest is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no backup manifest supplied")
    if not manifest.entries:
        return ProbeResult(name, ProbeStatus.FAIL, f"backup {manifest.backup_id} names no files")

    restored = ""
    if ctx.backup_restore_root is not None:
        root = Path(ctx.backup_restore_root)
        if not root.is_dir():
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"restore root {root} is not present")
        try:
            verdict, offenders = verify_restore(root, manifest)
        except OSError as exc:
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"restore root unreadable: {exc}")
        if verdict is not RestoreVerdict.EXACT:
            return ProbeResult(name, ProbeStatus.FAIL, f"restore {verdict.value}: {list(offenders)[:3]}")
        restored = f", restore verified EXACT over {len(manifest.entries)} entries"

    try:
        created = _parse_utc(manifest.created_at)
    except ValueError:
        return ProbeResult(
            name,
            ProbeStatus.CANNOT_CHECK,
            f"backup created_at {manifest.created_at!r} is not an ISO-8601 timestamp; age not checkable{restored}",
        )
    if ctx.now is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"no clock supplied; backup age not checkable{restored}")
    age = ctx.now - created
    if age < 0:
        return ProbeResult(
            name, ProbeStatus.CANNOT_CHECK, f"backup timestamp is {-age}s ahead of the supplied clock{restored}"
        )
    if age > ctx.backup_max_age_seconds:
        return ProbeResult(
            name, ProbeStatus.DEGRADED, f"backup {manifest.backup_id} is {age}s old (budget {ctx.backup_max_age_seconds}s){restored}"
        )
    return ProbeResult(name, ProbeStatus.OK, f"backup {manifest.backup_id} is {age}s old{restored}")


# --- migration --------------------------------------------------------------


def probe_migration(ctx: ProbeContext) -> ProbeResult:
    """Canonical parity between the source store and the migrated target."""

    name = "migration"
    if ctx.migration_source is None or ctx.migration_target is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "migration source and/or target projection not supplied")
    report = compare_migration_parity(ctx.migration_source, ctx.migration_target)
    if report.verdict is ParityVerdict.MATCH:
        return ProbeResult(name, ProbeStatus.OK, f"parity MATCH at {report.source_digest[:12]}")
    if report.verdict is ParityVerdict.MISMATCH:
        return ProbeResult(
            name,
            ProbeStatus.FAIL,
            f"parity MISMATCH source={report.source_digest[:12]} target={report.target_digest[:12]} {list(report.differences)}",
        )
    return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"parity CANNOT_CHECK: {list(report.differences)}")


# --- provenance -------------------------------------------------------------


def probe_provenance(ctx: ProbeContext) -> ProbeResult:
    """Verify the build provenance record against the actual artifact bytes."""

    name = "provenance"
    if ctx.provenance is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no build provenance record supplied")
    if ctx.artifact_bytes is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no artifact bytes supplied; a record cannot verify itself")
    verdict = ctx.provenance.verify(ctx.artifact_bytes)
    if verdict is ProvenanceVerdict.VERIFIED:
        return ProbeResult(name, ProbeStatus.OK, f"VERIFIED {ctx.provenance.artifact_ref}")
    return ProbeResult(name, ProbeStatus.FAIL, f"{verdict.value} for {ctx.provenance.artifact_ref}")


# --- secrets ----------------------------------------------------------------


def probe_secrets(ctx: ProbeContext) -> ProbeResult:
    """Declared secrets must resolve. Only references ever enter the detail string."""

    name = "secrets"
    store = ctx.secret_store
    if store is None:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no secret store supplied")
    if not ctx.required_secret_names:
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "no required secret names declared")
    resolve = getattr(store, "resolve", None)
    reference = getattr(store, "reference", None)
    if not callable(resolve) or not callable(reference):
        return ProbeResult(name, ProbeStatus.CANNOT_CHECK, "secret store exposes no resolve/reference contract")
    missing: list[str] = []
    for secret_name in ctx.required_secret_names:
        try:
            resolve(secret_name)  # value deliberately not bound: it must never reach a detail string
        except KeyError:
            missing.append(secret_name)
        except Exception as exc:  # noqa: BLE001 — an unreachable secret manager did not check
            return ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"secret store unavailable: {type(exc).__name__}: {exc}")
    if missing:
        return ProbeResult(
            name, ProbeStatus.FAIL, "unresolvable: " + ", ".join(str(reference(n)) for n in sorted(missing))
        )
    return ProbeResult(
        name, ProbeStatus.OK, "resolvable: " + ", ".join(str(reference(n)) for n in ctx.required_secret_names)
    )


# --- registry ---------------------------------------------------------------


PROBE_FUNCTIONS: dict[str, Callable[[ProbeContext], ProbeResult]] = {
    "backup": probe_backup,
    "database": probe_database,
    "index": probe_index,
    "migration": probe_migration,
    "object_store": probe_object_store,
    "provenance": probe_provenance,
    "secrets": probe_secrets,
    "status_freshness": probe_status_freshness,
    "workflow_workers": probe_workflow_workers,
}


def build_default_probes(ctx: ProbeContext) -> dict[str, Callable[[], ProbeResult]]:
    """Bind every probe to one context, ready for ``OperatorDoctor.register``."""

    return {name: (lambda fn=fn: fn(ctx)) for name, fn in PROBE_FUNCTIONS.items()}  # type: ignore[misc]


def build_doctor(ctx: ProbeContext) -> OperatorDoctor:
    doctor = OperatorDoctor()
    for name, probe in build_default_probes(ctx).items():
        doctor.register(name, probe)
    return doctor


def worst_status(results: Sequence[ProbeResult]) -> ProbeStatus:
    """Delegates to the canonical rollup in engineering_ops.

    There must be exactly one definition of "overall health" in the codebase.
    This function exists for callers that imported it here; the ordering lives
    in OperatorDoctor.overall.
    """

    return OperatorDoctor.overall(results)

def render_report(results: Sequence[ProbeResult]) -> str:
    lines = [f"ORION DOCTOR  overall={worst_status(results).value}  probes={len(results)}"]
    for result in sorted(results, key=lambda r: (-_SEVERITY[r.status], r.subsystem)):
        lines.append(f"  {result.status.value:<12} {result.subsystem:<18} {result.detail}")
    return "\n".join(lines)


__all__ = [
    "PROBE_FUNCTIONS",
    "ProbeContext",
    "build_default_probes",
    "build_doctor",
    "probe_backup",
    "probe_database",
    "probe_index",
    "probe_migration",
    "probe_object_store",
    "probe_provenance",
    "probe_secrets",
    "probe_status_freshness",
    "probe_workflow_workers",
    "render_report",
    "worst_status",
]
