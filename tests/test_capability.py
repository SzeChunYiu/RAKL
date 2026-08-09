from dataclasses import FrozenInstanceError

import pytest

from rakl.capability import (
    CapabilityAttribution,
    CapabilityMetricObservation,
    CapabilityShapingOperator,
    CapabilityTrial,
    CapabilityTrialVerdict,
    MetricDirection,
    MetricKind,
    OperatorVerdict,
    evaluate_capability_shaping,
    validate_capability_operator,
)


def _operator(
    *,
    claimed_attribution: CapabilityAttribution = (
        CapabilityAttribution.DECOMPOSITION_GAIN
    ),
    frozen_before_evaluation: bool | None = True,
    strengths_exploited: tuple[str, ...] = ("rapid_subproblem_generation",),
    weaknesses_targeted: tuple[str, ...] = ("long_horizon_constraint_loss",),
    amplification_mechanisms: tuple[str, ...] = ("atomic_decomposition",),
    compensators: tuple[str, ...] = ("typed_dependency_handoff",),
    verification_oracles: tuple[str, ...] = ("known_answer_tests",),
) -> CapabilityShapingOperator:
    return CapabilityShapingOperator(
        operator_id="cap-op-v1",
        atomic_operation="decomposition",
        strengths_exploited=strengths_exploited,
        weaknesses_targeted=weaknesses_targeted,
        amplification_mechanisms=amplification_mechanisms,
        compensators=compensators,
        verification_oracles=verification_oracles,
        handoff_contract="typed_atomic_children",
        claimed_attribution=claimed_attribution,
        frozen_before_evaluation=frozen_before_evaluation,
    )


def _metrics(
    *,
    quality_baseline: float = 0.60,
    quality_shaped: float = 0.72,
    failure_baseline: float = 0.30,
    failure_shaped: float = 0.18,
    blocking_baseline: float = 0.0,
    blocking_shaped: float = 0.0,
    cost_baseline: float = 1.0,
    cost_shaped: float = 1.0,
) -> tuple[CapabilityMetricObservation, ...]:
    return (
        CapabilityMetricObservation(
            name="task_success_rate",
            kind=MetricKind.QUALITY,
            direction=MetricDirection.HIGHER_IS_BETTER,
            baseline=quality_baseline,
            shaped=quality_shaped,
        ),
        CapabilityMetricObservation(
            name="target_failure_mode_rate",
            kind=MetricKind.TARGET_FAILURE,
            direction=MetricDirection.LOWER_IS_BETTER,
            baseline=failure_baseline,
            shaped=failure_shaped,
        ),
        CapabilityMetricObservation(
            name="blocking_validity_violation_rate",
            kind=MetricKind.BLOCKING_VALIDITY,
            direction=MetricDirection.LOWER_IS_BETTER,
            baseline=blocking_baseline,
            shaped=blocking_shaped,
            blocking=True,
        ),
        CapabilityMetricObservation(
            name="cost_per_valid_result",
            kind=MetricKind.COST,
            direction=MetricDirection.LOWER_IS_BETTER,
            baseline=cost_baseline,
            shaped=cost_shaped,
        ),
    )


def _trial(**overrides) -> CapabilityTrial:
    values = dict(
        trial_id="trial-v1",
        benchmark_id="SELF_RAKL_RESEARCH_015_FROZEN_BENCHMARK",
        operator=_operator(),
        benchmark_frozen_before_trial=True,
        baseline_model_id="same-model",
        shaped_model_id="same-model",
        baseline_model_config_id="temperature-0",
        shaped_model_config_id="temperature-0",
        baseline_task_packet_id="packet-1",
        shaped_task_packet_id="packet-1",
        baseline_output_contract_id="contract-1",
        shaped_output_contract_id="contract-1",
        baseline_evaluator_id="evaluator-1",
        shaped_evaluator_id="evaluator-1",
        baseline_resource_ids=("search", "python"),
        shaped_resource_ids=("search", "python"),
        resource_delta_declared=False,
        hidden_labels_exposed=False,
        operator_modified_after_outcome_inspection=False,
        claims_independent_review=False,
        review_context_is_independent=None,
        metrics=_metrics(),
    )
    values.update(overrides)
    return CapabilityTrial(**values)


def test_valid_operator_names_strength_weakness_compensator_and_oracle():
    report = validate_capability_operator(_operator())
    assert report.verdict is OperatorVerdict.VALID


def test_strength_without_amplification_mechanism_cannot_be_checked():
    report = validate_capability_operator(_operator(amplification_mechanisms=()))
    assert report.verdict is OperatorVerdict.CANNOT_CHECK
    assert "strength_declared_without_amplification_mechanism" in report.reasons


