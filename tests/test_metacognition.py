import pytest

from rakl.metacognition import (
    MetacognitiveAuditCase,
    MetacognitiveAuditVerdict,
    MetacognitiveCompletenessAuditor,
)


def assess(**kwargs):
    return MetacognitiveCompletenessAuditor.assess(MetacognitiveAuditCase(**kwargs))


def test_mcc001_no_trigger_skips_reflection():
    report = assess(reflection_cost=8.0, expected_failure_cost=1.0)
    assert report.verdict == MetacognitiveAuditVerdict.NO_AUDIT_REQUIRED
    assert report.capability_upgrade_authorized is False


def test_mcc002_known_high_confidence_error_reopens_known_fiber():
    report = assess(
        trigger_signals=("HIGH_CONFIDENCE_ERROR",),
        known_failure_fiber="equivalence_detection",
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.KNOWN_WEAKNESS
    assert "equivalence_detection" in " ".join(report.reasons)


def test_mcc003_single_unclassified_error_is_calibration_not_ontology_claim():
    report = assess(
        trigger_signals=("HIGH_CONFIDENCE_ERROR",),
        repeated_unclassified_residuals=1,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CALIBRATION_WEAKNESS
    assert report.requires_ontology_benchmark is False


def test_mcc004_repeated_unclassified_residual_opens_ontology_candidate():
    report = assess(
        trigger_signals=("REPEATED_UNCLASSIFIED_RESIDUAL",),
        repeated_unclassified_residuals=3,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.ONTOLOGY_GAP_CANDIDATE
    assert report.requires_ontology_benchmark is True
    assert report.capability_upgrade_authorized is False


def test_mcc005_target_cut_outside_operator_basis_opens_method_basis_candidate():
    report = assess(
        trigger_signals=("TARGET_UNREACHABLE",),
        target_reachable=False,
        epistemic_cut_identified=True,
        incumbent_operator_can_resolve_cut=False,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.METHOD_BASIS_GAP_CANDIDATE
    assert report.requires_new_operator_benchmark is True
    assert report.capability_upgrade_authorized is False


def test_mcc006_explanation_reconstruction_exposes_missing_mechanistic_element():
    report = assess(
        trigger_signals=("EXPLANATION_RECONSTRUCTION",),
        explanation_required_elements=(
            "building_blocks",
            "interaction",
            "observation_map",
        ),
        explanation_provided_elements=("building_blocks", "observation_map"),
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.EXPLANATION_GAP
    assert report.missing_explanation_elements == ("interaction",)


def test_mcc007_generic_be_unbiased_is_not_countermodel():
    report = assess(
        trigger_signals=("BIAS_RISK",),
        countermodel_requested=True,
        countermodel_supplied=False,
        generic_be_unbiased_instruction_only=True,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.INDEPENDENT_REVIEW_REQUIRED
    assert "not a countermodel" in " ".join(report.reasons)


def test_mcc008_same_context_review_gets_no_independent_credit():
    report = assess(
        trigger_signals=("EXTERNAL_REVIEW",),
        external_review_present=True,
        external_review_process_independent=False,
        external_review_lineage_independent=False,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.INDEPENDENT_REVIEW_REQUIRED
    assert report.independent_review_credit is False


def test_mcc009_domain_calibration_is_not_globalized():
    report = assess(
        trigger_signals=("DOMAIN_TRANSFER",),
        calibrated_domains=("retrieval",),
        target_domain="mechanism_identification",
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CANNOT_CHECK
    assert "mechanism_identification" in " ".join(report.reasons)


def test_mcc010_low_value_reflection_respects_cost_gate():
    report = assess(
        trigger_signals=("LOW_VALUE_UNCERTAINTY",),
        reflection_cost=10.0,
        expected_failure_cost=0.5,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.NO_AUDIT_REQUIRED


def test_mcc011_calibration_improvement_is_not_capability_improvement():
    report = assess(
        trigger_signals=("FEEDBACK_UPDATE",),
        calibration_improved=True,
        task_sensitivity_improved=False,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CALIBRATED_NO_NEW_GAP
    assert report.capability_upgrade_authorized is False
    assert "not represented as a capability upgrade" in " ".join(report.reasons)


def test_mcc012_missing_external_outcome_evidence_fails_closed():
    report = assess(
        trigger_signals=("HIGH_CONFIDENCE_ERROR",),
        outcome_evidence_available=False,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CANNOT_CHECK


def test_mcc013_known_operator_resolving_cut_prevents_operator_invention():
    report = assess(
        trigger_signals=("TARGET_UNREACHABLE",),
        target_reachable=False,
        epistemic_cut_identified=True,
        incumbent_operator_can_resolve_cut=True,
        known_failure_fiber="experiment_design",
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.KNOWN_WEAKNESS
    assert report.requires_new_operator_benchmark is False


def test_mcc014_clean_audit_does_not_manufacture_a_gap():
    report = assess(
        trigger_signals=("HIGH_VALUE_CHECKPOINT",),
        outcome_evidence_available=True,
        repeated_unclassified_residuals=0,
        explanation_required_elements=("assumptions", "mechanism", "falsifier"),
        explanation_provided_elements=("assumptions", "mechanism", "falsifier"),
        countermodel_requested=True,
        countermodel_supplied=True,
        external_review_present=True,
        external_review_process_independent=True,
        external_review_lineage_independent=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CALIBRATED_NO_NEW_GAP
    assert report.independent_review_credit is True
    assert report.audit_opened_a_gap is False


def test_high_value_trigger_overrides_reflection_cost_gate():
    report = assess(
        trigger_signals=("HIGH_CONFIDENCE_ERROR",),
        reflection_cost=100.0,
        expected_failure_cost=1.0,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CALIBRATION_WEAKNESS


def test_unidentified_cut_cannot_support_missing_operator_claim():
    report = assess(
        trigger_signals=("TARGET_UNREACHABLE",),
        target_reachable=False,
        epistemic_cut_identified=False,
        incumbent_operator_can_resolve_cut=False,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CANNOT_CHECK
    assert report.requires_new_operator_benchmark is False


def test_unregistered_trigger_fails_closed():
    report = assess(
        trigger_signals=("MYSTERY_REFLECTION_SIGNAL",),
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CANNOT_CHECK


def test_feedback_effects_must_be_measured_before_interpretation():
    report = assess(
        trigger_signals=("FEEDBACK_UPDATE",),
        calibration_improved=True,
        task_sensitivity_improved=None,
        outcome_evidence_available=True,
    )
    assert report.verdict == MetacognitiveAuditVerdict.CANNOT_CHECK


@pytest.mark.parametrize(
    "field,value",
    [
        ("reflection_cost", -1.0),
        ("expected_failure_cost", -1.0),
        ("repeated_unclassified_residuals", -1),
    ],
)
def test_negative_measurements_are_rejected(field, value):
    kwargs = {field: value}
    with pytest.raises(ValueError):
        MetacognitiveAuditCase(**kwargs)


def test_empty_typed_values_are_rejected():
    with pytest.raises(ValueError):
        MetacognitiveAuditCase(trigger_signals=("",))
    with pytest.raises(ValueError):
        MetacognitiveAuditCase(explanation_required_elements=("",))
    with pytest.raises(ValueError):
        MetacognitiveAuditCase(calibrated_domains=("",))
