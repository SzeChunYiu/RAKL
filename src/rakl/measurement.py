from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .similarity import SimilarityRelation, SimilarityWitness, WitnessVerdict, validate_similarity_witness


class MeasurementRelationVerdict(str, Enum):
    SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY = "SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY"
    OBSERVATIONALLY_EQUIVALENT_PROPOSAL_ONLY = "OBSERVATIONALLY_EQUIVALENT_PROPOSAL_ONLY"
    OBSERVATIONALLY_DISTINGUISHABLE = "OBSERVATIONALLY_DISTINGUISHABLE"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class MeasurementSpecification:
    """Context needed to interpret one reported or predicted observation.

    Instrument, measurement model, procedure, operator, measurand and result are
    kept distinct.  A measurement result can be traceable even when the two
    compared instruments are not identical.
    """

    observation_id: str
    measurand_id: str
    feature_of_interest_id: str
    unit_id: str
    measurement_model_id: str
    observation_operator_id: str
    procedure_id: str
    instrument_id: str
    calibration_chain: Tuple[str, ...]
    traceability_reference_id: Optional[str]
    calibration_valid: Optional[bool]
    traceability_required: bool
    traceability_valid: Optional[bool]
    standard_uncertainty: Optional[float]
    resolution: Optional[float]
    regime: Tuple[str, ...]
    phenomenon_scope: Tuple[str, ...]


@dataclass(frozen=True)
class MeasurementMapping:
    """Predeclared map that makes two measurement specifications comparable.

    ``combined_standard_uncertainty`` is supplied by a separately justified
    uncertainty-combination rule.  This support layer intentionally does not
    assume independence or silently apply root-sum-square composition.
    """

    mapping_id: str
    declared_before_results: Optional[bool]
    measurand_mapping_valid: Optional[bool]
    feature_mapping_valid: Optional[bool]
    unit_transform_id: Optional[str]
    unit_transform_invertible: Optional[bool]
    measurement_model_compatibility: Optional[bool]
    observation_operator_compatibility: Optional[bool]
    uncertainty_combination_rule_id: Optional[str]
    uncertainty_combination_valid: Optional[bool]
    combined_standard_uncertainty: Optional[float]
    probes_in_common_coordinate: Optional[bool]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class ObservationProbe:
    probe_id: str
    source_prediction: float
    target_prediction: float


@dataclass(frozen=True)
class MeasurementRelationTrial:
    witness: SimilarityWitness
    source: MeasurementSpecification
    target: MeasurementSpecification
    mapping: MeasurementMapping
    equivalence_tolerance: Optional[float]
    probes: Tuple[ObservationProbe, ...]
    probe_family_frozen_before_results: Optional[bool]
    hidden_labels_exposed_before_freeze: Optional[bool]


@dataclass(frozen=True)
class MeasurementRelationReport:
    verdict: MeasurementRelationVerdict
    reasons: Tuple[str, ...]
    combined_standard_uncertainty: Optional[float] = None

    @property
    def activates_scientific_authority(self) -> bool:
        return False

    @property
    def activates_target_authority(self) -> bool:
        return False

    @property
    def implies_same_mechanism(self) -> bool:
        return False


def _require_text(name: str, value: str, missing: list[str]) -> None:
    if not value:
        missing.append(f"{name}_missing")


def _validate_spec(prefix: str, spec: MeasurementSpecification) -> Tuple[str, ...]:
    missing: list[str] = []
    for name, value in (
        ("observation_id", spec.observation_id),
        ("measurand_id", spec.measurand_id),
        ("feature_of_interest_id", spec.feature_of_interest_id),
        ("unit_id", spec.unit_id),
        ("measurement_model_id", spec.measurement_model_id),
        ("observation_operator_id", spec.observation_operator_id),
        ("procedure_id", spec.procedure_id),
        ("instrument_id", spec.instrument_id),
    ):
        _require_text(f"{prefix}_{name}", value, missing)
    if not spec.regime:
        missing.append(f"{prefix}_regime_missing")
    if not spec.phenomenon_scope:
        missing.append(f"{prefix}_phenomenon_scope_missing")
    if spec.standard_uncertainty is not None and spec.standard_uncertainty < 0:
        missing.append(f"{prefix}_standard_uncertainty_negative")
    if spec.resolution is not None and spec.resolution <= 0:
        missing.append(f"{prefix}_resolution_nonpositive")
    return tuple(missing)


