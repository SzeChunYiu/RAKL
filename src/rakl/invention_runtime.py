from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Tuple

from .constructive_lattice import ConstructiveKnowledgeState
from .formalism import VerificationReport
from .hard_gates import (
    FullPositiveGoalReport,
    HardGateContract,
    HardGateObservation,
    HardGateState,
    evaluate_full_positive_goal,
)
from .invention import (
    CandidateScore,
    CandidateTheory,
    GoalAssessment,
    GoalAssessmentVerdict,
    InventionMove,
    PositiveGoalContract,
    ResidualKind,
    ResidualSignature,
    residual_from_goal_assessment,
)
from .search_controller import (
    SearchBudget,
    SearchLoopState,
    SearchRoundPlan,
    plan_next_search_round,
    record_search_round,
)
from .typed_lattice import KnowledgeAtomKind, LatticeSynthesisSeed, TypedKnowledgeLattice


_HARD_GATE_RESIDUAL_MAP = {
    "CALIBRATION": ResidualKind.CALIBRATION,
    "TRANSPORT": ResidualKind.TRANSPORT,
    "POSITIVE_FORWARD_LCB": ResidualKind.PREDICTIVE,
    "STRICT_AVAILABILITY": ResidualKind.CLOCK,
    "IDENTICAL_CAUSAL_ROWS": ResidualKind.OBSERVATION,
    "MECHANISM_ANCESTRY": ResidualKind.CAUSAL,
    "MECHANISM_FALSIFIERS_EXECUTED": ResidualKind.CAUSAL,
    "STRUCTURED_RESIDUAL_CLOSED": ResidualKind.UNCLASSIFIED,
    "DESCRIPTIVE_AXES_COVERED": ResidualKind.UNCLASSIFIED,
    "FORMAL_VERIFICATION": ResidualKind.UNCLASSIFIED,
}


@dataclass(frozen=True)
class RuntimeCandidateAssessment:
    candidate_id: str
    verdict: GoalAssessmentVerdict
    reasons: Tuple[str, ...]
    spawned_residual: Optional[ResidualSignature]
    full_goal_report: Optional[FullPositiveGoalReport] = None


