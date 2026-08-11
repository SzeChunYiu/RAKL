from __future__ import annotations

from dataclasses import replace

from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_pre_candidate_trace,
    audit_research_trace,
)


def _entry(
    i: int,
    event_type: ResearchTraceEventType,
    *,
    timestamp: str | None = None,
    previous_event_hash: str = "",
) -> ResearchTraceEntry:
    outputs = (f"output:{i}",)
    if event_type is ResearchTraceEventType.OBSTRUCTION_TRANSFORMATION_REVIEW:
        outputs = ("sha256:shortcut",)
    return ResearchTraceEntry(
        event_id=f"e{i}",
        atom_id="atom-C",
        event_type=event_type,
        timestamp=timestamp or f"2026-08-11T04:{i:02d}:00+00:00",
        state_summary=f"state {i}",
        action_summary=f"action {i}",
        evidence_pointers=("sha256:context",)
        if event_type is ResearchTraceEventType.CONTEXT_FROZEN
        else (f"artifact:{i}",),
        alternatives_considered=("alternative A", "alternative B"),
        decision_rationale="selected because it best discriminates the current residual under the frozen context",
        outputs=outputs,
        uncertainties=("remaining uncertainty",),
        residuals=("residual",)
        if event_type is ResearchTraceEventType.RESIDUAL_OPENED
        else (),
        next_steps=("next atomic action",),
        artifact_hash=f"sha256:event-{i}",
        previous_event_hash=previous_event_hash,
    )


def _build_trace(
    events: tuple[tuple[int, ResearchTraceEventType, str | None], ...]
) -> MathResearchTrace:
    entries: list[ResearchTraceEntry] = []
    previous_hash = ""
    for i, event_type, timestamp in events:
        entry = _entry(
            i,
            event_type,
            timestamp=timestamp,
            previous_event_hash=previous_hash,
        )
        entries.append(entry)
        previous_hash = entry.artifact_hash
    return MathResearchTrace(trace_id="trace-C", entries=tuple(entries))


def _trace() -> MathResearchTrace:
    return _build_trace(
        (
            (1, ResearchTraceEventType.ATOMIZED, None),
            (2, ResearchTraceEventType.CONTEXT_FROZEN, None),
            (3, ResearchTraceEventType.ANALOGY_SCAN, None),
            (4, ResearchTraceEventType.METHOD_TRANSFER_REVIEW, None),
            (5, ResearchTraceEventType.EXPERT_CONTEXT_REVIEW, None),
            (6, ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW, None),
            (7, ResearchTraceEventType.OBSTRUCTION_TRANSFORMATION_REVIEW, None),
            (8, ResearchTraceEventType.NEXT_STEP_PROPOSED, None),
        )
    )


def test_complete_pre_candidate_trace_passes() -> None:
    report = audit_pre_candidate_trace(
        _trace(),
        atom_id="atom-C",
        context_packet_hash="sha256:context",
        obstruction_transformation_review_hash="sha256:shortcut",
    )
    assert report.verdict is TraceGateVerdict.PASS


def test_missing_trace_fails_closed() -> None:
    report = audit_pre_candidate_trace(
        None, atom_id="atom-C", context_packet_hash="sha256:context"
    )
    assert report.verdict is TraceGateVerdict.CANNOT_CHECK


