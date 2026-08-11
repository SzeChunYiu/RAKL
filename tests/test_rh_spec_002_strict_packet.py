from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from rakl.math_context import (
    ContextGateVerdict,
    CrossDomainAnalogy,
    MathContextFiber,
    MethodTransfer,
    audit_math_context_fiber,
)
from rakl.math_research_assurance import MathResearchRecord
from rakl.math_research_runtime import plan_math_research
from rakl.problem_solving_algebra import ProblemSignature
from rakl.research_memory import (
    MemoryQueryStatus,
    ResearchMemoryReview,
    ResearchMemoryVerdict,
    audit_research_memory_review,
)
from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
    TraceGateVerdict,
    audit_pre_candidate_trace,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/real_math/millennium/riemann_hypothesis"
PNP_MEMORY = ROOT / "research/real_math/millennium/p_vs_np/07_memory"


def _load(base: Path, relative: str) -> dict:
    return json.loads((base / relative).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _fiber(raw: dict) -> MathContextFiber:
    return MathContextFiber(
        atom_id=raw["atom_id"],
        object_context=raw["object_context"],
        structural_coordinates=tuple(raw["structural_coordinates"]),
        equivalent_formulations=tuple(raw["equivalent_formulations"]),
        solved_analogues=tuple(raw.get("solved_analogues", ())),
        near_solved_analogues=tuple(raw.get("near_solved_analogues", ())),
        method_transfers=tuple(
            MethodTransfer(
                source_context=item["source_context"],
                method=item["method"],
                shared_structure=tuple(item["shared_structure"]),
                required_assumptions=tuple(item["required_assumptions"]),
                disanalogies=tuple(item["disanalogies"]),
                repair_question=item["repair_question"],
                source_anchors=tuple(item["source_anchors"]),
            )
            for item in raw["method_transfers"]
        ),
        explicit_disanalogies=tuple(raw["explicit_disanalogies"]),
        source_anchors=tuple(raw["source_anchors"]),
        analogy_scan_status=raw["analogy_scan_status"],
        cross_domain_analogies=tuple(
            CrossDomainAnalogy(
                source_kind=item["source_kind"],
                source_situation=item["source_situation"],
                common_abstraction=tuple(item["common_abstraction"]),
                source_to_target_mapping=tuple(item["source_to_target_mapping"]),
                shared_constraints=tuple(item["shared_constraints"]),
                disanalogies=tuple(item["disanalogies"]),
                proposed_principle=item["proposed_principle"],
                validation_obligation=item["validation_obligation"],
                provenance_note=item["provenance_note"],
            )
            for item in raw.get("cross_domain_analogies", ())
        ),
        analogy_scan_notes=raw.get("analogy_scan_notes", ""),
        frozen_at=raw["frozen_at"],
        first_candidate_at=raw.get("first_candidate_at"),
        packet_hash=raw["packet_hash"],
    )


def _memory(raw: dict) -> ResearchMemoryReview:
    return ResearchMemoryReview(
        target_atom_id=raw["target_atom_id"],
        target_context_hash=raw["target_context_hash"],
        tool_inventory_snapshot_hash=raw["tool_inventory_snapshot_hash"],
        failure_lattice_snapshot_hash=raw["failure_lattice_snapshot_hash"],
        tool_query_status=MemoryQueryStatus(raw["tool_query_status"]),
        failure_query_status=MemoryQueryStatus(raw["failure_query_status"]),
        candidate_method_families=tuple(raw["candidate_method_families"]),
        relevant_tool_ids=tuple(raw.get("relevant_tool_ids", ())),
        relevant_failure_ids=tuple(raw.get("relevant_failure_ids", ())),
        selected_tool_ids=tuple(raw.get("selected_tool_ids", ())),
        tool_applicability_notes=tuple(raw.get("tool_applicability_notes", ())),
        failure_reuse_notes=tuple(raw.get("failure_reuse_notes", ())),
        unresolved_warnings=tuple(raw.get("unresolved_warnings", ())),
        evidence_pointers=tuple(raw.get("evidence_pointers", ())),
        artifact_hash=raw["artifact_hash"],
    )


def _trace(raw: dict) -> MathResearchTrace:
    previous = ""
    entries = []
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


def test_rh_spec_002_strict_packet_passes_before_limit_calibration() -> None:
    context_raw = _load(BASE, "01_frontier/RH_SPEC_002_CONTEXT_FIBER_20260811.json")
    context_for_hash = copy.deepcopy(context_raw)
    context_for_hash["packet_hash"] = ""
    assert context_raw["packet_hash"] == _canonical_hash(context_for_hash)
    assert context_raw["first_candidate_at"] is None
    fiber = _fiber(context_raw)
    assert audit_math_context_fiber(fiber).verdict is ContextGateVerdict.PASS

    tools_raw = _load(PNP_MEMORY, "O9d12a2a1_RESEARCH_TOOL_INVENTORY_20260811.json")
    failures_raw = _load(PNP_MEMORY, "O9d12a2a1_FAILURE_EXPERIENCE_LATTICE_20260811.json")
    memory_raw = _load(BASE, "07_memory/RH_SPEC_002_RESEARCH_MEMORY_REVIEW_20260811.json")
    assert memory_raw["tool_inventory_snapshot_hash"] == _canonical_hash(tools_raw)
    assert memory_raw["failure_lattice_snapshot_hash"] == _canonical_hash(failures_raw)
    memory_for_hash = copy.deepcopy(memory_raw)
    memory_for_hash["artifact_hash"] = ""
    assert memory_raw["artifact_hash"] == _canonical_hash(memory_for_hash)
    assert memory_raw["selected_tool_ids"] == []
    memory = _memory(memory_raw)
    assert (
        audit_research_memory_review(
            memory,
            atom_id=fiber.atom_id,
            context_hash=fiber.packet_hash,
        ).verdict
        is ResearchMemoryVerdict.PASS
    )

    trace_raw = _load(BASE, "09_trace/RH_SPEC_002_OPEN_TRACE_20260811.json")
    trace = _trace(trace_raw)
    assert (
        audit_pre_candidate_trace(
            trace,
            atom_id=fiber.atom_id,
            context_packet_hash=fiber.packet_hash,
        ).verdict
        is TraceGateVerdict.PASS
    )
    assert all(
        entry.event_type is not ResearchTraceEventType.CANDIDATE_PROPOSED
        for entry in trace.entries
    )

    plan = plan_math_research(
        signature=ProblemSignature(
            objects=(
                "finite/restricted RH spectral approximants",
                "normalized regularized entire determinants",
                "Riemann Xi function",
                "limiting self-adjoint spectral object",
            ),
            relations=(
                "local-uniform entire-function convergence",
                "resolvent/form convergence",
                "spectral pollution exclusion",
                "zero completeness and multiplicity transport",
                "exact arithmetic determinant/trace identification",
            ),
            domain="analytic number theory / spectral approximation / operator theory",
            goal_type="calibrate convergence packages before any RH spectral-limit theorem candidate",
        ),
        record=MathResearchRecord(claim_id=fiber.atom_id),
        context_fiber=fiber,
        memory_review=memory,
        research_trace=trace,
    )
    assert plan.context_gate.verdict is ContextGateVerdict.PASS
    assert plan.memory_gate.verdict is ResearchMemoryVerdict.PASS
    assert plan.trace_gate.verdict is TraceGateVerdict.PASS
    assert plan.candidate_generation_allowed
    assert plan.pre_candidate_actions == ()
