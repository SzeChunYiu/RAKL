from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Optional, Tuple


class ConclusionClass(str, Enum):
    NEGATIVE = "NEGATIVE"
    INDETERMINATE = "INDETERMINATE"
    POSITIVE = "POSITIVE"


class AssumptionSensitivityVerdict(str, Enum):
    ROBUST_WITHIN_REGISTERED_ENVELOPE_PROPOSAL_ONLY = "ROBUST_WITHIN_REGISTERED_ENVELOPE_PROPOSAL_ONLY"
    ASSUMPTION_SENSITIVE = "ASSUMPTION_SENSITIVE"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    CANNOT_COMPARE = "CANNOT_COMPARE"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class AssumptionScenario:
    scenario_id: str
    assumption_id: str
    context_scope: Tuple[str, ...]
    target_qoi: str
    estimate: Optional[float]
    frozen_before_results: Optional[bool]
    evidence_id: Optional[str] = None


@dataclass(frozen=True)
class AssumptionSensitivityTrial:
    baseline_id: str
    baseline_estimate: float
    material_delta: float
    baseline_context_scope: Tuple[str, ...]
    baseline_target_qoi: str
    scenarios: Tuple[AssumptionScenario, ...]
    scenario_family_frozen_before_results: Optional[bool]
    hidden_confirmation_outcomes_exposed_before_freeze: Optional[bool]
    envelope_complete_for_registered_question: Optional[bool]
    negative_history_preserved: Optional[bool]


@dataclass(frozen=True)
class ScenarioAssessment:
    scenario_id: str
    assumption_id: str
    conclusion: Optional[ConclusionClass]
    estimate: Optional[float]


@dataclass(frozen=True)
class AssumptionSensitivityReport:
    verdict: AssumptionSensitivityVerdict
    baseline_conclusion: Optional[ConclusionClass]
    scenario_assessments: Tuple[ScenarioAssessment, ...]
    sensitive_scenario_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_assumption_truth(self) -> bool:
        return False

    @property
    def grants_mechanism_authority(self) -> bool:
        return False

    @property
    def grants_scientific_promotion(self) -> bool:
        return False


def classify_conclusion(estimate: float, material_delta: float) -> ConclusionClass:
    """Classify a scalar estimand relative to a predeclared material threshold."""
    if not isfinite(estimate):
        raise ValueError("estimate must be finite")
    if not isfinite(material_delta) or material_delta < 0:
        raise ValueError("material_delta must be finite and non-negative")
    if estimate > material_delta:
        return ConclusionClass.POSITIVE
    if estimate < -material_delta:
        return ConclusionClass.NEGATIVE
    return ConclusionClass.INDETERMINATE


