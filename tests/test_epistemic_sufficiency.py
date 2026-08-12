from dataclasses import replace

from rakl.authority_ledger import AuthorityAxis
from rakl.epistemic_sufficiency import (
    AcquisitionKind,
    EpistemicAction,
    EpistemicDecisionCase,
    EpistemicDecisionVerdict,
    EvidenceAcquisitionAction,
    EvidenceObligation,
    ObligationKind,
    assess_epistemic_action,
    recommend_epistemic_action,
)


def _case(**overrides):
    values = dict(
        case_id="case-1",
        claim_id="claim-1",
        requested_axis=AuthorityAxis.MECHANISM,
        known_answer_validated=True,
        frozen_before_action=True,
        support_sufficient=False,
        refutation_sufficient=False,
        conflict_present=False,
        scope_overbroad=False,
        narrower_scope_available=False,
        obligations=(),
        acquisition_actions=(),
        max_acquisition_cost=10.0,
        terminal_abstention_licensed=True,
        irreversible_consequential_action_already_taken=False,
    )
    values.update(overrides)
    return EpistemicDecisionCase(**values)


def test_sufficient_support_requires_commit_not_blanket_abstention():
    case = _case(support_sufficient=True)
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.COMMIT_SUPPORTED
    assert expected.grants_scientific_authority is False

    observed = assess_epistemic_action(case, EpistemicAction.ABSTAIN_CANNOT_CHECK)
    assert observed.verdict is EpistemicDecisionVerdict.PREMATURE_ABSTENTION


def test_sufficient_refutation_requires_refuting_commit():
    case = _case(refutation_sufficient=True)
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.COMMIT_REFUTED


def test_missing_measurement_with_bounded_action_requires_evidence_gathering():
    obligation = EvidenceObligation("measure-pressure", ObligationKind.EVIDENCE)
    action = EvidenceAcquisitionAction(
        "read-calibrated-gauge",
        AcquisitionKind.GATHER_EVIDENCE,
        (obligation.obligation_id,),
        cost=1.0,
    )
    case = _case(obligations=(obligation,), acquisition_actions=(action,))
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.GATHER_MORE_EVIDENCE
    assert expected.recommended_action_id == "read-calibrated-gauge"

    premature = assess_epistemic_action(case, EpistemicAction.ABSTAIN_CANNOT_CHECK)
    assert premature.verdict is EpistemicDecisionVerdict.PREMATURE_ABSTENTION


def test_unavailable_route_licenses_terminal_abstention_when_registered():
    obligation = EvidenceObligation("missing-measurement", ObligationKind.EVIDENCE)
    case = _case(obligations=(obligation,), terminal_abstention_licensed=True)
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.ABSTAIN_CANNOT_CHECK
    assert assess_epistemic_action(case, EpistemicAction.ABSTAIN_CANNOT_CHECK).verdict is EpistemicDecisionVerdict.CORRECT_NEXT_ACTION


def test_unavailable_route_can_be_blocked_without_claiming_terminal_abstention():
    obligation = EvidenceObligation("external-lab", ObligationKind.EXTERNAL_VERIFICATION)
    case = _case(obligations=(obligation,), terminal_abstention_licensed=False)
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.BLOCKED_NO_AVAILABLE_ROUTE


def test_conflicting_evidence_selects_registered_discriminator():
    obligation = EvidenceObligation("distinguish-m1-m2", ObligationKind.DISCRIMINATOR)
    discriminator = EvidenceAcquisitionAction(
        "regime-shift-probe",
        AcquisitionKind.RUN_DISCRIMINATOR,
        (obligation.obligation_id,),
        cost=2.0,
    )
    case = _case(
        conflict_present=True,
        obligations=(obligation,),
        acquisition_actions=(discriminator,),
    )
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.RUN_DISCRIMINATOR
    assert expected.recommended_action_id == "regime-shift-probe"


