from dataclasses import replace

import pytest

from rakl.search_policy_learning import (
    CounterfactualSearchRun,
    FailureDrivenUpdateVerdict,
    RootCauseCertificationVerdict,
    SearchFailureSignature,
    SearchPolicy,
    SearchRootCauseDiagnostic,
    build_search_failure_receipt,
    certify_search_root_cause,
    derive_search_policy_update,
    propose_registered_counterfactual_policy,
)


def _run(run_id, policy, passed):
    return CounterfactualSearchRun(
        run_id=run_id,
        policy=policy,
        evaluation_receipt_hash=f"eval-{run_id}",
        outcome_passed=passed,
        case_subject_hash="case",
        task_input_hash="task",
        candidate_pool_hash="pool",
        model_subject_hash="model",
        tool_contract_hash="tools",
        resource_contract_hash="resources",
    )


def _issued_low_information_certificate():
    incumbent = SearchPolicy("p1", min_expected_information_gain=0.0)
    counterfactual = propose_registered_counterfactual_policy(
        incumbent,
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        to_policy_version="probe-p2",
    )
    diagnostic = SearchRootCauseDiagnostic(
        diagnostic_id="diag-binding",
        certificate_id="cert-binding",
        failure_id="failure-binding",
        question_id="q-binding",
        hypothesized_signature=SearchFailureSignature.LOW_INFORMATION_GAIN,
        validated_reference_signature=SearchFailureSignature.LOW_INFORMATION_GAIN,
        diagnosis_reference_receipt_hash="gold-binding",
        causal_evidence_ids=("case-binding",),
        baseline=_run("baseline-binding", incumbent, False),
        counterfactual=_run("counterfactual-binding", counterfactual, True),
        frozen_before_policy_update=True,
    )
    result = certify_search_root_cause(diagnostic)
    assert result.verdict is RootCauseCertificationVerdict.ROOT_CAUSE_CERTIFIED
    assert result.certificate is not None
    return incumbent, result.certificate


def test_dataclass_replace_cannot_forge_an_issued_root_cause_certificate():
    _, certificate = _issued_low_information_certificate()
    with pytest.raises(ValueError, match="issued immutable record"):
        replace(
            certificate,
            signature=SearchFailureSignature.QUERY_DRIFT,
            intervention_parameters=("max_semantic_expansion_terms",),
        )


def test_same_version_policy_content_drift_invalidates_certified_repair_subject():
    incumbent, certificate = _issued_low_information_certificate()
    receipt = build_search_failure_receipt(certificate)

    drifted_same_version = replace(
        incumbent,
        min_expected_information_gain=0.05,
    )
    result = derive_search_policy_update(
        receipt,
        drifted_same_version,
        update_id="update-after-drift",
        to_policy_version="p2",
    )

    assert result.verdict is FailureDrivenUpdateVerdict.INVALID
    assert result.proposal is None
    assert "certified_root_cause_subject_not_valid_for_current_policy_repair" in result.reasons


def test_exact_certified_incumbent_still_authorizes_only_the_registered_challenger():
    incumbent, certificate = _issued_low_information_certificate()
    receipt = build_search_failure_receipt(certificate)
    result = derive_search_policy_update(
        receipt,
        incumbent,
        update_id="update-exact",
        to_policy_version="p2",
    )
    assert result.verdict is FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED
    assert result.proposal is not None
    assert result.proposal.root_cause_certificate_id == certificate.certificate_id
    assert result.proposal.claims_policy_is_better is False