def test_weakness_without_compensator_cannot_be_checked():
    report = validate_capability_operator(_operator(compensators=()))
    assert report.verdict is OperatorVerdict.CANNOT_CHECK
    assert "weakness_declared_without_compensator" in report.reasons


def test_posthoc_operator_is_rejected():
    report = validate_capability_operator(_operator(frozen_before_evaluation=False))
    assert report.verdict is OperatorVerdict.REJECT


def test_matched_same_resource_gain_can_show_amplification_and_suppression():
    report = evaluate_capability_shaping(_trial())
    assert (
        report.verdict
        is CapabilityTrialVerdict.VALIDATED_AMPLIFICATION_AND_SUPPRESSION
    )
    assert report.activates_default is False
    assert report.establishes_intrinsic_model_improvement is False


def test_failure_suppression_without_quality_gain_is_kept_separate():
    report = evaluate_capability_shaping(
        _trial(
            metrics=_metrics(
                quality_baseline=0.60,
                quality_shaped=0.60,
                failure_baseline=0.30,
                failure_shaped=0.15,
            )
        )
    )
    assert report.verdict is CapabilityTrialVerdict.VALIDATED_FAILURE_SUPPRESSION


def test_decorative_scaffold_with_only_cost_overhead_has_no_gain():
    report = evaluate_capability_shaping(
        _trial(
            metrics=_metrics(
                quality_baseline=0.60,
                quality_shaped=0.60,
                failure_baseline=0.30,
                failure_shaped=0.30,
                cost_baseline=1.0,
                cost_shaped=1.4,
            )
        )
    )
    assert report.verdict is CapabilityTrialVerdict.NO_MEASURED_GAIN
    assert "cost_per_valid_result" in report.worsened_metrics


def test_blocking_regression_dominates_quality_gain():
    report = evaluate_capability_shaping(
        _trial(
            metrics=_metrics(
                quality_baseline=0.60,
                quality_shaped=0.80,
                blocking_baseline=0.0,
                blocking_shaped=0.05,
            )
        )
    )
    assert report.verdict is CapabilityTrialVerdict.BLOCKING_REGRESSION


def test_declared_external_solver_gain_is_system_gain_not_model_gain():
    operator = _operator(
        claimed_attribution=CapabilityAttribution.EXTERNAL_CAPABILITY_SUBSTITUTION
    )
    report = evaluate_capability_shaping(
        _trial(
            operator=operator,
            shaped_resource_ids=("search", "python", "deterministic_solver"),
            resource_delta_declared=True,
        )
    )
    assert report.verdict is CapabilityTrialVerdict.SYSTEM_GAIN_WITH_RESOURCE_DELTA
    assert report.establishes_intrinsic_model_improvement is False


def test_hidden_resource_delta_invalidates_workflow_claim():
    report = evaluate_capability_shaping(
        _trial(
            shaped_resource_ids=("search", "python", "deterministic_solver"),
            resource_delta_declared=False,
        )
    )
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID
    assert "undeclared_external_resource_delta" in report.reasons


def test_resource_delta_cannot_be_called_pure_decomposition_gain():
    report = evaluate_capability_shaping(
        _trial(
            shaped_resource_ids=("search", "python", "deterministic_solver"),
            resource_delta_declared=True,
        )
    )
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID
    assert "resource_delta_incompatible_with_claimed_attribution" in report.reasons


def test_different_base_models_invalidates_same_model_attribution():
    report = evaluate_capability_shaping(_trial(shaped_model_id="stronger-model"))
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID
    assert "base_model_mismatch" in report.reasons


def test_different_task_packet_invalidates_comparison():
    report = evaluate_capability_shaping(
        _trial(shaped_task_packet_id="easier-packet")
    )
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID
    assert "task_packet_mismatch" in report.reasons


def test_hidden_label_exposure_invalidates_trial():
    report = evaluate_capability_shaping(_trial(hidden_labels_exposed=True))
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID


def test_posthoc_operator_adaptation_invalidates_trial():
    report = evaluate_capability_shaping(
        _trial(operator_modified_after_outcome_inspection=True)
    )
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID


def test_same_context_review_cannot_be_labeled_independent():
    report = evaluate_capability_shaping(
        _trial(
            claims_independent_review=True,
            review_context_is_independent=False,
        )
    )
    assert report.verdict is CapabilityTrialVerdict.TRIAL_INVALID
    assert "same_context_review_mislabeled_independent" in report.reasons


def test_unknown_benchmark_freeze_chronology_is_cannot_check():
    report = evaluate_capability_shaping(
        _trial(benchmark_frozen_before_trial=None)
    )
    assert report.verdict is CapabilityTrialVerdict.CANNOT_CHECK


def test_operator_contract_is_immutable():
    operator = _operator()
    with pytest.raises(FrozenInstanceError):
        operator.operator_id = "changed"  # type: ignore[misc]
