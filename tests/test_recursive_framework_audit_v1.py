"""RFA v1 known-world conformance (frozen benchmark execution).

Every case in ``RFA_V1_FROZEN_BENCHMARK.json`` is executed through BOTH the
production ``rakl.recursive_framework_audit.decide`` and the vendored handoff
reference, and both must emit the frozen ``expected_action``.  Structural
invariants S01–S08 are checked directly.  Passing this suite is conformance
evidence only — not utility evidence for the recursive formulation principle.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from rakl.recursive_framework_audit import (
    AncestorChallenge,
    AuditAction,
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    AtomicityReceipt,
    RecursiveAuditDecision,
    RecursiveAuditProjection,
    audit_before_commit,
    decide,
    metacognitive_gap_candidates,
    request_self_rakl_escalation,
)
from rakl.metacognition import MetacognitiveAuditVerdict, formulation_gap_candidate
from rakl.self_evolution_controller import CURRENT_SELF_EVOLUTION_CONTROLLER

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "research" / "recursive_framework_audit_v1"
BENCHMARK = LANE / "RFA_V1_FROZEN_BENCHMARK.json"
REFERENCE = LANE / "reference" / "recursive_framework_audit_reference.py"
RUNNER = LANE / "run_rfa_v1_conformance.py"
RESULT = LANE / "RFA_V1_CONFORMANCE_RESULT.json"

FLAG_FIELDS = (
    "split_required",
    "merge_required",
    "parent_challenge_supported",
    "distinct_local_repair_families_failed",
    "evaluator_invalid",
    "external_trust_root",
    "resource_bound",
)


def _reference_module():
    spec = importlib.util.spec_from_file_location("rfa_reference", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_residual(case: dict) -> dict:
    """Unify known-world residual dicts and R/H (causes, flags) encodings."""

    residual = dict(case.get("residual", {}))
    if "residual_causes" in case:
        residual["plausible_causes"] = case["residual_causes"]
    for key, value in case.get("residual_flags", {}).items():
        residual[key] = value
    residual.setdefault("plausible_causes", [])
    return residual


def _decide_cases() -> list[tuple[str, dict, dict, str]]:
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    cases: list[tuple[str, dict, dict, str]] = []
    for family in benchmark["known_world_families"]:
        cases.append((family["case_id"], family["node"], _build_residual(family), family["expected_action"]))
    for case in benchmark["reference_conformance_cases"]:
        cases.append((case["case_id"], case["node"], _build_residual(case), case["expected_action"]))
    for case in benchmark["hostile_priority_cases"]:
        cases.append((case["case_id"], case["node"], _build_residual(case), case["expected_action"]))
    assert cases, "frozen benchmark must supply decide cases"
    return cases


def _production_decide(node_spec: dict, residual_spec: dict) -> AuditAction:
    node = AuditNode(
        closure_coordinates_pass=node_spec["closure_coordinates_pass"],
        material_open_residual=node_spec["material_open_residual"],
    )
    residual = AuditResidual(
        plausible_causes=tuple(AuditCoordinate(c) for c in residual_spec["plausible_causes"]),
        **{k: residual_spec[k] for k in FLAG_FIELDS if k in residual_spec},
    )
    return decide(node, residual).action


def _reference_decide(module, node_spec: dict, residual_spec: dict) -> str:
    node = module.Node(
        closure_coordinates_pass=node_spec["closure_coordinates_pass"],
        material_open_residual=node_spec["material_open_residual"],
    )
    residual = module.Residual(
        plausible_causes=tuple(module.Coordinate(c) for c in residual_spec["plausible_causes"]),
        **{k: residual_spec[k] for k in FLAG_FIELDS if k in residual_spec},
    )
    return module.decide(node, residual).action.value


# Pinned raw-input divergences between production and the vendored reference.
# The reference checks ``len(causes) == 1`` literally, so a duplicated
# coordinate bypasses its single-cause branch; production canonicalizes
# duplicates at AuditResidual construction (benchmark H07: "repeated identical
# cause is one responsibility level").  On canonical inputs both are
# action-identical everywhere.
CANONICAL_DIVERGENCES = {
    "H07_duplicate_causes_dedup": "reference literal len==1 misses duplicated single cause; production canonicalizes",
}


@pytest.mark.parametrize(("case_id", "node_spec", "residual_spec", "expected"), _decide_cases())
def test_frozen_case_matches_expected_and_vendored_reference(
    case_id: str, node_spec: dict, residual_spec: dict, expected: str
) -> None:
    production = _production_decide(node_spec, residual_spec).value
    assert production == expected, f"{case_id}: production emitted {production}"
    canonical = {**residual_spec, "plausible_causes": list(dict.fromkeys(residual_spec["plausible_causes"]))}
    reference = _reference_decide(_reference_module(), node_spec, canonical)
    assert production == reference, f"{case_id}: production/reference divergence ({production} vs {reference})"
    if case_id not in CANONICAL_DIVERGENCES:
        raw_reference = _reference_decide(_reference_module(), node_spec, residual_spec)
        assert production == raw_reference, (
            f"{case_id}: unpinned production/reference divergence ({production} vs {raw_reference})"
        )


def test_benchmark_frozen_before_execution_and_claims_no_authority() -> None:
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    assert benchmark["status"] == "FROZEN_BEFORE_EXECUTION"
    assert benchmark["authority"] == "KNOWN_WORLD_CONFORMANCE_ONLY"
    assert len(benchmark["known_world_families"]) == 11
    assert len(benchmark["reference_conformance_cases"]) == 14
    assert len(benchmark["hostile_priority_cases"]) == 12
    assert len(benchmark["structural_invariant_checks"]) == 8


# ---------------------------------------------------------------------------
# Structural invariants S01–S08
# ---------------------------------------------------------------------------


def test_s01_atomicity_terminal_rejects_forever() -> None:
    receipt = AtomicityReceipt(
        target_id="atom-x",
        split_family="regime-split",
        evaluator_epoch="EV-1",
        evidence_cutoff="2026-08-15",
    )
    assert receipt.terminal == "PROVISIONALLY_ATOMIC_AT_REGISTERED_CUTOFF"
    with pytest.raises(ValueError, match="ATOM_PROVEN_FOREVER"):
        AtomicityReceipt(
            target_id="atom-x",
            split_family="regime-split",
            evaluator_epoch="EV-1",
            evidence_cutoff="2026-08-15",
            terminal="ATOM_PROVEN_FOREVER",
        )


def test_s02_atomicity_is_index_relative() -> None:
    base = dict(
        target_id="atom-x",
        split_family="regime-split",
        evaluator_epoch="EV-1",
        evidence_cutoff="2026-08-15",
    )
    receipt = AtomicityReceipt(**base)
    other = AtomicityReceipt(**{**base, "evaluator_epoch": "EV-2"})
    assert receipt != other
    assert not receipt.valid_for("atom-x", "regime-split", "EV-2", "2026-08-15")
    assert not other.valid_for("atom-x", "regime-split", "EV-1", "2026-08-15")
    assert receipt.valid_for("atom-x", "regime-split", "EV-1", "2026-08-15")


def test_s03_supersession_stales_descendants_and_preserves_evidence() -> None:
    challenge = AncestorChallenge(
        ancestor_fiber_id="fiber-parent",
        challenge_evidence_digest="digest-abc",
        failed_local_repair_families=("interface-repair", "measurement-revision"),
        dependent_descendant_ids=("fiber-child-1", "fiber-child-2"),
    )
    assert challenge.admissible_for_ascent
    assert not challenge.descendant_closure_stale("fiber-child-1")
    registered = challenge.with_supersession()
    assert registered.descendant_closure_stale("fiber-child-1")
    assert registered.descendant_closure_stale("fiber-child-2")
    assert not registered.descendant_closure_stale("fiber-unrelated")
    # Negative history stays addressable: evidence digest survives supersession.
    assert registered.challenge_evidence_digest == challenge.challenge_evidence_digest


def test_s04_evaluator_change_closes_epoch() -> None:
    epoch_1 = RecursiveAuditProjection(fiber_id="f", evaluator_epoch="EV-1")
    epoch_2 = RecursiveAuditProjection(fiber_id="f", evaluator_epoch="EV-2")
    same = RecursiveAuditProjection(fiber_id="f", evaluator_epoch="EV-1", material_open_residual=False)
    assert epoch_1.epoch_id != epoch_2.epoch_id
    assert epoch_1.same_epoch(epoch_2) is False
    assert epoch_1.same_epoch(same) is True
    ungrounded = RecursiveAuditProjection(fiber_id="f").same_epoch(epoch_1)
    assert ungrounded is None  # no cross-epoch comparison offered


def test_s05_every_decision_and_receipt_is_non_sovereign() -> None:
    for case_id, node_spec, residual_spec, _ in _decide_cases():
        decision = _decide_via_production(node_spec, residual_spec)
        assert decision.grants_scientific_authority is False, case_id
        assert decision.grants_method_promotion_authority is False, case_id
    for receipt in (
        AtomicityReceipt("t", "sf", "EV", "2026-08-15"),
        RecursiveAuditProjection(fiber_id="f"),
    ):
        assert receipt.grants_scientific_authority is False
        assert receipt.grants_method_promotion_authority is False


def _decide_via_production(node_spec: dict, residual_spec: dict) -> RecursiveAuditDecision:
    node = AuditNode(
        closure_coordinates_pass=node_spec["closure_coordinates_pass"],
        material_open_residual=node_spec["material_open_residual"],
    )
    residual = AuditResidual(
        plausible_causes=tuple(AuditCoordinate(c) for c in residual_spec["plausible_causes"]),
        **{k: residual_spec[k] for k in FLAG_FIELDS if k in residual_spec},
    )
    return decide(node, residual)


def test_s06_decide_is_pure_function_of_node_and_residual() -> None:
    node = AuditNode(closure_coordinates_pass=False, material_open_residual=True)
    residual = AuditResidual(plausible_causes=(AuditCoordinate.QUESTION,))
    first = decide(node, residual)
    second = decide(node, residual)
    assert first == second
    assert decide(AuditNode(), AuditResidual()).action is AuditAction.SOLVE_CURRENT


def test_s07_escalation_cannot_bypass_controller() -> None:
    decision = decide(
        AuditNode(closure_coordinates_pass=False, material_open_residual=True),
        AuditResidual(plausible_causes=(AuditCoordinate.METHOD,)),
    )
    request = request_self_rakl_escalation(decision, evidence_digest="digest")
    assert request.controller_version == CURRENT_SELF_EVOLUTION_CONTROLLER.version
    assert request.controller_grants_scientific_authority is False
    assert request.controller_grants_method_promotion_authority is False
    assert request.grants_scientific_authority is False
    assert request.grants_method_promotion_authority is False
    assert request.enters_existing_challenger_protocol is True


def test_s08_audit_before_commit_three_branches() -> None:
    from rakl.recursive_framework_audit import FrameworkCandidate, ProblemStatement, QuestionFormulationCandidate

    clean = ProblemStatement(
        problem_id="p1",
        question_candidates=(QuestionFormulationCandidate("q1", "What is X?"),),
        evaluator_epoch="EV-1",
    )
    assert audit_before_commit(clean).action is AuditAction.SOLVE_CURRENT

    divergent = ProblemStatement(
        problem_id="p2",
        question_candidates=(
            QuestionFormulationCandidate("q1", "What is X?"),
            QuestionFormulationCandidate("q2", "What is Y?"),
        ),
        evaluator_epoch="EV-1",
    )
    assert audit_before_commit(divergent).action is AuditAction.RUN_DISCRIMINATOR

    divergent_frameworks = ProblemStatement(
        problem_id="p3",
        question_candidates=(QuestionFormulationCandidate("q1", "What is X?"),),
        framework_candidates=(
            FrameworkCandidate("fw-1", licensed_scope="regime A"),
            FrameworkCandidate("fw-2", licensed_scope="regime B"),
        ),
        evaluator_epoch="EV-1",
    )
    assert audit_before_commit(divergent_frameworks).action is AuditAction.RUN_DISCRIMINATOR

    invalid = ProblemStatement(
        problem_id="p4",
        question_candidates=(QuestionFormulationCandidate("q1", "What is X?"),),
        evaluator_epoch="EV-1",
        evaluator_validated=False,
    )
    assert audit_before_commit(invalid).action is AuditAction.AUDIT_EVALUATOR


def test_metacognitive_gap_candidates_cover_all_coordinates_and_fail_closed() -> None:
    for coordinate in AuditCoordinate:
        assert formulation_gap_candidate(coordinate) is not MetacognitiveAuditVerdict.CANNOT_CHECK
    assert formulation_gap_candidate("NOT_A_COORDINATE") is MetacognitiveAuditVerdict.CANNOT_CHECK
    residual = AuditResidual(
        plausible_causes=(AuditCoordinate.METHOD, AuditCoordinate.QUESTION, AuditCoordinate.METHOD),
    )
    candidates = metacognitive_gap_candidates(residual)
    assert candidates == (
        MetacognitiveAuditVerdict.METHOD_BASIS_GAP_CANDIDATE,
        MetacognitiveAuditVerdict.QUESTION_FORMULATION_GAP_CANDIDATE,
    )


def test_duplicate_causes_canonicalized_at_construction_and_reference_pin() -> None:
    residual = AuditResidual(
        plausible_causes=(AuditCoordinate.QUESTION, AuditCoordinate.QUESTION),
    )
    assert residual.plausible_causes == (AuditCoordinate.QUESTION,)
    assert (
        decide(AuditNode(), residual).action is AuditAction.REFRAME_QUESTION
    )  # benchmark H07 semantics

    # The vendored reference's raw-input behavior on duplicates is pinned as a
    # known divergence (its literal len==1 check bypasses the single-cause
    # branch); if this pin breaks, the reference was re-vendored — re-examine.
    module = _reference_module()
    node = module.Node(closure_coordinates_pass=False, material_open_residual=True)
    raw = module.Residual(plausible_causes=(module.Coordinate.QUESTION, module.Coordinate.QUESTION))
    assert module.decide(node, raw).action.value == "SOLVE_CURRENT"


# ---------------------------------------------------------------------------
# Committed conformance result (exact reproduction, no floats)
# ---------------------------------------------------------------------------


def _runner_module():
    spec = importlib.util.spec_from_file_location("rfa_v1_conformance_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_result_reproduces_exactly_and_pins_the_freeze() -> None:
    committed = json.loads(RESULT.read_text(encoding="utf-8"))
    assert committed["status"] == "KNOWN_WORLD_CONFORMANCE_PASS"
    assert committed["benchmark_git_blob_sha"] == "3cdcb8bfe0a38080a6031778a59bc37531655e93"
    assert committed["grants_scientific_authority"] is False
    assert committed["grants_method_promotion_authority"] is False
    assert committed["case_counts"]["total"] == 37
    assert committed["case_counts"]["failures"] == 0

    recomputed = _runner_module().execute()
    assert recomputed == committed  # exact reproduction, Python-version independent


def test_committed_result_contains_no_floats() -> None:
    def walk(node: object) -> None:
        assert not isinstance(node, float), f"float found: {node!r}"
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads(RESULT.read_text(encoding="utf-8")))