def _traceability_status(spec: MeasurementSpecification, prefix: str) -> Tuple[str, Optional[bool]]:
    if spec.calibration_valid is False:
        return (f"{prefix}_calibration_invalid", False)
    if spec.calibration_valid is None:
        return (f"{prefix}_calibration_validity_unknown", None)

    if not spec.traceability_required:
        return (f"{prefix}_traceability_not_required_for_scope", True)

    if spec.traceability_valid is False:
        return (f"{prefix}_traceability_invalid", False)
    if spec.traceability_valid is None:
        return (f"{prefix}_traceability_validity_unknown", None)
    if not spec.calibration_chain:
        return (f"{prefix}_calibration_chain_missing", False)
    if not spec.traceability_reference_id:
        return (f"{prefix}_traceability_reference_missing", False)
    return (f"{prefix}_traceability_valid", True)


def evaluate_measurement_relation(trial: MeasurementRelationTrial) -> MeasurementRelationReport:
    """Evaluate measurement-aware SAME_OBSERVABLE/OBSERVATIONALLY_EQUIVALENT.

    This layer certifies only a scoped measurement relation. It never establishes
    mechanism identity, generator identity, or target scientific authority.
    Generic ``SimilarityWitness`` validation remains a structural compatibility
    check; this evaluator is the additional measurement certificate.
    """

    if trial.witness.relation not in {
        SimilarityRelation.SAME_OBSERVABLE,
        SimilarityRelation.OBSERVATIONALLY_EQUIVALENT,
    }:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.REJECT,
            ("measurement_extension_used_for_non_measurement_relation",),
        )

    if trial.hidden_labels_exposed_before_freeze is True:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.TRIAL_INVALID,
            ("hidden_label_or_discriminator_exposed_before_mapping_freeze",),
        )
    if trial.hidden_labels_exposed_before_freeze is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("hidden_label_exposure_status_unknown",),
        )
    if trial.mapping.declared_before_results is False:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.TRIAL_INVALID,
            ("measurement_mapping_fitted_posthoc",),
        )
    if trial.mapping.declared_before_results is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("measurement_mapping_chronology_unknown",),
        )

    missing = list(_validate_spec("source", trial.source)) + list(_validate_spec("target", trial.target))
    if not trial.mapping.mapping_id:
        missing.append("measurement_mapping_id_missing")
    if not trial.mapping.evidence_ids:
        missing.append("measurement_mapping_evidence_missing")
    if missing:
        return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, tuple(missing))

    base_report = validate_similarity_witness(trial.witness)
    if base_report.verdict is WitnessVerdict.REJECT:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.REJECT,
            tuple(f"similarity_witness:{reason}" for reason in base_report.reasons),
        )
    if base_report.verdict is WitnessVerdict.CANNOT_CHECK:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            tuple(f"similarity_witness:{reason}" for reason in base_report.reasons),
        )

    if trial.witness.source_id != trial.source.observation_id or trial.witness.target_id != trial.target.observation_id:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.REJECT,
            ("measurement_specs_do_not_match_similarity_endpoints",),
        )

    if trial.source.measurand_id != trial.target.measurand_id:
        if trial.mapping.measurand_mapping_valid is False:
            return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("measurand_mismatch",))
        if trial.mapping.measurand_mapping_valid is None:
            return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, ("measurand_mapping_unknown",))

    if trial.source.feature_of_interest_id != trial.target.feature_of_interest_id:
        if trial.mapping.feature_mapping_valid is False:
            return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("feature_of_interest_mismatch",))
        if trial.mapping.feature_mapping_valid is None:
            return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, ("feature_mapping_unknown",))

    if trial.source.unit_id != trial.target.unit_id:
        if not trial.mapping.unit_transform_id:
            return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, ("unit_transform_missing",))
        if trial.mapping.unit_transform_invertible is False:
            return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("unit_transform_not_invertible",))
        if trial.mapping.unit_transform_invertible is None:
            return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, ("unit_transform_invertibility_unknown",))

    if not set(trial.source.regime).intersection(trial.target.regime):
        return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("measurement_regime_disjoint",))
    if not set(trial.source.phenomenon_scope).intersection(trial.target.phenomenon_scope):
        return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("phenomenon_scope_disjoint",))

    if trial.source.measurement_model_id != trial.target.measurement_model_id:
        if trial.mapping.measurement_model_compatibility is False:
            return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("measurement_model_mismatch",))
        if trial.mapping.measurement_model_compatibility is None:
            return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, ("measurement_model_compatibility_unknown",))

    if trial.source.observation_operator_id != trial.target.observation_operator_id:
        if trial.mapping.observation_operator_compatibility is False:
            return MeasurementRelationReport(MeasurementRelationVerdict.REJECT, ("observation_operator_mismatch",))
        if trial.mapping.observation_operator_compatibility is None:
            return MeasurementRelationReport(MeasurementRelationVerdict.CANNOT_CHECK, ("observation_operator_compatibility_unknown",))

    source_trace_reason, source_trace = _traceability_status(trial.source, "source")
    target_trace_reason, target_trace = _traceability_status(trial.target, "target")
    if source_trace is False or target_trace is False:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.REJECT,
            tuple(reason for reason, state in ((source_trace_reason, source_trace), (target_trace_reason, target_trace)) if state is False),
        )
    if source_trace is None or target_trace is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            tuple(reason for reason, state in ((source_trace_reason, source_trace), (target_trace_reason, target_trace)) if state is None),
        )

    if trial.source.traceability_required and trial.target.traceability_required:
        if trial.source.traceability_reference_id != trial.target.traceability_reference_id:
            return MeasurementRelationReport(
                MeasurementRelationVerdict.REJECT,
                ("no_common_traceability_reference",),
            )

    if trial.source.standard_uncertainty is None or trial.target.standard_uncertainty is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("measurement_uncertainty_missing",),
        )
    if trial.source.resolution is None or trial.target.resolution is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("measurement_resolution_missing",),
        )

    if not trial.mapping.uncertainty_combination_rule_id:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("uncertainty_combination_rule_missing",),
        )
    if trial.mapping.uncertainty_combination_valid is False:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.REJECT,
            ("uncertainty_combination_rule_invalid",),
        )
    if trial.mapping.uncertainty_combination_valid is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("uncertainty_combination_rule_validity_unknown",),
        )
    if trial.mapping.combined_standard_uncertainty is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("combined_standard_uncertainty_missing",),
        )
    if trial.mapping.combined_standard_uncertainty < 0:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.REJECT,
            ("combined_standard_uncertainty_negative",),
        )
    combined_uncertainty = trial.mapping.combined_standard_uncertainty

    if trial.witness.relation is SimilarityRelation.SAME_OBSERVABLE:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY,
            (
                "same_or_witnessed_measurand",
                "same_or_witnessed_feature_of_interest",
                "units_are_common_or_predeclared_transformable",
                "measurement_models_are_common_or_witnessed_compatible",
                "observation_operators_are_common_or_witnessed_compatible",
                "calibration_and_required_traceability_are_valid",
                "uncertainty_combination_is_predeclared_and_validated",
                "measurement_relation_does_not_imply_same_mechanism",
            ),
            combined_uncertainty,
        )

    if trial.probe_family_frozen_before_results is False:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.TRIAL_INVALID,
            ("discriminating_probe_family_selected_posthoc",),
            combined_uncertainty,
        )
    if trial.probe_family_frozen_before_results is None:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("probe_family_freeze_chronology_unknown",),
            combined_uncertainty,
        )
    if not trial.probes:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("frozen_discriminating_probe_family_missing",),
            combined_uncertainty,
        )
    if trial.equivalence_tolerance is None or trial.equivalence_tolerance <= 0:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("equivalence_tolerance_missing_or_nonpositive",),
            combined_uncertainty,
        )

    if trial.source.unit_id != trial.target.unit_id:
        if trial.mapping.probes_in_common_coordinate is not True:
            return MeasurementRelationReport(
                MeasurementRelationVerdict.CANNOT_CHECK,
                ("probe_predictions_not_certified_in_common_coordinate",),
                combined_uncertainty,
            )

    tolerance = trial.equivalence_tolerance
    if combined_uncertainty > tolerance or max(trial.source.resolution, trial.target.resolution) > tolerance:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.CANNOT_CHECK,
            ("measurement_capability_insufficient_for_declared_equivalence_tolerance",),
            combined_uncertainty,
        )

    separating = tuple(
        probe.probe_id
        for probe in trial.probes
        if abs(probe.source_prediction - probe.target_prediction) > tolerance
    )
    if separating:
        return MeasurementRelationReport(
            MeasurementRelationVerdict.OBSERVATIONALLY_DISTINGUISHABLE,
            tuple(f"separating_probe:{probe_id}" for probe_id in separating),
            combined_uncertainty,
        )

    return MeasurementRelationReport(
        MeasurementRelationVerdict.OBSERVATIONALLY_EQUIVALENT_PROPOSAL_ONLY,
        (
            "all_frozen_probes_indistinguishable_at_declared_tolerance",
            "measurement_capability_resolves_declared_tolerance",
            "equivalence_is_relative_to_probe_family_operator_model_regime_and_qoi",
            "observational_equivalence_does_not_imply_same_mechanism",
        ),
        combined_uncertainty,
    )
