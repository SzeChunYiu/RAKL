from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil
from statistics import median
from typing import Tuple


class ModelCriticismVerdict(str, Enum):
    ADEQUATE_ON_FROZEN_PROBES_PROPOSAL_ONLY = "ADEQUATE_ON_FROZEN_PROBES_PROPOSAL_ONLY"
    STRUCTURED_RESIDUAL_DETECTED = "STRUCTURED_RESIDUAL_DETECTED"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class CriticismProbe:
    probe_id: str
    scientific_coordinate: str
    context_scope: Tuple[str, ...]
    observed_statistic: float
    predictive_samples: Tuple[float, ...]
    materiality_tolerance: float
    frozen_before_results: bool | None


@dataclass(frozen=True)
class ModelCriticismTrial:
    model_id: str
    observed_population_id: str
    predictive_population_id: str
    probes: Tuple[CriticismProbe, ...]
    probe_family_frozen_before_results: bool | None
    hidden_confirmation_outcomes_exposed_before_freeze: bool | None
    family_alpha: float
    multiplicity_policy: str
    predictive_distribution_bound_to_model: bool | None
    residual_mapping_predeclared: bool | None


@dataclass(frozen=True)
class ProbeCriticism:
    probe_id: str
    scientific_coordinate: str
    empirical_two_sided_tail: float
    absolute_discrepancy_from_predictive_median: float
    adjusted_alpha: float
    material_failure: bool


@dataclass(frozen=True)
class ModelCriticismReport:
    verdict: ModelCriticismVerdict
    reasons: Tuple[str, ...]
    probe_reports: Tuple[ProbeCriticism, ...] = ()
    residual_coordinates: Tuple[str, ...] = ()

    @property
    def grants_scientific_truth(self) -> bool:
        return False

    @property
    def grants_mechanism_authority(self) -> bool:
        return False

    @property
    def establishes_global_model_closure(self) -> bool:
        return False


def _empirical_two_sided_tail(observed: float, samples: Tuple[float, ...]) -> float:
    n = len(samples)
    lower = (1 + sum(value <= observed for value in samples)) / (n + 1)
    upper = (1 + sum(value >= observed for value in samples)) / (n + 1)
    return min(1.0, 2.0 * min(lower, upper))


