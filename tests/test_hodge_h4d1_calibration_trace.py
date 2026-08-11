from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_research_trace,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/hodge/deformation/09_trace"


def _load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _entry(raw: dict) -> ResearchTraceEntry:
    return ResearchTraceEntry(
        event_id=raw["event_id"],
        atom_id=raw["atom_id"],
        event_type=ResearchTraceEventType(raw["event_type"]),
        timestamp=raw["timestamp"],
        state_summary=raw["state_summary"],
        action_summary=raw["action_summary"],
        evidence_pointers=tuple(raw["evidence_pointers"]),
        alternatives_considered=tuple(raw.get("alternatives_considered", ())),
        decision_rationale=raw.get("decision_rationale", ""),
        outputs=tuple(raw.get("outputs", ())),
        uncertainties=tuple(raw.get("uncertainties", ())),
        residuals=tuple(raw.get("residuals", ())),
        next_steps=tuple(raw.get("next_steps", ())),
        artifact_hash=raw["artifact_hash"],
        previous_event_hash=raw.get("previous_event_hash", ""),
    )


def test_h4d1_calibration_continuation_extends_hash_chain_without_candidate() -> None:
    pre = _load("H4d1_PRE_CANDIDATE_TRACE_20260811.json")
    continuation = _load("H4d1_CALIBRATION_TRACE_CONTINUATION_20260811.json")

    assert continuation["trace_id"] == pre["trace_id"]
    assert continuation["continuation_of_event_id"] == pre["entries"][-1]["event_id"]
    assert continuation["continuation_of_artifact_hash"] == pre["entries"][-1]["artifact_hash"]

    previous = pre["entries"][-1]["artifact_hash"]
    for raw in continuation["entries"]:
        assert raw["previous_event_hash"] == previous
        payload = copy.deepcopy(raw)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash

    combined = tuple(_entry(raw) for raw in pre["entries"] + continuation["entries"])
    report = audit_research_trace(MathResearchTrace(trace_id=pre["trace_id"], entries=combined))
    assert report.verdict is TraceGateVerdict.PASS

    assert [raw["event_type"] for raw in continuation["entries"]] == [
        "RESULT_RECORDED",
        "RESIDUAL_OPENED",
    ]
    assert continuation["entries"][-1]["residuals"][0].startswith("H4d1a:")
    assert all(
        entry.event_type is not ResearchTraceEventType.CANDIDATE_PROPOSED
        for entry in combined
    )
