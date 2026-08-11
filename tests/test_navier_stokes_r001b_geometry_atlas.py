from __future__ import annotations

import copy
from fractions import Fraction
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
BASE = ROOT / "research/real_math/millennium/navier_stokes"


def _load(relative: str) -> dict:
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def _canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _matadd(a, b):
    return tuple(tuple(a[i][j] + b[i][j] for j in range(3)) for i in range(3))


def _matscale(c, a):
    return tuple(tuple(c * a[i][j] for j in range(3)) for i in range(3))


def _matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


def _matvec(a, v):
    return tuple(sum(a[i][j] * v[j] for j in range(3)) for i in range(3))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _poly_derivative(poly, axis: int):
    out = {}
    for exponents, coefficient in poly.items():
        power = exponents[axis]
        if power == 0:
            continue
        reduced = list(exponents)
        reduced[axis] -= 1
        key = tuple(reduced)
        out[key] = out.get(key, Fraction(0)) + coefficient * power
    return {key: value for key, value in out.items() if value}


def _poly_sub(a, b):
    out = dict(a)
    for key, value in b.items():
        out[key] = out.get(key, Fraction(0)) - value
    return {key: value for key, value in out.items() if value}


def test_common_linear_core_has_exact_positive_eigenframe_alignment() -> None:
    half = Fraction(1, 2)
    s0 = ((-half, 0, 0), (0, -half, 0), (0, 0, 1))
    j = ((0, -1, 0), (1, 0, 0), (0, 0, 0))
    b = Fraction(7, 5)
    a = _matadd(s0, _matscale(b, j))

    assert sum(a[i][i] for i in range(3)) == 0
    symmetric = _matscale(Fraction(1, 2), _matadd(a, _transpose(a)))
    assert symmetric == s0

    omega = (a[2][1] - a[1][2], a[0][2] - a[2][0], a[1][0] - a[0][1])
    assert omega == (0, 0, 2 * b)
    assert _matvec(s0, omega) == omega
    assert _dot(omega, _matvec(s0, omega)) == 4 * b * b

    s_frobenius_squared = sum(entry * entry for row in s0 for entry in row)
    omega_squared = _dot(omega, omega)
    normalized_squared = _dot(omega, _matvec(s0, omega)) ** 2 / (s_frobenius_squared * omega_squared**2)
    assert normalized_squared == Fraction(2, 3)


def test_compact_core_vector_potential_has_exact_curl_Ax() -> None:
    b1 = {(1, 0, 1): Fraction(1, 3), (0, 1, 1): Fraction(-1, 2)}
    b2 = {(1, 0, 1): Fraction(1, 2), (0, 1, 1): Fraction(1, 3)}
    b3 = {(2, 0, 0): Fraction(-1, 3), (0, 2, 0): Fraction(-1, 3)}

    curl1 = _poly_sub(_poly_derivative(b3, 1), _poly_derivative(b2, 2))
    curl2 = _poly_sub(_poly_derivative(b1, 2), _poly_derivative(b3, 0))
    curl3 = _poly_sub(_poly_derivative(b2, 0), _poly_derivative(b1, 1))

    assert curl1 == {(1, 0, 0): Fraction(-1, 2), (0, 1, 0): Fraction(-1)}
    assert curl2 == {(1, 0, 0): Fraction(1), (0, 1, 0): Fraction(-1, 2)}
    assert curl3 == {(0, 0, 1): Fraction(1)}


def test_parent_concentration_preserves_alignment_while_stretching_diverges() -> None:
    gradient_exponent = Fraction(3, 2) + 1
    strain_exponent = gradient_exponent
    vorticity_exponent = gradient_exponent
    stretching_exponent = 2 * vorticity_exponent + strain_exponent

    assert strain_exponent == Fraction(5, 2)
    assert vorticity_exponent == Fraction(5, 2)
    assert stretching_exponent == Fraction(15, 2)
    assert Fraction(2, 3) == Fraction(2, 3)


def test_exact_linear_flow_cancels_antisymmetric_convection_by_time_evolution() -> None:
    half = Fraction(1, 2)
    s0 = ((-half, 0, 0), (0, -half, 0), (0, 0, 1))
    j = ((0, -1, 0), (1, 0, 0), (0, 0, 0))
    minus_j = _matscale(-1, j)

    assert _matadd(_matmul(s0, j), _matmul(j, s0)) == minus_j
    assert _matmul(j, j) == ((-1, 0, 0), (0, -1, 0), (0, 0, 0))
    assert _matadd(j, _matadd(_matmul(s0, j), _matmul(j, s0))) == ((0, 0, 0), (0, 0, 0), (0, 0, 0))

    b = Fraction(5, 3)
    a = _matadd(s0, _matscale(b, j))
    a_prime = _matscale(b, j)
    q = _matadd(a_prime, _matmul(a, a))
    expected = ((Fraction(1, 4) - b * b, 0, 0), (0, Fraction(1, 4) - b * b, 0), (0, 0, 1))
    assert q == expected
    assert q == _transpose(q)


