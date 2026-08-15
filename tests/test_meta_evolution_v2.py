from __future__ import annotations

import json
from pathlib import Path

from rakl.evolution import EvolutionVerdict
from rakl.mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict
from rakl.meta_evolution import CandidateDelta, EvolutionLayer, SelfEvolutionAction
from rakl.meta_evolution_v2 import (
    BlockingValidity,
    ContextualMutationCredit,
    ContextualMutationPolicy,
    DiagnosisBoundEvolutionPortrait,
    FailureEpochIdentity,
    OuterAssuranceBinding,
    ValidatedCandidateDelta,
    assess_mutation_governance_v2,
    plan_self_evolution_v2,
    update_contextual_mutation_policy,
    validity_gated_pareto_frontier,
)


_BENCHMARK = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "self_rakl_p4_p6_question_saturation_v2"
    / "META_EVOLUTION_V2_FROZEN_BENCHMARK.json"
)


def _cases() -> dict[str, dict[str, object]]:
    packet = json.loads(_BENCHMARK.read_text(encoding="utf-8"))
    assert packet["status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    return {case["id"]: case for case in packet["cases"]}


def _portrait(case: dict[str, object]) -> DiagnosisBoundEvolutionPortrait:
    return DiagnosisBoundEvolutionPortrait(
        diagnosis_verdict=MechanicDiagnosisVerdict(case["diagnosis_verdict"]),
        causes=tuple(MechanicCause(value) for value in case["causes"]),
        discriminator_ids=tuple(case.get("discriminator_ids", ())),
        stagnant=bool(case.get("stagnant", True)),
        failure_epochs=tuple(
            FailureEpochIdentity(epoch_id=epoch_id, family_id=family_id)
            for epoch_id, family_id in case.get("failure_epochs", ())
        ),
    )


def test_discriminator_required_is_consumed_before_mutation_routing() -> None:
    case = _cases()["MEV2-C1-DISCRIMINATOR-FIRST"]
    plan = plan_self_evolution_v2(_portrait(case))

    assert plan.action is SelfEvolutionAction.RUN_DISCRIMINATOR
    assert plan.target_layers == ()
    assert "registered_discriminator_required_before_mutation" in plan.reasons


def test_identified_single_cause_routes_to_the_registered_layer() -> None:
    case = _cases()["MEV2-C2-IDENTIFIED-MUTATES"]
    plan = plan_self_evolution_v2(_portrait(case))

    assert plan.action is SelfEvolutionAction.PROPOSE_MUTATION
    assert tuple(layer.value for layer in plan.target_layers) == tuple(case["expected_target_layers"])


def _outer(case: dict[str, object]) -> OuterAssuranceBinding:
    raw = case["outer_assurance"]
    return OuterAssuranceBinding(
        assurance_id=raw["assurance_id"],
        subject_sha=raw["subject_sha"],
        evaluator_id=raw["evaluator_id"],
        benchmark_hash=raw["benchmark_hash"],
        frozen_before_candidate_outcome=raw["frozen_before_candidate_outcome"],
        candidate_outcomes_used_to_define_evaluator=raw[
            "candidate_outcomes_used_to_define_evaluator"
        ],
    )


def test_same_target_evaluator_cannot_serve_as_outer_assurance() -> None:
    case = _cases()["MEV2-C3-SAME-EVALUATOR-NOT-OUTER"]
    assessment = assess_mutation_governance_v2(
        target_layer=EvolutionLayer(case["target_layer"]),
        target_evaluator_id=case["target_evaluator_id"],
        candidate_subject_sha=case["outer_assurance"]["subject_sha"],
        outer_assurance=_outer(case),
    )

    assert assessment.eligible_for_auto_promotion is False
    assert assessment.requires_outer_assurance is True
    assert "target_evaluator_cannot_be_its_own_outer_assurance" in assessment.reasons


def test_postoutcome_outer_assurance_is_rejected() -> None:
    case = _cases()["MEV2-C4-POSTOUTCOME-OUTER-REJECTED"]
    assessment = assess_mutation_governance_v2(
        target_layer=EvolutionLayer(case["target_layer"]),
        target_evaluator_id=case["target_evaluator_id"],
        candidate_subject_sha=case["outer_assurance"]["subject_sha"],
        outer_assurance=_outer(case),
    )

    assert assessment.eligible_for_auto_promotion is False
    assert "outer_assurance_not_frozen_before_candidate_outcome" in assessment.reasons


def test_fresh_identity_separated_outer_assurance_can_enter_protected_gate() -> None:
    case = _cases()["MEV2-C5-FRESH-OUTER-ADMITTED"]
    assessment = assess_mutation_governance_v2(
        target_layer=EvolutionLayer(case["target_layer"]),
        target_evaluator_id=case["target_evaluator_id"],
        candidate_subject_sha=case["outer_assurance"]["subject_sha"],
        outer_assurance=_outer(case),
    )

    assert assessment.eligible_for_auto_promotion is True
    assert assessment.requires_outer_assurance is True
    assert assessment.grants_scientific_authority is False


def test_mutation_credit_is_contextual_not_global() -> None:
    case = _cases()["MEV2-C6-CREDIT-STAYS-IN-SCOPE"]
    credited_scope = case["credited_scope"]
    unrelated_scope = case["unrelated_scope"]
    initial = float(case["initial_weight"])
    policy = ContextualMutationPolicy(
        (
            ContextualMutationCredit(
                operator_id=case["operator_id"],
                target_layer=EvolutionLayer.REPRESENTATION,
                scope_key=credited_scope,
                weight=initial,
            ),
            ContextualMutationCredit(
                operator_id=case["operator_id"],
                target_layer=EvolutionLayer.SEARCH_OPERATOR,
                scope_key=unrelated_scope,
                weight=initial,
            ),
        )
    )

    updated = update_contextual_mutation_policy(
        policy,
        operator_id=case["operator_id"],
        target_layer=EvolutionLayer.REPRESENTATION,
        scope_key=credited_scope,
        outcome=EvolutionVerdict(case["outcome"]),
    )

    assert updated.weight_for(
        operator_id=case["operator_id"],
        target_layer=EvolutionLayer.REPRESENTATION,
        scope_key=credited_scope,
    ) > initial
    assert updated.weight_for(
        operator_id=case["operator_id"],
        target_layer=EvolutionLayer.SEARCH_OPERATOR,
        scope_key=unrelated_scope,
    ) == initial


def test_duplicate_failure_family_does_not_open_topology() -> None:
    case = _cases()["MEV2-C7-DUPLICATE-FAILURES-DO-NOT-ESCALATE"]
    plan = plan_self_evolution_v2(_portrait(case))
    values = {layer.value for layer in plan.target_layers}

    assert set(case["expected_contains"]) <= values
    assert set(case["expected_excludes"]).isdisjoint(values)


def test_three_distinct_failure_families_can_open_topology() -> None:
    case = _cases()["MEV2-C8-DISTINCT-FAILURES-CAN-ESCALATE"]
    plan = plan_self_evolution_v2(_portrait(case))
    values = {layer.value for layer in plan.target_layers}

    assert set(case["expected_contains"]) <= values


def test_blocking_invalid_and_unknown_candidates_are_excluded_before_pareto() -> None:
    case = _cases()["MEV2-C9-HARD-INVALID-EXCLUDED"]
    items = []
    for raw in case["candidates"]:
        validity = BlockingValidity(raw["blocking_validity"])
        items.append(
            ValidatedCandidateDelta(
                candidate=CandidateDelta(
                    candidate_id=raw["id"],
                    quality=float(raw["quality"]),
                    cost=float(raw["cost"]),
                    latency=float(raw["latency"]),
                    robustness=float(raw["robustness"]),
                    complexity=float(raw["complexity"]),
                ),
                blocking_validity=validity,
                blocking_reasons=()
                if validity is BlockingValidity.PASS
                else ("registered_blocking_gate_not_passed",),
            )
        )

    frontier = validity_gated_pareto_frontier(items)
    assert [item.candidate.candidate_id for item in frontier] == case["expected_frontier"]
    assert {item["id"] for item in case["candidates"]} - {
        item.candidate.candidate_id for item in frontier
    } >= set(case["expected_excluded"])
