import pytest

from rakl.epistemic_evolution import (
    EvolutionSurface,
    FrameworkVariantCard,
    InferentialState,
    QoIInference,
    TournamentDecision,
    TournamentEvidence,
    assess_framework_challenger,
)
from rakl.evolution import EvolutionTrial


def _trial(child="search-v2"):
    return EvolutionTrial(
        parent_version="search-v1",
        child_version=child,
        development_benchmark_id="dev-search",
        development_improvements={"search_utility": 0.20},
        assurance_benchmark_id="fresh-search",
        transfer_improvements={"search_utility": 0.15},
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
        blocking_failures=(),
        assurance_exposure_limit=1,
        assurance_exposures_before_trial=0,
    )


def _search_card(**overrides):
    values = dict(
        variant_id="search-v2",
        parent_version="search-v1",
        surfaces_changed=(EvolutionSurface.RANKING,),
        triggering_evidence_ids=("failure-trajectory-17",),
        root_cause_receipt_ids=("root-cause-17",),
        external_inspirations=("Agentic-R",),
        difference_witness_hash="a" * 64,
        hypothesized_gain_qois=("search_utility",),
        specific_falsifiers=("fresh search utility does not improve",),
        protected_invariants=("retrieval/rank/popularity != evidence",),
        motivating_case_ids=("motivate-17",),
        development_case_ids=("dev-1", "dev-2"),
        fresh_assurance_case_ids=("fresh-1", "fresh-2"),
        rollback_variant_id="search-v1",
        failure_driven_update_ids=("search-policy-update-17",),
        frozen_before_fresh_assurance=True,
    )
    values.update(overrides)
    return FrameworkVariantCard(**values)


def _evidence(**overrides):
    values = dict(
        trial=_trial(),
        development_inference=(
            QoIInference("search_utility", InferentialState.DISTINGUISHABLE_BENEFIT, 0.20),
            QoIInference(
                "authority_leakage",
                InferentialState.MEASURED_BUT_INDISTINGUISHABLE,
                0.0,
                hard_protected=True,
            ),
        ),
        fresh_assurance_inference=(
            QoIInference("search_utility", InferentialState.DISTINGUISHABLE_BENEFIT, 0.15),
            QoIInference(
                "authority_leakage",
                InferentialState.MEASURED_BUT_INDISTINGUISHABLE,
                0.0,
                hard_protected=True,
            ),
        ),
        regression_atlas_passed=True,
        resource_only_gain=False,
        history_preserved=True,
        competitor_or_parent_control_bound=True,
        bound_failure_driven_update_ids=("search-policy-update-17",),
    )
    values.update(overrides)
    return TournamentEvidence(**values)


def test_search_variant_without_failure_driven_update_receipt_is_invalid_at_construction():
    with pytest.raises(ValueError, match="failure-driven policy update receipt"):
        _search_card(failure_driven_update_ids=())


def test_non_search_epistemic_variant_does_not_require_search_policy_update_receipt():
    card = FrameworkVariantCard(
        variant_id="binding-v2",
        parent_version="binding-v1",
        surfaces_changed=(EvolutionSurface.CLAIM_EVIDENCE_BINDING,),
        triggering_evidence_ids=("wrong-evidence-case",),
        root_cause_receipt_ids=("binding-root-cause",),
        external_inspirations=(),
        difference_witness_hash="b" * 64,
        hypothesized_gain_qois=("evidence_fidelity",),
        specific_falsifiers=("wrong-evidence rate does not decrease",),
        protected_invariants=("experience/search/routing/proposal != scientific authority",),
        motivating_case_ids=("m1",),
        development_case_ids=("d1",),
        fresh_assurance_case_ids=("f1",),
        rollback_variant_id="binding-v1",
        frozen_before_fresh_assurance=True,
    )
    assert card.failure_driven_update_ids == ()


def test_search_policy_update_receipt_must_be_exactly_bound_in_tournament_evidence():
    result = assess_framework_challenger(
        _search_card(),
        _evidence(bound_failure_driven_update_ids=()),
    )
    assert result.decision is TournamentDecision.INVALID
    assert "failure_driven_search_policy_update_receipts_not_exactly_bound" in result.reasons


def test_unrelated_failure_update_receipt_cannot_be_substituted():
    result = assess_framework_challenger(
        _search_card(),
        _evidence(bound_failure_driven_update_ids=("different-update",)),
    )
    assert result.decision is TournamentDecision.INVALID
    assert result.promotion_eligible is False


def test_exact_failure_arrow_plus_fresh_gain_can_only_create_promotion_eligibility():
    result = assess_framework_challenger(_search_card(), _evidence())
    assert result.decision is TournamentDecision.PROMOTE_PARETO_IMPROVEMENT_ELIGIBLE
    assert result.promotion_eligible is True
    assert result.promotes_incumbent is False
    assert result.grants_scientific_authority is False


def test_unknown_strongest_control_binding_is_cannot_identify_not_promotion_eligible():
    result = assess_framework_challenger(
        _search_card(),
        _evidence(competitor_or_parent_control_bound=None),
    )
    assert result.decision is TournamentDecision.CANNOT_IDENTIFY
    assert "strongest parent/competitor control binding is unknown" in result.reasons
    assert result.promotion_eligible is False


def test_explicitly_unbound_strongest_control_keeps_variant_experimental():
    result = assess_framework_challenger(
        _search_card(),
        _evidence(competitor_or_parent_control_bound=False),
    )
    assert result.decision is TournamentDecision.KEEP_EXPERIMENTAL
    assert result.promotion_eligible is False


def test_duplicate_failure_driven_receipts_are_rejected():
    with pytest.raises(ValueError, match="failure-driven update ids must be unique"):
        _search_card(
            failure_driven_update_ids=("search-policy-update-17", "search-policy-update-17")
        )


def test_failure_driven_provenance_does_not_override_fresh_assurance_failure():
    evidence = _evidence(
        fresh_assurance_inference=(
            QoIInference(
                "search_utility",
                InferentialState.MEASURED_BUT_INDISTINGUISHABLE,
                0.02,
            ),
            QoIInference(
                "authority_leakage",
                InferentialState.MEASURED_BUT_INDISTINGUISHABLE,
                0.0,
                hard_protected=True,
            ),
        )
    )
    result = assess_framework_challenger(_search_card(), evidence)
    assert result.decision is TournamentDecision.REJECT_NO_FRESH_GAIN
    assert result.promotion_eligible is False
