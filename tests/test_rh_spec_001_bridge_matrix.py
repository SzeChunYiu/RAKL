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
    audit_pre_candidate_trace,
    audit_research_trace,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/riemann_hypothesis"
MATRIX = BASE / "01_frontier/RH_SPEC_001_OPERATOR_BRIDGE_MATRIX_20260811.json"
CHILD_CONTEXT = BASE / "01_frontier/RH_SPEC_002_CONTEXT_FIBER_20260811.json"
CHILD_TRACE = BASE / "09_trace/RH_SPEC_002_OPEN_TRACE_20260811.json"

REQUIRED_OBLIGATIONS = {
    "B1_STATE_SPACE_DOMAIN",
    "B2_SELF_ADJOINT_OR_POSITIVE_FORM",
    "B3_TRACE_DETERMINANT_LEGITIMACY",
    "B4_EXACT_ARITHMETIC_MATCHING",
    "B5_ZERO_COMPLETENESS_MULTIPLICITY",
    "B6_NON_CIRCULARITY",
    "B7_GLOBALIZATION_PARAMETER_CONTINUATION",
    "B8_LIMIT_TOPOLOGY_SPECTRAL_POLLUTION",
}

ALLOWED_STATUSES = {
    "CLOSED_IN_SOURCE_SCOPE",
    "RESTRICTED_OR_LOCAL",
    "OPEN",
    "RH_EQUIVALENT_IF_ASSUMED",
    "SOLVED_ANALOGUE_ONLY",
    "NOT_TARGETED",
}


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_trace() -> MathResearchTrace:
    raw = json.loads(CHILD_TRACE.read_text(encoding="utf-8"))
    entries = []
    previous = ""
    for item in raw["entries"]:
        payload = copy.deepcopy(item)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        assert item["previous_event_hash"] == previous
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
    return MathResearchTrace(trace_id=raw["trace_id"], entries=tuple(entries))


def test_rh_spec_001_bridge_matrix_selects_limit_child_without_candidate() -> None:
    raw = json.loads(MATRIX.read_text(encoding="utf-8"))
    payload = copy.deepcopy(raw)
    payload["artifact_hash"] = ""
    assert raw["artifact_hash"] == _canonical_hash(payload)

    obligations = {item["id"] for item in raw["obligations"]}
    assert obligations == REQUIRED_OBLIGATIONS
    assert set(raw["status_vocabulary"]) == ALLOWED_STATUSES

    for route in raw["routes"]:
        assert set(route["statuses"]) == REQUIRED_OBLIGATIONS
        assert set(route["statuses"].values()) <= ALLOWED_STATUSES

    selected = set(raw["expert_selection"]["selected_obligation_family"])
    assert {
        "B5_ZERO_COMPLETENESS_MULTIPLICITY",
        "B7_GLOBALIZATION_PARAMETER_CONTINUATION",
        "B8_LIMIT_TOPOLOGY_SPECTRAL_POLLUTION",
    } <= selected

    next_atom = raw["next_atom"]
    assert next_atom["atom_id"] == "RH-SPEC-002"
    assert next_atom["status"] == "PRE_CANDIDATE_CONTEXT_REQUIRED"
    assert "candidate" not in next_atom
    assert raw["root_status"] == "OPEN_NO_SOLUTION_CERTIFICATE"
    assert "NO_MATHEMATICAL_CANDIDATE" in raw["authority"]


def test_rh_spec_002_trace_completes_pre_candidate_chronology_without_candidate() -> None:
    context = json.loads(CHILD_CONTEXT.read_text(encoding="utf-8"))
    trace = _load_trace()
    assert audit_research_trace(trace).verdict is TraceGateVerdict.PASS
    assert (
        audit_pre_candidate_trace(
            trace,
            atom_id="RH-SPEC-002",
            context_packet_hash=context["packet_hash"],
        ).verdict
        is TraceGateVerdict.PASS
    )
    assert all(
        entry.event_type is not ResearchTraceEventType.CANDIDATE_PROPOSED
        for entry in trace.entries
    )
