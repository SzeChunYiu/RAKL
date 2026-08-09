from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping, Optional, Tuple

from .invention import (
    CandidateScore,
    GoalAssessmentVerdict,
    InventionOperator,
    InventionTask,
    ResidualSignature,
    invention_tasks_for_residual,
)


class SearchLoopVerdict(str, Enum):
    PLAN_READY = "PLAN_READY"
    GOAL_ACHIEVED = "GOAL_ACHIEVED"
    RESOURCE_BLOCK_NONTERMINAL = "RESOURCE_BLOCK_NONTERMINAL"
    CANNOT_CHECK = "CANNOT_CHECK"


class OperatorFamily(str, Enum):
    STRUCTURE = "STRUCTURE"
    DYNAMICS = "DYNAMICS"
    ABSTRACTION = "ABSTRACTION"
    OBSERVATION = "OBSERVATION"
    ANALOGY = "ANALOGY"
    ASSUMPTION = "ASSUMPTION"
    SYMMETRY = "SYMMETRY"
    RESIDUAL = "RESIDUAL"


_OPERATOR_FAMILY: Mapping[InventionOperator, OperatorFamily] = {
    InventionOperator.COMPOSE: OperatorFamily.STRUCTURE,
    InventionOperator.RECOMBINE: OperatorFamily.STRUCTURE,
    InventionOperator.ADD_LATENT_STATE: OperatorFamily.STRUCTURE,
    InventionOperator.REMOVE_LATENT_STATE: OperatorFamily.STRUCTURE,
    InventionOperator.SPLIT_REGIME: OperatorFamily.STRUCTURE,
    InventionOperator.MERGE_REGIME: OperatorFamily.STRUCTURE,
    InventionOperator.CHANGE_CLOCK: OperatorFamily.OBSERVATION,
    InventionOperator.COARSE_GRAIN: OperatorFamily.ABSTRACTION,
    InventionOperator.FINE_GRAIN: OperatorFamily.ABSTRACTION,
    InventionOperator.GENERALIZE: OperatorFamily.ABSTRACTION,
    InventionOperator.SPECIALIZE: OperatorFamily.ABSTRACTION,
    InventionOperator.TAKE_LIMIT: OperatorFamily.ABSTRACTION,
    InventionOperator.DUALIZE: OperatorFamily.ABSTRACTION,
    InventionOperator.STOCHASTICIZE: OperatorFamily.DYNAMICS,
    InventionOperator.DETERMINIZE: OperatorFamily.DYNAMICS,
    InventionOperator.ADD_FEEDBACK: OperatorFamily.DYNAMICS,
    InventionOperator.REMOVE_FEEDBACK: OperatorFamily.DYNAMICS,
    InventionOperator.ADD_COUPLING: OperatorFamily.DYNAMICS,
    InventionOperator.REMOVE_COUPLING: OperatorFamily.DYNAMICS,
    InventionOperator.ADD_INTERACTION: OperatorFamily.DYNAMICS,
    InventionOperator.RELAX_ASSUMPTION: OperatorFamily.ASSUMPTION,
    InventionOperator.STRENGTHEN_ASSUMPTION: OperatorFamily.ASSUMPTION,
    InventionOperator.ADD_INVARIANT: OperatorFamily.SYMMETRY,
    InventionOperator.BREAK_SYMMETRY: OperatorFamily.SYMMETRY,
    InventionOperator.ADD_SYMMETRY: OperatorFamily.SYMMETRY,
    InventionOperator.NONLINEARIZE: OperatorFamily.DYNAMICS,
    InventionOperator.LINEARIZE: OperatorFamily.DYNAMICS,
    InventionOperator.IMPORT_ANALOGICAL_MOTIF: OperatorFamily.ANALOGY,
    InventionOperator.CHANGE_OBSERVATION_MAP: OperatorFamily.OBSERVATION,
    InventionOperator.EXPLAIN_RESIDUAL: OperatorFamily.RESIDUAL,
}


@dataclass(frozen=True)
class SearchBudget:
    max_rounds: int
    max_candidate_proposals: int
    max_tasks_per_round: int
    max_retries_per_operator: int = 3
    renewable: bool = True

    def __post_init__(self) -> None:
        if min(
            self.max_rounds,
            self.max_candidate_proposals,
            self.max_tasks_per_round,
            self.max_retries_per_operator,
        ) < 1:
            raise ValueError("all search budget coordinates must be positive")


@dataclass(frozen=True)
class SearchLoopState:
    search_id: str
    round_index: int = 0
    candidate_proposals: int = 0
    operator_attempts: Tuple[Tuple[str, int], ...] = ()
    latest_goal_verdict: Optional[GoalAssessmentVerdict] = None
    exhausted_budget_count: int = 0

    def __post_init__(self) -> None:
        if not self.search_id:
            raise ValueError("search_id is required")
        if min(self.round_index, self.candidate_proposals, self.exhausted_budget_count) < 0:
            raise ValueError("search counters cannot be negative")

    def attempt_map(self) -> dict[str, int]:
        return dict(self.operator_attempts)


@dataclass(frozen=True)
class GenerationRequest:
    request_id: str
    residual_id: str
    task: InventionTask
    operator_family: OperatorFamily
    preferred_parent_candidate_ids: Tuple[str, ...]
    generation_channel: str


@dataclass(frozen=True)
class SearchRoundPlan:
    verdict: SearchLoopVerdict
    reasons: Tuple[str, ...]
    round_index: int
    requests: Tuple[GenerationRequest, ...] = ()
    reopen_fiber_ids: Tuple[str, ...] = ()
    budget_renewal_required: bool = False


