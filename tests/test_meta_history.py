from __future__ import annotations

import json
from pathlib import Path

from rakl.meta_history import (
    HistoricalIssueKind,
    HistoricalLedgerVerdict,
    compile_meta_fiber_history,
    discover_meta_ledger_paths,
    git_blob_sha,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    research = root / "research"
    research.mkdir(parents=True)
    return root, research


def _definition(fiber_id: str, question: str = "q") -> dict[str, str]:
    return {"fiber_id": fiber_id, "status": "OPEN", "question": question}


def test_discovery_is_pattern_based_and_includes_new_delta(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    _write_json(research / "META_FIBER_BACKLOG.json", {"fibers": [_definition("META_N001_ALPHA")]})
    _write_json(research / "META_FIBER_BACKLOG_999_DELTA.json", {"new_fibers": [_definition("META_N999_OMEGA")]})
    names = {path.name for path in discover_meta_ledger_paths(research)}
    assert names == {"META_FIBER_BACKLOG.json", "META_FIBER_BACKLOG_999_DELTA.json"}


def test_source_scoped_reallocation_preserves_older_canonical_identity(tmp_path: Path) -> None:
    root, research = _repo(tmp_path)
    base = research / "META_FIBER_BACKLOG_033_DELTA.json"
    _write_json(base, {"round": 33, "fibers": [_definition("META_N101_OLD_CONCEPT", "old question")]})
    source = research / "SELF_RAKL_RESEARCH_034.md"
    source.write_text("## New fibers\n- `META_N101_NEW_CONCEPT`\n", encoding="utf-8")
    reconciliation = research / "META_FIBER_REGISTRY_RECONCILIATION_035B.json"
    _write_json(
        reconciliation,
        {
            "sources": [
                {"path": "research/META_FIBER_BACKLOG_033_DELTA.json", "blob_sha": git_blob_sha(base.read_bytes())},
                {"path": "research/SELF_RAKL_RESEARCH_034.md", "blob_sha": git_blob_sha(source.read_bytes())},
            ],
            "explicit_aliases": [
                {"historical_id": "META_N101_NEW_CONCEPT", "canonical_id": "META_N108_NEW_CONCEPT"}
            ],
        },
    )
    _write_json(
        research / "META_FIBER_BACKLOG_035B_RECONCILIATION_DELTA.json",
        {
            "canonical_round034_fibers": [
                {"fiber_id": "META_N108_NEW_CONCEPT", "historical_id": "META_N101_NEW_CONCEPT", "state": "OPEN"}
            ]
        },
    )

    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    ids = {item.fiber_id for item in report.canonical_fibers}
    assert "META_N101_OLD_CONCEPT" in ids
    assert "META_N108_NEW_CONCEPT" in ids
    assert "META_N101_NEW_CONCEPT" not in ids
    collision_issues = [issue for issue in report.issues if issue.kind == HistoricalIssueKind.NAMESPACE_SLOT_COLLISION]
    assert collision_issues
    assert all(issue.resolved for issue in collision_issues)
    assert not report.unresolved_issues


def test_reallocation_does_not_globalize_same_raw_identifier(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    source = research / "SELF_RAKL_RESEARCH_034.md"
    source.write_text("## New fibers\n- `META_N101_NEW_CONCEPT`\n", encoding="utf-8")
    _write_json(research / "META_FIBER_BACKLOG_033_DELTA.json", {"fibers": [_definition("META_N101_OLD_CONCEPT")]})
    _write_json(
        research / "META_FIBER_REGISTRY_RECONCILIATION_035B.json",
        {
            "sources": [{"path": "research/SELF_RAKL_RESEARCH_034.md", "blob_sha": git_blob_sha(source.read_bytes())}],
            "explicit_aliases": [{"historical_id": "META_N101_NEW_CONCEPT", "canonical_id": "META_N108_NEW_CONCEPT"}],
        },
    )
    _write_json(research / "META_FIBER_BACKLOG_035B_RECONCILIATION_DELTA.json", {"new_fibers": [_definition("META_N108_NEW_CONCEPT")]})
    _write_json(research / "META_FIBER_BACKLOG_036_DELTA.json", {"new_fibers": [_definition("META_N101_NEW_CONCEPT", "unscoped reuse")]})

    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CONFLICTED
    assert any(
        issue.kind in {HistoricalIssueKind.NAMESPACE_SLOT_COLLISION, HistoricalIssueKind.CANONICAL_SLOT_COLLISION}
        and not issue.resolved
        for issue in report.issues
    )


def test_orphan_requires_explicit_nonretroactive_disposition(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    _write_json(research / "META_FIBER_BACKLOG.json", {"priority": ["META_N041_ORPHAN"]})
    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CONFLICTED
    assert any(issue.kind == HistoricalIssueKind.ORPHAN_REFERENCE and not issue.resolved for issue in report.issues)

    _write_json(
        research / "META_FIBER_REGISTRY_RECONCILIATION_023.json",
        {
            "target_reference": "META_N041_ORPHAN",
            "disposition": "HISTORICAL_ORPHAN_REFERENCE_CLOSED_AS_SEMANTICALLY_SUBSUMED",
            "retroactive_definition_created": False,
        },
    )
    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    assert "META_N041_ORPHAN" not in {item.fiber_id for item in report.canonical_fibers}
    orphan = [issue for issue in report.issues if issue.kind == HistoricalIssueKind.ORPHAN_REFERENCE]
    assert orphan and all(issue.resolved for issue in orphan)


def test_reconciliation_source_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    source = research / "SELF_RAKL_RESEARCH_034.md"
    source.write_text("## New fibers\n- `META_N101_NEW_CONCEPT`\n", encoding="utf-8")
    _write_json(
        research / "META_FIBER_REGISTRY_RECONCILIATION_035B.json",
        {
            "sources": [{"path": "research/SELF_RAKL_RESEARCH_034.md", "blob_sha": "0" * 40}],
            "explicit_aliases": [{"historical_id": "META_N101_NEW_CONCEPT", "canonical_id": "META_N108_NEW_CONCEPT"}],
        },
    )
    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CANNOT_CHECK
    assert any(issue.kind == HistoricalIssueKind.SOURCE_BLOB_MISMATCH for issue in report.unresolved_issues)


def test_malformed_json_fails_closed(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    (research / "META_FIBER_BACKLOG_001_DELTA.json").write_text("{not-json", encoding="utf-8")
    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CANNOT_CHECK
    assert any(issue.kind == HistoricalIssueKind.INVALID_JSON for issue in report.unresolved_issues)


def test_unclassified_fiber_record_fails_closed(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    _write_json(research / "META_FIBER_BACKLOG_001_DELTA.json", {"mystery": [{"fiber_id": "META_N001_ALPHA"}]})
    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CANNOT_CHECK
    assert any(issue.kind == HistoricalIssueKind.UNCLASSIFIED_FIBER_RECORD for issue in report.unresolved_issues)


def test_semantically_similar_ids_are_not_merged(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    _write_json(
        research / "META_FIBER_BACKLOG.json",
        {
            "fibers": [
                _definition("META_N001_CAUSAL_TRANSFER", "same mechanism transfer"),
                _definition("META_N002_MECHANISM_TRANSFER", "same mechanism transfer"),
            ]
        },
    )
    report = compile_meta_fiber_history(research)
    assert report.verdict == HistoricalLedgerVerdict.CONSISTENT
    assert {item.fiber_id for item in report.canonical_fibers} == {
        "META_N001_CAUSAL_TRANSFER",
        "META_N002_MECHANISM_TRANSFER",
    }


def test_compilation_is_deterministic(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    _write_json(research / "META_FIBER_BACKLOG_002_DELTA.json", {"new_fibers": [_definition("META_N002_BETA")]})
    _write_json(research / "META_FIBER_BACKLOG.json", {"fibers": [_definition("META_N001_ALPHA")]})
    first = compile_meta_fiber_history(research)
    second = compile_meta_fiber_history(research)
    assert first.ledger_digest == second.ledger_digest
    assert first.events == second.events


def test_report_cannot_mint_any_authority(tmp_path: Path) -> None:
    _, research = _repo(tmp_path)
    _write_json(research / "META_FIBER_BACKLOG.json", {"fibers": [_definition("META_N001_ALPHA")]})
    report = compile_meta_fiber_history(research)
    assert report.can_support_registry_bookkeeping()
    assert not report.can_grant_scientific_authority()
    assert not report.can_grant_method_authority()
    assert not report.can_grant_target_authority()
    assert not report.can_grant_independent_review_credit()
    assert not report.can_grant_framework_saturation()


def test_live_repository_history_compiles_without_unresolved_identity_failure() -> None:
    research = Path(__file__).resolve().parents[1] / "research"
    report = compile_meta_fiber_history(research)
    assert len(report.covered_artifact_paths) >= 40
    assert report.verdict == HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY, (
        report.verdict,
        [(issue.kind.value, issue.source_path, issue.fiber_id, issue.message) for issue in report.unresolved_issues],
    )
    assert not report.unresolved_issues
    canonical = {item.fiber_id for item in report.canonical_fibers}
    assert "META_N101_METACOGNITIVE_METHOD_COMPLETENESS" in canonical
    assert "META_N106_HELD_OUT_MISSING_OPERATOR_DISCOVERY" in canonical
    assert "META_N108_COMPRESSION_RECONSTRUCTION_UNDERSTANDING" in canonical
    assert "META_N113_SOCIAL_EPISTEMIC_ROUTING" in canonical
    assert "META_N041_ANALOGY_PORTFOLIO_DIVERSITY" not in canonical
    resolved_kinds = {issue.kind for issue in report.issues if issue.resolved}
    assert HistoricalIssueKind.NAMESPACE_SLOT_COLLISION in resolved_kinds
    assert HistoricalIssueKind.ORPHAN_REFERENCE in resolved_kinds
