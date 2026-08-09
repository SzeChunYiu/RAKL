from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .invention import (
    CandidateScore,
    GoalAssessment,
    GoalAssessmentVerdict,
    PositiveGoalContract,
    evaluate_positive_goal,
)
from .formalism import VerificationReport


class HardGateState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class HardGateRequirement:
    gate_id: str
    description: str
    evidence_required: bool = True

    def __post_init__(self) -> None:
        if not self.gate_id or not self.description:
            raise ValueError("gate id and description are required")


@dataclass(frozen=True)
class HardGateObservation:
    gate_id: str
    candidate_id: str
    state: HardGateState
    evidence_ids: Tuple[str, ...] = ()
    detail: str = ""


@dataclass(frozen=True)
class HardGateContract:
    contract_id: str
    requirements: Tuple[HardGateRequirement, ...]
    frozen_before_candidate_results: Optional[bool]

    def __post_init__(self) -> None:
        if not self.contract_id:
            raise ValueError("hard-gate contract id is required")
        ids = [item.gate_id for item in self.requirements]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("hard-gate requirements must be nonempty and unique")


@dataclass(frozen=True)
class HardGateReport:
    state: HardGateState
    reasons: Tuple[str, ...]
    passed_gate_ids: Tuple[str, ...] = ()
    failed_gate_ids: Tuple[str, ...] = ()
    unresolved_gate_ids: Tuple[str, ...] = ()


def evaluate_hard_gates(
    contract: HardGateContract,
    observations: Tuple[HardGateObservation, ...],
    *,
    candidate_id: str,
) -> HardGateReport:
    if contract.frozen_before_candidate_results is None:
        return HardGateReport(
            HardGateState.CANNOT_CHECK,
            ("hard_gate_contract_chronology_unknown",),
        )
    if contract.frozen_before_candidate_results is False:
        return HardGateReport(
            HardGateState.FAIL,
            ("hard_gate_contract_modified_after_candidate_results",),
            failed_gate_ids=("CONTRACT_INTEGRITY",),
        )

    by_gate: dict[str, HardGateObservation] = {}
    for observation in observations:
        if observation.candidate_id != candidate_id:
            continue
        if observation.gate_id in by_gate and by_gate[observation.gate_id] != observation:
            return HardGateReport(
                HardGateState.FAIL,
                (f"conflicting_gate_observations:{observation.gate_id}",),
                failed_gate_ids=(observation.gate_id,),
            )
        by_gate[observation.gate_id] = observation

    passed: list[str] = []
    failed: list[str] = []
    unresolved: list[str] = []
    reasons: list[str] = []
    for requirement in contract.requirements:
        observation = by_gate.get(requirement.gate_id)
        if observation is None:
            unresolved.append(requirement.gate_id)
            reasons.append(f"gate_observation_missing:{requirement.gate_id}")
            continue
        if requirement.evidence_required and observation.state is not HardGateState.CANNOT_CHECK and not observation.evidence_ids:
            unresolved.append(requirement.gate_id)
            reasons.append(f"gate_evidence_missing:{requirement.gate_id}")
            continue
        if observation.state is HardGateState.PASS:
            passed.append(requirement.gate_id)
        elif observation.state is HardGateState.FAIL:
            failed.append(requirement.gate_id)
            reasons.append(f"gate_failed:{requirement.gate_id}:{observation.detail}")
        else:
            unresolved.append(requirement.gate_id)
            reasons.append(f"gate_unresolved:{requirement.gate_id}:{observation.detail}")

    if failed:
        return HardGateReport(
            HardGateState.FAIL,
            tuple(reasons),
            tuple(passed),
            tuple(failed),
            tuple(unresolved),
        )
    if unresolved:
        return HardGateReport(
            HardGateState.CANNOT_CHECK,
            tuple(reasons),
            tuple(passed),
            (),
            tuple(unresolved),
        )
    return HardGateReport(
        HardGateState.PASS,
        ("all_required_hard_gates_passed_for_exact_candidate",),
        tuple(passed),
        (),
        (),
    )


@dataclass(frozen=True)
class FullPositiveGoalReport:
    verdict: GoalAssessmentVerdict
    reasons: Tuple[str, ...]
    numeric_assessment: GoalAssessment
    hard_gate_report: HardGateReport

    @property
    def goal_achieved(self) -> bool:
        return self.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED


def evaluate_full_positive_goal(
    numeric_contract: PositiveGoalContract,
    hard_gate_contract: HardGateContract,
    score: CandidateScore,
    verification: Optional[VerificationReport],
    observations: Tuple[HardGateObservation, ...],
) -> FullPositiveGoalReport:
    numeric = evaluate_positive_goal(numeric_contract, score, verification)
    gates = evaluate_hard_gates(
        hard_gate_contract,
        observations,
        candidate_id=score.candidate_id,
    )

    if numeric.verdict is GoalAssessmentVerdict.BLOCKED_INTEGRITY:
        return FullPositiveGoalReport(
            GoalAssessmentVerdict.BLOCKED_INTEGRITY,
            numeric.reasons,
            numeric,
            gates,
        )
    if gates.state is HardGateState.FAIL:
        return FullPositiveGoalReport(
            GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE,
            ("one_or_more_frozen_hard_gates_failed",) + gates.reasons,
            numeric,
            gates,
        )
    if numeric.verdict is GoalAssessmentVerdict.CANNOT_CHECK or gates.state is HardGateState.CANNOT_CHECK:
        return FullPositiveGoalReport(
            GoalAssessmentVerdict.CANNOT_CHECK,
            ("positive_goal_evidence_incomplete",) + numeric.reasons + gates.reasons,
            numeric,
            gates,
        )
    if numeric.verdict is GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE:
        return FullPositiveGoalReport(
            GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE,
            numeric.reasons,
            numeric,
            gates,
        )
    return FullPositiveGoalReport(
        GoalAssessmentVerdict.GOAL_ACHIEVED,
        (
            "numeric_goal_thresholds_passed",
            "all_exact_hard_gates_passed",
            "candidate_is_eligible_for_independent_review_and_promotion",
        ),
        numeric,
        gates,
    )


def polymarket_crypto_spot_gate_contract() -> HardGateContract:
    """Round-035/036 exact non-negotiable spot-science gates."""

    requirements = (
        HardGateRequirement("TYPED_FORMALISM", "typed mechanism/formalism candidate exists"),
        HardGateRequirement("DESCRIPTIVE_AXES_COVERED", "registered descriptive axes covered or derived as projections"),
        HardGateRequirement("MECHANISM_ANCESTRY", "building blocks -> interactions -> state/regime -> spot observable ancestry"),
        HardGateRequirement("STRUCTURED_RESIDUAL_CLOSED", "remaining structured residual is below registered materiality or observation/noise model explains it"),
        HardGateRequirement("MECHANISM_FALSIFIERS_EXECUTED", "mechanism-specific falsifiers executed"),
        HardGateRequirement("FULL_HISTORY_TEACHER_NONVACUOUS", "full-history teacher is nonvacuous"),
        HardGateRequirement("IDENTICAL_CAUSAL_ROWS", "candidate comparisons use identical causal rows"),
        HardGateRequirement("STRICT_AVAILABILITY", "all predictive inputs satisfy strict decision-time availability"),
        HardGateRequirement("FROZEN_5M_15M_TARGET", "5m/15m target definition frozen before results"),
        HardGateRequirement("MATERIALITY_PREDECLARED", "predictive materiality threshold frozen before result"),
        HardGateRequirement("MULTIPLICITY_AWARE", "uncertainty accounts for registered multiplicity"),
        HardGateRequirement("POSITIVE_FORWARD_LCB", "positive untouched/forward lower confidence bound passes"),
        HardGateRequirement("CALIBRATION", "predictive distribution passes registered calibration gates"),
        HardGateRequirement("TRANSPORT", "predictive result passes registered transport gates"),
        HardGateRequirement("MECHANISM_PREDICTION_LINK", "predictive signal is linked to mechanism or explicitly typed phenomenological authority"),
        HardGateRequirement("FORMAL_VERIFICATION", "formal verification stack passes for exact candidate"),
        HardGateRequirement("EXACT_CANDIDATE_BINDING", "all certifying receipts are bound to exact candidate identity"),
        HardGateRequirement("INDEPENDENT_REVIEW", "independent frozen review passes"),
        HardGateRequirement("EVIDENCE_LINEAGE", "claim/evidence lineage is intact"),
        HardGateRequirement("NO_BLOCKING_INTEGRITY_FAILURE", "no target leakage, post-result rescue, hidden multiplicity, or fabricated evidence"),
    )
    return HardGateContract(
        "polymarket-crypto-spot-round036-hard-gates",
        requirements,
        frozen_before_candidate_results=True,
    )