@dataclass
class InventionRuntime:
    """Stateful executable coordinator for one positive-goal invention lane."""

    knowledge: ConstructiveKnowledgeState
    typed_lattice: TypedKnowledgeLattice
    search_budget: SearchBudget
    search_state: SearchLoopState
    hard_gate_contract: Optional[HardGateContract] = None
    resolved_residual_ids: set[str] = field(default_factory=set)
    assessment_counter: int = 0

    @classmethod
    def create(
        cls,
        *,
        knowledge: ConstructiveKnowledgeState,
        typed_lattice: Optional[TypedKnowledgeLattice] = None,
        search_budget: SearchBudget,
        search_id: str,
        hard_gate_contract: Optional[HardGateContract] = None,
    ) -> "InventionRuntime":
        if knowledge.goal_contract is None:
            raise ValueError("constructive knowledge state must have a positive goal contract")
        return cls(
            knowledge,
            typed_lattice or TypedKnowledgeLattice.empty(),
            search_budget,
            SearchLoopState(search_id),
            hard_gate_contract,
        )

    @property
    def goal_contract(self) -> PositiveGoalContract:
        assert self.knowledge.goal_contract is not None
        return self.knowledge.goal_contract

    @property
    def goal_achieved(self) -> bool:
        return self.knowledge.goal_achieved

    def active_residuals(self) -> Tuple[ResidualSignature, ...]:
        return tuple(
            residual
            for residual_id, residual in self.knowledge.residuals.items()
            if residual_id not in self.resolved_residual_ids
        )

    def register_candidate(self, candidate: CandidateTheory) -> None:
        self.knowledge.register_candidate(candidate)

    def register_move(self, move: InventionMove) -> None:
        self.knowledge.register_move(move)

    def register_score(self, score: CandidateScore) -> None:
        self.knowledge.register_score(score)

    def register_residual(self, residual: ResidualSignature) -> None:
        self.knowledge.register_residual(residual)

    def mark_residual_resolved(self, residual_id: str) -> None:
        if residual_id not in self.knowledge.residuals:
            raise KeyError(f"unknown residual: {residual_id}")
        self.resolved_residual_ids.add(residual_id)

    def synthesis_seeds(
        self,
        residual_id: str,
        required_kinds: Tuple[KnowledgeAtomKind, ...],
        *,
        max_paths: int = 64,
    ) -> Tuple[LatticeSynthesisSeed, ...]:
        residual = self.knowledge.residuals[residual_id]
        return self.typed_lattice.synthesis_seeds(
            residual,
            required_kinds,
            max_paths=max_paths,
        )

    def plan_next_round(self) -> SearchRoundPlan:
        return plan_next_search_round(
            self.search_state,
            self.active_residuals(),
            self.knowledge.frontier(),
            self.search_budget,
        )

    def record_round(
        self,
        plan: SearchRoundPlan,
        *,
        proposals_materialized: int,
    ) -> None:
        self.search_state = record_search_round(
            self.search_state,
            plan,
            proposals_materialized=proposals_materialized,
        )

    def _residual_from_hard_gate_failure(
        self,
        candidate_id: str,
        report: FullPositiveGoalReport,
        *,
        evidence_ids: Tuple[str, ...],
        implicated_fiber_ids: Tuple[str, ...],
    ) -> ResidualSignature:
        kinds: list[ResidualKind] = []
        for gate_id in report.hard_gate_report.failed_gate_ids + report.hard_gate_report.unresolved_gate_ids:
            kind = _HARD_GATE_RESIDUAL_MAP.get(gate_id, ResidualKind.UNCLASSIFIED)
            if kind not in kinds:
                kinds.append(kind)
        if not kinds:
            kinds.append(ResidualKind.UNCLASSIFIED)
        self.assessment_counter += 1
        return ResidualSignature(
            residual_id=f"runtime:{self.search_state.search_id}:{candidate_id}:{self.assessment_counter}",
            kinds=tuple(kinds),
            description="; ".join(report.reasons),
            implicated_fiber_ids=implicated_fiber_ids,
            failed_candidate_ids=(candidate_id,),
            evidence_ids=evidence_ids,
            diagnostics={"full_goal_verdict": report.verdict.value},
        )

    def assess_candidate(
        self,
        candidate_id: str,
        verification: Optional[VerificationReport],
        *,
        hard_gate_observations: Tuple[HardGateObservation, ...] = (),
        evidence_ids: Tuple[str, ...] = (),
        implicated_fiber_ids: Tuple[str, ...] = (),
    ) -> RuntimeCandidateAssessment:
        if candidate_id not in self.knowledge.candidates:
            raise KeyError(f"unknown candidate: {candidate_id}")
        score = self.knowledge.scores.get(candidate_id)
        if score is None:
            return RuntimeCandidateAssessment(
                candidate_id,
                GoalAssessmentVerdict.CANNOT_CHECK,
                ("candidate_score_missing",),
                None,
            )

        full_report: Optional[FullPositiveGoalReport] = None
        if self.hard_gate_contract is not None:
            full_report = evaluate_full_positive_goal(
                self.goal_contract,
                self.hard_gate_contract,
                score,
                verification,
                hard_gate_observations,
            )
            verdict = full_report.verdict
            reasons = full_report.reasons
            numeric = full_report.numeric_assessment
        else:
            numeric = self.knowledge.evaluate_candidate(candidate_id, verification)
            verdict = numeric.verdict
            reasons = numeric.reasons

        # Persist the effective goal state into the constructive knowledge state so the
        # controller and callers share one closure truth.
        self.knowledge.assessments[candidate_id] = GoalAssessment(
            verdict,
            reasons,
            numeric.unmet_criteria,
            numeric.next_action,
        )
        self.search_state = replace(self.search_state, latest_goal_verdict=verdict)

        if verdict is GoalAssessmentVerdict.GOAL_ACHIEVED:
            for residual_id in tuple(self.knowledge.residuals):
                if candidate_id in self.knowledge.residuals[residual_id].failed_candidate_ids:
                    continue
            return RuntimeCandidateAssessment(candidate_id, verdict, reasons, None, full_report)

        spawned: Optional[ResidualSignature]
        if full_report is not None and full_report.hard_gate_report.state is not HardGateState.PASS:
            spawned = self._residual_from_hard_gate_failure(
                candidate_id,
                full_report,
                evidence_ids=evidence_ids,
                implicated_fiber_ids=implicated_fiber_ids,
            )
        else:
            self.assessment_counter += 1
            spawned = residual_from_goal_assessment(
                numeric,
                candidate_id=candidate_id,
                residual_id=f"runtime:{self.search_state.search_id}:{candidate_id}:{self.assessment_counter}",
                implicated_fiber_ids=implicated_fiber_ids,
                evidence_ids=evidence_ids,
            )
        if spawned is not None:
            self.register_residual(spawned)

        return RuntimeCandidateAssessment(
            candidate_id,
            verdict,
            reasons,
            spawned,
            full_report,
        )
