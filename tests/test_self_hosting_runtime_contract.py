from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

import pytest

from rakl.epistemic_evolution import (
    EvolutionSurface,
    InferentialState,
    QoIInference,
    TournamentEvidence,
)
from rakl.evolution import EvolutionTrial
from rakl.evolution_archive import (
    RAKLVariant,
    VariantStatus,
    initialize_evolution_archive,
)
from rakl.self_hosting_runtime import (
    MechanicMutationSpec,
    SelfHostingDecision,
    assess_resume_readiness,
    evaluate_mechanic_mutation,
    inspect_for_self_hosting,
    register_mechanic_mutation,
)


class Verdict(str, Enum):
    PLAN_READY = "PLAN_READY"
    GOAL_ACHIEVED = "GOAL_ACHIEVED"
    CANNOT_CHECK = "CANNOT_CHECK"
    RESOURCE_BLOCK_NONTERMINAL = "RESOURCE_BLOCK_NONTERMINAL"


@dataclass(frozen=True)
class Plan:
    verdict: Verdict
    reasons: tuple[str, ...]
    round_index: int = 0
    reopen_fiber_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Residual:
    residual_id: str


@dataclass(frozen=True)
class State:
    search_id: str


class Runtime:
    def __init__(self, plan: Plan, residuals=(Residual("r1"),)):
        self._plan = plan
        self._residuals = residuals
        self.search_state = State("search-1")

    def plan_next_round(self):
        return self._plan

    def active_residuals(self):
        return self._residuals


def _archive():
    return initialize_evolution_archive(
        RAKLVariant(
            variant_id="v1",
            method_hash="1" * 64,
            parent_ids=(),
            capability_tags=("baseline",),
            resource_profile=(("model_calls", 10.0),),
            created_by_episode_ids=(),
            status=VariantStatus.INCUMBENT,
        )
    )


def _escalation(parent="v1"):
    runtime = Runtime(
        Plan(
            Verdict.CANNOT_CHECK,
            (
                "all_registered_residual_operator_routes_exhausted_under_current_operator_basis",
                "open_METHOD_BASIS_GAP_CANDIDATE_and_evolve_operator_basis",
            ),
            reopen_fiber_ids=("fiber-1",),
        )
    )
    return inspect_for_self_hosting(
        runtime,
        parent_variant_id=parent,
        triggering_episode_ids=("episode-1",),
    )


def _spec(**overrides):
    values = dict(
        mutation_id="mut-1",
        variant_id="v2",
        parent_variant_id="v1",
        method_hash="2" * 64,
        surface=EvolutionSurface.PLANNING_SEARCH,
        component_kind="search_operator_basis",
        changed_component_ids=("operator-basis",),
        difference_witness_hash="d" * 64,
        hypothesized_gain_qois=("closure_rate",),
        specific_falsifiers=("fresh closure rate does not improve",),
        protected_invariants=("proposal != scientific authority",),
        motivating_case_ids=("m1",),
        development_case_ids=("d1", "d2"),
        fresh_assurance_case_ids=("a1", "a2"),
        capability_tags=("self_hosting",),
        resource_profile=(("model_calls", 10.0),),
        resource_delta=(("model_calls", 0.0),),
    )
    values.update(overrides)
    return MechanicMutationSpec(**values)


def _evidence(root_receipt_id: str, **overrides):
    trial = EvolutionTrial(
        parent_version="v1",
        child_version="v2",
        development_benchmark_id="dev",
        development_improvements={"closure_rate": 0.2},
        assurance_benchmark_id="fresh",
        transfer_improvements={"closure_rate": 0.1},
        transfer_regressions={},
        tests_passed=True,
        receipt_present=True,
        development_benchmark_frozen_before_result=True,
        assurance_benchmark_frozen_before_mutation=True,
        assurance_hidden_from_proposer=True,
        assurance_evaluator_separate=True,
        candidate_identity_verified=True,
        resource_comparability_verified=True,
        history_preserved=True,
        assurance_exposure_limit=1,
        assurance_exposures_before_trial=0,
    )
    values = dict(
        trial=trial,
        development_inference=(
            QoIInference("closure_rate", InferentialState.DISTINGUISHABLE_BENEFIT, 0.2),
        ),
        fresh_assurance_inference=(
            QoIInference("closure_rate", InferentialState.DISTINGUISHABLE_BENEFIT, 0.1),
        ),
        regression_atlas_passed=True,
        resource_only_gain=False,
        history_preserved=True,
        competitor_or_parent_control_bound=True,
        bound_failure_driven_update_ids=(root_receipt_id,),
    )
    values.update(overrides)
    return TournamentEvidence(**values)


def test_plan_ready_never_escalates():
    result = inspect_for_self_hosting(
        Runtime(Plan(Verdict.PLAN_READY, ("normal",))),
        parent_variant_id="v1",
    )
    assert result.decision is SelfHostingDecision.OBJECT_SEARCH_READY
    assert result.receipt is None


def test_resource_exhaustion_never_masquerades_as_method_gap():
    result = inspect_for_self_hosting(
        Runtime(Plan(Verdict.RESOURCE_BLOCK_NONTERMINAL, ("current_search_budget_exhausted",))),
        parent_variant_id="v1",
    )
    assert result.decision is SelfHostingDecision.CANNOT_CHECK
    assert result.receipt is None


