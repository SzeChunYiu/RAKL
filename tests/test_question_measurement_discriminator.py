from __future__ import annotations

from rakl.question_measurement_discriminator import (
    InterventionOutcome,
    ResponsibilityDiscriminatorContract,
    ResponsibilityDiscriminatorEvidence,
    ResponsibilityVerdict,
    assess_responsibility,
    project_identified_residual,
)
from rakl.recursive_framework_audit import AuditAction, AuditNode, decide


PERSIST = InterventionOutcome.RESIDUAL_PERSISTS
RESOLVE = InterventionOutcome.RESIDUAL_RESOLVED
UNKNOWN = InterventionOutcome.CANNOT_CHECK


def _contract() -> ResponsibilityDiscriminatorContract:
    return ResponsibilityDiscriminatorContract(
        residual_id="r1",
        question_intervention_id="q1",
        measurement_intervention_id="m1",
        evaluator_epoch="eval-v1",
        evidence_cutoff="cut-v1",
        resource_contract="cpu-local-v1",
    )


def _evidence(q: InterventionOutcome, m: InterventionOutcome, joint: InterventionOutcome) -> ResponsibilityDiscriminatorEvidence:
    return ResponsibilityDiscriminatorEvidence(
        residual_id="r1",
        question_intervention_id="q1",
        measurement_intervention_id="m1",
        evaluator_epoch="eval-v1",
        evidence_cutoff="cut-v1",
        resource_contract="cpu-local-v1",
        baseline_outcome=PERSIST,
        question_only_outcome=q,
        measurement_only_outcome=m,
        joint_outcome=joint,
    )


def _rfa_action(decision) -> AuditAction:
    residual = project_identified_residual(decision)
    assert residual is not None
    return decide(AuditNode(closure_coordinates_pass=False, material_open_residual=True), residual).action


def test_question_only_localizes_to_existing_reframe_action() -> None:
    decision = assess_responsibility(_contract(), _evidence(RESOLVE, PERSIST, RESOLVE))
    assert decision.verdict is ResponsibilityVerdict.QUESTION_RESPONSIBLE
    assert _rfa_action(decision) is AuditAction.REFRAME_QUESTION


def test_measurement_only_localizes_to_existing_measurement_action() -> None:
    decision = assess_responsibility(_contract(), _evidence(PERSIST, RESOLVE, RESOLVE))
    assert decision.verdict is ResponsibilityVerdict.MEASUREMENT_RESPONSIBLE
    assert _rfa_action(decision) is AuditAction.REVISE_MEASUREMENT


def test_both_single_coordinate_repairs_refuse_unique_localization() -> None:
    decision = assess_responsibility(_contract(), _evidence(RESOLVE, RESOLVE, RESOLVE))
    assert decision.verdict is ResponsibilityVerdict.BOTH_PLAUSIBLE
    assert _rfa_action(decision) is AuditAction.RUN_DISCRIMINATOR


def test_joint_only_records_interaction_not_unique_cause() -> None:
    decision = assess_responsibility(_contract(), _evidence(PERSIST, PERSIST, RESOLVE))
    assert decision.verdict is ResponsibilityVerdict.JOINT_ONLY
    assert _rfa_action(decision) is AuditAction.RUN_DISCRIMINATOR


def test_neither_local_broadens_audit_instead_of_inventing_cause() -> None:
    decision = assess_responsibility(_contract(), _evidence(PERSIST, PERSIST, PERSIST))
    assert decision.verdict is ResponsibilityVerdict.NEITHER_LOCAL
    assert decision.identified_coordinates == ()
    assert project_identified_residual(decision) is None


def test_missing_intervention_is_cannot_check_not_no_effect() -> None:
    decision = assess_responsibility(_contract(), _evidence(UNKNOWN, PERSIST, PERSIST))
    assert decision.verdict is ResponsibilityVerdict.CANNOT_CHECK
    assert project_identified_residual(decision) is None


def test_evaluator_epoch_mismatch_fails_closed() -> None:
    evidence = _evidence(RESOLVE, PERSIST, RESOLVE)
    evidence = ResponsibilityDiscriminatorEvidence(
        **{**evidence.__dict__, "evaluator_epoch": "eval-v2"}
    )
    decision = assess_responsibility(_contract(), evidence)
    assert decision.verdict is ResponsibilityVerdict.CANNOT_CHECK


def test_discriminator_objects_never_grant_authority() -> None:
    contract = _contract()
    decision = assess_responsibility(contract, _evidence(RESOLVE, PERSIST, RESOLVE))
    assert contract.grants_scientific_authority is False
    assert contract.grants_method_promotion_authority is False
    assert decision.grants_scientific_authority is False
    assert decision.grants_method_promotion_authority is False
