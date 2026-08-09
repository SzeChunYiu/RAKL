from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .core import KnowledgeFiber
from .formalism import VerificationReport
from .invention import (
    CandidateScore,
    CandidateTheory,
    GoalAssessment,
    GoalAssessmentVerdict,
    InventionMove,
    InventionTask,
    PositiveGoalContract,
    ResidualSignature,
    evaluate_positive_goal,
    invention_tasks_for_residual,
    pareto_frontier,
)


@dataclass
class ConstructiveKnowledgeState:
    """Executable bridge between a KnowledgeFiber and theory invention state.

    The underlying KnowledgeFiber remains the semantic/evidence atlas. This state owns
    candidate theories, residuals and constructive moves that are generated from it.
    Nothing is promoted back into canonical knowledge merely by registration here.
    """

    fiber: KnowledgeFiber
    residuals: dict[str, ResidualSignature] = field(default_factory=dict)
    candidates: dict[str, CandidateTheory] = field(default_factory=dict)
    moves: dict[str, InventionMove] = field(default_factory=dict)
    scores: dict[str, CandidateScore] = field(default_factory=dict)
    goal_contract: Optional[PositiveGoalContract] = None
    assessments: dict[str, GoalAssessment] = field(default_factory=dict)

    def register_residual(self, residual: ResidualSignature) -> None:
        existing = self.residuals.get(residual.residual_id)
        if existing is not None and existing != residual:
            raise ValueError(
                f"residual identity is immutable: {residual.residual_id}"
            )
        self.residuals[residual.residual_id] = residual
        self.fiber.dimensions.setdefault("residual_signatures", set()).add(
            residual.residual_id
        )

    def register_candidate(self, candidate: CandidateTheory) -> None:
        if candidate.formalism.object_id != self.fiber.object_id:
            raise ValueError(
                "candidate formalism object does not match constructive knowledge fiber"
            )
        existing = self.candidates.get(candidate.candidate_id)
        if existing is not None and existing != candidate:
            raise ValueError(
                f"candidate identity is immutable: {candidate.candidate_id}"
            )
        self.candidates[candidate.candidate_id] = candidate
        self.fiber.dimensions.setdefault("formalism_candidates", set()).add(
            candidate.candidate_id
        )

    def register_move(self, move: InventionMove) -> None:
        missing = set(move.residual_ids) - self.residuals.keys()
        if missing:
            raise KeyError(
                f"invention move references unregistered residuals: {sorted(missing)}"
            )
        existing = self.moves.get(move.move_id)
        if existing is not None and existing != move:
            raise ValueError(f"invention move identity is immutable: {move.move_id}")
        self.moves[move.move_id] = move
        self.fiber.dimensions.setdefault("invention_moves", set()).add(move.move_id)

    def set_goal_contract(self, contract: PositiveGoalContract) -> None:
        if self.goal_contract is not None and self.goal_contract != contract:
            raise ValueError(
                "positive goal contract is immutable once bound to a constructive lane"
            )
        self.goal_contract = contract
        self.fiber.dimensions.setdefault("goal_contracts", set()).add(contract.contract_id)

    def register_score(self, score: CandidateScore) -> None:
        if score.candidate_id not in self.candidates:
            raise KeyError(f"score references unknown candidate: {score.candidate_id}")
        self.scores[score.candidate_id] = score

    def frontier(self) -> Tuple[CandidateScore, ...]:
        return pareto_frontier(self.scores.values())

    def invention_tasks(
        self,
        residual_id: str,
        *,
        max_operators: int = 8,
    ) -> Tuple[InventionTask, ...]:
        return invention_tasks_for_residual(
            self.residuals[residual_id],
            max_operators=max_operators,
        )

    def evaluate_candidate(
        self,
        candidate_id: str,
        verification: Optional[VerificationReport],
    ) -> GoalAssessment:
        if self.goal_contract is None:
            raise RuntimeError("positive goal contract is not bound")
        if candidate_id not in self.candidates:
            raise KeyError(f"unknown candidate: {candidate_id}")
        score = self.scores.get(candidate_id)
        if score is None:
            assessment = GoalAssessment(
                GoalAssessmentVerdict.CANNOT_CHECK,
                ("candidate_score_missing",),
                next_action="evaluate the registered theory score vector",
            )
        else:
            assessment = evaluate_positive_goal(
                self.goal_contract,
                score,
                verification,
            )
        self.assessments[candidate_id] = assessment
        return assessment

    @property
    def goal_achieved(self) -> bool:
        return any(
            assessment.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
            for assessment in self.assessments.values()
        )

    @property
    def continuation_required(self) -> bool:
        return not self.goal_achieved
