from __future__ import annotations

from pathlib import Path

from rakl.ledger_compiler import compile_meta_fiber_ledger


def test_compiler_records_literal_occurrences_without_auto_reconciliation(tmp_path):
    research = tmp_path / "research"
    research.mkdir()
    (research / "a.json").write_text(
        '{"fiber":"META_N123_ALPHA","other":"META_N123_BETA"}\n',
        encoding="utf-8",
    )
    ledger = compile_meta_fiber_ledger(tmp_path, include_roots=("research",))
    assert ledger.fiber_ids == ("META_N123_ALPHA", "META_N123_BETA")
    assert ledger.namespace_collisions == ((123, ("META_N123_ALPHA", "META_N123_BETA")),)
    assert ledger.grants_identity_reconciliation is False
    assert ledger.grants_scientific_authority is False


def test_compiler_hashes_source_and_lineage(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "x.md").write_text("one\nMETA_N124_GAMMA\n", encoding="utf-8")
    ledger = compile_meta_fiber_ledger(tmp_path, include_roots=("docs",))
    occurrence = ledger.occurrences[0]
    assert occurrence.source_path == "docs/x.md"
    assert occurrence.line_number == 2
    assert len(occurrence.source_sha256) == 64
    assert len(occurrence.line_sha256) == 64


def test_current_repository_full_ledger_is_compilable():
    root = Path(__file__).resolve().parents[1]
    ledger = compile_meta_fiber_ledger(root)
    assert "META_N122_CHALLENGE_LEARNING_CONTROL" in ledger.fiber_ids
    assert "META_N106_HELD_OUT_MISSING_OPERATOR_DISCOVERY" in ledger.fiber_ids
    assert len(ledger.source_files) > 10