def test_wrong_discriminator_identity_is_not_credited():
    obligation = EvidenceObligation("distinguish", ObligationKind.DISCRIMINATOR)
    right = EvidenceAcquisitionAction(
        "right-probe",
        AcquisitionKind.RUN_DISCRIMINATOR,
        (obligation.obligation_id,),
        cost=1.0,
    )
    wrong = EvidenceAcquisitionAction(
        "wrong-probe",
        AcquisitionKind.RUN_DISCRIMINATOR,
        (obligation.obligation_id,),
        cost=5.0,
    )
    case = _case(
        conflict_present=True,
        obligations=(obligation,),
        acquisition_actions=(right, wrong),
    )
    result = assess_epistemic_action(
        case,
        EpistemicAction.RUN_DISCRIMINATOR,
        observed_action_id="wrong-probe",
    )
    assert result.verdict is EpistemicDecisionVerdict.WRONG_EVIDENCE_ACQUISITION
    assert result.recommended_action_id == "right-probe"


def test_scope_overbreadth_is_restricted_before_commit():
    case = _case(
        support_sufficient=True,
        scope_overbroad=True,
        narrower_scope_available=True,
    )
    expected = recommend_epistemic_action(case)
    assert expected.recommended_action is EpistemicAction.RESTRICT_SCOPE

    bad = assess_epistemic_action(case, EpistemicAction.COMMIT_SUPPORTED)
    assert bad.verdict is EpistemicDecisionVerdict.UNLICENSED_COMMIT


def test_irreversible_action_before_required_check_is_posthoc_abstention_failure():
    obligation = EvidenceObligation("safety-check", ObligationKind.EVIDENCE)
    action = EvidenceAcquisitionAction(
        "check-first",
        AcquisitionKind.GATHER_EVIDENCE,
        (obligation.obligation_id,),
        cost=1.0,
    )
    case = _case(
        obligations=(obligation,),
        acquisition_actions=(action,),
        irreversible_consequential_action_already_taken=True,
    )
    result = recommend_epistemic_action(case)
    assert result.verdict is EpistemicDecisionVerdict.POST_HOC_ABSTENTION
    assert "irreversible_action_preceded_required_epistemic_check" in result.reasons


def test_continuing_to_gather_after_sufficiency_is_detected():
    case = _case(support_sufficient=True)
    result = assess_epistemic_action(case, EpistemicAction.GATHER_MORE_EVIDENCE)
    assert result.verdict is EpistemicDecisionVerdict.UNNECESSARY_EVIDENCE_GATHERING


def test_commit_before_sufficiency_is_unlicensed():
    obligation = EvidenceObligation("need-replication", ObligationKind.EVIDENCE)
    case = _case(obligations=(obligation,), terminal_abstention_licensed=True)
    result = assess_epistemic_action(case, EpistemicAction.COMMIT_SUPPORTED)
    assert result.verdict is EpistemicDecisionVerdict.UNLICENSED_COMMIT


def test_unknown_or_unvalidated_gold_fails_closed():
    unknown = recommend_epistemic_action(_case(known_answer_validated=None))
    assert unknown.verdict is EpistemicDecisionVerdict.CANNOT_CHECK

    unvalidated = recommend_epistemic_action(_case(known_answer_validated=False))
    assert unvalidated.verdict is EpistemicDecisionVerdict.CANNOT_CHECK


def test_posthoc_decision_contract_is_invalid():
    result = recommend_epistemic_action(_case(frozen_before_action=False))
    assert result.verdict is EpistemicDecisionVerdict.INVALID


def test_alignment_and_external_verification_actions_remain_distinct():
    align_obligation = EvidenceObligation("align-qoi", ObligationKind.ALIGNMENT)
    align_action = EvidenceAcquisitionAction(
        "align-contexts",
        AcquisitionKind.CHECK_ALIGNMENT,
        (align_obligation.obligation_id,),
        cost=1.0,
    )
    align_case = _case(
        obligations=(align_obligation,),
        acquisition_actions=(align_action,),
    )
    assert recommend_epistemic_action(align_case).recommended_action is EpistemicAction.CHECK_ALIGNMENT

    verify_obligation = EvidenceObligation("external-check", ObligationKind.EXTERNAL_VERIFICATION)
    verify_action = EvidenceAcquisitionAction(
        "request-independent-check",
        AcquisitionKind.REQUEST_EXTERNAL_VERIFICATION,
        (verify_obligation.obligation_id,),
        cost=1.0,
    )
    verify_case = _case(
        obligations=(verify_obligation,),
        acquisition_actions=(verify_action,),
    )
    assert recommend_epistemic_action(verify_case).recommended_action is EpistemicAction.REQUEST_EXTERNAL_VERIFICATION
