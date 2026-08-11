from __future__ import annotations

from rakl.research_memory import (
    MemoryQueryStatus,
    ResearchMemoryReview,
    ResearchMemoryVerdict,
    audit_research_memory_review,
)


def _review(**overrides: object) -> ResearchMemoryReview:
    values: dict[str, object] = {
        "target_atom_id": "atom-C",
        "target_context_hash": "sha256:context",
        "tool_inventory_snapshot_hash": "sha256:tools",
        "failure_lattice_snapshot_hash": "sha256:failures",
        "tool_query_status": MemoryQueryStatus.MATCHES_FOUND,
        "failure_query_status": MemoryQueryStatus.MATCHES_FOUND,
        "candidate_method_families": ("spectral", "reuse-stable invariant"),
        "relevant_tool_ids": ("tool-1",),
        "relevant_failure_ids": ("failure-1",),
        "selected_tool_ids": ("tool-1",),
        "tool_applicability_notes": ("preconditions match but target validation is required",),
        "failure_reuse_notes": ("failure-1 is a transfer warning, not a global blacklist",),
        "unresolved_warnings": ("reuse-stability remains unverified",),
        "evidence_pointers": ("snapshot:tools", "snapshot:failures"),
        "artifact_hash": "sha256:memory",
    }
    values.update(overrides)
    return ResearchMemoryReview(**values)  # type: ignore[arg-type]


def test_complete_dual_memory_review_passes() -> None:
    report = audit_research_memory_review(
        _review(), atom_id="atom-C", context_hash="sha256:context"
    )
    assert report.verdict is ResearchMemoryVerdict.PASS


def test_missing_review_fails_closed() -> None:
    report = audit_research_memory_review(
        None, atom_id="atom-C", context_hash="sha256:context"
    )
    assert report.verdict is ResearchMemoryVerdict.CANNOT_CHECK


def test_positive_match_status_requires_ids_and_applicability_review() -> None:
    report = audit_research_memory_review(
        _review(relevant_tool_ids=(), tool_applicability_notes=()),
        atom_id="atom-C",
        context_hash="sha256:context",
    )
    assert report.verdict is ResearchMemoryVerdict.FAIL
    assert "tool_matches_status_without_tool_ids" in report.reasons
    assert "tool_matches_not_assessed_for_applicability" in report.reasons


def test_failure_match_requires_reuse_scope_review() -> None:
    report = audit_research_memory_review(
        _review(relevant_failure_ids=(), failure_reuse_notes=()),
        atom_id="atom-C",
        context_hash="sha256:context",
    )
    assert report.verdict is ResearchMemoryVerdict.FAIL
    assert "failure_matches_status_without_failure_ids" in report.reasons
    assert "failure_matches_not_assessed_for_reuse_scope" in report.reasons


def test_empty_queries_are_allowed_only_when_explicit() -> None:
    report = audit_research_memory_review(
        _review(
            tool_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH,
            failure_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH,
            relevant_tool_ids=(),
            relevant_failure_ids=(),
            selected_tool_ids=(),
            tool_applicability_notes=(),
            failure_reuse_notes=(),
        ),
        atom_id="atom-C",
        context_hash="sha256:context",
    )
    assert report.verdict is ResearchMemoryVerdict.PASS


def test_bound_universe_no_match_requires_coverage_receipt_hash() -> None:
    """Cross-problem 'no match' without a coverage receipt fails closed (#119)."""

    report = audit_research_memory_review(
        _review(
            tool_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE,
            failure_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH,
            relevant_tool_ids=(),
            relevant_failure_ids=(),
            selected_tool_ids=(),
            tool_applicability_notes=(),
            failure_reuse_notes=(),
            cross_problem_coverage_receipt_hash="",
        ),
        atom_id="atom-C",
        context_hash="sha256:context",
    )
    assert report.verdict is ResearchMemoryVerdict.FAIL
    assert "cross_problem_no_match_without_coverage_receipt_hash" in report.reasons


def test_bound_universe_no_match_passes_with_coverage_receipt_hash() -> None:
    report = audit_research_memory_review(
        _review(
            tool_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE,
            failure_query_status=MemoryQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE,
            relevant_tool_ids=(),
            relevant_failure_ids=(),
            selected_tool_ids=(),
            tool_applicability_notes=(),
            failure_reuse_notes=(),
            cross_problem_coverage_receipt_hash="a" * 64,
        ),
        atom_id="atom-C",
        context_hash="sha256:context",
    )
    assert report.verdict is ResearchMemoryVerdict.PASS


def test_selected_tool_must_come_from_relevant_query() -> None:
    report = audit_research_memory_review(
        _review(selected_tool_ids=("tool-unseen",)),
        atom_id="atom-C",
        context_hash="sha256:context",
    )
    assert report.verdict is ResearchMemoryVerdict.FAIL
    assert "selected_tool_was_not_in_relevant_tool_query" in report.reasons