def evaluate_assumption_sensitivity(trial: AssumptionSensitivityTrial) -> AssumptionSensitivityReport:
    """Evaluate robustness over a frozen, scope-compatible assumption envelope.

    The evaluator compares conclusion classes over registered perturbations. It
    never establishes that an assumption is true, and it never treats a changed
    population or QoI as an assumption perturbation of the same scientific claim.
    """

    if not trial.baseline_id.strip() or not trial.baseline_target_qoi.strip() or not trial.baseline_context_scope:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.CANNOT_CHECK,
            None,
            (),
            (),
            ("baseline_identity_scope_or_qoi_missing",),
        )
    try:
        baseline_conclusion = classify_conclusion(trial.baseline_estimate, trial.material_delta)
    except ValueError as exc:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.TRIAL_INVALID,
            None,
            (),
            (),
            (str(exc),),
        )

    if trial.hidden_confirmation_outcomes_exposed_before_freeze is True:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.TRIAL_INVALID,
            baseline_conclusion,
            (),
            (),
            ("confirmation_outcomes_exposed_before_assumption_envelope_freeze",),
        )
    if trial.hidden_confirmation_outcomes_exposed_before_freeze is None:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.CANNOT_CHECK,
            baseline_conclusion,
            (),
            (),
            ("confirmation_exposure_status_unknown",),
        )
    if trial.scenario_family_frozen_before_results is False:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.TRIAL_INVALID,
            baseline_conclusion,
            (),
            (),
            ("assumption_scenario_family_selected_posthoc",),
        )
    if trial.scenario_family_frozen_before_results is None:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.CANNOT_CHECK,
            baseline_conclusion,
            (),
            (),
            ("assumption_scenario_family_freeze_unknown",),
        )
    if trial.negative_history_preserved is False:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.TRIAL_INVALID,
            baseline_conclusion,
            (),
            (),
            ("negative_history_not_preserved",),
        )
    if trial.negative_history_preserved is None:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.CANNOT_CHECK,
            baseline_conclusion,
            (),
            (),
            ("negative_history_preservation_unknown",),
        )
    if trial.envelope_complete_for_registered_question is None:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.CANNOT_CHECK,
            baseline_conclusion,
            (),
            (),
            ("assumption_envelope_completeness_unknown",),
        )
    if not trial.scenarios:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.CANNOT_CHECK,
            baseline_conclusion,
            (),
            (),
            ("registered_assumption_scenarios_missing",),
        )

    seen: set[str] = set()
    assessments: list[ScenarioAssessment] = []
    unavailable: list[str] = []
    for scenario in trial.scenarios:
        if not scenario.scenario_id.strip() or scenario.scenario_id in seen:
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.TRIAL_INVALID,
                baseline_conclusion,
                tuple(assessments),
                (),
                ("scenario_id_missing_or_duplicate",),
            )
        seen.add(scenario.scenario_id)
        if not scenario.assumption_id.strip():
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.CANNOT_CHECK,
                baseline_conclusion,
                tuple(assessments),
                (),
                (f"assumption_id_missing:{scenario.scenario_id}",),
            )
        if scenario.frozen_before_results is False:
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.TRIAL_INVALID,
                baseline_conclusion,
                tuple(assessments),
                (),
                (f"scenario_selected_posthoc:{scenario.scenario_id}",),
            )
        if scenario.frozen_before_results is None:
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.CANNOT_CHECK,
                baseline_conclusion,
                tuple(assessments),
                (),
                (f"scenario_freeze_unknown:{scenario.scenario_id}",),
            )
        if scenario.context_scope != trial.baseline_context_scope:
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.CANNOT_COMPARE,
                baseline_conclusion,
                tuple(assessments),
                (),
                (f"scenario_context_or_population_differs_from_baseline:{scenario.scenario_id}",),
            )
        if scenario.target_qoi != trial.baseline_target_qoi:
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.CANNOT_COMPARE,
                baseline_conclusion,
                tuple(assessments),
                (),
                (f"scenario_target_or_qoi_differs_from_baseline:{scenario.scenario_id}",),
            )
        if scenario.estimate is None:
            unavailable.append(scenario.scenario_id)
            assessments.append(
                ScenarioAssessment(
                    scenario_id=scenario.scenario_id,
                    assumption_id=scenario.assumption_id,
                    conclusion=None,
                    estimate=None,
                )
            )
            continue
        try:
            conclusion = classify_conclusion(float(scenario.estimate), trial.material_delta)
        except ValueError as exc:
            return AssumptionSensitivityReport(
                AssumptionSensitivityVerdict.TRIAL_INVALID,
                baseline_conclusion,
                tuple(assessments),
                (),
                (f"{scenario.scenario_id}:{exc}",),
            )
        assessments.append(
            ScenarioAssessment(
                scenario_id=scenario.scenario_id,
                assumption_id=scenario.assumption_id,
                conclusion=conclusion,
                estimate=float(scenario.estimate),
            )
        )

    if unavailable:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.PARTIALLY_IDENTIFIED,
            baseline_conclusion,
            tuple(assessments),
            (),
            tuple(f"registered_scenario_result_unavailable:{scenario_id}" for scenario_id in unavailable)
            + ("robustness_over_the_complete_registered_envelope_is_not_identified",),
        )

    sensitive = tuple(
        assessment.scenario_id
        for assessment in assessments
        if assessment.conclusion is not baseline_conclusion
    )
    if sensitive:
        return AssumptionSensitivityReport(
            AssumptionSensitivityVerdict.ASSUMPTION_SENSITIVE,
            baseline_conclusion,
            tuple(assessments),
            sensitive,
            (
                "at_least_one_predeclared_assumption_scenario_changes_the_material_conclusion_class",
                "baseline_result_cannot_be_reported_as_robust_over_the_registered_envelope",
                "sensitivity_does_not_identify_which_assumption_is_true",
            ),
        )

    reasons = [
        "all_evaluated_predeclared_scenarios_preserve_the_baseline_material_conclusion_class",
        "robustness_is_relative_to_the_registered_assumption_envelope",
        "robustness_does_not_prove_assumptions_true_or_mechanism_identified",
    ]
    if trial.envelope_complete_for_registered_question is False:
        reasons.append("registered_envelope_explicitly_not_complete_for_all_possible_assumptions")
    return AssumptionSensitivityReport(
        AssumptionSensitivityVerdict.ROBUST_WITHIN_REGISTERED_ENVELOPE_PROPOSAL_ONLY,
        baseline_conclusion,
        tuple(assessments),
        (),
        tuple(reasons),
    )