def test_exact_operator_basis_dead_end_creates_method_gap_receipt():
    result = _escalation()
    assert result.decision is SelfHostingDecision.ESCALATION_REQUIRED
    assert result.receipt is not None
    assert result.receipt.diagnosis.candidate_causes[0].value == "METHOD_OPERATOR_GAP"
    assert result.receipt.grants_scientific_authority is False
    assert result.receipt.grants_promotion_authority is False


def test_operator_gap_without_residual_identity_fails_closed():
    runtime = Runtime(
        Plan(
            Verdict.CANNOT_CHECK,
            ("all_registered_residual_operator_routes_exhausted_under_current_operator_basis",),
        ),
        residuals=(),
    )
    result = inspect_for_self_hosting(runtime, parent_variant_id="v1")
    assert result.decision is SelfHostingDecision.CANNOT_CHECK


def test_mutation_rejects_stale_parent():
    receipt = _escalation().receipt
    assert receipt is not None
    with pytest.raises(ValueError, match="stale"):
        register_mechanic_mutation(_archive(), receipt, _spec(parent_variant_id="old"))


def test_registered_search_mutation_binds_failure_driven_update_receipt():
    receipt = _escalation().receipt
    assert receipt is not None
    registered = register_mechanic_mutation(_archive(), receipt, _spec())
    assert registered.variant_card.failure_driven_update_ids == (receipt.receipt_id,)
    assert registered.variant_card.root_cause_receipt_ids == (receipt.receipt_id,)
    child = next(v for v in registered.archive.variants if v.variant_id == "v2")
    assert child.status is VariantStatus.CHALLENGER


def test_fresh_assurance_overlap_rejected_before_registration():
    with pytest.raises(ValueError, match="disjoint"):
        _spec(fresh_assurance_case_ids=("d2", "a2"))


def test_tournament_rejection_cannot_reach_archive_assurance():
    receipt = _escalation().receipt
    assert receipt is not None
    registered = register_mechanic_mutation(_archive(), receipt, _spec())
    bad = _evidence(
        receipt.receipt_id,
        fresh_assurance_inference=(
            QoIInference("closure_rate", InferentialState.DISTINGUISHABLE_HARM, -0.1),
        ),
    )
    result = evaluate_mechanic_mutation(registered, bad, trial_id="t1")
    assert result.decision is SelfHostingDecision.CHALLENGER_REJECTED
    child = next(v for v in result.archive.variants if v.variant_id == "v2")
    assert child.status is VariantStatus.REJECTED
    assert result.promotes_incumbent is False


def test_tournament_win_without_protected_assurance_remains_pending():
    receipt = _escalation().receipt
    assert receipt is not None
    registered = register_mechanic_mutation(_archive(), receipt, _spec())
    result = evaluate_mechanic_mutation(
        registered,
        _evidence(receipt.receipt_id),
        trial_id="t2",
    )
    assert result.tournament.promotion_eligible is True
    assert result.decision is SelfHostingDecision.ASSURANCE_PENDING
    assert result.archive.incumbent_id == "v1"
    child = next(v for v in result.archive.variants if v.variant_id == "v2")
    assert child.status is VariantStatus.CHALLENGER


def test_unbound_failure_receipt_is_invalid_at_tournament_boundary():
    receipt = _escalation().receipt
    assert receipt is not None
    registered = register_mechanic_mutation(_archive(), receipt, _spec())
    result = evaluate_mechanic_mutation(
        registered,
        _evidence(receipt.receipt_id, bound_failure_driven_update_ids=()),
        trial_id="t3",
    )
    assert result.decision is SelfHostingDecision.CHALLENGER_REJECTED


def test_resume_requires_governed_incumbent_identity():
    decision, _ = assess_resume_readiness(_archive(), expected_variant_id="v2")
    assert decision is SelfHostingDecision.CANNOT_CHECK

    receipt = _escalation().receipt
    assert receipt is not None
    registered = register_mechanic_mutation(_archive(), receipt, _spec())
    decision, _ = assess_resume_readiness(registered.archive, expected_variant_id="v2")
    assert decision is SelfHostingDecision.GOVERNANCE_PROMOTION_REQUIRED

    variants = tuple(
        replace(v, status=VariantStatus.INCUMBENT if v.variant_id == "v2" else VariantStatus.ASSURED)
        for v in registered.archive.variants
    )
    promoted = replace(registered.archive, variants=variants, incumbent_id="v2")
    decision, _ = assess_resume_readiness(promoted, expected_variant_id="v2")
    assert decision is SelfHostingDecision.RESUME_WITH_INCUMBENT

def test_method_gap_cannot_justify_unrelated_authority_surface():
    with pytest.raises(ValueError, match="search-evolution surface"):
        _spec(surface=EvolutionSurface.CLAIM_EVIDENCE_BINDING)


def test_mutation_hashes_must_be_exact_sha256_shape():
    with pytest.raises(ValueError, match="method_hash"):
        _spec(method_hash="not-a-hash")
    with pytest.raises(ValueError, match="difference_witness_hash"):
        _spec(difference_witness_hash="abc")
