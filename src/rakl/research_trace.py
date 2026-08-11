from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple


class TraceGateVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


class ResearchTraceEventType(str, Enum):
    PROBLEM_FROZEN = "PROBLEM_FROZEN"
    ATOMIZED = "ATOMIZED"
    CONTEXT_FROZEN = "CONTEXT_FROZEN"
    ANALOGY_SCAN = "ANALOGY_SCAN"
    METHOD_TRANSFER_REVIEW = "METHOD_TRANSFER_REVIEW"
    EXPERT_CONTEXT_REVIEW = "EXPERT_CONTEXT_REVIEW"
    EXPERIENCE_MEMORY_REVIEW = "EXPERIENCE_MEMORY_REVIEW"
    NEXT_STEP_PROPOSED = "NEXT_STEP_PROPOSED"
    CANDIDATE_PROPOSED = "CANDIDATE_PROPOSED"
    FALSIFIER_RUN = "FALSIFIER_RUN"
    RESULT_RECORDED = "RESULT_RECORDED"
    RESIDUAL_OPENED = "RESIDUAL_OPENED"
    FORMALIZED = "FORMALIZED"
    PROOF_CHECKED = "PROOF_CHECKED"
    NOVELTY_CHECKED = "NOVELTY_CHECKED"
    REVIEWED = "REVIEWED"
    PROMOTED = "PROMOTED"


@dataclass(frozen=True)
class ResearchTraceEntry:
    """One append-only auditable research decision/event.

    This is not a raw private chain-of-thought transcript. It records the public
    research state needed for reproducibility: what was known, what action was
    taken, which alternatives were considered, a concise evidence-grounded
    decision rationale, what happened, what remains uncertain, and what comes next.
    """

    event_id: str
    atom_id: str
    event_type: ResearchTraceEventType
    timestamp: str
    state_summary: str
    action_summary: str
    evidence_pointers: Tuple[str, ...]
    alternatives_considered: Tuple[str, ...] = ()
    decision_rationale: str = ""
    outputs: Tuple[str, ...] = ()
    uncertainties: Tuple[str, ...] = ()
    residuals: Tuple[str, ...] = ()
    next_steps: Tuple[str, ...] = ()
    artifact_hash: str = ""
    previous_event_hash: str = ""


@dataclass(frozen=True)
class MathResearchTrace:
    trace_id: str
    entries: Tuple[ResearchTraceEntry, ...]


@dataclass(frozen=True)
class ResearchTraceReport:
    verdict: TraceGateVerdict
    reasons: Tuple[str, ...]


REQUIRED_PRE_CANDIDATE_EVENTS: Tuple[ResearchTraceEventType, ...] = (
    ResearchTraceEventType.ATOMIZED,
    ResearchTraceEventType.CONTEXT_FROZEN,
    ResearchTraceEventType.ANALOGY_SCAN,
    ResearchTraceEventType.METHOD_TRANSFER_REVIEW,
    ResearchTraceEventType.EXPERT_CONTEXT_REVIEW,
    ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW,
    ResearchTraceEventType.NEXT_STEP_PROPOSED,
)

