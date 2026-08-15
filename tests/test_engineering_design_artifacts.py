from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_postgres_draft_scopes_semantic_and_atlas_foreign_keys_by_project():
    sql = (ROOT / "research/orion_engineering_closure_v1/POSTGRES_SCHEMA_DRAFT.sql").read_text("utf-8")
    required = (
        "PRIMARY KEY(project_id, fiber_id)",
        "FOREIGN KEY(project_id, parent_fiber_id)",
        "PRIMARY KEY(project_id, atom_id)",
        "FOREIGN KEY(project_id, fiber_id)",
        "PRIMARY KEY(project_id, witness_id)",
        "FOREIGN KEY(project_id, left_atom_id)",
        "FOREIGN KEY(project_id, right_atom_id)",
        "CREATE TABLE atlas_chart (",
        "PRIMARY KEY(project_id, chart_id)",
        "CREATE TABLE atlas_transition (",
        "FOREIGN KEY(project_id, source_chart_id)",
        "FOREIGN KEY(project_id, target_chart_id)",
        "CREATE TABLE atlas_obstruction_version (",
    )
    for text in required:
        assert text in sql


def test_postgres_draft_keeps_idempotency_and_status_coordinates_nonambiguous():
    sql = (ROOT / "research/orion_engineering_closure_v1/POSTGRES_SCHEMA_DRAFT.sql").read_text("utf-8")
    assert "UNIQUE(project_id, idempotency_key)" in sql
    assert "action_payload_hash char(64)" in sql
    assert "UNIQUE(project_snapshot_id, target_id, fiber_id)" in sql
    assert "SERIALIZABLE" in sql and "40001" in sql
