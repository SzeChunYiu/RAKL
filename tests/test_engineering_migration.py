import pytest

from rakl.engineering_migration import (
    ParityVerdict,
    build_import_receipt,
    compare_migration_parity,
)


def test_migration_parity_matches_canonical_content_not_object_identity():
    left = {"b": 2, "a": [1, 2]}
    right = {"a": [1, 2], "b": 2}
    report = compare_migration_parity(left, right)
    assert report.verdict is ParityVerdict.MATCH


def test_import_receipt_requires_parity_and_is_content_identified():
    report = compare_migration_parity({"x": 1}, {"x": 1})
    receipt = build_import_receipt(
        import_id="import:legacy-episodes",
        project_id="project:demo",
        source_store_kind="EPISODE_JSONL_V1",
        source_store_identity="file:/legacy/episodes.jsonl",
        source_head_hash="head:abc",
        target_backend_identity="postgres:cluster:v1",
        imported_object_ids=("episode:1", "episode:2"),
        parity_report=report,
        created_at_utc="2026-08-15T15:00:00+00:00",
    )
    assert receipt.receipt_id.startswith("import-receipt:")
    with pytest.raises(ValueError, match="MATCH parity"):
        build_import_receipt(
            import_id="bad",
            project_id="p",
            source_store_kind="X",
            source_store_identity="Y",
            source_head_hash="Z",
            target_backend_identity="T",
            imported_object_ids=("1",),
            parity_report=compare_migration_parity({"x": 1}, {"x": 2}),
            created_at_utc="2026-08-15T15:00:00+00:00",
        )
