import pytest

from rakl.evolution import (
    AssuranceReserve,
    EvolutionTrial,
    EvolutionVerdict,
    SelfEvolutionAssessor,
)


def clean_trial(**overrides):
    values = dict(
        parent_version="parent",
        child_version="child",
        development_benchmark_id="dev-v1",
        development_improvements={"known_answer_accuracy": 0.10},
        assurance_benchmark_id="assurance-v1",
        transfer_improvements={"known_answer_accuracy": 0.05},
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


def verdict(**overrides):
    return SelfEvolutionAssessor.assess(clean_trial(**overrides))


def test_clean_blind_transfer_supports_scoped_evolution_evidence():
    report = verdict()
    assert report.verdict == EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE
    assert report.supports_scoped_evolution is True
    assert report.assurance_fresh is True


def test_development_gain_without_holdout_is_local_only():
    report = verdict(assurance_benchmark_id=None, transfer_improvements=None)
    assert report.verdict == EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY
    assert report.supports_scoped_evolution is False


def test_transfer_regression_is_meta_overfit():
    report = verdict(transfer_regressions={"authority_leakage": 0.1})
    assert report.verdict == EvolutionVerdict.META_OVERFIT
    assert "authority_leakage" in report.transfer_regression_qois


def test_blocking_failure_cannot_be_compensated_by_large_gain():
    report = verdict(
        development_improvements={"token_efficiency": 100.0},
        transfer_improvements={"token_efficiency": 100.0},
        blocking_failures=("fabricated citation",),
    )
    assert report.verdict == EvolutionVerdict.BLOCKED
    assert any("fabricated citation" in reason for reason in report.reasons)


def test_no_development_gain_is_no_improvement():
    report = verdict(development_improvements={"known_answer_accuracy": 0.0})
    assert report.verdict == EvolutionVerdict.NO_IMPROVEMENT


def test_consumed_assurance_cannot_validate_another_generation():
    report = verdict(assurance_exposures_before_trial=1, assurance_exposure_limit=1)
    assert report.verdict == EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED
    assert report.assurance_fresh is False
    assert any("exposure budget" in reason for reason in report.reasons)


def test_optimizer_controlled_assurance_evaluator_is_not_independent():
    report = verdict(assurance_evaluator_separate=False)
    assert report.verdict == EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED
    assert any("not separate" in reason for reason in report.reasons)


def test_missing_candidate_identity_is_cannot_check():
    report = verdict(candidate_identity_verified=None)
    assert report.verdict == EvolutionVerdict.CANNOT_CHECK
    assert any("candidate identity" in reason for reason in report.reasons)


def test_assurance_not_frozen_before_mutation_is_cannot_check():
    report = verdict(assurance_benchmark_frozen_before_mutation=False)
    assert report.verdict == EvolutionVerdict.CANNOT_CHECK
    assert any("assurance benchmark" in reason for reason in report.reasons)


def test_undeclared_resource_mismatch_is_cannot_check():
    report = verdict(resource_comparability_verified=False)
    assert report.verdict == EvolutionVerdict.CANNOT_CHECK
    assert any("comparability" in reason for reason in report.reasons)


def test_lost_negative_history_blocks_evolution_claim():
    report = verdict(history_preserved=False)
    assert report.verdict == EvolutionVerdict.BLOCKED
    assert any("history" in reason for reason in report.reasons)


def test_fresh_rotated_assurance_can_validate_later_generation():
    report = SelfEvolutionAssessor.assess(
        clean_trial(
            parent_version="generation-4",
            child_version="generation-5",
            assurance_benchmark_id="fresh-assurance-generation-5",
            assurance_exposures_before_trial=0,
        )
    )
    assert report.verdict == EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE


def test_revealed_holdout_only_supports_observed_transfer():
    report = verdict(assurance_hidden_from_proposer=False)
    assert report.verdict == EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED
    assert any("not blind" in reason for reason in report.reasons)


def test_failed_tests_block_even_when_transfer_is_positive():
    report = verdict(tests_passed=False)
    assert report.verdict == EvolutionVerdict.BLOCKED


def test_missing_receipt_blocks_evolution_claim():
    report = verdict(receipt_present=False)
    assert report.verdict == EvolutionVerdict.BLOCKED


def test_unfrozen_development_benchmark_is_cannot_check():
    report = verdict(development_benchmark_frozen_before_result=False)
    assert report.verdict == EvolutionVerdict.CANNOT_CHECK


def test_positive_development_but_zero_transfer_is_local_only():
    report = verdict(transfer_improvements={"known_answer_accuracy": 0.0})
    assert report.verdict == EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY


def test_assurance_reserve_is_consumable_and_never_silently_resets():
    reserve = AssuranceReserve("holdout-A", exposure_limit=1)
    assert reserve.available is True
    assert reserve.remaining_exposures == 1

    used = reserve.consume()
    assert used.available is False
    assert used.remaining_exposures == 0
    assert used.optimizer_visible_exposures == 1

    overused = used.consume()
    assert overused.available is False
    assert overused.optimizer_visible_exposures == 2


def test_assurance_reserve_rejects_invalid_counts():
    with pytest.raises(ValueError):
        AssuranceReserve("", exposure_limit=1)
    with pytest.raises(ValueError):
        AssuranceReserve("x", exposure_limit=0)
    with pytest.raises(ValueError):
        AssuranceReserve("x", optimizer_visible_exposures=-1)
