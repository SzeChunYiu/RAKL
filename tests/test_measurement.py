from dataclasses import FrozenInstanceError, replace

import pytest

from rakl.measurement import (
    MeasurementMapping,
    MeasurementRelationTrial,
    MeasurementRelationVerdict,
    MeasurementSpecification,
    ObservationProbe,
    evaluate_measurement_relation,
)
from rakl.similarity import (
    MappingAdmissibility,
    ProbeFamily,
    SimilarityRelation,
    SimilarityWitness,
    WitnessVerdict,
    validate_similarity_witness,
)


def _witness(relation: SimilarityRelation = SimilarityRelation.SAME_OBSERVABLE) -> SimilarityWitness:
    return SimilarityWitness(
        relation=relation,
        source_id="obs-source",
        target_id="obs-target",
        source_domain="lab-A",
        target_domain="lab-B",
        question_or_qoi="are these observations commensurable for the declared QoI?",
        mapping_pairs=(("measurand", "measurand"), ("result", "result")),
        preserved=("measurand", "measurement_scale"),
        not_preserved=("instrument_identity",),
        regime=("ambient",),
        evidence_ids=("map-evidence",),
        mapping_admissibility=MappingAdmissibility(
            family_id="measurement-map-v1",
            declared_before_fit=True,
            constraints=("typed_roles", "measurement_context"),
            constraint_violations=(),
            null_calibration_passed=True,
        ),
        probe_family=ProbeFamily(
            family_id="measurement-probes-v1",
            probe_ids=("p1", "p2"),
        ),
    )


def _spec(observation_id: str, **overrides) -> MeasurementSpecification:
    values = dict(
        observation_id=observation_id,
        measurand_id="surface-temperature",
        feature_of_interest_id="sample-42",
        unit_id="K",
        observation_operator_id="contact-thermometry-v1",
        procedure_id="procedure-v1",
        instrument_id=f"instrument-{observation_id}",
        calibration_chain=("working-standard", "national-standard"),
        traceability_reference_id="SI-kelvin",
        calibration_valid=True,
        traceability_required=True,
        traceability_valid=True,
        standard_uncertainty=0.02,
        resolution=0.01,
        regime=("ambient", "steady"),
        phenomenon_scope=("2026-Q3",),
    )
    values.update(overrides)
    return MeasurementSpecification(**values)


def _mapping(**overrides) -> MeasurementMapping:
    values = dict(
        mapping_id="measurement-map-v1",
        declared_before_results=True,
        measurand_mapping_valid=True,
        feature_mapping_valid=True,
        unit_transform_id=None,
        unit_transform_invertible=None,
        observation_operator_compatibility=True,
        evidence_ids=("calibration-certificate", "procedure-comparison"),
    )
    values.update(overrides)
    return MeasurementMapping(**values)


def _trial(relation: SimilarityRelation = SimilarityRelation.SAME_OBSERVABLE, **overrides) -> MeasurementRelationTrial:
    values = dict(
        witness=_witness(relation),
        source=_spec("obs-source"),
        target=_spec("obs-target"),
        mapping=_mapping(),
        equivalence_tolerance=0.1,
        probes=(ObservationProbe("p1", 300.00, 300.03), ObservationProbe("p2", 302.00, 302.04)),
        probe_family_frozen_before_results=True,
        hidden_labels_exposed_before_freeze=False,
    )
    values.update(overrides)
    return MeasurementRelationTrial(**values)


def test_m01_same_measurand_operator_calibrated_is_supported_proposal_only():
    report = evaluate_measurement_relation(_trial())
    assert report.verdict is MeasurementRelationVerdict.SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY
    assert report.activates_scientific_authority is False
    assert report.activates_target_authority is False
    assert report.implies_same_mechanism is False


def test_m02_equal_numbers_do_not_rescue_different_measurands():
    target = _spec("obs-target", measurand_id="humidity")
    report = evaluate_measurement_relation(
        _trial(target=target, mapping=_mapping(measurand_mapping_valid=False))
    )
    assert report.verdict is MeasurementRelationVerdict.REJECT
    assert "measurand_mismatch" in report.reasons


def test_m03_feature_of_interest_mismatch_requires_witnessed_map():
    target = _spec("obs-target", feature_of_interest_id="sample-99")
    report = evaluate_measurement_relation(
        _trial(target=target, mapping=_mapping(feature_mapping_valid=False))
    )
    assert report.verdict is MeasurementRelationVerdict.REJECT
    assert "feature_of_interest_mismatch" in report.reasons


def test_m04_predeclared_invertible_unit_transform_is_allowed():
    target = _spec("obs-target", unit_id="degC")
    report = evaluate_measurement_relation(
        _trial(
            target=target,
            mapping=_mapping(unit_transform_id="kelvin-to-celsius", unit_transform_invertible=True),
        )
    )
    assert report.verdict is MeasurementRelationVerdict.SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY


def test_m05_posthoc_measurement_transform_invalidates_trial():
    report = evaluate_measurement_relation(
        _trial(mapping=_mapping(declared_before_results=False))
    )
    assert report.verdict is MeasurementRelationVerdict.TRIAL_INVALID


def test_m06_unknown_operator_compatibility_cannot_check():
    target = _spec("obs-target", observation_operator_id="infrared-radiometry-v2")
    report = evaluate_measurement_relation(
        _trial(target=target, mapping=_mapping(observation_operator_compatibility=None))
    )
    assert report.verdict is MeasurementRelationVerdict.CANNOT_CHECK
    assert "observation_operator_compatibility_unknown" in report.reasons


