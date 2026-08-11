from __future__ import annotations

from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_pre_candidate_trace,
)


def _entry(i: int, event_type: ResearchTraceEventType) -> ResearchTraceEntry:
    return ResearchTraceEntry(
        event_id=f"e{i}",
        atom_id="atom-C",
        event_type=event_type,
        timestamp=f"2026-08-11T04:0{i}:00+00:00",
        state_summary=f"state {i}",
        action_summary=f"action {i}",
        evidence_pointers=("sha256:context",) if event_type is ResearchTraceEventType.CONTEXT_FROZEN else (f"artifact:{i}",),
        alternatives_considered=("alternative A", "alternative B"),
        decision_rationale="selected because it best discriminates the current residual under the frozen context",
        outputs=(f"output:{i}",),
        uncertainties=("remaining uncertainty",),
        next_steps=("next atomic action",),
        artifact_hash=f"sha256:event-{i}",
    )


def _trace() -> MathResearchTrace:
    return MathResearchTrace(
        trace_id="trace-C",
        entries=(
            _entry(1, ResearchTraceEventType.ATOMIZED),
            _entry(2, ResearchTraceEventType.CONTEXT_FROZEN),
            _entry(3, ResearchTraceEventType.ANALOGY_SCAN),
            _entry(4, ResearchTraceEventType.METHOD_TRANSFER_REVIEW),
            _entry(5, ResearchTraceEventType.NEXT_STEP_PROPOSED),
        ),
    )


def test_complete_pre_candidate_trace_passes() -> None:
    report = audit_pre_candidate_trace(
        _trace(), atom_id="atom-C", context_packet_hash="sha256:context"
    )
    assert report.verdict is TraceGateVerdict.PASS


def test_missing_trace_fails_closed() -> None:
    report = audit_pre_candidate_trace(
        None, atom_id="atom-C", context_packet_hash="sha256:context"
    )
    assert report.verdict is TraceGateVerdict.CANNOT_CHECK


def test_missing_atomization_event_blocks() -> None:
    trace = MathResearchTrace(trace_id="trace-C", entries=_trace().entries[1:])
    report = audit_pre_candidate_trace(
        trace, atom_id="atom-C", context_packet_hash="sha256:context"
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "required_trace_event_missing:ATOMIZED" in report.reasons


def test_context_trace_must_bind_context_hash() -> None:
    entries = list(_trace().entries)
    context = entries[1]
    entries[1] = ResearchTraceEntry(
        event_id=context.event_id,
        atom_id=context.atom_id,
        event_type=context.event_type,
        timestamp=context.timestamp,
        state_summary=context.state_summary,
        action_summary=context.action_summary,
        evidence_pointers=("wrong-hash",),
        artifact_hash=context.artifact_hash,
    )
    report = audit_pre_candidate_trace(
        MathResearchTrace(trace_id="trace-C", entries=tuple(entries)),
        atom_id="atom-C",
        context_packet_hash="sha256:context",
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "trace_context_event_not_bound_to_context_packet_hash" in report.reasons


def test_candidate_before_trace_completion_is_rejected() -> None:
    entries = list(_trace().entries)
    entries.insert(3, _entry(6, ResearchTraceEventType.CANDIDATE_PROPOSED))
    # Move the candidate earlier in time than the final required trace events.
    candidate = entries[3]
    entries[3] = ResearchTraceEntry(
        event_id=candidate.event_id,
        atom_id=candidate.atom_id,
        event_type=candidate.event_type,
        timestamp="2026-08-11T04:02:30+00:00",
        state_summary=candidate.state_summary,
        action_summary=candidate.action_summary,
        evidence_pointers=candidate.evidence_pointers,
        artifact_hash=candidate.artifact_hash,
    )
    report = audit_pre_candidate_trace(
        MathResearchTrace(trace_id="trace-C", entries=tuple(entries)),
        atom_id="atom-C",
        context_packet_hash="sha256:context",
    )
    assert report.verdict is TraceGateVerdict.FAIL
    assert "candidate_recorded_before_pre_candidate_trace_complete" in report.reasons