def test_missing_experience_memory_review_blocks_candidate_generation() -> None:
    trace = _build_trace(
        (
            (1, ResearchTraceEventType.ATOMIZED, None),
            (2, ResearchTraceEventType.CONTEXT_FROZEN, None),
            (3, ResearchTraceEventType.ANALOGY_SCAN, None),
            (4, ResearchTraceEventType.METHOD_TRANSFER_REVIEW, None),
            (5, ResearchTraceEventType.EXPERT_CONTEXT_REVIEW, None),
            (7, ResearchTraceEventType.OBSTRUCTION_TRANSFORMATION_REVIEW, None),
            (8, ResearchTraceEventType.NEXT_STEP_PROPOSED, None),
        )
    )
    report = audit_pre_candidate_trace(
        trace, atom_id="atom-C", context_packet_hash="sha256:context"
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "required_trace_event_missing:EXPERIENCE_MEMORY_REVIEW" in report.reasons


def test_missing_obstruction_transformation_review_blocks_candidate_generation() -> None:
    trace = _build_trace(
        (
            (1, ResearchTraceEventType.ATOMIZED, None),
            (2, ResearchTraceEventType.CONTEXT_FROZEN, None),
            (3, ResearchTraceEventType.ANALOGY_SCAN, None),
            (4, ResearchTraceEventType.METHOD_TRANSFER_REVIEW, None),
            (5, ResearchTraceEventType.EXPERT_CONTEXT_REVIEW, None),
            (6, ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW, None),
            (8, ResearchTraceEventType.NEXT_STEP_PROPOSED, None),
        )
    )
    report = audit_pre_candidate_trace(
        trace, atom_id="atom-C", context_packet_hash="sha256:context"
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert (
        "required_trace_event_missing:OBSTRUCTION_TRANSFORMATION_REVIEW"
        in report.reasons
    )


def test_context_trace_must_bind_context_hash() -> None:
    entries = list(_trace().entries)
    entries[1] = replace(entries[1], evidence_pointers=("wrong-hash",), outputs=())
    report = audit_pre_candidate_trace(
        MathResearchTrace(trace_id="trace-C", entries=tuple(entries)),
        atom_id="atom-C",
        context_packet_hash="sha256:context",
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "trace_context_event_not_bound_to_context_packet_hash" in report.reasons


def test_shortcut_trace_must_bind_shortcut_review_hash() -> None:
    entries = list(_trace().entries)
    entries[6] = replace(entries[6], evidence_pointers=("wrong",), outputs=("wrong",))
    report = audit_pre_candidate_trace(
        MathResearchTrace(trace_id="trace-C", entries=tuple(entries)),
        atom_id="atom-C",
        context_packet_hash="sha256:context",
        obstruction_transformation_review_hash="sha256:shortcut",
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "trace_shortcut_event_not_bound_to_review_hash" in report.reasons


def test_candidate_before_trace_completion_is_rejected() -> None:
    trace = _build_trace(
        (
            (1, ResearchTraceEventType.ATOMIZED, "2026-08-11T04:01:00+00:00"),
            (2, ResearchTraceEventType.CONTEXT_FROZEN, "2026-08-11T04:02:00+00:00"),
            (9, ResearchTraceEventType.CANDIDATE_PROPOSED, "2026-08-11T04:02:30+00:00"),
            (3, ResearchTraceEventType.ANALOGY_SCAN, "2026-08-11T04:03:00+00:00"),
            (4, ResearchTraceEventType.METHOD_TRANSFER_REVIEW, "2026-08-11T04:04:00+00:00"),
            (5, ResearchTraceEventType.EXPERT_CONTEXT_REVIEW, "2026-08-11T04:05:00+00:00"),
            (6, ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW, "2026-08-11T04:06:00+00:00"),
            (7, ResearchTraceEventType.OBSTRUCTION_TRANSFORMATION_REVIEW, "2026-08-11T04:07:00+00:00"),
            (8, ResearchTraceEventType.NEXT_STEP_PROPOSED, "2026-08-11T04:08:00+00:00"),
        )
    )
    report = audit_pre_candidate_trace(
        trace,
        atom_id="atom-C",
        context_packet_hash="sha256:context",
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "candidate_recorded_before_pre_candidate_trace_complete" in report.reasons


def test_hash_chain_break_is_rejected() -> None:
    entries = list(_trace().entries)
    entries[3] = replace(entries[3], previous_event_hash="wrong")
    report = audit_research_trace(
        MathResearchTrace(trace_id="trace-C", entries=tuple(entries))
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "trace_entry_3:previous_event_hash_mismatch" in report.reasons


def test_next_step_requires_alternatives_rationale_and_next_action() -> None:
    entries = list(_trace().entries)
    entries[-1] = replace(
        entries[-1],
        alternatives_considered=(),
        decision_rationale="",
        next_steps=(),
    )
    report = audit_research_trace(
        MathResearchTrace(trace_id="trace-C", entries=tuple(entries))
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "trace_entry_7:alternatives_considered_missing" in report.reasons
    assert "trace_entry_7:decision_rationale_missing" in report.reasons
    assert "trace_entry_7:next_steps_missing" in report.reasons