def test_m07_equal_values_under_incompatible_operators_are_rejected():
    target = _spec("obs-target", observation_operator_id="infrared-radiometry-v2")
    report = evaluate_measurement_relation(
        _trial(target=target, mapping=_mapping(observation_operator_compatibility=False))
    )
    assert report.verdict is MeasurementRelationVerdict.REJECT
    assert "observation_operator_mismatch" in report.reasons


def test_m08_distinct_instruments_can_measure_same_observable_with_traceability():
    source = _spec("obs-source", instrument_id="thermometer-A")
    target = _spec("obs-target", instrument_id="thermometer-B")
    report = evaluate_measurement_relation(_trial(source=source, target=target))
    assert report.verdict is MeasurementRelationVerdict.SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY
    assert report.implies_same_mechanism is False


def test_m09_broken_traceability_chain_rejects_claim():
    target = _spec("obs-target", calibration_chain=())
    report = evaluate_measurement_relation(_trial(target=target))
    assert report.verdict is MeasurementRelationVerdict.REJECT
    assert "target_calibration_chain_missing" in report.reasons


def test_m10_unknown_traceability_is_cannot_check_not_reject():
    target = _spec("obs-target", traceability_valid=None)
    report = evaluate_measurement_relation(_trial(target=target))
    assert report.verdict is MeasurementRelationVerdict.CANNOT_CHECK
    assert "target_traceability_validity_unknown" in report.reasons


def test_m11_frozen_probe_family_can_support_observational_equivalence():
    report = evaluate_measurement_relation(_trial(SimilarityRelation.OBSERVATIONALLY_EQUIVALENT))
    assert report.verdict is MeasurementRelationVerdict.OBSERVATIONALLY_EQUIVALENT_PROPOSAL_ONLY
    assert report.activates_target_authority is False


def test_m12_one_separating_probe_refutes_observational_equivalence():
    report = evaluate_measurement_relation(
        _trial(
            SimilarityRelation.OBSERVATIONALLY_EQUIVALENT,
            probes=(ObservationProbe("p-separates", 300.0, 300.5),),
        )
    )
    assert report.verdict is MeasurementRelationVerdict.OBSERVATIONALLY_DISTINGUISHABLE
    assert "separating_probe:p-separates" in report.reasons


def test_m13_missing_frozen_probe_family_cannot_establish_equivalence():
    report = evaluate_measurement_relation(
        _trial(SimilarityRelation.OBSERVATIONALLY_EQUIVALENT, probes=())
    )
    assert report.verdict is MeasurementRelationVerdict.CANNOT_CHECK
    assert "frozen_discriminating_probe_family_missing" in report.reasons


def test_m14_uncertainty_larger_than_tolerance_cannot_establish_equivalence():
    target = _spec("obs-target", standard_uncertainty=0.2)
    report = evaluate_measurement_relation(
        _trial(
            SimilarityRelation.OBSERVATIONALLY_EQUIVALENT,
            target=target,
            equivalence_tolerance=0.1,
        )
    )
    assert report.verdict is MeasurementRelationVerdict.CANNOT_CHECK
    assert "measurement_capability_insufficient_for_declared_equivalence_tolerance" in report.reasons


def test_m15_disjoint_regimes_reject_measurement_relation():
    target = _spec("obs-target", regime=("cryogenic",))
    report = evaluate_measurement_relation(_trial(target=target))
    assert report.verdict is MeasurementRelationVerdict.REJECT
    assert "measurement_regime_disjoint" in report.reasons


def test_m16_same_observable_never_implies_same_mechanism():
    report = evaluate_measurement_relation(_trial())
    assert report.verdict is MeasurementRelationVerdict.SAME_OBSERVABLE_SUPPORTED_PROPOSAL_ONLY
    assert report.implies_same_mechanism is False


def test_m17_valid_measurement_relation_cannot_mint_target_authority():
    report = evaluate_measurement_relation(_trial())
    assert report.activates_target_authority is False
    with pytest.raises(FrozenInstanceError):
        report.verdict = MeasurementRelationVerdict.REJECT  # type: ignore[misc]


def test_m18_hidden_discriminator_exposure_invalidates_trial():
    report = evaluate_measurement_relation(
        _trial(hidden_labels_exposed_before_freeze=True)
    )
    assert report.verdict is MeasurementRelationVerdict.TRIAL_INVALID


def test_generic_similarity_validator_fails_closed_for_measurement_relations():
    for relation in (
        SimilarityRelation.SAME_OBSERVABLE,
        SimilarityRelation.OBSERVATIONALLY_EQUIVALENT,
    ):
        report = validate_similarity_witness(_witness(relation))
        assert report.verdict is WitnessVerdict.CANNOT_CHECK
        assert "measurement_context_extension_required" in report.reasons


def test_measurement_contract_is_immutable():
    spec = _spec("obs-source")
    with pytest.raises(FrozenInstanceError):
        spec.measurand_id = "changed"  # type: ignore[misc]


def test_non_measurement_relation_is_rejected_by_measurement_extension():
    report = evaluate_measurement_relation(_trial(SimilarityRelation.RELATIONALLY_ANALOGOUS))
    assert report.verdict is MeasurementRelationVerdict.REJECT
    assert "measurement_extension_used_for_non_measurement_relation" in report.reasons