def _frontier_parent_ids(frontier: Tuple[CandidateScore, ...], limit: int = 4) -> Tuple[str, ...]:
    # Preserve diverse Pareto survivors. The frontier is not re-ranked by one scalar;
    # this stable ordering is only a deterministic parent shortlist.
    return tuple(score.candidate_id for score in frontier[:limit])


def plan_next_search_round(
    state: SearchLoopState,
    residuals: Tuple[ResidualSignature, ...],
    frontier: Tuple[CandidateScore, ...],
    budget: SearchBudget,
) -> SearchRoundPlan:
    if state.latest_goal_verdict is GoalAssessmentVerdict.GOAL_ACHIEVED:
        return SearchRoundPlan(
            SearchLoopVerdict.GOAL_ACHIEVED,
            ("positive_goal_already_achieved",),
            state.round_index,
        )

    if not residuals:
        return SearchRoundPlan(
            SearchLoopVerdict.CANNOT_CHECK,
            ("positive_goal_not_achieved_but_no_registered_residual_is_available",),
            state.round_index,
        )

    round_exhausted = state.round_index >= budget.max_rounds
    proposal_exhausted = state.candidate_proposals >= budget.max_candidate_proposals
    if round_exhausted or proposal_exhausted:
        return SearchRoundPlan(
            SearchLoopVerdict.RESOURCE_BLOCK_NONTERMINAL,
            (
                "current_search_budget_exhausted",
                "budget_exhaustion_is_not_negative_project_closure",
            ),
            state.round_index,
            reopen_fiber_ids=tuple(
                dict.fromkeys(fid for residual in residuals for fid in residual.implicated_fiber_ids)
            ),
            budget_renewal_required=budget.renewable,
        )

    attempt_map = state.attempt_map()
    parents = _frontier_parent_ids(frontier)
    all_tasks: list[tuple[ResidualSignature, InventionTask]] = []
    for residual in residuals:
        for task in invention_tasks_for_residual(residual, max_operators=12):
            attempts = attempt_map.get(task.operator.value, 0)
            if attempts >= budget.max_retries_per_operator:
                continue
            all_tasks.append((residual, task))

    if not all_tasks:
        return SearchRoundPlan(
            SearchLoopVerdict.CANNOT_CHECK,
            (
                "all_registered_residual_operator_routes_exhausted_under_current_operator_basis",
                "open_METHOD_BASIS_GAP_CANDIDATE_and_evolve_operator_basis",
            ),
            state.round_index,
            reopen_fiber_ids=tuple(
                dict.fromkeys(fid for residual in residuals for fid in residual.implicated_fiber_ids)
            ),
        )

    # Diversity-first selection: first take one task from as many operator families and
    # residuals as possible, then fill remaining slots. This prevents one familiar move
    # from monopolizing a round after repeated failures.
    selected: list[tuple[ResidualSignature, InventionTask]] = []
    used_families: set[OperatorFamily] = set()
    used_residuals: set[str] = set()
    for residual, task in all_tasks:
        family = _OPERATOR_FAMILY[task.operator]
        if family in used_families and residual.residual_id in used_residuals:
            continue
        selected.append((residual, task))
        used_families.add(family)
        used_residuals.add(residual.residual_id)
        if len(selected) >= budget.max_tasks_per_round:
            break
    if len(selected) < budget.max_tasks_per_round:
        for item in all_tasks:
            if item in selected:
                continue
            selected.append(item)
            if len(selected) >= budget.max_tasks_per_round:
                break

    remaining_proposals = budget.max_candidate_proposals - state.candidate_proposals
    selected = selected[:remaining_proposals]
    requests = tuple(
        GenerationRequest(
            request_id=f"{state.search_id}:round{state.round_index + 1}:{index}:{task.operator.value}",
            residual_id=residual.residual_id,
            task=task,
            operator_family=_OPERATOR_FAMILY[task.operator],
            preferred_parent_candidate_ids=parents,
            generation_channel=(
                "symbolic_or_solver_first"
                if task.operator in {
                    InventionOperator.NONLINEARIZE,
                    InventionOperator.LINEARIZE,
                    InventionOperator.STOCHASTICIZE,
                    InventionOperator.ADD_INTERACTION,
                }
                else "multi_proposer_typed_delta"
            ),
        )
        for index, (residual, task) in enumerate(selected)
    )
    return SearchRoundPlan(
        SearchLoopVerdict.PLAN_READY,
        (
            "residual_driven_diverse_invention_round_planned",
            "requests_require_typed_candidate_output_and_predeclared_falsifiers",
        ),
        state.round_index + 1,
        requests,
        tuple(dict.fromkeys(fid for residual in residuals for fid in residual.implicated_fiber_ids)),
    )


def record_search_round(
    state: SearchLoopState,
    plan: SearchRoundPlan,
    *,
    proposals_materialized: int,
    latest_goal_verdict: Optional[GoalAssessmentVerdict] = None,
) -> SearchLoopState:
    if proposals_materialized < 0 or proposals_materialized > len(plan.requests):
        raise ValueError("materialized proposal count is inconsistent with round plan")
    attempts = state.attempt_map()
    for request in plan.requests[:proposals_materialized]:
        key = request.task.operator.value
        attempts[key] = attempts.get(key, 0) + 1
    exhausted = state.exhausted_budget_count + (
        1 if plan.verdict is SearchLoopVerdict.RESOURCE_BLOCK_NONTERMINAL else 0
    )
    return replace(
        state,
        round_index=max(state.round_index, plan.round_index),
        candidate_proposals=state.candidate_proposals + proposals_materialized,
        operator_attempts=tuple(sorted(attempts.items())),
        latest_goal_verdict=latest_goal_verdict or state.latest_goal_verdict,
        exhausted_budget_count=exhausted,
    )
