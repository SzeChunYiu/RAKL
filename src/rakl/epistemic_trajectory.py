"""Integrated Epistemic Mechanics trajectory benchmark core (refs #431).

Individual RAKL mechanisms can pass their own unit/property tests while failing
when composed. This module therefore evaluates a *trajectory* of epistemic
state-changing or authority-inert actions using standardized receipts. It does
not import the #427/#428/#430 challenger modules directly; adapters can normalize
those child reports (or external controls) into this contract after their exact
versions freeze.

The benchmark is intentionally objective/fail-closed. Gold steps must be
known-answer validated and frozen before candidate output. The evaluator checks
exact action, exact evidence/root binding, frozen step order, authority
continuity/noninterference, timing and negative-history preservation. A
correct-looking terminal action with wrong evidence therefore cannot pass, and
an always-CANNOT_CHECK strategy loses valid-update recall on positive controls.

No report here mutates scientific state or grants authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence, Tuple

__all__ = [
    "EpistemicStepFamily",
    "EpistemicTrajectoryCase",
    "GoldEpistemicStep",
    "ObservedEpistemicStep",
    "StepEvaluation",
    "TrajectoryEvaluation",
    "TrajectoryPanelMetrics",
    "TrajectoryVerdict",
    "evaluate_epistemic_trajectory",
    "summarize_trajectory_panel",
]


class EpistemicStepFamily(str, Enum):
    CLAIM_EVIDENCE_BINDING = "CLAIM_EVIDENCE_BINDING"
    PROVENANCE_INDEPENDENCE = "PROVENANCE_INDEPENDENCE"
    AUTHORITY_TRANSPORT = "AUTHORITY_TRANSPORT"
    SEQUENTIAL_SUFFICIENCY = "SEQUENTIAL_SUFFICIENCY"
    MECHANISM_FIDELITY = "MECHANISM_FIDELITY"
    REVISION_SUPERSESSION = "REVISION_SUPERSESSION"
    EXPERIENCE_NONINTERFERENCE = "EXPERIENCE_NONINTERFERENCE"
    SEARCH_ROUTING = "SEARCH_ROUTING"
    LEGITIMATE_UPDATE_CONTROL = "LEGITIMATE_UPDATE_CONTROL"


class TrajectoryVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class GoldEpistemicStep:
    step_id: str
    family: EpistemicStepFamily
    licensed_action: str
    forbidden_actions: Tuple[str, ...] = ()
    required_evidence_ids: Tuple[str, ...] = ()
    required_root_ids: Tuple[str, ...] = ()
    required_negative_history_ids: Tuple[str, ...] = ()
    authority_change_licensed: bool = False
    expected_authority_after: str | None = None
    positive_update_opportunity: bool = False
    latest_safe_sequence: int | None = None

    def __post_init__(self) -> None:
        if not self.step_id.strip() or not self.licensed_action.strip():
            raise ValueError("gold epistemic step requires step id and licensed action")
        if self.licensed_action in set(self.forbidden_actions):
            raise ValueError("licensed action cannot also be forbidden")
        if self.authority_change_licensed and self.expected_authority_after is None:
            raise ValueError("authority-changing gold step requires expected authority-after fingerprint")
        if not self.authority_change_licensed and self.expected_authority_after is not None:
            raise ValueError("authority-inert gold step cannot prescribe a changed authority fingerprint")
        if self.latest_safe_sequence is not None and self.latest_safe_sequence < 1:
            raise ValueError("latest safe sequence must be positive")


@dataclass(frozen=True)
class ObservedEpistemicStep:
    step_id: str
    family: EpistemicStepFamily
    action: str
    evidence_ids: Tuple[str, ...]
    root_ids: Tuple[str, ...]
    negative_history_ids: Tuple[str, ...]
    authority_before: str
    authority_after: str
    sequence_index: int

    def __post_init__(self) -> None:
        if not self.step_id.strip() or not self.action.strip():
            raise ValueError("observed epistemic step requires step id and action")
        if not self.authority_before.strip() or not self.authority_after.strip():
            raise ValueError("observed step requires authority fingerprints")
        if self.sequence_index < 1:
            raise ValueError("observed sequence index must be positive")


@dataclass(frozen=True)
class EpistemicTrajectoryCase:
    case_id: str
    initial_authority_fingerprint: str
    gold_steps: Tuple[GoldEpistemicStep, ...]
    known_answer_validated: bool | None
    frozen_before_output: bool | None
    twin_family_id: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.initial_authority_fingerprint.strip():
            raise ValueError("trajectory case requires case id and initial authority fingerprint")
        if not self.gold_steps:
            raise ValueError("trajectory case requires at least one gold step")
        ids = [step.step_id for step in self.gold_steps]
        if len(ids) != len(set(ids)):
            raise ValueError("gold step ids must be unique")


@dataclass(frozen=True)
class StepEvaluation:
    step_id: str
    family: EpistemicStepFamily
    action_correct: bool
    evidence_binding_correct: bool
    root_accounting_correct: bool
    authority_transition_correct: bool
    timing_correct: bool
    negative_history_preserved: bool
    authority_leak: bool
    premature_abstention: bool
    forbidden_action_taken: bool
    reasons: Tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return all(
            (
                self.action_correct,
                self.evidence_binding_correct,
                self.root_accounting_correct,
                self.authority_transition_correct,
                self.timing_correct,
                self.negative_history_preserved,
                not self.authority_leak,
                not self.premature_abstention,
                not self.forbidden_action_taken,
            )
        )


@dataclass(frozen=True)
class TrajectoryEvaluation:
    case_id: str
    verdict: TrajectoryVerdict
    steps: Tuple[StepEvaluation, ...] = ()
    continuity_correct: bool | None = None
    reasons: Tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.verdict is TrajectoryVerdict.PASS

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class TrajectoryPanelMetrics:
    case_count: int
    valid_case_count: int
    pass_count: int
    step_count: int
    authority_leak_count: int
    authority_inert_opportunity_count: int
    positive_update_correct_count: int
    positive_update_opportunity_count: int
    evidence_binding_correct_count: int
    root_accounting_correct_count: int
    timing_correct_count: int
    negative_history_correct_count: int
    premature_abstention_count: int
    always_abstain_detected: bool

    @property
    def trajectory_success_rate(self) -> float | None:
        return self.pass_count / self.valid_case_count if self.valid_case_count else None

    @property
    def authority_leakage_rate(self) -> float | None:
        if not self.authority_inert_opportunity_count:
            return None
        return self.authority_leak_count / self.authority_inert_opportunity_count

    @property
    def valid_update_recall(self) -> float | None:
        if not self.positive_update_opportunity_count:
            return None
        return self.positive_update_correct_count / self.positive_update_opportunity_count

    @property
    def evidence_binding_accuracy(self) -> float | None:
        return self.evidence_binding_correct_count / self.step_count if self.step_count else None

    @property
    def root_accounting_accuracy(self) -> float | None:
        return self.root_accounting_correct_count / self.step_count if self.step_count else None

    @property
    def timing_accuracy(self) -> float | None:
        return self.timing_correct_count / self.step_count if self.step_count else None

    @property
    def negative_history_preservation_rate(self) -> float | None:
        return self.negative_history_correct_count / self.step_count if self.step_count else None

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _exact_tuple_match(left: Sequence[str], right: Sequence[str]) -> bool:
    return tuple(sorted(left)) == tuple(sorted(right))


def evaluate_epistemic_trajectory(
    case: EpistemicTrajectoryCase,
    observed_steps: Sequence[ObservedEpistemicStep],
) -> TrajectoryEvaluation:
    """Evaluate one known-answer epistemic trajectory."""

    if case.known_answer_validated is None:
        return TrajectoryEvaluation(
            case.case_id,
            TrajectoryVerdict.CANNOT_CHECK,
            reasons=("known_answer_validation_unknown",),
        )
    if case.known_answer_validated is False:
        return TrajectoryEvaluation(
            case.case_id,
            TrajectoryVerdict.CANNOT_CHECK,
            reasons=("trajectory_gold_not_known_answer_validated",),
        )
    if case.frozen_before_output is None:
        return TrajectoryEvaluation(
            case.case_id,
            TrajectoryVerdict.CANNOT_CHECK,
            reasons=("trajectory_freeze_chronology_unknown",),
        )
    if case.frozen_before_output is False:
        return TrajectoryEvaluation(
            case.case_id,
            TrajectoryVerdict.INVALID,
            reasons=("trajectory_gold_defined_posthoc",),
        )

    gold_by_id = {step.step_id: step for step in case.gold_steps}
    observed_by_id: dict[str, ObservedEpistemicStep] = {}
    for step in observed_steps:
        if step.step_id in observed_by_id:
            return TrajectoryEvaluation(
                case.case_id,
                TrajectoryVerdict.INVALID,
                reasons=(f"duplicate_observed_step:{step.step_id}",),
            )
        observed_by_id[step.step_id] = step

    missing = sorted(set(gold_by_id) - set(observed_by_id))
    extras = sorted(set(observed_by_id) - set(gold_by_id))
    if missing or extras:
        reasons = tuple(
            (["missing_steps:" + ",".join(missing)] if missing else [])
            + (["unexpected_steps:" + ",".join(extras)] if extras else [])
        )
        return TrajectoryEvaluation(case.case_id, TrajectoryVerdict.INVALID, reasons=reasons)

    ordered_observed = sorted(observed_steps, key=lambda step: step.sequence_index)
    if len({step.sequence_index for step in ordered_observed}) != len(ordered_observed):
        return TrajectoryEvaluation(
            case.case_id,
            TrajectoryVerdict.INVALID,
            reasons=("duplicate_sequence_index",),
        )

    gold_order = [step.step_id for step in case.gold_steps]
    observed_order = [step.step_id for step in ordered_observed]
    order_correct = observed_order == gold_order

    continuity_correct = order_correct
    previous_after = case.initial_authority_fingerprint
    step_results: list[StepEvaluation] = []

    for observed in ordered_observed:
        gold = gold_by_id[observed.step_id]
        reasons: list[str] = []
        if observed.family is not gold.family:
            reasons.append("step_family_mismatch")

        if observed.authority_before != previous_after:
            continuity_correct = False
            reasons.append("authority_fingerprint_discontinuity")

        action_correct = observed.action == gold.licensed_action
        forbidden = observed.action in set(gold.forbidden_actions)
        if not action_correct:
            reasons.append("licensed_action_mismatch")
        if forbidden:
            reasons.append("forbidden_action_taken")

        evidence_correct = _exact_tuple_match(observed.evidence_ids, gold.required_evidence_ids)
        if not evidence_correct:
            reasons.append("evidence_binding_mismatch")

        roots_correct = _exact_tuple_match(observed.root_ids, gold.required_root_ids)
        if not roots_correct:
            reasons.append("evidence_root_accounting_mismatch")

        if gold.authority_change_licensed:
            authority_correct = observed.authority_after == gold.expected_authority_after
            authority_leak = False
            if not authority_correct:
                reasons.append("licensed_authority_transition_result_mismatch")
        else:
            authority_correct = observed.authority_after == observed.authority_before
            authority_leak = not authority_correct
            if authority_leak:
                reasons.append("unlicensed_authority_change")

        if gold.latest_safe_sequence is None:
            timing_correct = True
        else:
            timing_correct = observed.sequence_index <= gold.latest_safe_sequence
            if not timing_correct:
                reasons.append("posthoc_or_too_late_epistemic_action")

        required_history = set(gold.required_negative_history_ids)
        history_correct = required_history.issubset(set(observed.negative_history_ids))
        if not history_correct:
            reasons.append("negative_history_not_preserved")

        premature_abstention = (
            observed.action == "ABSTAIN_CANNOT_CHECK"
            and gold.positive_update_opportunity
            and gold.licensed_action != "ABSTAIN_CANNOT_CHECK"
        )
        if premature_abstention:
            reasons.append("premature_abstention_on_valid_update_control")

        step_results.append(
            StepEvaluation(
                step_id=gold.step_id,
                family=gold.family,
                action_correct=action_correct and observed.family is gold.family,
                evidence_binding_correct=evidence_correct,
                root_accounting_correct=roots_correct,
                authority_transition_correct=authority_correct,
                timing_correct=timing_correct,
                negative_history_preserved=history_correct,
                authority_leak=authority_leak,
                premature_abstention=premature_abstention,
                forbidden_action_taken=forbidden,
                reasons=tuple(reasons),
            )
        )
        previous_after = observed.authority_after

    passed = order_correct and continuity_correct and all(step.passed for step in step_results)
    reason_set = {reason for step in step_results for reason in step.reasons}
    if not order_correct:
        reason_set.add("epistemic_step_order_mismatch")
    if not continuity_correct:
        reason_set.add("authority_trajectory_discontinuity")
    reasons = () if passed else tuple(sorted(reason_set))
    return TrajectoryEvaluation(
        case_id=case.case_id,
        verdict=TrajectoryVerdict.PASS if passed else TrajectoryVerdict.FAIL,
        steps=tuple(step_results),
        continuity_correct=continuity_correct,
        reasons=reasons,
    )


def summarize_trajectory_panel(
    cases: Sequence[EpistemicTrajectoryCase],
    evaluations: Sequence[TrajectoryEvaluation],
    observed_by_case: Sequence[tuple[str, Sequence[ObservedEpistemicStep]]] = (),
) -> TrajectoryPanelMetrics:
    """Aggregate a panel without treating trajectory steps as independent sample n."""

    case_by_id = {case.case_id: case for case in cases}
    evaluation_by_id = {evaluation.case_id: evaluation for evaluation in evaluations}
    if len(case_by_id) != len(cases) or len(evaluation_by_id) != len(evaluations):
        raise ValueError("case/evaluation ids must be unique")
    if set(evaluation_by_id) - set(case_by_id):
        raise ValueError("evaluation refers to unknown trajectory case")

    observed_map: dict[str, Sequence[ObservedEpistemicStep]] = {}
    for case_id, observed in observed_by_case:
        if case_id not in case_by_id:
            raise ValueError(f"observed trajectory refers to unknown case: {case_id}")
        if case_id in observed_map:
            raise ValueError(f"duplicate observed trajectory case: {case_id}")
        observed_map[case_id] = observed

    valid_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.verdict in {TrajectoryVerdict.PASS, TrajectoryVerdict.FAIL}
    ]
    steps = [step for evaluation in valid_evaluations for step in evaluation.steps]

    gold_lookup = {
        (case.case_id, step.step_id): step
        for case in cases
        for step in case.gold_steps
    }
    positive_opportunities = 0
    positive_correct = 0
    authority_inert_opportunities = 0
    authority_leaks = 0
    valid_case_ids = {evaluation.case_id for evaluation in valid_evaluations}
    for evaluation in valid_evaluations:
        for result in evaluation.steps:
            gold = gold_lookup[(evaluation.case_id, result.step_id)]
            if gold.positive_update_opportunity:
                positive_opportunities += 1
                if result.action_correct and result.authority_transition_correct:
                    positive_correct += 1
            if not gold.authority_change_licensed:
                authority_inert_opportunities += 1
                if result.authority_leak:
                    authority_leaks += 1

    observed_actions = [
        step.action
        for case_id, observed_steps in observed_map.items()
        if case_id in valid_case_ids
        for step in observed_steps
    ]
    always_abstain = bool(observed_actions) and all(
        action == "ABSTAIN_CANNOT_CHECK" for action in observed_actions
    ) and positive_opportunities > 0

    return TrajectoryPanelMetrics(
        case_count=len(cases),
        valid_case_count=len(valid_evaluations),
        pass_count=sum(evaluation.verdict is TrajectoryVerdict.PASS for evaluation in valid_evaluations),
        step_count=len(steps),
        authority_leak_count=authority_leaks,
        authority_inert_opportunity_count=authority_inert_opportunities,
        positive_update_correct_count=positive_correct,
        positive_update_opportunity_count=positive_opportunities,
        evidence_binding_correct_count=sum(step.evidence_binding_correct for step in steps),
        root_accounting_correct_count=sum(step.root_accounting_correct for step in steps),
        timing_correct_count=sum(step.timing_correct for step in steps),
        negative_history_correct_count=sum(step.negative_history_preserved for step in steps),
        premature_abstention_count=sum(step.premature_abstention for step in steps),
        always_abstain_detected=always_abstain,
    )
