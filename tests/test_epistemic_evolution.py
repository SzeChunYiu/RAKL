import pytest

from rakl.epistemic_evolution import (
    EvolutionSurface,
    FrameworkVariantCard,
    InferentialState,
    QoIInference,
    TournamentDecision,
    TournamentEvidence,
    assess_framework_challenger,
    detect_meta_overfit,
)
from rakl.evolution import EvolutionTrial


def _card(**overrides):
    values = dict(
        variant_id="v2",
        parent_version="v1",
        surfaces_changed=(EvolutionSurface.CLAIM_EVIDENCE_BINDING,),
        triggering_evidence_ids=("failure-1",),
        root_cause_receipt_ids=("root-cause-1",),
        external_inspirations=("AAR:2602.13855",),
        difference_witness_hash="d" * 64,
        hypothesized_gain_qois=("evidence_fidelity",),
        specific_falsifiers=("wrong-evidence rate does not fall on fresh cases",),
        protected_invariants=("experience/search/routing/proposal != scientific authority",),
        motivating_case_ids=("motivate-1",),
        development_case_ids=("dev-1", "dev-2"),
        fresh_assurance_case_ids=("fresh-1", "fresh-2"),
        rollback_variant_id="v1",
        resource_delta=(("model_calls", 0.0),),
        frozen_before_fresh_assurance=True,
    )
    values.update(overrides)
    return FrameworkVariantCard(**values)


