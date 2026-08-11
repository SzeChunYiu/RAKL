from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

from rakl.failure_lattice import (
    FailureDiagnosisStatus,
    FailureExperience,
    validate_failure_experience,
)
from rakl.research_tool_inventory import (
    ResearchTool,
    ResearchToolAuthority,
    validate_research_tool,
)
from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_research_trace,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/riemann_hypothesis"
ORACLE = BASE / "05_oracles/li_prefix_quartet_calibration.py"


def _load(relative: str) -> dict:
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _fraction_hash(value: Fraction) -> str:
    raw = f"{value.numerator}/{value.denominator}".encode("ascii")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _load_oracle_module():
    spec = importlib.util.spec_from_file_location("rh_li_prefix_oracle", ORACLE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_symmetric_quartet_delays_li_sign_failure_beyond_626() -> None:
    oracle = _load_oracle_module()
    z = oracle.quartet_transform()
    assert z == (Fraction(159997, 160001), Fraction(1600, 160001))

    values = oracle.li_quartet_values(627)
    assert len(values) == 627
    assert all(value > 0 for value in values[:626])
    assert values[626] < 0
    assert oracle.first_negative(values) == (627, values[626])

    receipt = _load("05_oracles/RH_ANA_001_LI_PREFIX_CALIBRATION_20260811.json")
    assert receipt["result"]["all_1_through_626_positive"] is True
    assert receipt["result"]["first_negative_index"] == 627
    assert receipt["result"]["lambda_1_exact_fraction_sha256"] == _fraction_hash(values[0])
    assert receipt["result"]["lambda_626_exact_fraction_sha256"] == _fraction_hash(values[625])
    assert receipt["result"]["lambda_627_exact_fraction_sha256"] == _fraction_hash(values[626])
    assert "NO_ZETA_ZERO_EVIDENCE" in receipt["authority"]


def test_rh_li_prefix_failure_and_tool_are_scoped_and_content_bound() -> None:
    failure_raw = _load(
        "07_memory/RH_ANA_001_POSTCAL_FAILURE_EXPERIENCE_LATTICE_20260811.json"
    )
    assert failure_raw["links"] == []
    assert len(failure_raw["experiences"]) == 1
    raw_failure = failure_raw["experiences"][0]
    failure_for_hash = copy.deepcopy(raw_failure)
    failure_for_hash["artifact_hash"] = ""
    assert raw_failure["artifact_hash"] == _canonical_hash(failure_for_hash)

    failure = FailureExperience(
        failure_id=raw_failure["failure_id"],
        atom_id=raw_failure["atom_id"],
        candidate_id=raw_failure["candidate_id"],
        context_packet_hash=raw_failure["context_packet_hash"],
        research_trace_event_id=raw_failure["research_trace_event_id"],
        method_family=raw_failure["method_family"],
        failure_mode=raw_failure["failure_mode"],
        residual_signature=tuple(raw_failure["residual_signature"]),
        broken_assumptions=tuple(raw_failure["broken_assumptions"]),
        scope_conditions=tuple(raw_failure["scope_conditions"]),
        competing_diagnoses=tuple(raw_failure["competing_diagnoses"]),
        selected_diagnosis=raw_failure["selected_diagnosis"],
        diagnosis_status=FailureDiagnosisStatus(raw_failure["diagnosis_status"]),
        evidence_pointers=tuple(raw_failure["evidence_pointers"]),
        falsifier_or_attempt=raw_failure["falsifier_or_attempt"],
        observed_result=raw_failure["observed_result"],
        artifact_hash=raw_failure["artifact_hash"],
        timestamp=raw_failure["timestamp"],
        local_repair_attempts=tuple(raw_failure.get("local_repair_attempts", ())),
    )
    assert validate_failure_experience(failure) == ()
    assert failure.diagnosis_status is FailureDiagnosisStatus.SUPPORTED
    assert "synthetic" in " ".join(failure.scope_conditions).lower()

    tools_raw = _load(
        "07_memory/RH_ANA_001_POSTCAL_RESEARCH_TOOL_INVENTORY_20260811.json"
    )
    assert len(tools_raw["tools"]) == 1
    raw_tool = tools_raw["tools"][0]
    tool_for_hash = copy.deepcopy(raw_tool)
    tool_for_hash["artifact_hash"] = ""
    assert raw_tool["artifact_hash"] == _canonical_hash(tool_for_hash)

    tool = ResearchTool(
        tool_id=raw_tool["tool_id"],
        name=raw_tool["name"],
        kind=raw_tool["kind"],
        abstraction=raw_tool["abstraction"],
        source_atom_id=raw_tool["source_atom_id"],
        source_candidate_id=raw_tool["source_candidate_id"],
        source_result_ids=tuple(raw_tool["source_result_ids"]),
        source_context_hash=raw_tool["source_context_hash"],
        authority=ResearchToolAuthority(raw_tool["authority"]),
        preconditions=tuple(raw_tool["preconditions"]),
        structural_signature=tuple(raw_tool["structural_signature"]),
        operation=raw_tool["operation"],
        guaranteed_effects=tuple(raw_tool["guaranteed_effects"]),
        non_guarantees=tuple(raw_tool["non_guarantees"]),
        validation_obligations=tuple(raw_tool["validation_obligations"]),
        evidence_pointers=tuple(raw_tool["evidence_pointers"]),
        known_failure_ids=tuple(raw_tool.get("known_failure_ids", ())),
        successful_reuse_ids=tuple(raw_tool.get("successful_reuse_ids", ())),
        proof_backing=tuple(raw_tool.get("proof_backing", ())),
        artifact_hash=raw_tool["artifact_hash"],
    )
    assert validate_research_tool(tool) == ()
    assert tool.authority is ResearchToolAuthority.VERIFIED_LOCAL
    assert tool.known_failure_ids == ("F-RH-ANA-001-FINITE-LI-PREFIX",)
    assert any("does not prove any actual zeta zero" in item for item in tool.non_guarantees)


def test_li_prefix_calibration_extends_the_existing_hash_chained_public_trace() -> None:
    base_raw = _load("09_trace/RH_ANA_001_PRE_CANDIDATE_TRACE_20260811.json")
    continuation = _load("09_trace/RH_ANA_001_TRACE_CONTINUATION_LI_PREFIX_20260811.json")

    assert continuation["trace_id"] == base_raw["trace_id"]
    assert continuation["parent_tail_event_id"] == base_raw["entries"][-1]["event_id"]
    assert continuation["parent_tail_hash"] == base_raw["entries"][-1]["artifact_hash"]

    raw_entries = base_raw["entries"] + continuation["entries"]
    previous = ""
    entries: list[ResearchTraceEntry] = []
    for raw in raw_entries:
        assert raw["previous_event_hash"] == previous
        payload = copy.deepcopy(raw)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash
        entries.append(
            ResearchTraceEntry(
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
        )

    trace = MathResearchTrace(trace_id=base_raw["trace_id"], entries=tuple(entries))
    assert audit_research_trace(trace).verdict is TraceGateVerdict.PASS
    assert [entry.event_type for entry in entries[-4:]] == [
        ResearchTraceEventType.FALSIFIER_RUN,
        ResearchTraceEventType.RESULT_RECORDED,
        ResearchTraceEventType.RESIDUAL_OPENED,
        ResearchTraceEventType.REVIEWED,
    ]
    assert all(entry.event_type is not ResearchTraceEventType.PROMOTED for entry in entries)
    assert entries[-1].outputs == (
        "review:ACCEPT_SCOPED_CALIBRATION",
        "root_status:OPEN_NO_SOLUTION_CERTIFICATE",
    )
