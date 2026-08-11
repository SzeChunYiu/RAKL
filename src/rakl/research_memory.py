from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class MemoryQueryStatus(str, Enum):
    MATCHES_FOUND = "MATCHES_FOUND"
    NO_RELEVANT_MATCH = "NO_RELEVANT_MATCH"


class ResearchMemoryVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ResearchMemoryReview:
    """Frozen pre-candidate review of both positive and negative experience.

    The review binds the current atom/context to snapshots of the scoped tool
    inventory and global failure lattice.  Empty result sets are allowed only
    when explicitly recorded as NO_RELEVANT_MATCH; silence is not a search.
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
    elif review.relevant_tool_ids:
        reasons.append("tool_ids_present_despite_no_relevant_match_status")

    if review.failure_query_status is MemoryQueryStatus.MATCHES_FOUND:
        if not review.relevant_failure_ids:
            reasons.append("failure_matches_status_without_failure_ids")
        if not review.failure_reuse_notes:
            reasons.append("failure_matches_not_assessed_for_reuse_scope")
    elif review.relevant_failure_ids:
        reasons.append("failure_ids_present_despite_no_relevant_match_status")

    if review.selected_tool_ids and not set(review.selected_tool_ids).issubset(
        set(review.relevant_tool_ids)
    ):
        reasons.append("selected_tool_was_not_in_relevant_tool_query")

    if reasons:
        return ResearchMemoryReport(ResearchMemoryVerdict.FAIL, tuple(reasons))
    return ResearchMemoryReport(
        ResearchMemoryVerdict.PASS,
        ("success_and_failure_experience_reviewed_before_candidate_generation",),
    )
