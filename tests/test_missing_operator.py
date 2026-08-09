import pytest

from rakl.missing_operator import (
    MissingOperatorFailureCause as Cause,
    MissingOperatorTrial,
    MissingOperatorVerdict as Verdict,
    evaluate_missing_operator_trial,
)

H1 = "a" * 64
H2 = "b" * 64


def trial(**overrides):
    values = dict(
        world_id="sealed-primary",
        world_sha256=H1,
        evaluator_frozen_before_run=True,
        outcome_evidence_available=True,
        failure_cause=Cause.METHOD_BASIS,
        negative_history_preserved=True,
        resource_budget_matched=True,
        epistemic_cut_id="cut-1",
        incumbent_operator_can_resolve_cut=False,
        candidate_operator_family="INTERVENTION_DESIGN",
        candidate_definition_frozen_before_answer=True,
        primary_resolution_passed=True,
        fresh_transfer_world_id="sealed-transfer",
        fresh_transfer_world_sha256=H2,
        fresh_transfer_surface_shifted=True,
        fresh_transfer_passed=True,
    )
    values.update(overrides)
    return MissingOperatorTrial(**values)


def assess(**overrides):
    return evaluate_missing_operator_trial(trial(**overrides))


def test_success_is_proposal_only_and_never_authority():
    report = assess()
    assert report.verdict == Verdict.OPERATOR_FAMILY_PROPOSAL_ONLY
    assert report.gap_detected and report.operator_family_identified and report.fresh_transfer_validated
    assert report.eligible_for_matched_class_b_comparison
    assert not report.grants_scientific_authority
    assert not report.grants_target_authority
    assert not report.grants_method_promotion_authority
    assert not report.establishes_framework_saturation


def test_incumbent_solvable_world_does_not_invent_operator():
    report = assess(
        failure_cause=Cause.NONE,
        incumbent_operator_can_resolve_cut=True,
        candidate_operator_family=None,
        candidate_definition_frozen_before_answer=None,
        primary_resolution_passed=None,
        fresh_transfer_world_id=None,
        fresh_transfer_world_sha256=None,
        fresh_transfer_surface_shifted=None,
        fresh_transfer_passed=None,
    )
    assert report.verdict == Verdict.NO_NEW_OPERATOR_REQUIRED and not report.gap_detected


def test_missing_measurement_routes_to_evidence_not_method_invention():
    assert assess(failure_cause=Cause.MISSING_EVIDENCE_OR_MEASUREMENT).verdict == Verdict.EVIDENCE_ACQUISITION_REQUIRED


def test_implementation_failure_routes_to_repair():
    assert assess(failure_cause=Cause.IMPLEMENTATION).verdict == Verdict.IMPLEMENTATION_REPAIR_REQUIRED


def test_unknown_failure_cause_fails_closed():
    assert assess(failure_cause=Cause.UNKNOWN).verdict == Verdict.CANNOT_CHECK


def test_hidden_label_solver_leakage_invalidates_trial():
    assert assess(hidden_label_exposed_to_solver=True).verdict == Verdict.TRIAL_INVALID


def test_hidden_label_retrieval_leakage_invalidates_trial():
    assert assess(hidden_label_exposed_via_retrieval=True).verdict == Verdict.TRIAL_INVALID


def test_posthoc_evaluator_invalidates_trial():
    assert assess(evaluator_frozen_before_run=False).verdict == Verdict.TRIAL_INVALID


def test_unknown_evaluator_chronology_cannot_check():
    assert assess(evaluator_frozen_before_run=None).verdict == Verdict.CANNOT_CHECK


def test_negative_history_rewrite_invalidates_trial():
    assert assess(negative_history_preserved=False).verdict == Verdict.TRIAL_INVALID


def test_resource_mismatch_prevents_comparison():
    report = assess(resource_budget_matched=False)
    assert report.verdict == Verdict.CANNOT_COMPARE and not report.eligible_for_matched_class_b_comparison


def test_method_gap_requires_identified_epistemic_cut():
    assert assess(epistemic_cut_id=None).verdict == Verdict.CANNOT_CHECK


def test_existing_operator_resolution_reopens_incumbent():
    report = assess(incumbent_operator_can_resolve_cut=True)
    assert report.verdict == Verdict.NO_NEW_OPERATOR_REQUIRED


def test_gap_can_be_detected_before_operator_is_identified():
    report = assess(
        candidate_operator_family=None,
        candidate_definition_frozen_before_answer=None,
        primary_resolution_passed=None,
        fresh_transfer_world_id=None,
        fresh_transfer_world_sha256=None,
        fresh_transfer_surface_shifted=None,
        fresh_transfer_passed=None,
    )
    assert report.verdict == Verdict.METHOD_BASIS_GAP_DETECTED_OPERATOR_UNIDENTIFIED
    assert report.gap_detected and not report.operator_family_identified


def test_posthoc_candidate_semantic_expansion_invalidates_trial():
    assert assess(candidate_definition_frozen_before_answer=False).verdict == Verdict.TRIAL_INVALID


def test_nonresolving_candidate_is_refuted():
    report = assess(primary_resolution_passed=False)
    assert report.verdict == Verdict.REFUTED and report.gap_detected


def test_multiple_surviving_operator_families_preserve_nonidentifiability():
    report = assess(
        surviving_alternative_operator_families=("ACTIVE_SENSING", "INTERVENTION_DESIGN"),
        discriminating_probe_available=True,
    )
    assert report.verdict == Verdict.PARTIALLY_IDENTIFIED
    assert not report.operator_family_identified
    assert any("discriminating probe" in reason for reason in report.reasons)


def test_primary_fit_without_fresh_transfer_identity_cannot_check():
    report = assess(
        fresh_transfer_world_id=None,
        fresh_transfer_world_sha256=None,
        fresh_transfer_surface_shifted=None,
        fresh_transfer_passed=None,
    )
    assert report.verdict == Verdict.CANNOT_CHECK and report.operator_family_identified


def test_fresh_transfer_must_be_surface_or_domain_shifted():
    assert assess(fresh_transfer_surface_shifted=False).verdict == Verdict.CANNOT_CHECK


def test_primary_fit_but_transfer_failure_is_only_partial_identification():
    report = assess(fresh_transfer_passed=False)
    assert report.verdict == Verdict.PARTIALLY_IDENTIFIED
    assert report.operator_family_identified and not report.fresh_transfer_validated


def test_authority_claim_invalidates_benchmark_result():
    assert assess(scientific_or_target_authority_claimed=True).verdict == Verdict.TRIAL_INVALID
    assert assess(method_promotion_claimed=True).verdict == Verdict.TRIAL_INVALID


def test_same_context_review_gets_no_independent_credit():
    report = assess(
        independent_review_present=True,
        independent_review_process_context=False,
        independent_review_evidence_lineage=True,
    )
    assert not report.independent_review_credit


def test_two_axis_independence_is_required_for_review_credit():
    report = assess(
        independent_review_present=True,
        independent_review_process_context=True,
        independent_review_evidence_lineage=True,
    )
    assert report.independent_review_credit
    assert report.verdict == Verdict.OPERATOR_FAMILY_PROPOSAL_ONLY


def test_malformed_hashes_are_rejected_at_packet_construction():
    with pytest.raises(ValueError):
        trial(world_sha256="bad")
    with pytest.raises(ValueError):
        trial(fresh_transfer_world_sha256="bad")
