from __future__ import annotations

import pytest

from rakl.challenge_learning import (
    ChallengeLearningCase,
    FailureCause,
    LearningControlVerdict,
    choose_learning_control,
)


def verdict(**kwargs) -> LearningControlVerdict:
    return choose_learning_control(ChallengeLearningCase(**kwargs)).verdict


def test_cl01_high_progress_persists():
    assert verdict(
        outcome_evidence_available=True,
        competence_previous=0.30,
        competence_current=0.50,
        new_discriminating_residual=True,
    ) == LearningControlVerdict.PERSIST_STRATEGY


def test_cl02_flat_repeated_failure_switches():
    assert verdict(
        outcome_evidence_available=True,
        competence_previous=0.20,
        competence_current=0.20,
        repeated_equivalent_failures=3,
    ) == LearningControlVerdict.SWITCH_STRATEGY


def test_cl03_method_gap_seeks_qualified_independent_help():
    report = choose_learning_control(
        ChallengeLearningCase(
            outcome_evidence_available=True,
            failure_cause=FailureCause.METHOD_BASIS_GAP,
            method_basis_gap_supported=True,
            incumbent_operator_available=False,
            independent_help_available=True,
            help_process_independent=True,
            help_lineage_independent=True,
        )
    )
    assert report.verdict == LearningControlVerdict.SEEK_INDEPENDENT_HELP
    assert report.independent_help_credit is True
    assert not report.capability_promotion_authorized


def test_cl04_method_gap_invents_when_no_help_or_incumbent():
    assert verdict(
        outcome_evidence_available=True,
        method_basis_gap_supported=True,
        incumbent_operator_available=False,
    ) == LearningControlVerdict.INVENT_OR_ASSIMILATE_OPERATOR


@pytest.mark.parametrize(
    "cause",
    [FailureCause.EVIDENCE_MISSING, FailureCause.MEASUREMENT_OR_CLOCK_ERROR],
)
def test_cl05_missing_observation_acquires_evidence_not_method(cause):
    assert verdict(
        outcome_evidence_available=True,
        failure_cause=cause,
    ) == LearningControlVerdict.ACQUIRE_EVIDENCE_OR_MEASUREMENT


def test_cl06_implementation_error_repairs_implementation():
    assert verdict(
        outcome_evidence_available=True,
        failure_cause=FailureCause.IMPLEMENTATION_ERROR,
    ) == LearningControlVerdict.REPAIR_IMPLEMENTATION


def test_cl07_productive_failure_runs_discriminator():
    assert verdict(
        outcome_evidence_available=True,
        new_discriminating_residual=True,
        plausible_failure_causes=(
            FailureCause.REPRESENTATION_MISMATCH,
            FailureCause.MODEL_CLASS_MISSPECIFICATION,
        ),
        registered_discriminating_challenge_available=True,
    ) == LearningControlVerdict.RUN_DISCRIMINATING_CHALLENGE


def test_cl08_rumination_stops():
    assert verdict(
        outcome_evidence_available=True,
        reflection_rounds_without_gain=2,
    ) == LearningControlVerdict.STOP_REFLECTION


def test_cl09_skill_regression_reactivates():
    assert verdict(
        outcome_evidence_available=True,
        competence_previous=0.85,
        competence_current=0.55,
        matched_competence_probe=True,
        skill_previously_validated=True,
        environment_or_dependency_changed=True,
    ) == LearningControlVerdict.REACTIVATE_AND_RETEST_SKILL


def test_cl10_mastered_challenge_advances_frontier():
    assert verdict(
        outcome_evidence_available=True,
        competence_previous=0.95,
        competence_current=0.95,
        current_challenge_mastered=True,
    ) == LearningControlVerdict.ADVANCE_CHALLENGE_FRONTIER


def test_cl11_negative_progress_diagnoses_regression():
    assert verdict(
        outcome_evidence_available=True,
        competence_previous=0.80,
        competence_current=0.60,
        matched_competence_probe=True,
    ) == LearningControlVerdict.DIAGNOSE_REGRESSION


def test_cl12_same_context_help_is_not_independent():
    report = choose_learning_control(
        ChallengeLearningCase(
            outcome_evidence_available=True,
            competence_previous=0.25,
            competence_current=0.25,
            repeated_equivalent_failures=2,
            independent_help_available=True,
            help_process_independent=False,
            help_lineage_independent=False,
        )
    )
    assert report.verdict == LearningControlVerdict.SWITCH_STRATEGY
    assert report.independent_help_credit is False


def test_cl13_stochastic_miss_requires_discrimination_not_invention():
    assert verdict(
        outcome_evidence_available=True,
        failure_cause=FailureCause.STOCHASTIC_OR_UNIDENTIFIED,
        registered_discriminating_challenge_available=True,
    ) == LearningControlVerdict.RUN_DISCRIMINATING_CHALLENGE


def test_cl14_no_outcome_cannot_check():
    assert verdict(
        outcome_evidence_available=False,
        method_basis_gap_supported=True,
    ) == LearningControlVerdict.CANNOT_CHECK


def test_cl15_blocking_validity_dominates_gain():
    assert verdict(
        outcome_evidence_available=True,
        competence_previous=0.20,
        competence_current=0.90,
        blocking_validity_failure=True,
    ) == LearningControlVerdict.REPAIR_VALIDITY_FAILURE


def test_cl16_project_failure_routes_dual_residuals():
    assert verdict(
        outcome_evidence_available=True,
        science_residual_present=True,
        method_residual_present=True,
    ) == LearningControlVerdict.ROUTE_SCIENCE_AND_METHOD_RESIDUALS


def test_controller_never_mints_scientific_or_promotion_authority():
    report = choose_learning_control(
        ChallengeLearningCase(
            outcome_evidence_available=True,
            method_basis_gap_supported=True,
            incumbent_operator_available=False,
        )
    )
    assert report.scientific_authority_minted is False
    assert report.capability_promotion_authorized is False


def test_partial_competence_pair_is_rejected():
    with pytest.raises(ValueError, match="must be supplied together"):
        ChallengeLearningCase(
            outcome_evidence_available=True,
            competence_previous=0.5,
        )


def test_competence_outside_unit_interval_rejected():
    with pytest.raises(ValueError, match="within"):
        ChallengeLearningCase(
            outcome_evidence_available=True,
            competence_previous=0.5,
            competence_current=1.1,
        )
