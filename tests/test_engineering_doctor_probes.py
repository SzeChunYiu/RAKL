"""E20 — every doctor probe against BOTH a healthy and a deliberately broken subsystem.

A probe that only ever returns OK proves nothing, so each probe below has a
healthy row and at least one broken row, plus the row that matters most: the
unavailable case, which must be CANNOT_CHECK and never OK.

The two whole-system assertions are at the top of the file:

  * ``ProbeContext()`` — nothing wired — must yield CANNOT_CHECK for every probe
    and OK for none.
  * a fully healthy fixture must yield OK for every probe and raise no alarm.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rakl.engineering_doctor_probes import (
    PROBE_FUNCTIONS,
    ProbeContext,
    build_doctor,
    probe_backup,
    probe_database,
    probe_index,
    probe_migration,
    probe_object_store,
    probe_provenance,
    probe_secrets,
    probe_status_freshness,
    probe_workflow_workers,
    render_report,
    worst_status,
)
from rakl.engineering_http import SecretStore
from rakl.engineering_index import RebuildableSemanticIndex
from rakl.engineering_atlas_store import (
    AtlasChartRecord,
    AtlasPlaneBatch,
    SqliteAtlasPlaneStore,
    atlas_revision_for,
)
from rakl.engineering_ops import (
    BuildProvenance,
    OperatorDoctor,
    ProbeResult,
    ProbeStatus,
    take_backup,
)
from rakl.engineering_semantic_store import (
    SemanticAtomVersion,
    SemanticFiber,
    SqliteSemanticStateStore,
)
from rakl.engineering_workflow import ActivitySpec
from rakl.engineering_workflow_workers import ClaimVerdict, SqliteWorkerWorkflowEngine
from rakl.project_runtime import CanonicalPayloadStore

CREATED_AT = "2026-08-15T00:00:00+00:00"
NOW = int(datetime.fromisoformat(CREATED_AT).astimezone(timezone.utc).timestamp()) + 60

ARTIFACT = b"orion-release-artifact-bytes"


def _sha256(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _atom(atom_id: str, sequence: int, *, supersedes: str | None = None) -> SemanticAtomVersion:
    return SemanticAtomVersion(
        atom_id=atom_id,
        fiber_id="fiber:root",
        kind="MECHANISM_NODE",
        label=f"label {atom_id} v{sequence}",
        evidence_ids=(f"evidence:{atom_id}:{sequence}",),
        payload={"value": sequence},
        valid_from_sequence=sequence,
        supersedes_version_id=supersedes,
    )


def _semantic(tmp_path):
    store = SqliteSemanticStateStore(tmp_path / "semantic.sqlite3")
    store.add_fiber(SemanticFiber("fiber:root"), valid_from_snapshot_id="snapshot:0")
    store.add_atom_version(_atom("a", 0), valid_from_snapshot_id="snapshot:0")
    index = RebuildableSemanticIndex()
    index.rebuild(store, sequence=0)
    return store, index


def _workflow(tmp_path, *, external_effect: bool = False):
    engine = SqliteWorkerWorkflowEngine(tmp_path / "workflow.sqlite3")
    spec = ActivitySpec(
        activity_id="act:1",
        invocation_id="inv:1",
        input_digest="d" * 64,
        retry_safe=True,
        external_effect=external_effect,
        max_attempts=5,
    )
    engine.schedule("wf:1", spec, idempotency_key="idem:1")
    claim = engine.claim("wf:1", "act:1", worker_id="worker-a", now=NOW, ttl=30)
    assert claim.verdict is ClaimVerdict.ACQUIRED
    return engine, claim.lease


@pytest.fixture()
def healthy(tmp_path) -> ProbeContext:
    """One fully wired, fully healthy system."""

    store, index = _semantic(tmp_path)

    objects_root = tmp_path / "store" / "sha256"
    payload_store = CanonicalPayloadStore(objects_root)
    stored = payload_store.put_bytes(b"canonical evidence payload")

    engine, _lease = _workflow(tmp_path)

    backup_src = tmp_path / "backup_src"
    (backup_src / "nested").mkdir(parents=True)
    (backup_src / "nested" / "x.json").write_text('{"k":1}')
    (backup_src / "y.bin").write_bytes(b"\x00\x01\x02")
    manifest = take_backup(backup_src, backup_id="bk-1", created_at=CREATED_AT)

    secrets = SecretStore()
    secrets.put("ORION_DB_PASSWORD", "s3cr3t-value-that-must-never-render")

    return ProbeContext(
        now=NOW,
        database_path=Path(store.path),
        database_expected_tables=("semantic_atoms", "semantic_atom_versions", "semantic_fibers"),
        object_store_root=objects_root,
        expected_object_digests=(stored.sha256,),
        semantic_store=store,
        semantic_index=index,
        semantic_sequence=0,
        workflow_db_path=Path(engine.path),
        stored_status={
            "project_id": "orion",
            "status_id": "status:1",
            "freshness": "FRESH",
            "hard_gates": {"evidence_sufficiency": "PASS"},
            "saturation_axes": {"knowledge": "SATURATED"},
        },
        backup_manifest=manifest,
        backup_restore_root=backup_src,
        backup_max_age_seconds=3600,
        migration_source={"atoms": [1, 2, 3]},
        migration_target={"atoms": [1, 2, 3]},
        provenance=BuildProvenance(
            source_commit="c" * 40,
            lock_digest="l" * 64,
            build_procedure_digest="b" * 64,
            artifact_ref="registry.example/orion@sha256:" + _sha256(ARTIFACT),
            artifact_digest=_sha256(ARTIFACT),
            config_digest="f" * 64,
            release_manifest_digest="r" * 64,
        ),
        artifact_bytes=ARTIFACT,
        secret_store=secrets,
        required_secret_names=("ORION_DB_PASSWORD",),
    )


# --- the two whole-system assertions ---------------------------------------


def test_unwired_context_cannot_check_everything_and_reports_nothing_ok() -> None:
    """The non-negotiable rule, tested over the whole probe set at once."""

    results = [probe(ProbeContext()) for probe in PROBE_FUNCTIONS.values()]
    assert len(results) == len(PROBE_FUNCTIONS)
    assert all(r.status is ProbeStatus.CANNOT_CHECK for r in results), [
        (r.subsystem, r.status.value, r.detail) for r in results if r.status is not ProbeStatus.CANNOT_CHECK
    ]
    assert not any(r.status is ProbeStatus.OK for r in results)
    assert worst_status(results) is ProbeStatus.CANNOT_CHECK


def test_healthy_system_raises_no_alarm(healthy: ProbeContext) -> None:
    """The no-alarm case: a checker that cries wolf on a healthy system gets switched off."""

    results = build_doctor(healthy).run()
    assert len(results) == len(PROBE_FUNCTIONS)
    assert all(r.status is ProbeStatus.OK for r in results), [
        (r.subsystem, r.status.value, r.detail) for r in results if r.status is not ProbeStatus.OK
    ]
    assert worst_status(results) is ProbeStatus.OK
    assert "overall=OK" in render_report(results)


# --- database ---------------------------------------------------------------


def test_database_probe_ok_on_live_store(healthy: ProbeContext) -> None:
    result = probe_database(healthy)
    assert result.status is ProbeStatus.OK
    assert "integrity_check=ok" in result.detail


def test_missing_database_is_cannot_check_and_creates_no_file(tmp_path) -> None:
    path = tmp_path / "absent.sqlite3"
    result = probe_database(ProbeContext(database_path=path))
    assert result.status is ProbeStatus.CANNOT_CHECK
    assert not path.exists(), "a diagnostic must not create the database it failed to find"


def test_the_trap_this_probe_avoids_naive_connect_would_report_ok(tmp_path) -> None:
    """Documented hazard: sqlite3.connect() creates the file and then passes integrity_check."""

    path = tmp_path / "would_be_created.sqlite3"
    db = sqlite3.connect(path)
    try:
        assert path.exists()
        assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    finally:
        db.close()
    # the real probe refuses that path
    assert probe_database(ProbeContext(database_path=tmp_path / "still_absent.sqlite3")).status is ProbeStatus.CANNOT_CHECK


def test_non_database_file_is_fail_not_cannot_check(tmp_path) -> None:
    path = tmp_path / "garbage.sqlite3"
    path.write_bytes(b"not a database" * 64)
    result = probe_database(ProbeContext(database_path=path))
    assert result.status is ProbeStatus.FAIL
    assert "not a database" in result.detail


def test_corrupted_database_pages_are_fail(tmp_path) -> None:
    """A real store with real rows, then flipped bytes on a non-header page."""

    store = SqliteAtlasPlaneStore(tmp_path / "atlas.sqlite3")
    batch = AtlasPlaneBatch(
        sequence=0,
        base_atlas_revision="base",
        batch_id="batch:1",
        charts=tuple(AtlasChartRecord(f"chart:{i}", "layer", ("x", "y")) for i in range(20)),
    )
    store.commit_batch(
        batch, committed_snapshot_id="snapshot:0", expected_atlas_revision=atlas_revision_for(0, batch)
    )
    db_path = Path(store.path)
    assert probe_database(ProbeContext(database_path=db_path)).status is ProbeStatus.OK
    raw = bytearray(db_path.read_bytes())
    assert len(raw) > 8192, "fixture must be large enough to corrupt a non-header page"
    for offset in range(4096, 8192):
        raw[offset] ^= 0xFF
    db_path.write_bytes(bytes(raw))
    result = probe_database(ProbeContext(database_path=db_path))
    assert result.status is ProbeStatus.FAIL


def test_database_missing_declared_table_is_fail(healthy: ProbeContext, tmp_path) -> None:
    ctx = ProbeContext(
        database_path=healthy.database_path,
        database_expected_tables=("semantic_atoms", "table_that_was_never_migrated"),
    )
    result = probe_database(ctx)
    assert result.status is ProbeStatus.FAIL
    assert "table_that_was_never_migrated" in result.detail


def test_unreadable_database_path_is_cannot_check(tmp_path) -> None:
    assert probe_database(ProbeContext(database_path=tmp_path)).status is ProbeStatus.CANNOT_CHECK


# --- object store -----------------------------------------------------------


def test_object_store_ok_when_declared_objects_verify(healthy: ProbeContext) -> None:
    assert probe_object_store(healthy).status is ProbeStatus.OK


def test_object_store_corruption_is_fail(healthy: ProbeContext) -> None:
    store = CanonicalPayloadStore(healthy.object_store_root)
    digest = healthy.expected_object_digests[0]
    store.path_for(digest).write_bytes(b"rebound content")
    result = probe_object_store(healthy)
    assert result.status is ProbeStatus.FAIL
    assert "corrupt" in result.detail


def test_object_store_missing_declared_object_is_fail(healthy: ProbeContext) -> None:
    ctx = ProbeContext(
        object_store_root=healthy.object_store_root,
        expected_object_digests=(_sha256(b"never stored"),),
    )
    result = probe_object_store(ctx)
    assert result.status is ProbeStatus.FAIL
    assert "missing" in result.detail


def test_object_store_without_declared_digests_is_cannot_check(healthy: ProbeContext) -> None:
    ctx = ProbeContext(object_store_root=healthy.object_store_root)
    assert probe_object_store(ctx).status is ProbeStatus.CANNOT_CHECK


def test_absent_object_store_root_is_cannot_check(tmp_path) -> None:
    ctx = ProbeContext(object_store_root=tmp_path / "nope", expected_object_digests=("0" * 64,))
    assert probe_object_store(ctx).status is ProbeStatus.CANNOT_CHECK


# --- index ------------------------------------------------------------------


def test_index_ok_when_current(healthy: ProbeContext) -> None:
    assert probe_index(healthy).status is ProbeStatus.OK


def test_index_lag_is_degraded_not_ok_and_not_fail(healthy: ProbeContext) -> None:
    store = healthy.semantic_store
    store.add_atom_version(_atom("later", 1), valid_from_snapshot_id="snapshot:1")
    ctx = ProbeContext(
        semantic_store=store, semantic_index=healthy.semantic_index, semantic_sequence=1
    )
    result = probe_index(ctx)
    assert result.status is ProbeStatus.DEGRADED
    assert "index lag" in result.detail


def test_never_built_index_is_cannot_check(healthy: ProbeContext) -> None:
    empty = RebuildableSemanticIndex()
    ctx = ProbeContext(semantic_store=healthy.semantic_store, semantic_index=empty)
    result = probe_index(ctx)
    assert result.status is ProbeStatus.CANNOT_CHECK
    assert "never been built" in result.detail


def test_index_probe_with_unreadable_store_is_cannot_check(healthy: ProbeContext) -> None:
    class Broken:
        def semantic_revision(self, sequence: int) -> str:
            raise sqlite3.OperationalError("database is locked")

    ctx = ProbeContext(semantic_store=Broken(), semantic_index=healthy.semantic_index)
    assert probe_index(ctx).status is ProbeStatus.CANNOT_CHECK


# --- workflow workers -------------------------------------------------------


def test_workflow_ok_with_a_live_lease(healthy: ProbeContext) -> None:
    result = probe_workflow_workers(healthy)
    assert result.status is ProbeStatus.OK
    assert "1 live leases" in result.detail


def test_expired_lease_is_degraded(healthy: ProbeContext) -> None:
    ctx = ProbeContext(now=NOW + 3600, workflow_db_path=healthy.workflow_db_path)
    result = probe_workflow_workers(ctx)
    assert result.status is ProbeStatus.DEGRADED
    assert "expired and reclaimable" in result.detail


def test_recovery_required_activity_is_fail(tmp_path) -> None:
    engine, lease = _workflow(tmp_path, external_effect=True)
    engine.mark_effect_started(lease)
    # worker-a dies; worker-b finds an ambiguous external effect
    claim = engine.claim("wf:1", "act:1", worker_id="worker-b", now=NOW + 3600, ttl=30)
    assert claim.verdict is ClaimVerdict.RECOVERY_REQUIRED
    result = probe_workflow_workers(ProbeContext(now=NOW + 3600, workflow_db_path=Path(engine.path)))
    assert result.status is ProbeStatus.FAIL
    assert "RECOVERY_REQUIRED" in result.detail


def test_recovery_required_outranks_a_stuck_lease(tmp_path) -> None:
    engine, lease = _workflow(tmp_path, external_effect=True)
    engine.mark_effect_started(lease)
    engine.claim("wf:1", "act:1", worker_id="worker-b", now=NOW + 3600, ttl=30)
    assert probe_workflow_workers(ProbeContext(now=NOW + 9999, workflow_db_path=Path(engine.path))).status is ProbeStatus.FAIL


def test_workflow_without_a_clock_is_cannot_check(healthy: ProbeContext) -> None:
    result = probe_workflow_workers(ProbeContext(workflow_db_path=healthy.workflow_db_path))
    assert result.status is ProbeStatus.CANNOT_CHECK
    assert "injected clock" in result.detail


def test_wrong_database_is_not_a_workflow_database(healthy: ProbeContext) -> None:
    result = probe_workflow_workers(ProbeContext(now=NOW, workflow_db_path=healthy.database_path))
    assert result.status is ProbeStatus.CANNOT_CHECK
    assert "not a worker workflow database" in result.detail


def test_missing_workflow_database_creates_no_file(tmp_path) -> None:
    path = tmp_path / "absent-workflow.sqlite3"
    assert probe_workflow_workers(ProbeContext(now=NOW, workflow_db_path=path)).status is ProbeStatus.CANNOT_CHECK
    assert not path.exists()


# --- stored status ----------------------------------------------------------


def test_status_freshness_ok_on_fresh_record(healthy: ProbeContext) -> None:
    assert probe_status_freshness(healthy).status is ProbeStatus.OK


def test_stale_stored_freshness_is_degraded() -> None:
    result = probe_status_freshness(ProbeContext(stored_status={"freshness": "STALE", "status_id": "s9"}))
    assert result.status is ProbeStatus.DEGRADED
    assert "STALE" in result.detail


def test_failing_stored_hard_gate_is_fail() -> None:
    result = probe_status_freshness(
        ProbeContext(stored_status={"freshness": "FRESH", "hard_gates": {"evidence_sufficiency": "FAIL"}})
    )
    assert result.status is ProbeStatus.FAIL
    assert "evidence_sufficiency" in result.detail


def test_absent_freshness_is_cannot_check_not_ok() -> None:
    result = probe_status_freshness(ProbeContext(stored_status={"project_id": "orion"}))
    assert result.status is ProbeStatus.CANNOT_CHECK


def test_uninterpretable_gate_verdict_is_cannot_check() -> None:
    result = probe_status_freshness(
        ProbeContext(stored_status={"freshness": "FRESH", "hard_gates": {"g": "MAYBE"}})
    )
    assert result.status is ProbeStatus.CANNOT_CHECK


# --- backup -----------------------------------------------------------------


def test_backup_ok_when_recent_and_restorable(healthy: ProbeContext) -> None:
    result = probe_backup(healthy)
    assert result.status is ProbeStatus.OK
    assert "restore verified EXACT" in result.detail


def test_stale_backup_is_degraded(healthy: ProbeContext) -> None:
    ctx = ProbeContext(
        now=NOW + 10 * 86_400,
        backup_manifest=healthy.backup_manifest,
        backup_restore_root=healthy.backup_restore_root,
        backup_max_age_seconds=3600,
    )
    result = probe_backup(ctx)
    assert result.status is ProbeStatus.DEGRADED
    assert "budget 3600s" in result.detail


def test_corrupted_restore_is_fail(healthy: ProbeContext) -> None:
    (healthy.backup_restore_root / "y.bin").write_bytes(b"\xff\xff\xff")
    result = probe_backup(healthy)
    assert result.status is ProbeStatus.FAIL
    assert "CORRUPTED_BLOB" in result.detail


def test_missing_restore_blob_is_fail(healthy: ProbeContext) -> None:
    (healthy.backup_restore_root / "y.bin").unlink()
    result = probe_backup(healthy)
    assert result.status is ProbeStatus.FAIL
    assert "MISSING_BLOB" in result.detail


def test_backup_that_names_no_files_is_fail(tmp_path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    manifest = take_backup(empty, backup_id="bk-empty", created_at=CREATED_AT)
    result = probe_backup(ProbeContext(now=NOW, backup_manifest=manifest))
    assert result.status is ProbeStatus.FAIL
    assert "names no files" in result.detail


def test_backup_without_a_clock_is_cannot_check(healthy: ProbeContext) -> None:
    ctx = ProbeContext(backup_manifest=healthy.backup_manifest)
    result = probe_backup(ctx)
    assert result.status is ProbeStatus.CANNOT_CHECK
    assert "age not checkable" in result.detail


def test_backup_with_unparseable_timestamp_is_cannot_check(tmp_path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a").write_text("x")
    manifest = take_backup(src, backup_id="bk", created_at="last tuesday")
    result = probe_backup(ProbeContext(now=NOW, backup_manifest=manifest))
    assert result.status is ProbeStatus.CANNOT_CHECK


def test_absent_restore_root_is_cannot_check(healthy: ProbeContext, tmp_path) -> None:
    ctx = ProbeContext(
        now=NOW, backup_manifest=healthy.backup_manifest, backup_restore_root=tmp_path / "gone"
    )
    assert probe_backup(ctx).status is ProbeStatus.CANNOT_CHECK


# --- migration --------------------------------------------------------------


def test_migration_parity_match_is_ok(healthy: ProbeContext) -> None:
    assert probe_migration(healthy).status is ProbeStatus.OK


def test_migration_parity_mismatch_is_fail() -> None:
    result = probe_migration(ProbeContext(migration_source={"a": 1}, migration_target={"a": 2}))
    assert result.status is ProbeStatus.FAIL
    assert "MISMATCH" in result.detail


def test_uncanonicalizable_migration_projection_is_cannot_check() -> None:
    result = probe_migration(ProbeContext(migration_source={"a": object()}, migration_target={"a": 1}))
    assert result.status is ProbeStatus.CANNOT_CHECK


def test_half_supplied_migration_is_cannot_check() -> None:
    assert probe_migration(ProbeContext(migration_source={"a": 1})).status is ProbeStatus.CANNOT_CHECK


# --- provenance -------------------------------------------------------------


def test_provenance_verified_is_ok(healthy: ProbeContext) -> None:
    assert probe_provenance(healthy).status is ProbeStatus.OK


def test_provenance_artifact_mismatch_is_fail(healthy: ProbeContext) -> None:
    ctx = ProbeContext(provenance=healthy.provenance, artifact_bytes=b"different bytes")
    result = probe_provenance(ctx)
    assert result.status is ProbeStatus.FAIL
    assert "ARTIFACT_MISMATCH" in result.detail


def test_provenance_mutable_tag_is_fail() -> None:
    provenance = BuildProvenance(
        source_commit="c" * 40,
        lock_digest="l" * 64,
        build_procedure_digest="b" * 64,
        artifact_ref="registry.example/orion:latest",
        artifact_digest=_sha256(ARTIFACT),
        config_digest="f" * 64,
        release_manifest_digest="r" * 64,
    )
    result = probe_provenance(ProbeContext(provenance=provenance, artifact_bytes=ARTIFACT))
    assert result.status is ProbeStatus.FAIL
    assert "MUTABLE_TAG_WITHOUT_DIGEST" in result.detail


def test_provenance_without_artifact_bytes_is_cannot_check(healthy: ProbeContext) -> None:
    result = probe_provenance(ProbeContext(provenance=healthy.provenance))
    assert result.status is ProbeStatus.CANNOT_CHECK
    assert "cannot verify itself" in result.detail


# --- secrets ----------------------------------------------------------------


def test_secrets_ok_when_declared_names_resolve(healthy: ProbeContext) -> None:
    assert probe_secrets(healthy).status is ProbeStatus.OK


def test_unresolvable_secret_is_fail(healthy: ProbeContext) -> None:
    ctx = ProbeContext(
        secret_store=healthy.secret_store,
        required_secret_names=("ORION_DB_PASSWORD", "ORION_OIDC_CLIENT_SECRET"),
    )
    result = probe_secrets(ctx)
    assert result.status is ProbeStatus.FAIL
    assert "ORION_OIDC_CLIENT_SECRET" in result.detail


def test_no_declared_secrets_is_cannot_check(healthy: ProbeContext) -> None:
    assert probe_secrets(ProbeContext(secret_store=healthy.secret_store)).status is ProbeStatus.CANNOT_CHECK


def test_secret_values_never_reach_the_rendered_report(healthy: ProbeContext) -> None:
    results = build_doctor(healthy).run()
    rendered = render_report(results)
    assert "s3cr3t-value-that-must-never-render" not in rendered
    assert "secret://ORION_DB_PASSWORD@v1" in rendered


# --- triage -----------------------------------------------------------------


def test_a_real_fail_is_never_masked_by_an_unavailable_probe() -> None:
    results = (
        ProbeResult("database", ProbeStatus.FAIL, "malformed"),
        ProbeResult("secrets", ProbeStatus.CANNOT_CHECK, "no store"),
        ProbeResult("index", ProbeStatus.DEGRADED, "lag"),
    )
    assert worst_status(results) is ProbeStatus.FAIL
    assert render_report(results).splitlines()[0].startswith("ORION DOCTOR  overall=FAIL")


def test_a_doctor_that_ran_nothing_is_cannot_check_not_ok() -> None:
    assert worst_status(()) is ProbeStatus.CANNOT_CHECK


def test_probe_that_raises_is_cannot_check_via_the_harness(healthy: ProbeContext) -> None:
    doctor = build_doctor(healthy)
    doctor.register("exploding", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    results = doctor.run()
    exploded = [r for r in results if r.status is ProbeStatus.CANNOT_CHECK]
    assert exploded and "boom" in exploded[0].detail
    assert worst_status(results) is ProbeStatus.CANNOT_CHECK


# --- observed behaviour of engineering_ops.OperatorDoctor.render ------------
# Pinned, not fixed: engineering_ops.py is not this fibre's patch surface.


def test_render_reports_cannot_check_for_a_doctor_with_no_probes() -> None:
    """A doctor that ran no probes checked nothing, and nothing checked is CANNOT_CHECK.

    This used to render overall=OK -- a registration step that silently did
    nothing rendered healthy. OperatorDoctor.overall is now the one canonical
    rollup and worst_status delegates to it, so both agree.
    """

    rendered = OperatorDoctor.render(OperatorDoctor().run())
    assert "overall=CANNOT_CHECK" in rendered
    assert "probes=0" in rendered
    assert worst_status(OperatorDoctor().run()) is ProbeStatus.CANNOT_CHECK


def test_render_never_lets_cannot_check_mask_a_fail() -> None:
    """A confirmed FAIL is never softened by an unrelated probe being unavailable.

    render used to rank by enum declaration order, where CANNOT_CHECK came after
    FAIL, so one FAIL beside one CANNOT_CHECK rendered overall=CANNOT_CHECK and
    hid the failure. Severity is now an explicit total order:
    OK < DEGRADED < CANNOT_CHECK < FAIL.
    """

    results = (
        ProbeResult("database", ProbeStatus.FAIL, "malformed"),
        ProbeResult("secrets", ProbeStatus.CANNOT_CHECK, "no store"),
    )
    assert "overall=FAIL" in OperatorDoctor.render(results)
    assert worst_status(results) is ProbeStatus.FAIL
    assert OperatorDoctor.overall(results) is worst_status(results)