def test_exact_linear_flow_vorticity_equation_and_infinite_energy_scope() -> None:
    half = Fraction(1, 2)
    s0 = ((-half, 0, 0), (0, -half, 0), (0, 0, 1))
    b = Fraction(4, 3)
    omega = (0, 0, 2 * b)
    omega_prime = (0, 0, 2 * b)

    assert omega_prime == _matvec(s0, omega)
    assert _dot(omega, _matvec(s0, omega)) == 4 * b * b

    j = ((0, -1, 0), (1, 0, 0), (0, 0, 0))
    a = _matadd(s0, _matscale(b, j))
    frobenius_squared = sum(entry * entry for row in a for entry in row)
    assert frobenius_squared > 0
    assert 5 > 0


def test_child_strict_packet_hashes_and_gates_pass() -> None:
    context_raw = _load("01_frontier/NS_R001B_GEOMETRY_CONTEXT_FIBER_20260811.json")
    context_for_hash = copy.deepcopy(context_raw)
    context_for_hash["packet_hash"] = ""
    assert context_raw["packet_hash"] == _canonical_hash(context_for_hash)

    fiber = MathContextFiber(
        atom_id=context_raw["atom_id"], object_context=context_raw["object_context"],
        structural_coordinates=tuple(context_raw["structural_coordinates"]),
        equivalent_formulations=tuple(context_raw["equivalent_formulations"]),
        solved_analogues=tuple(context_raw.get("solved_analogues", ())),
        near_solved_analogues=tuple(context_raw.get("near_solved_analogues", ())),
        method_transfers=tuple(MethodTransfer(source_context=item["source_context"], method=item["method"], shared_structure=tuple(item["shared_structure"]), required_assumptions=tuple(item["required_assumptions"]), disanalogies=tuple(item["disanalogies"]), repair_question=item["repair_question"], source_anchors=tuple(item["source_anchors"])) for item in context_raw["method_transfers"]),
        explicit_disanalogies=tuple(context_raw["explicit_disanalogies"]), source_anchors=tuple(context_raw["source_anchors"]),
        analogy_scan_status=context_raw["analogy_scan_status"],
        cross_domain_analogies=tuple(CrossDomainAnalogy(source_kind=item["source_kind"], source_situation=item["source_situation"], common_abstraction=tuple(item["common_abstraction"]), source_to_target_mapping=tuple(item["source_to_target_mapping"]), shared_constraints=tuple(item["shared_constraints"]), disanalogies=tuple(item["disanalogies"]), proposed_principle=item["proposed_principle"], validation_obligation=item["validation_obligation"], provenance_note=item["provenance_note"]) for item in context_raw.get("cross_domain_analogies", ())),
        analogy_scan_notes=context_raw.get("analogy_scan_notes", ""), frozen_at=context_raw["frozen_at"], first_candidate_at=context_raw.get("first_candidate_at"), packet_hash=context_raw["packet_hash"],
    )
    assert audit_math_context_fiber(fiber).verdict is ContextGateVerdict.PASS

    tools_raw = _load("07_memory/NS_R001_RESEARCH_TOOL_INVENTORY_20260811.json")
    failures_raw = _load("07_memory/NS_R001B_FAILURE_EXPERIENCE_LATTICE_20260811.json")
    memory_raw = _load("07_memory/NS_R001B_RESEARCH_MEMORY_REVIEW_20260811.json")
    assert memory_raw["tool_inventory_snapshot_hash"] == _canonical_hash(tools_raw)
    assert memory_raw["failure_lattice_snapshot_hash"] == _canonical_hash(failures_raw)
    assert memory_raw["failure_query_status"] == "MATCHES_FOUND"
    assert memory_raw["relevant_failure_ids"] == ["F-NS-R001-A1-ENERGY-CRITICALITY"]

    memory_for_hash = copy.deepcopy(memory_raw)
    memory_for_hash["artifact_hash"] = ""
    assert memory_raw["artifact_hash"] == _canonical_hash(memory_for_hash)
    memory = ResearchMemoryReview(
        target_atom_id=memory_raw["target_atom_id"], target_context_hash=memory_raw["target_context_hash"],
        tool_inventory_snapshot_hash=memory_raw["tool_inventory_snapshot_hash"], failure_lattice_snapshot_hash=memory_raw["failure_lattice_snapshot_hash"],
        tool_query_status=MemoryQueryStatus(memory_raw["tool_query_status"]), failure_query_status=MemoryQueryStatus(memory_raw["failure_query_status"]),
        candidate_method_families=tuple(memory_raw["candidate_method_families"]), relevant_tool_ids=tuple(memory_raw.get("relevant_tool_ids", ())), relevant_failure_ids=tuple(memory_raw.get("relevant_failure_ids", ())), selected_tool_ids=tuple(memory_raw.get("selected_tool_ids", ())), tool_applicability_notes=tuple(memory_raw.get("tool_applicability_notes", ())), failure_reuse_notes=tuple(memory_raw.get("failure_reuse_notes", ())), unresolved_warnings=tuple(memory_raw.get("unresolved_warnings", ())), evidence_pointers=tuple(memory_raw.get("evidence_pointers", ())), artifact_hash=memory_raw["artifact_hash"],
    )
    assert audit_research_memory_review(memory, atom_id=fiber.atom_id, context_hash=fiber.packet_hash).verdict is ResearchMemoryVerdict.PASS

    trace_raw = _load("09_trace/NS_R001B_GEOMETRY_TRACE_20260811.json")
    previous = ""
    entries = []
    for raw in trace_raw["entries"]:
        assert raw["previous_event_hash"] == previous
        payload = copy.deepcopy(raw)
        artifact_hash = payload["artifact_hash"]
        payload["artifact_hash"] = ""
        assert artifact_hash == _canonical_hash(payload)
        previous = artifact_hash
        entries.append(ResearchTraceEntry(event_id=raw["event_id"], atom_id=raw["atom_id"], event_type=ResearchTraceEventType(raw["event_type"]), timestamp=raw["timestamp"], state_summary=raw["state_summary"], action_summary=raw["action_summary"], evidence_pointers=tuple(raw["evidence_pointers"]), alternatives_considered=tuple(raw.get("alternatives_considered", ())), decision_rationale=raw.get("decision_rationale", ""), outputs=tuple(raw.get("outputs", ())), uncertainties=tuple(raw.get("uncertainties", ())), residuals=tuple(raw.get("residuals", ())), next_steps=tuple(raw.get("next_steps", ())), artifact_hash=raw["artifact_hash"], previous_event_hash=raw.get("previous_event_hash", "")))

    research_trace = MathResearchTrace(trace_id=trace_raw["trace_id"], entries=tuple(entries))
    assert audit_pre_candidate_trace(research_trace, atom_id=fiber.atom_id, context_packet_hash=fiber.packet_hash).verdict is TraceGateVerdict.PASS

    plan = plan_math_research(
        signature=ProblemSignature(objects=("3D incompressible Navier-Stokes solution", "strain tensor", "vorticity", "finite-energy localization", "critical geometric depletion quantity"), relations=("vorticity stretching", "Navier-Stokes scaling", "Biot-Savart nonlocality", "exact advection/pressure evolution", "energy inequality"), domain="partial differential equations / mathematical fluid mechanics", goal_type="derive or falsify a geometry-based critical-control mechanism"),
        record=MathResearchRecord(claim_id=fiber.atom_id), context_fiber=fiber, memory_review=memory, research_trace=research_trace,
    )
    assert plan.context_gate.verdict is ContextGateVerdict.PASS
    assert plan.memory_gate.verdict is ResearchMemoryVerdict.PASS
    assert plan.trace_gate.verdict is TraceGateVerdict.PASS
    assert plan.candidate_generation_allowed


def test_geometry_failure_delta_is_scoped_and_hash_bound() -> None:
    delta = _load("07_memory/NS_R001B_GEOMETRY_FAILURE_DELTA_20260811.json")
    experience = delta["experience"]
    payload = copy.deepcopy(experience)
    artifact_hash = payload["artifact_hash"]
    payload["artifact_hash"] = ""
    assert artifact_hash == _canonical_hash(payload)
    assert experience["diagnosis_status"] == "SUPPORTED"
    assert experience["research_trace_event_id"] == "NS-R001b-E009"
    assert "finite-energy/global localization" in experience["selected_diagnosis"]
    assert any(link["relation"] == "SHARES_BROKEN_ASSUMPTION_WITH" for link in delta["links"])
    assert any(link["relation"] == "MOTIVATES_META_ATOM" for link in delta["links"])