REQUIRED_TRACE_ACTIONS: Tuple[str, ...] = (
    "record_atomization_result",
    "record_current_context_snapshot_and_context_packet_hash",
    "record_cross_domain_analogy_scan_result",
    "record_method_transfer_matrix_and_disanalogies",
    "record_role_separated_expert_context_review",
    "record_success_tool_and_failure_lattice_memory_review",
    "record_proposed_next_step_with_alternatives_and_decision_rationale",
)


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def audit_research_trace(trace: MathResearchTrace | None) -> ResearchTraceReport:
    """Validate the append-only public research decision ledger.

    The audit checks chronology, hash chaining and event-specific minimum content.
    It never treats the trace's rationale as proof or scientific evidence.
    """

    if trace is None:
        return ResearchTraceReport(
            TraceGateVerdict.CANNOT_CHECK,
            ("math_research_trace_missing",),
        )

    reasons: list[str] = []
    if not trace.trace_id:
        reasons.append("trace_id_missing")
    if not trace.entries:
        reasons.append("trace_entries_missing")
        return ResearchTraceReport(TraceGateVerdict.FAIL, tuple(reasons))

    ids: set[str] = set()
    previous_time: datetime | None = None
    previous_hash = ""

    for index, entry in enumerate(trace.entries):
        prefix = f"trace_entry_{index}"
        if not entry.event_id:
            reasons.append(f"{prefix}:event_id_missing")
        elif entry.event_id in ids:
            reasons.append(f"{prefix}:duplicate_event_id")
        ids.add(entry.event_id)

        if not entry.atom_id:
            reasons.append(f"{prefix}:atom_id_missing")
        if not entry.state_summary:
            reasons.append(f"{prefix}:state_summary_missing")
        if not entry.action_summary:
            reasons.append(f"{prefix}:action_summary_missing")
        if not entry.evidence_pointers:
            reasons.append(f"{prefix}:evidence_pointers_missing")
        if not entry.artifact_hash:
            reasons.append(f"{prefix}:artifact_hash_missing")

        timestamp = _parse_time(entry.timestamp)
        if timestamp is None:
            reasons.append(f"{prefix}:timestamp_missing_or_invalid")
        elif previous_time is not None and timestamp < previous_time:
            reasons.append(f"{prefix}:timestamp_regression")
        else:
            previous_time = timestamp

        if index == 0:
            if entry.previous_event_hash:
                reasons.append(f"{prefix}:first_event_previous_hash_must_be_empty")
        elif entry.previous_event_hash != previous_hash:
            reasons.append(f"{prefix}:previous_event_hash_mismatch")
        previous_hash = entry.artifact_hash

        if entry.event_type in {
            ResearchTraceEventType.EXPERT_CONTEXT_REVIEW,
            ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW,
            ResearchTraceEventType.NEXT_STEP_PROPOSED,
            ResearchTraceEventType.CANDIDATE_PROPOSED,
        }:
            if not entry.alternatives_considered:
                reasons.append(f"{prefix}:alternatives_considered_missing")
            if not entry.decision_rationale:
                reasons.append(f"{prefix}:decision_rationale_missing")

        if entry.event_type is ResearchTraceEventType.EXPERT_CONTEXT_REVIEW:
            if not entry.uncertainties:
                reasons.append(f"{prefix}:expert_review_uncertainties_missing")

        if entry.event_type is ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW:
            if not entry.outputs:
                reasons.append(f"{prefix}:memory_review_outputs_missing")
            if not entry.uncertainties:
                reasons.append(f"{prefix}:memory_review_warnings_or_uncertainties_missing")

        if entry.event_type is ResearchTraceEventType.NEXT_STEP_PROPOSED:
            if not entry.next_steps:
                reasons.append(f"{prefix}:next_steps_missing")

        if entry.event_type is ResearchTraceEventType.CANDIDATE_PROPOSED:
            if not entry.outputs:
                reasons.append(f"{prefix}:candidate_identity_output_missing")

        if entry.event_type is ResearchTraceEventType.RESULT_RECORDED:
            if not (entry.outputs or entry.residuals):
                reasons.append(f"{prefix}:result_output_or_residual_missing")

        if entry.event_type is ResearchTraceEventType.RESIDUAL_OPENED:
            if not entry.residuals:
                reasons.append(f"{prefix}:residuals_missing")
            if not entry.next_steps:
                reasons.append(f"{prefix}:residual_next_steps_missing")

    if reasons:
        return ResearchTraceReport(TraceGateVerdict.FAIL, tuple(reasons))
    return ResearchTraceReport(
        TraceGateVerdict.PASS,
        ("auditable_research_trace_integrity_passed",),
    )


def audit_pre_candidate_trace(
    trace: MathResearchTrace | None,
    *,
    atom_id: str,
    context_packet_hash: str,
) -> ResearchTraceReport:
    """Require a chronological public research ledger before candidate generation."""

    base = audit_research_trace(trace)
    if base.verdict is not TraceGateVerdict.PASS:
        return base
    assert trace is not None

    reasons: list[str] = []
    if not atom_id:
        reasons.append("trace_atom_id_missing")

    atom_entries = [entry for entry in trace.entries if entry.atom_id == atom_id]
    event_types = [entry.event_type for entry in atom_entries]
    positions: list[int] = []
    for required in REQUIRED_PRE_CANDIDATE_EVENTS:
        if required not in event_types:
            reasons.append(f"required_trace_event_missing:{required.value}")
        else:
            positions.append(event_types.index(required))
    if positions and positions != sorted(positions):
        reasons.append("pre_candidate_trace_events_out_of_order")

    context_entries = [
        entry
        for entry in atom_entries
        if entry.event_type is ResearchTraceEventType.CONTEXT_FROZEN
    ]
    if context_entries and context_packet_hash:
        if not any(
            context_packet_hash in entry.evidence_pointers
            or context_packet_hash in entry.outputs
            for entry in context_entries
        ):
            reasons.append("trace_context_event_not_bound_to_context_packet_hash")

    candidate_positions = [
        i
        for i, entry in enumerate(atom_entries)
        if entry.event_type is ResearchTraceEventType.CANDIDATE_PROPOSED
    ]
    if candidate_positions and positions:
        if min(candidate_positions) <= max(positions):
            reasons.append("candidate_recorded_before_pre_candidate_trace_complete")

    if reasons:
        return ResearchTraceReport(TraceGateVerdict.FAIL, tuple(reasons))
    return ResearchTraceReport(
        TraceGateVerdict.PASS,
        ("auditable_pre_candidate_research_trace_complete",),
    )