def evaluate_model_criticism(trial: ModelCriticismTrial) -> ModelCriticismReport:
    if not trial.model_id.strip() or not trial.observed_population_id.strip() or not trial.predictive_population_id.strip():
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("model_or_population_identity_missing",))
    if trial.observed_population_id != trial.predictive_population_id:
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("observed_predictive_population_mismatch",))
    if trial.hidden_confirmation_outcomes_exposed_before_freeze is True:
        return ModelCriticismReport(ModelCriticismVerdict.TRIAL_INVALID, ("confirmation_outcomes_exposed_before_probe_freeze",))
    if trial.hidden_confirmation_outcomes_exposed_before_freeze is None:
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("confirmation_exposure_status_unknown",))
    if trial.probe_family_frozen_before_results is False:
        return ModelCriticismReport(ModelCriticismVerdict.TRIAL_INVALID, ("probe_family_selected_posthoc",))
    if trial.probe_family_frozen_before_results is None:
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("probe_family_freeze_chronology_unknown",))
    if trial.predictive_distribution_bound_to_model is False:
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("predictive_distribution_not_bound_to_model",))
    if trial.predictive_distribution_bound_to_model is None:
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("predictive_distribution_binding_unknown",))
    if not trial.probes:
        return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("frozen_probe_family_missing",))
    if not (0.0 < trial.family_alpha < 1.0):
        return ModelCriticismReport(ModelCriticismVerdict.TRIAL_INVALID, ("family_alpha_out_of_range",))

    policy = trial.multiplicity_policy.strip().upper()
    if len(trial.probes) == 1:
        if policy not in {"SINGLE", "BONFERRONI"}:
            return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("single_probe_policy_not_declared",))
        adjusted_alpha = trial.family_alpha
    else:
        if policy != "BONFERRONI":
            return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, ("multiple_probe_policy_not_supported_or_missing",))
        adjusted_alpha = trial.family_alpha / len(trial.probes)

    reports: list[ProbeCriticism] = []
    residuals: list[str] = []
    seen_ids: set[str] = set()
    for probe in trial.probes:
        if not probe.probe_id.strip() or probe.probe_id in seen_ids:
            return ModelCriticismReport(ModelCriticismVerdict.TRIAL_INVALID, ("probe_id_missing_or_duplicate",))
        seen_ids.add(probe.probe_id)
        if not probe.scientific_coordinate.strip() or not probe.context_scope:
            return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, (f"probe_scope_missing:{probe.probe_id}",))
        if probe.frozen_before_results is False:
            return ModelCriticismReport(ModelCriticismVerdict.TRIAL_INVALID, (f"probe_selected_posthoc:{probe.probe_id}",))
        if probe.frozen_before_results is None:
            return ModelCriticismReport(ModelCriticismVerdict.CANNOT_CHECK, (f"probe_freeze_unknown:{probe.probe_id}",))
        if probe.materiality_tolerance < 0:
            return ModelCriticismReport(ModelCriticismVerdict.TRIAL_INVALID, (f"negative_materiality_tolerance:{probe.probe_id}",))

        # The add-one empirical tail has a smallest attainable two-sided p-value
        # of approximately 2/(B+1).  If that cannot resolve the declared alpha,
        # the critic must not call a tail failure absent stronger external evidence.
        min_n = max(1, ceil(2.0 / adjusted_alpha - 1.0))
        if len(probe.predictive_samples) < min_n:
            return ModelCriticismReport(
                ModelCriticismVerdict.CANNOT_CHECK,
                (f"predictive_samples_insufficient_for_declared_tail_resolution:{probe.probe_id}",),
            )

        center = float(median(probe.predictive_samples))
        discrepancy = abs(float(probe.observed_statistic) - center)
        p_tail = _empirical_two_sided_tail(float(probe.observed_statistic), probe.predictive_samples)
        material_failure = discrepancy > probe.materiality_tolerance and p_tail <= adjusted_alpha
        reports.append(
            ProbeCriticism(
                probe_id=probe.probe_id,
                scientific_coordinate=probe.scientific_coordinate,
                empirical_two_sided_tail=p_tail,
                absolute_discrepancy_from_predictive_median=discrepancy,
                adjusted_alpha=adjusted_alpha,
                material_failure=material_failure,
            )
        )
        if material_failure:
            residuals.append(probe.scientific_coordinate)

    if residuals:
        if trial.residual_mapping_predeclared is None:
            return ModelCriticismReport(
                ModelCriticismVerdict.PARTIALLY_IDENTIFIED,
                ("structured_residual_detected_but_residual_mapping_chronology_unknown",),
                tuple(reports),
                tuple(sorted(set(residuals))),
            )
        reasons = [
            "at_least_one_frozen_probe_has_material_predictive_discrepancy",
            "failed_probe_is_evidence_against_scoped_model_adequacy_not_proof_of_one_replacement_mechanism",
        ]
        if trial.residual_mapping_predeclared is False:
            reasons.append("residual_interpretation_is_posthoc_proposal_only")
            verdict = ModelCriticismVerdict.PARTIALLY_IDENTIFIED
        else:
            reasons.append("residual_coordinate_mapping_was_predeclared")
            verdict = ModelCriticismVerdict.STRUCTURED_RESIDUAL_DETECTED
        return ModelCriticismReport(
            verdict,
            tuple(reasons),
            tuple(reports),
            tuple(sorted(set(residuals))),
        )

    return ModelCriticismReport(
        ModelCriticismVerdict.ADEQUATE_ON_FROZEN_PROBES_PROPOSAL_ONLY,
        (
            "no_material_predictive_discrepancy_detected_on_frozen_probe_family",
            "adequacy_is_relative_to_probe_context_population_and_resolution",
            "probe_adequacy_does_not_establish_model_truth_or_mechanism_identity",
        ),
        tuple(reports),
        (),
    )
