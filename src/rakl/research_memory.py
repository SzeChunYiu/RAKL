from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class MemoryQueryStatus(str, Enum):
    """Outcome of one dual-memory inventory query.

    ``NO_RELEVANT_MATCH`` remains valid for *local* tool/failure inventory search
    (the dual-memory pre-candidate gate).  It does **not** license a
    cross-problem completeness or counting claim.

    ``NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE`` is the only status that may back a
    cross-problem "no other domain / no relevant memory / second reuse" style
    statement, and it requires a bound ``cross_problem_coverage_receipt_hash``
    pointing at a :class:`~rakl.memory_coverage.CrossProblemCoverageReceipt`.
    A narrative unbounded "no match" is deliberately not representable here.
    """

    MATCHES_FOUND = "MATCHES_FOUND"
    NO_RELEVANT_MATCH = "NO_RELEVANT_MATCH"
    NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE = "NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE"


class ResearchMemoryVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ResearchMemoryReview:
    """Frozen pre-candidate review of both positive and negative experience.

    The review binds the current atom/context to snapshots of the scoped tool
    inventory and global failure lattice.  Empty result sets are allowed only
    when explicitly recorded as ``NO_RELEVANT_MATCH`` (local inventory) or
    ``NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE`` (cross-problem, coverage-bound);
    silence is not a search.
    """

    target_atom_id: str
    target_context_hash: str
    tool_inventory_snapshot_hash: str
    failure_lattice_snapshot_hash: str
    tool_query_status: MemoryQueryStatus
    failure_query_status: MemoryQueryStatus
    candidate_method_families: Tuple[str, ...]
    relevant_tool_ids: Tuple[str, ...] = ()
    relevant_failure_ids: Tuple[str, ...] = ()
    selected_tool_ids: Tuple[str, ...] = ()
    tool_applicability_notes: Tuple[str, ...] = ()
    failure_reuse_notes: Tuple[str, ...] = ()
    unresolved_warnings: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()
    artifact_hash: str = ""
    #: Content hash of a CrossProblemCoverageReceipt.  Required whenever either
    #: query status is ``NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE``.
    cross_problem_coverage_receipt_hash: str = ""


@dataclass(frozen=True)
class ResearchMemoryReport:
    verdict: ResearchMemoryVerdict
    reasons: Tuple[str, ...]


REQUIRED_MEMORY_ACTIONS: Tuple[str, ...] = (
    "query_scoped_success_tool_inventory",
    "query_global_failure_experience_lattice",
    "assess_tool_applicability_and_failure_reuse_scope",
    "record_memory_review_in_public_trace",
)

_BOUND_UNIVERSE_STATUSES = frozenset(
    {MemoryQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE}
)
_EMPTY_ALLOWED_STATUSES = frozenset(
    {
        MemoryQueryStatus.NO_RELEVANT_MATCH,
        MemoryQueryStatus.NO_RELEVANT_MATCH_IN_BOUND_UNIVERSE,
    }
)


def audit_research_memory_review(
    review: ResearchMemoryReview | None,
    *,
    atom_id: str,
    context_hash: str,
) -> ResearchMemoryReport:
    if review is None:
        return ResearchMemoryReport(
            ResearchMemoryVerdict.CANNOT_CHECK,
            ("research_memory_review_missing",),
        )

    reasons: list[str] = []
    if review.target_atom_id != atom_id:
        reasons.append("memory_review_atom_mismatch")
    if review.target_context_hash != context_hash:
        reasons.append("memory_review_context_mismatch")
    if not review.tool_inventory_snapshot_hash:
        reasons.append("tool_inventory_snapshot_hash_missing")
    if not review.failure_lattice_snapshot_hash:
        reasons.append("failure_lattice_snapshot_hash_missing")
    if not review.candidate_method_families:
        reasons.append("candidate_method_families_missing")
    if not review.evidence_pointers:
        reasons.append("memory_review_evidence_missing")
    if not review.artifact_hash:
        reasons.append("memory_review_artifact_hash_missing")

    if review.tool_query_status is MemoryQueryStatus.MATCHES_FOUND:
        if not review.relevant_tool_ids:
            reasons.append("tool_matches_status_without_tool_ids")
        if not review.tool_applicability_notes:
            reasons.append("tool_matches_not_assessed_for_applicability")
    elif review.tool_query_status in _EMPTY_ALLOWED_STATUSES:
        if review.relevant_tool_ids:
            reasons.append("tool_ids_present_despite_no_relevant_match_status")
    else:
        reasons.append("tool_query_status_unrecognized")

    if review.failure_query_status is MemoryQueryStatus.MATCHES_FOUND:
        if not review.relevant_failure_ids:
            reasons.append("failure_matches_status_without_failure_ids")
        if not review.failure_reuse_notes:
            reasons.append("failure_matches_not_assessed_for_reuse_scope")
    elif review.failure_query_status in _EMPTY_ALLOWED_STATUSES:
        if review.relevant_failure_ids:
            reasons.append("failure_ids_present_despite_no_relevant_match_status")
    else:
        reasons.append("failure_query_status_unrecognized")

    if review.selected_tool_ids and not set(review.selected_tool_ids).issubset(
        set(review.relevant_tool_ids)
    ):
        reasons.append("selected_tool_was_not_in_relevant_tool_query")

    # Cross-problem completeness / counting claims must bind a coverage receipt.
    # Local inventory ``NO_RELEVANT_MATCH`` stays coverage-free by design (#119).
    bound_statuses_used = (
        review.tool_query_status in _BOUND_UNIVERSE_STATUSES
        or review.failure_query_status in _BOUND_UNIVERSE_STATUSES
    )
    if bound_statuses_used and not review.cross_problem_coverage_receipt_hash:
        reasons.append("cross_problem_no_match_without_coverage_receipt_hash")
    if (
        review.cross_problem_coverage_receipt_hash
        and not bound_statuses_used
        and MemoryQueryStatus.MATCHES_FOUND
        not in (review.tool_query_status, review.failure_query_status)
    ):
        # A coverage hash with only local NO_RELEVANT_MATCH is not harmful, but
        # claiming bound-universe semantics without the status is rejected.
        pass

    if reasons:
        return ResearchMemoryReport(ResearchMemoryVerdict.FAIL, tuple(reasons))
    return ResearchMemoryReport(
        ResearchMemoryVerdict.PASS,
        ("success_and_failure_experience_reviewed_before_candidate_generation",),
    )
