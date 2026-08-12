"""Proposal-only sequential evidence-sufficiency mechanics (refs #429).

Scientific caution is not equivalent to always returning ``CANNOT_CHECK``.
Given an explicit, known-answer-validated evidence-sufficiency contract, a
research agent may be required to conclude, narrow scope, acquire one decisive
measurement, run a discriminator, repair context alignment, seek a protected
external check, or truly abstain.

This module operates only on bounded, externally supplied decision variables. It
does not infer semantic sufficiency from prose and it never grants scientific
authority. Canonical authority changes remain owned by the protected scientific
transition path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence, Tuple

from .authority_ledger import AuthorityAxis

__all__ = [
    "AcquisitionKind",
    "EpistemicAction",
    "EpistemicDecisionAssessment",
    "EpistemicDecisionCase",
    "EpistemicDecisionVerdict",
    "EvidenceAcquisitionAction",
    "EvidenceObligation",
    "ObligationKind",
    "assess_epistemic_action",
    "recommend_epistemic_action",
]


class ObligationKind(str, Enum):
    EVIDENCE = "EVIDENCE"
    DISCRIMINATOR = "DISCRIMINATOR"
    ALIGNMENT = "ALIGNMENT"
    EXTERNAL_VERIFICATION = "EXTERNAL_VERIFICATION"


class AcquisitionKind(str, Enum):
    GATHER_EVIDENCE = "GATHER_EVIDENCE"
    RUN_DISCRIMINATOR = "RUN_DISCRIMINATOR"
    CHECK_ALIGNMENT = "CHECK_ALIGNMENT"
    REQUEST_EXTERNAL_VERIFICATION = "REQUEST_EXTERNAL_VERIFICATION"


class EpistemicAction(str, Enum):
    COMMIT_SUPPORTED = "COMMIT_SUPPORTED"
    COMMIT_REFUTED = "COMMIT_REFUTED"
    RESTRICT_SCOPE = "RESTRICT_SCOPE"
    GATHER_MORE_EVIDENCE = "GATHER_MORE_EVIDENCE"
    RUN_DISCRIMINATOR = "RUN_DISCRIMINATOR"
    CHECK_ALIGNMENT = "CHECK_ALIGNMENT"
    REQUEST_EXTERNAL_VERIFICATION = "REQUEST_EXTERNAL_VERIFICATION"
    ABSTAIN_CANNOT_CHECK = "ABSTAIN_CANNOT_CHECK"
    BLOCKED_NO_AVAILABLE_ROUTE = "BLOCKED_NO_AVAILABLE_ROUTE"


class EpistemicDecisionVerdict(str, Enum):
    CORRECT_NEXT_ACTION = "CORRECT_NEXT_ACTION"
    PREMATURE_ABSTENTION = "PREMATURE_ABSTENTION"
    POST_HOC_ABSTENTION = "POST_HOC_ABSTENTION"
    UNLICENSED_COMMIT = "UNLICENSED_COMMIT"
    WRONG_EVIDENCE_ACQUISITION = "WRONG_EVIDENCE_ACQUISITION"
    UNNECESSARY_EVIDENCE_GATHERING = "UNNECESSARY_EVIDENCE_GATHERING"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class EvidenceObligation:
    obligation_id: str
    kind: ObligationKind
    blocking: bool = True
    satisfied: bool = False

    def __post_init__(self) -> None:
        if not self.obligation_id.strip():
            raise ValueError("evidence obligation requires a non-empty id")


@dataclass(frozen=True)
class EvidenceAcquisitionAction:
    action_id: str
    kind: AcquisitionKind
    resolves_obligation_ids: Tuple[str, ...]
    cost: float
    available: bool = True
    irreversible: bool = False

    def __post_init__(self) -> None:
        if not self.action_id.strip():
            raise ValueError("evidence acquisition action requires a non-empty id")
        if self.cost < 0:
            raise ValueError("evidence acquisition cost cannot be negative")
        if not self.resolves_obligation_ids:
            raise ValueError("evidence acquisition action must target an obligation")


@dataclass(frozen=True)
class EpistemicDecisionCase:
    case_id: str
    claim_id: str
    requested_axis: AuthorityAxis
    known_answer_validated: bool | None
    frozen_before_action: bool | None
    support_sufficient: bool
    refutation_sufficient: bool
    conflict_present: bool
    scope_overbroad: bool
    narrower_scope_available: bool
    obligations: Tuple[EvidenceObligation, ...]
    acquisition_actions: Tuple[EvidenceAcquisitionAction, ...]
    max_acquisition_cost: float
    terminal_abstention_licensed: bool
    irreversible_consequential_action_already_taken: bool = False

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.claim_id.strip():
            raise ValueError("epistemic decision case requires case and claim ids")
        if self.max_acquisition_cost < 0:
            raise ValueError("max acquisition cost cannot be negative")
        ids = [item.obligation_id for item in self.obligations]
        if len(ids) != len(set(ids)):
            raise ValueError("epistemic obligations must have unique ids")
        action_ids = [item.action_id for item in self.acquisition_actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("evidence acquisition actions must have unique ids")


@dataclass(frozen=True)
class EpistemicDecisionAssessment:
    verdict: EpistemicDecisionVerdict
    recommended_action: EpistemicAction | None
    recommended_action_id: str | None = None
    reasons: Tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False


def _open_blockers(case: EpistemicDecisionCase) -> tuple[EvidenceObligation, ...]:
    return tuple(item for item in case.obligations if item.blocking and not item.satisfied)


def _eligible_actions(
    case: EpistemicDecisionCase,
    blockers: Sequence[EvidenceObligation],
) -> tuple[EvidenceAcquisitionAction, ...]:
    blocker_ids = {item.obligation_id for item in blockers}
    return tuple(
        sorted(
            (
                action
                for action in case.acquisition_actions
                if action.available
                and action.cost <= case.max_acquisition_cost
                and blocker_ids.intersection(action.resolves_obligation_ids)
            ),
            key=lambda item: (item.cost, item.action_id),
        )
    )


def _action_for_kind(kind: AcquisitionKind) -> EpistemicAction:
    return {
        AcquisitionKind.GATHER_EVIDENCE: EpistemicAction.GATHER_MORE_EVIDENCE,
        AcquisitionKind.RUN_DISCRIMINATOR: EpistemicAction.RUN_DISCRIMINATOR,
        AcquisitionKind.CHECK_ALIGNMENT: EpistemicAction.CHECK_ALIGNMENT,
        AcquisitionKind.REQUEST_EXTERNAL_VERIFICATION: EpistemicAction.REQUEST_EXTERNAL_VERIFICATION,
    }[kind]


def recommend_epistemic_action(case: EpistemicDecisionCase) -> EpistemicDecisionAssessment:
    """Recommend the next epistemically licensed action for a frozen known-answer case."""

    if case.known_answer_validated is None:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CANNOT_CHECK,
            None,
            reasons=("known_answer_validation_unknown",),
        )
    if case.known_answer_validated is False:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CANNOT_CHECK,
            None,
            reasons=("decision_contract_not_known_answer_validated",),
        )
    if case.frozen_before_action is None:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CANNOT_CHECK,
            None,
            reasons=("decision_freeze_chronology_unknown",),
        )
    if case.frozen_before_action is False:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.INVALID,
            None,
            reasons=("decision_contract_defined_posthoc",),
        )
    if case.support_sufficient and case.refutation_sufficient:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.INVALID,
            None,
            reasons=("support_and_refutation_both_marked_sufficient",),
        )

    blockers = _open_blockers(case)
    eligible = _eligible_actions(case, blockers)

    if case.irreversible_consequential_action_already_taken and blockers:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.POST_HOC_ABSTENTION,
            EpistemicAction.BLOCKED_NO_AVAILABLE_ROUTE,
            reasons=("irreversible_action_preceded_required_epistemic_check",),
        )

    # Scope repair precedes commitment: sufficient evidence for a narrower claim
    # does not license the overbroad claim.
    if case.scope_overbroad:
        if case.narrower_scope_available:
            return EpistemicDecisionAssessment(
                EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
                EpistemicAction.RESTRICT_SCOPE,
            )
        if eligible:
            chosen = eligible[0]
            return EpistemicDecisionAssessment(
                EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
                _action_for_kind(chosen.kind),
                chosen.action_id,
            )
        action = (
            EpistemicAction.ABSTAIN_CANNOT_CHECK
            if case.terminal_abstention_licensed
            else EpistemicAction.BLOCKED_NO_AVAILABLE_ROUTE
        )
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
            action,
            reasons=("overbroad_scope_not_repairable_with_available_route",),
        )

    # Unresolved conflict must be discriminated if possible, never averaged away.
    if case.conflict_present:
        discriminators = tuple(
            action for action in eligible if action.kind is AcquisitionKind.RUN_DISCRIMINATOR
        )
        if discriminators:
            chosen = discriminators[0]
            return EpistemicDecisionAssessment(
                EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
                EpistemicAction.RUN_DISCRIMINATOR,
                chosen.action_id,
            )
        action = (
            EpistemicAction.ABSTAIN_CANNOT_CHECK
            if case.terminal_abstention_licensed
            else EpistemicAction.BLOCKED_NO_AVAILABLE_ROUTE
        )
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
            action,
            reasons=("unresolved_evidence_conflict",),
        )

    if blockers:
        # Prefer the cheapest action that addresses a blocking obligation. The
        # action kind is part of the known-answer contract; cost only breaks ties.
        if eligible:
            chosen = eligible[0]
            return EpistemicDecisionAssessment(
                EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
                _action_for_kind(chosen.kind),
                chosen.action_id,
            )
        action = (
            EpistemicAction.ABSTAIN_CANNOT_CHECK
            if case.terminal_abstention_licensed
            else EpistemicAction.BLOCKED_NO_AVAILABLE_ROUTE
        )
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
            action,
            reasons=("blocking_evidence_obligation_has_no_available_bounded_route",),
        )

    if case.support_sufficient:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
            EpistemicAction.COMMIT_SUPPORTED,
        )
    if case.refutation_sufficient:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
            EpistemicAction.COMMIT_REFUTED,
        )

    action = (
        EpistemicAction.ABSTAIN_CANNOT_CHECK
        if case.terminal_abstention_licensed
        else EpistemicAction.BLOCKED_NO_AVAILABLE_ROUTE
    )
    return EpistemicDecisionAssessment(
        EpistemicDecisionVerdict.CORRECT_NEXT_ACTION,
        action,
        reasons=("no_sufficient_evidence_and_no_registered_blocking_route",),
    )


def assess_epistemic_action(
    case: EpistemicDecisionCase,
    observed_action: EpistemicAction,
    *,
    observed_action_id: str | None = None,
) -> EpistemicDecisionAssessment:
    """Classify an observed action against the frozen sequential epistemic contract."""

    expected = recommend_epistemic_action(case)
    if expected.verdict in {
        EpistemicDecisionVerdict.CANNOT_CHECK,
        EpistemicDecisionVerdict.INVALID,
        EpistemicDecisionVerdict.POST_HOC_ABSTENTION,
    }:
        return expected

    recommended = expected.recommended_action
    if observed_action is recommended:
        if expected.recommended_action_id is not None and observed_action_id != expected.recommended_action_id:
            return EpistemicDecisionAssessment(
                EpistemicDecisionVerdict.WRONG_EVIDENCE_ACQUISITION,
                recommended,
                expected.recommended_action_id,
                reasons=("wrong_acquisition_action_for_open_obligation",),
            )
        return expected

    if observed_action is EpistemicAction.ABSTAIN_CANNOT_CHECK and recommended in {
        EpistemicAction.GATHER_MORE_EVIDENCE,
        EpistemicAction.RUN_DISCRIMINATOR,
        EpistemicAction.CHECK_ALIGNMENT,
        EpistemicAction.REQUEST_EXTERNAL_VERIFICATION,
        EpistemicAction.RESTRICT_SCOPE,
        EpistemicAction.COMMIT_SUPPORTED,
        EpistemicAction.COMMIT_REFUTED,
    }:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.PREMATURE_ABSTENTION,
            recommended,
            expected.recommended_action_id,
            reasons=("abstained_before_licensed_epistemic_resolution",),
        )

    if observed_action in {EpistemicAction.COMMIT_SUPPORTED, EpistemicAction.COMMIT_REFUTED}:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.UNLICENSED_COMMIT,
            recommended,
            expected.recommended_action_id,
            reasons=("committed_before_registered_evidence_sufficiency",),
        )

    if observed_action in {
        EpistemicAction.GATHER_MORE_EVIDENCE,
        EpistemicAction.RUN_DISCRIMINATOR,
        EpistemicAction.CHECK_ALIGNMENT,
        EpistemicAction.REQUEST_EXTERNAL_VERIFICATION,
    } and recommended in {EpistemicAction.COMMIT_SUPPORTED, EpistemicAction.COMMIT_REFUTED}:
        return EpistemicDecisionAssessment(
            EpistemicDecisionVerdict.UNNECESSARY_EVIDENCE_GATHERING,
            recommended,
            reasons=("continued_gathering_after_evidence_was_sufficient",),
        )

    return EpistemicDecisionAssessment(
        EpistemicDecisionVerdict.WRONG_EVIDENCE_ACQUISITION,
        recommended,
        expected.recommended_action_id,
        reasons=("observed_next_action_does_not_match_epistemic_contract",),
    )
