"""H21: a populated database with a missing table is refused on open, never silently repaired.

Both directions for every store that shares the CREATE-IF-NOT-EXISTS idiom:
  * populated + table dropped -> SchemaIntegrityError naming the table; nothing recreated; nothing served
  * fresh open -> fine; normal reopen -> fine; pre-guard database (all tables, no registry) -> upgraded, fine
"""

from __future__ import annotations

import sqlite3

import pytest

from rakl.engineering_atlas_store import SqliteAtlasPlaneStore
from rakl.engineering_control_store import SqliteControlProjectionStore
from rakl.engineering_evidence_store import SqliteEvidenceMetadataStore
from rakl.engineering_schema_guard import REGISTRY_TABLE, SchemaIntegrityError, guard_and_initialize_schema
from rakl.engineering_semantic_store import SqliteSemanticStateStore
from rakl.engineering_state import ProjectSnapshot
from rakl.engineering_store import SqliteEngineeringStateStore
from rakl.engineering_workflow import SqliteReferenceWorkflowEngine
from rakl.engineering_workflow_workers import SqliteWorkerWorkflowEngine

T0 = "2026-08-15T15:00:00+00:00"

STORES = [
    (SqliteEngineeringStateStore, "engineering_state_store", "transitions"),
    (SqliteSemanticStateStore, "engineering_semantic_store", "semantic_atom_versions"),
    (SqliteEvidenceMetadataStore, "engineering_evidence_store", "engineering_evidence_batch_commits"),
    (SqliteControlProjectionStore, "engineering_control_store", "control_projection"),
    (SqliteReferenceWorkflowEngine, "engineering_workflow_engine", "workflow_events"),
    (SqliteAtlasPlaneStore, "engineering_atlas_store", "atlas_transitions"),
    (SqliteWorkerWorkflowEngine, "engineering_worker_engine", "leases"),
]


def _tables(path) -> set[str]:
    with sqlite3.connect(path) as db:
        return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _snapshot() -> ProjectSnapshot:
    return ProjectSnapshot(
        project_id="p", sequence=0, previous_snapshot_id=None, evidence_cutoff="e0",
        semantic_state_revision="s0", metric_ledger_head="m0", episode_store_head="ep0",
        saturation_basis_ids=("b0",), authority_projection_revision="a0",
        controller_epoch_id="epoch0", created_at_utc=T0,
    )


@pytest.mark.parametrize("cls,component,table", STORES, ids=[c.__name__ for c, _, _ in STORES])
def test_dropped_table_is_refused_on_reopen_and_not_recreated(tmp_path, cls, component, table) -> None:
    path = tmp_path / "s.db"
    cls(path)
    assert table in _tables(path)
    with sqlite3.connect(path) as db:
        db.execute(f"DROP TABLE {table}")
    with pytest.raises(SchemaIntegrityError) as exc:
        cls(path)
    assert exc.value.component == component
    assert table in exc.value.missing_tables
    assert table in str(exc.value)
    assert table not in _tables(path), "the guard must not CREATE over a populated database"


@pytest.mark.parametrize("cls,component,table", STORES, ids=[c.__name__ for c, _, _ in STORES])
def test_fresh_open_and_normal_reopen_are_fine(tmp_path, cls, component, table) -> None:
    path = tmp_path / "s.db"
    cls(path)
    cls(path)          # normal reopen
    with sqlite3.connect(path) as db:
        rows = db.execute(f"SELECT component, schema_version FROM {REGISTRY_TABLE}").fetchall()
    assert any(r[0] == component for r in rows)


def test_state_store_head_is_not_served_over_a_dropped_ledger(tmp_path) -> None:
    path = tmp_path / "s.db"
    st = SqliteEngineeringStateStore(path)
    st.initialize_project(_snapshot())
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE transitions")
    with pytest.raises(SchemaIntegrityError):
        SqliteEngineeringStateStore(path).head("p")


def test_pre_guard_database_is_upgraded_not_refused(tmp_path) -> None:
    """A database from before the guard existed has all tables and no registry row: accepted and registered."""
    path = tmp_path / "s.db"
    SqliteEngineeringStateStore(path).initialize_project(_snapshot())
    with sqlite3.connect(path) as db:
        db.execute(f"DELETE FROM {REGISTRY_TABLE}")
    reopened = SqliteEngineeringStateStore(path)
    assert reopened.head("p").sequence == 0
    with sqlite3.connect(path) as db:
        assert db.execute(f"SELECT COUNT(*) FROM {REGISTRY_TABLE} WHERE component='engineering_state_store'").fetchone()[0] == 1


def test_schema_version_mismatch_is_refused(tmp_path) -> None:
    path = tmp_path / "s.db"
    SqliteEngineeringStateStore(path)
    with sqlite3.connect(path) as db:
        db.execute(f"UPDATE {REGISTRY_TABLE} SET schema_version='orion-engineering-state-store-v1' "
                   "WHERE component='engineering_state_store'")
    with pytest.raises(SchemaIntegrityError) as exc:
        SqliteEngineeringStateStore(path)
    assert exc.value.stored_version == "orion-engineering-state-store-v1"


def test_shared_file_components_are_guarded_independently(tmp_path) -> None:
    """The atomic coordinator opens three stores on ONE file; dropping a semantic table must not
    be reported as a state-store fault, and the state store must still open."""
    from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator

    path = tmp_path / "u.db"
    SqliteAtomicEngineeringCoordinator(path)
    with sqlite3.connect(path) as db:
        db.execute("DROP TABLE semantic_witnesses")
    SqliteEngineeringStateStore(path)             # unaffected component opens
    with pytest.raises(SchemaIntegrityError) as exc:
        SqliteSemanticStateStore(path)
    assert exc.value.component == "engineering_semantic_store"
    assert exc.value.missing_tables == ("semantic_witnesses",)


def test_guard_primitive_partial_unregistered_is_refused() -> None:
    """The primitive itself: some tables present, none registered -> partial -> refused."""
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE a(x)")
    with pytest.raises(SchemaIntegrityError) as exc:
        guard_and_initialize_schema(db, component="c", schema_version="v1", tables=("a", "b"),
                                    create_script="CREATE TABLE IF NOT EXISTS a(x); CREATE TABLE IF NOT EXISTS b(y);")
    assert exc.value.missing_tables == ("b",)
    assert {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")} >= {"a"}
    assert "b" not in {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def test_guard_primitive_fresh_then_verified() -> None:
    db = sqlite3.connect(":memory:")
    script = "CREATE TABLE IF NOT EXISTS a(x); CREATE TABLE IF NOT EXISTS b(y);"
    assert guard_and_initialize_schema(db, component="c", schema_version="v1", tables=("a", "b"), create_script=script) == "CREATED"
    assert guard_and_initialize_schema(db, component="c", schema_version="v1", tables=("a", "b"), create_script=script) == "VERIFIED"
