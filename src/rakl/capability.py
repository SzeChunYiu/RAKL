from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class MetricDirection(str, Enum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"


class MetricKind(str, Enum):
    QUALITY = "QUALITY"
    TARGET_FAILURE = "TARGET_FAILURE"
    BLOCKING_VALIDITY = "BLOCKING_VALIDITY"
    COST = "COST"
    LATENCY = "LATENCY"
    ATTRIBUTION = "ATTRIBUTION"
    OTHER = "OTHER"


class CapabilityAttribution(str, Enum):
    MODEL_UTILIZATION_AMPLIFICATION = "MODEL_UTILIZATION_AMPLIFICATION"
    FAILURE_SUPPRESSION = "FAILURE_SUPPRESSION"
    EXTERNAL_CAPABILITY_SUBSTITUTION = "EXTERNAL_CAPABILITY_SUBSTITUTION"
    SPECIALIST_COMPLEMENTATION = "SPECIALIST_COMPLEMENTATION"
    ROUTING_GAIN = "ROUTING_GAIN"
    DECOMPOSITION_GAIN = "DECOMPOSITION_GAIN"
    MEMORY_EXTERNALIZATION_GAIN = "MEMORY_EXTERNALIZATION_GAIN"
    UNRESOLVED_MIXED_ATTRIBUTION = "UNRESOLVED_MIXED_ATTRIBUTION"


class OperatorVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


class CapabilityTrialVerdict(str, Enum):
    VALIDATED_AMPLIFICATION = "VALIDATED_AMPLIFICATION"
    VALIDATED_FAILURE_SUPPRESSION = "VALIDATED_FAILURE_SUPPRESSION"
    VALIDATED_AMPLIFICATION_AND_SUPPRESSION = (
        "VALIDATED_AMPLIFICATION_AND_SUPPRESSION"
    )
    SYSTEM_GAIN_WITH_RESOURCE_DELTA = "SYSTEM_GAIN_WITH_RESOURCE_DELTA"
    NO_MEASURED_GAIN = "NO_MEASURED_GAIN"
    NONBLOCKING_REGRESSION = "NONBLOCKING_REGRESSION"
    BLOCKING_REGRESSION = "BLOCKING_REGRESSION"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class CapabilityShapingOperator:
    """Frozen contract for one atomic cognitive shaping intervention.

    The operator is descriptive and research-only. It cannot activate a workflow.
    """

    operator_id: str
    atomic_operation: str
    strengths_exploited: Tuple[str, ...]
    weaknesses_targeted: Tuple[str, ...]
    amplification_mechanisms: Tuple[str, ...]
    compensators: Tuple[str, ...]
    verification_oracles: Tuple[str, ...]
    handoff_contract: str
    claimed_attribution: CapabilityAttribution
    frozen_before_evaluation: Optional[bool]
    authority_boundary: str = "support_only_no_auto_promotion"


@dataclass(frozen=True)
class OperatorReport:
    verdict: OperatorVerdict
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class CapabilityMetricObservation:
    name: str
    kind: MetricKind
    direction: MetricDirection
    baseline: float
    shaped: float
    blocking: bool = False
    tolerance: float = 0.0


@dataclass(frozen=True)
class CapabilityTrial:
    """Matched baseline-vs-shaped trial for one capability operator."""

    trial_id: str
    benchmark_id: str
    operator: CapabilityShapingOperator
    benchmark_frozen_before_trial: Optional[bool]
    baseline_model_id: str
    shaped_model_id: str
    baseline_model_config_id: str
    shaped_model_config_id: str
    baseline_task_packet_id: str
    shaped_task_packet_id: str
    baseline_output_contract_id: str
    shaped_output_contract_id: str
    baseline_evaluator_id: str
    shaped_evaluator_id: str
    baseline_resource_ids: Tuple[str, ...]
    shaped_resource_ids: Tuple[str, ...]
    resource_delta_declared: Optional[bool]
    hidden_labels_exposed: Optional[bool]
    operator_modified_after_outcome_inspection: Optional[bool]
    claims_independent_review: bool
    review_context_is_independent: Optional[bool]
    metrics: Tuple[CapabilityMetricObservation, ...]


@dataclass(frozen=True)
class CapabilityTrialReport:
    verdict: CapabilityTrialVerdict
    attribution: CapabilityAttribution
    improved_metrics: Tuple[str, ...]
    worsened_metrics: Tuple[str, ...]
    unchanged_metrics: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def activates_default(self) -> bool:
        """Evaluation support never promotes a workflow by itself."""
        return False

    @property
    def establishes_intrinsic_model_improvement(self) -> bool:
        """RAKL does not infer weight-level model improvement from workflow trials."""
        return False


def validate_capability_operator(
    operator: CapabilityShapingOperator,
) -> OperatorReport:
    missing: list[str] = []
    for name, value in (
        ("operator_id", operator.operator_id),
        ("atomic_operation", operator.atomic_operation),
        ("handoff_contract", operator.handoff_contract),
        ("authority_boundary", operator.authority_boundary),
    ):
        if not value:
            missing.append(f"{name}_missing")

    if missing:
        return OperatorReport(OperatorVerdict.CANNOT_CHECK, tuple(missing))

    if operator.frozen_before_evaluation is None:
        return OperatorReport(
            OperatorVerdict.CANNOT_CHECK,
            ("operator_freeze_chronology_unknown",),
        )
    if operator.frozen_before_evaluation is False:
        return OperatorReport(
            OperatorVerdict.REJECT,
            ("operator_modified_or_defined_after_evaluation",),
        )

    if not operator.strengths_exploited and not operator.weaknesses_targeted:
        return OperatorReport(
            OperatorVerdict.REJECT,
            ("no_declared_capability_target",),
        )

    if operator.strengths_exploited and not operator.amplification_mechanisms:
        return OperatorReport(
            OperatorVerdict.CANNOT_CHECK,
            ("strength_declared_without_amplification_mechanism",),
        )

    if operator.weaknesses_targeted and not operator.compensators:
        return OperatorReport(
            OperatorVerdict.CANNOT_CHECK,
            ("weakness_declared_without_compensator",),
        )

    if not operator.verification_oracles:
        return OperatorReport(
            OperatorVerdict.CANNOT_CHECK,
            ("verification_oracle_missing",),
        )

    return OperatorReport(
        OperatorVerdict.VALID,
        (
            "atomic_operation_declared",
            "capability_targets_declared",
            "amplification_or_compensation_mechanisms_declared",
            "verification_oracle_declared",
            "handoff_contract_declared",
            "operator_frozen_before_evaluation",
            "support_only_authority_boundary",
        ),
    )


def _metric_state(metric: CapabilityMetricObservation) -> str:
    delta = metric.shaped - metric.baseline
    if abs(delta) <= metric.tolerance:
        return "unchanged"

    if metric.direction is MetricDirection.HIGHER_IS_BETTER:
        return "improved" if delta > 0 else "worsened"
    return "improved" if delta < 0 else "worsened"


def evaluate_capability_shaping(
    trial: CapabilityTrial,
) -> CapabilityTrialReport:
    """Evaluate one frozen capability-shaping trial fail-closed.

    This function classifies evidence. It cannot promote the operator or alter
    routing. Resource additions are kept distinct from same-resource workflow
    gains so system capability is not misreported as intrinsic model capability.
    """

    operator_report = validate_capability_operator(trial.operator)
    if operator_report.verdict is OperatorVerdict.REJECT:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("operator_contract_rejected", *operator_report.reasons),
        )
    if operator_report.verdict is OperatorVerdict.CANNOT_CHECK:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.CANNOT_CHECK,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("operator_contract_incomplete", *operator_report.reasons),
        )

    if trial.benchmark_frozen_before_trial is None:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.CANNOT_CHECK,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("benchmark_freeze_chronology_unknown",),
        )
    if trial.benchmark_frozen_before_trial is False:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("benchmark_not_frozen_before_trial",),
        )

    if trial.hidden_labels_exposed is None:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.CANNOT_CHECK,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("hidden_label_exposure_status_unknown",),
        )
    if trial.hidden_labels_exposed:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("hidden_labels_or_expected_outcomes_exposed",),
        )

    if trial.operator_modified_after_outcome_inspection is None:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.CANNOT_CHECK,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("operator_modification_chronology_unknown",),
        )
    if trial.operator_modified_after_outcome_inspection:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("posthoc_operator_adaptation",),
        )

    matched_contract_checks = (
        ("base_model", trial.baseline_model_id, trial.shaped_model_id),
        (
            "model_configuration",
            trial.baseline_model_config_id,
            trial.shaped_model_config_id,
        ),
        (
            "task_packet",
            trial.baseline_task_packet_id,
            trial.shaped_task_packet_id,
        ),
        (
            "output_contract",
            trial.baseline_output_contract_id,
            trial.shaped_output_contract_id,
        ),
        ("evaluator", trial.baseline_evaluator_id, trial.shaped_evaluator_id),
    )
    mismatches = tuple(
        f"{name}_mismatch"
        for name, baseline, shaped in matched_contract_checks
        if not baseline or not shaped or baseline != shaped
    )
    if mismatches:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            mismatches,
        )

    if trial.claims_independent_review:
        if trial.review_context_is_independent is None:
            return CapabilityTrialReport(
                CapabilityTrialVerdict.CANNOT_CHECK,
                trial.operator.claimed_attribution,
                (),
                (),
                (),
                ("review_independence_unknown",),
            )
        if trial.review_context_is_independent is False:
            return CapabilityTrialReport(
                CapabilityTrialVerdict.TRIAL_INVALID,
                trial.operator.claimed_attribution,
                (),
                (),
                (),
                ("same_context_review_mislabeled_independent",),
            )

    if trial.resource_delta_declared is None:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.CANNOT_CHECK,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("resource_delta_declaration_unknown",),
        )

    baseline_resources = frozenset(trial.baseline_resource_ids)
    shaped_resources = frozenset(trial.shaped_resource_ids)
    resources_differ = baseline_resources != shaped_resources

    if resources_differ and trial.resource_delta_declared is False:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("undeclared_external_resource_delta",),
        )

    resource_sensitive_attributions = {
        CapabilityAttribution.EXTERNAL_CAPABILITY_SUBSTITUTION,
        CapabilityAttribution.SPECIALIST_COMPLEMENTATION,
        CapabilityAttribution.UNRESOLVED_MIXED_ATTRIBUTION,
    }
    if resources_differ and (
        trial.operator.claimed_attribution not in resource_sensitive_attributions
    ):
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("resource_delta_incompatible_with_claimed_attribution",),
        )

    if not trial.metrics:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.CANNOT_CHECK,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("metric_observations_missing",),
        )

    metric_names = tuple(metric.name for metric in trial.metrics)
    if len(metric_names) != len(set(metric_names)):
        return CapabilityTrialReport(
            CapabilityTrialVerdict.TRIAL_INVALID,
            trial.operator.claimed_attribution,
            (),
            (),
            (),
            ("duplicate_metric_name",),
        )

    improved: list[str] = []
    worsened: list[str] = []
    unchanged: list[str] = []
    blocking_worsened: list[str] = []
    quality_improved = False
    target_failure_improved = False
    quality_or_failure_worsened = False

    for metric in trial.metrics:
        state = _metric_state(metric)
        if state == "improved":
            improved.append(metric.name)
            if metric.kind is MetricKind.QUALITY:
                quality_improved = True
            if metric.kind is MetricKind.TARGET_FAILURE:
                target_failure_improved = True
        elif state == "worsened":
            worsened.append(metric.name)
            if metric.blocking or metric.kind is MetricKind.BLOCKING_VALIDITY:
                blocking_worsened.append(metric.name)
            if metric.kind in {MetricKind.QUALITY, MetricKind.TARGET_FAILURE}:
                quality_or_failure_worsened = True
        else:
            unchanged.append(metric.name)

    if blocking_worsened:
        return CapabilityTrialReport(
            CapabilityTrialVerdict.BLOCKING_REGRESSION,
            trial.operator.claimed_attribution,
            tuple(improved),
            tuple(worsened),
            tuple(unchanged),
            (
                "blocking_validity_regression_dominates_other_gains",
                *tuple(f"blocking_worsened:{name}" for name in blocking_worsened),
            ),
        )

    if resources_differ:
        if quality_improved or target_failure_improved:
            return CapabilityTrialReport(
                CapabilityTrialVerdict.SYSTEM_GAIN_WITH_RESOURCE_DELTA,
                trial.operator.claimed_attribution,
                tuple(improved),
                tuple(worsened),
                tuple(unchanged),
                (
                    "system_level_gain_observed",
                    "external_resource_delta_prevents_pure_model_utilization_claim",
                ),
            )
        return CapabilityTrialReport(
            CapabilityTrialVerdict.NO_MEASURED_GAIN,
            trial.operator.claimed_attribution,
            tuple(improved),
            tuple(worsened),
            tuple(unchanged),
            ("resource_delta_added_without_registered_capability_gain",),
        )

    if quality_improved and target_failure_improved:
        verdict = CapabilityTrialVerdict.VALIDATED_AMPLIFICATION_AND_SUPPRESSION
        reason = "same_model_same_resource_quality_gain_and_failure_suppression"
    elif quality_improved:
        verdict = CapabilityTrialVerdict.VALIDATED_AMPLIFICATION
        reason = "same_model_same_resource_quality_gain"
    elif target_failure_improved:
        verdict = CapabilityTrialVerdict.VALIDATED_FAILURE_SUPPRESSION
        reason = "same_model_same_resource_target_failure_suppression"
    elif quality_or_failure_worsened:
        verdict = CapabilityTrialVerdict.NONBLOCKING_REGRESSION
        reason = "registered_capability_or_target_failure_metric_worsened"
    else:
        verdict = CapabilityTrialVerdict.NO_MEASURED_GAIN
        reason = "no_registered_quality_or_target_failure_gain"

    return CapabilityTrialReport(
        verdict,
        trial.operator.claimed_attribution,
        tuple(improved),
        tuple(worsened),
        tuple(unchanged),
        (
            reason,
            "no_automatic_default_activation",
            "workflow_trial_does_not_establish_intrinsic_model_weight_improvement",
        ),
    )