def _trial(**overrides):
    values = dict(
        parent_version="v1",
        child_version="v2",
        development_benchmark_id="dev-benchmark",
        development_improvements={"evidence_fidelity": 0.20},
        assurance_benchmark_id="fresh-benchmark",
        transfer_improvements={"evidence_fidelity": 0.15},
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
    values.update(overrides)
    return EvolutionTrial(**values)


def _evidence(**overrides):
    values = dict(
        trial=_trial(),
        development_inference=(
            QoIInference("evidence_fidelity", InferentialState.DISTINGUISHABLE_BENEFIT, 0.20),
            QoIInference("authority_leakage", InferentialState.MEASURED_BUT_INDISTINGUISHABLE, 0.0, hard_protected=True),
        ),
        fresh_assurance_inference=(
            QoIInference("evidence_fidelity", InferentialState.DISTINGUISHABLE_BENEFIT, 0.15),
            QoIInference("authority_leakage", InferentialState.MEASURED_BUT_INDISTINGUISHABLE, 0.0, hard_protected=True),
        ),
        regression_atlas_passed=True,
        resource_only_gain=False,
        history_preserved=True,
        competitor_or_parent_control_bound=True,
    )
    values.update(overrides)
    return TournamentEvidence(**values)


def test_clean_fresh_generalization_is_only_promotion_eligible_not_self_promotion():
    result = assess_framework_challenger(_card(), _evidence())
    assert result.decision is TournamentDecision.PROMOTE_PARETO_IMPROVEMENT_ELIGIBLE
    assert result.promotion_eligible is True
    assert result.promotes_incumbent is False
    assert result.grants_scientific_authority is False


def test_fresh_assurance_must_not_overlap_motivating_or_development_cases():
    with pytest.raises(ValueError, match="fresh assurance overlaps"):
        _card(fresh_assurance_case_ids=("fresh-1", "dev-2"))
    with pytest.raises(ValueError, match="fresh assurance overlaps"):
        _card(fresh_assurance_case_ids=("fresh-1", "motivate-1"))


def test_competitor_or_literature_inspiration_cannot_replace_root_cause_receipt():
    with pytest.raises(ValueError, match="root-cause receipt"):
        _card(root_cause_receipt_ids=())


def test_hard_authority_regression_rejects_even_with_large_capability_gain():
    evidence = _evidence(
        fresh_assurance_inference=(
            QoIInference("evidence_fidelity", InferentialState.DISTINGUISHABLE_BENEFIT, 0.90),
            QoIInference("authority_leakage", InferentialState.DISTINGUISHABLE_HARM, -0.20, hard_protected=True),
        )
    )
    result = assess_framework_challenger(_card(), evidence)
    assert result.decision is TournamentDecision.REJECT_NONCOMPENSATORY_REGRESSION
    assert result.hard_regression_qois == ("authority_leakage",)


def test_resource_only_gain_is_not_method_evolution():
    result = assess_framework_challenger(_card(), _evidence(resource_only_gain=True))
    assert result.decision is TournamentDecision.REJECT_RESOURCE_ONLY_GAIN


def test_development_win_without_fresh_gain_is_rejected_not_promoted():
    evidence = _evidence(
        fresh_assurance_inference=(
            QoIInference("evidence_fidelity", InferentialState.MEASURED_BUT_INDISTINGUISHABLE, 0.03),
            QoIInference("authority_leakage", InferentialState.MEASURED_BUT_INDISTINGUISHABLE, 0.0, hard_protected=True),
        )
    )
    result = assess_framework_challenger(_card(), evidence)
    assert result.decision is TournamentDecision.REJECT_NO_FRESH_GAIN
    assert result.promotion_eligible is False


def test_fresh_harm_after_development_win_is_meta_overfit():
    evidence = _evidence(
        trial=_trial(transfer_improvements={}, transfer_regressions={"evidence_fidelity": 0.10}),
        fresh_assurance_inference=(
            QoIInference("evidence_fidelity", InferentialState.DISTINGUISHABLE_HARM, -0.10),
        ),
    )
    result = assess_framework_challenger(_card(), evidence)
    assert result.decision is TournamentDecision.REJECT_OVERFIT


def test_underpowered_fresh_assurance_keeps_variant_experimental():
    evidence = _evidence(
        fresh_assurance_inference=(
            QoIInference("evidence_fidelity", InferentialState.UNDERPOWERED, 0.08),
        )
    )
    result = assess_framework_challenger(_card(), evidence)
    assert result.decision is TournamentDecision.KEEP_EXPERIMENTAL


def test_underlying_blind_assurance_contract_is_still_required():
    evidence = _evidence(trial=_trial(assurance_hidden_from_proposer=False))
    result = assess_framework_challenger(_card(), evidence)
    assert result.decision is TournamentDecision.CANNOT_IDENTIFY
    assert result.promotion_eligible is False


def test_regression_atlas_failure_is_noncompensatory():
    result = assess_framework_challenger(_card(), _evidence(regression_atlas_passed=False))
    assert result.decision is TournamentDecision.REJECT_NONCOMPENSATORY_REGRESSION


def test_unbound_strongest_parent_control_keeps_variant_experimental():
    result = assess_framework_challenger(
        _card(),
        _evidence(competitor_or_parent_control_bound=False),
    )
    assert result.decision is TournamentDecision.KEEP_EXPERIMENTAL


def test_partial_fresh_gain_only_licenses_scoped_improvement():
    card = _card(hypothesized_gain_qois=("evidence_fidelity", "search_utility"))
    result = assess_framework_challenger(card, _evidence())
    assert result.decision is TournamentDecision.PROMOTE_SCOPED_IMPROVEMENT_ELIGIBLE


def test_posthoc_challenger_mutation_is_invalid():
    result = assess_framework_challenger(
        _card(frozen_before_fresh_assurance=False),
        _evidence(),
    )
    assert result.decision is TournamentDecision.INVALID


def test_unknown_fresh_inference_blocks_identification():
    evidence = _evidence(
        fresh_assurance_inference=(
            QoIInference("evidence_fidelity", InferentialState.CANNOT_IDENTIFY),
        )
    )
    result = assess_framework_challenger(_card(), evidence)
    assert result.decision is TournamentDecision.CANNOT_IDENTIFY


def test_repeated_development_wins_that_fail_fresh_assurance_trigger_meta_overfit():
    first = assess_framework_challenger(
        _card(variant_id="v2"),
        _evidence(),
    )
    # Make the first one a failure despite dev gain.
    first = assess_framework_challenger(
        _card(variant_id="v2"),
        _evidence(
            fresh_assurance_inference=(
                QoIInference("evidence_fidelity", InferentialState.MEASURED_BUT_INDISTINGUISHABLE, 0.01),
            )
        ),
    )
    second = assess_framework_challenger(
        _card(variant_id="v3"),
        _evidence(
            trial=_trial(child_version="v3"),
            fresh_assurance_inference=(
                QoIInference("evidence_fidelity", InferentialState.DISTINGUISHABLE_HARM, -0.05),
            ),
        ),
    )
    report = detect_meta_overfit((('v2', first), ('v3', second)), minimum_promising_epochs=2)
    assert report.meta_overfit is True
    assert report.development_promising_epochs == 2
    assert report.fresh_failure_epochs == 2
    assert report.grants_scientific_authority is False
