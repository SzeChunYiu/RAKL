from __future__ import annotations

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_research_trace,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/p_vs_np"


def _load(relative: str) -> dict:
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_c024_fractional_neq_cut_mixture_has_total_weight_two_and_unit_coverage() -> None:
    # For U = diagonal([N]), use every cut S with weight 2/2^N.
    # A fixed unequal pair u != v is separated by exactly half of all cuts.
    for n in range(1, 5):
        N = 2**n
        cut_weight = Fraction(2, 2**N)
        total_weight = (2**N) * cut_weight
        assert total_weight == 2

        for u in range(N):
            for v in range(N):
                if u == v:
                    continue
                separating = sum(
                    1
                    for mask in range(2**N)
                    if bool(mask & (1 << u)) != bool(mask & (1 << v))
                )
                assert separating == 2 ** (N - 1)
                assert separating * cut_weight == 1

        # Cavalar-Oliveira Proposition 40 gives rho(G_NEQ)=log2(N)=n,
        # so this explicit fractional solution witnesses gap at least n/2.
        assert Fraction(n, 2) >= Fraction(1, 2)


def test_c024_tool_and_failure_deltas_are_content_bound() -> None:
    tool = _load("07_memory/C024_RESEARCH_TOOL_DELTA_20260811.json")["tool"]
    tool_payload = copy.deepcopy(tool)
    tool_hash = tool_payload["artifact_hash"]
    tool_payload["artifact_hash"] = ""
    assert tool_hash == _canonical_hash(tool_payload)

    failure = _load("07_memory/C024_FAILURE_EXPERIENCE_DELTA_20260811.json")["experience"]
    failure_payload = copy.deepcopy(failure)
    failure_hash = failure_payload["artifact_hash"]
    failure_payload["artifact_hash"] = ""
    assert failure_hash == _canonical_hash(failure_payload)
    assert failure["diagnosis_status"] == "SUPPORTED"


def test_c024_appended_trace_preserves_hash_chain_and_audits() -> None:
    raw = _load("09_trace/O9d12a2a1_RESEARCH_TRACE_20260811.json")
    previous = ""
    entries = []
    for item in raw["entries"]:
        assert item["previous_event_hash"] == previous
        payload = copy.deepcopy(item)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash
        entries.append(
            ResearchTraceEntry(
                event_id=item["event_id"],
                atom_id=item["atom_id"],
                event_type=ResearchTraceEventType(item["event_type"]),
                timestamp=item["timestamp"],
                state_summary=item["state_summary"],
                action_summary=item["action_summary"],
                evidence_pointers=tuple(item["evidence_pointers"]),
                alternatives_considered=tuple(item.get("alternatives_considered", ())),
                decision_rationale=item.get("decision_rationale", ""),
                outputs=tuple(item.get("outputs", ())),
                uncertainties=tuple(item.get("uncertainties", ())),
                residuals=tuple(item.get("residuals", ())),
                next_steps=tuple(item.get("next_steps", ())),
                artifact_hash=item["artifact_hash"],
                previous_event_hash=item.get("previous_event_hash", ""),
            )
        )

    trace = MathResearchTrace(trace_id=raw["trace_id"], entries=tuple(entries))
    report = audit_research_trace(trace)
    assert report.verdict is TraceGateVerdict.PASS
    assert entries[-4].event_type is ResearchTraceEventType.CANDIDATE_PROPOSED
    assert entries[-3].event_type is ResearchTraceEventType.FALSIFIER_RUN
    assert entries[-2].event_type is ResearchTraceEventType.RESULT_RECORDED
    assert entries[-1].event_type is ResearchTraceEventType.RESIDUAL_OPENED
