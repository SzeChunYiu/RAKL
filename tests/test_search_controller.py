from rakl.invention import CandidateScore, GoalAssessmentVerdict, ResidualKind, ResidualSignature
from rakl.search_controller import (
    SearchBudget,
    SearchLoopState,
    SearchLoopVerdict,
    plan_next_search_round,
    record_search_round,
)


def _residuals():
    return (
        ResidualSignature(
            "r-regime",
            (ResidualKind.REGIME, ResidualKind.VOLATILITY),
            "hidden regime and volatility residual",
            implicated_fiber_ids=("fiber:regime",),
        ),
        ResidualSignature(
            "r-pred",
            (ResidualKind.PREDICTIVE,),
            "predictive bridge remains weak",
            implicated_fiber_ids=("fiber:predictive",),
        ),
    )


def test_controller_plans_diverse_residual_driven_round():
    plan = plan_next_search_round(
        SearchLoopState("s"),
        _residuals(),
        (CandidateScore("c", 0.8, 0.7, 0.4, 0.7, 0.8, 0.7, 0.6, 2.0),),
        SearchBudget(10, 100, 6),
    )
    assert plan.verdict is SearchLoopVerdict.PLAN_READY
    assert len(plan.requests) >= 2
    assert {request.residual_id for request in plan.requests} == {"r-regime", "r-pred"}
    assert len({request.operator_family for request in plan.requests}) >= 2


def test_controller_tracks_operator_attempts():
    state = SearchLoopState("s")
    plan = plan_next_search_round(state, _residuals(), (), SearchBudget(10, 100, 4))
    updated = record_search_round(state, plan, proposals_materialized=len(plan.requests))
    assert updated.round_index == 1
    assert updated.candidate_proposals == len(plan.requests)
    assert sum(dict(updated.operator_attempts).values()) == len(plan.requests)


def test_budget_exhaustion_is_nonterminal_resource_block():
    state = SearchLoopState("s", round_index=2, candidate_proposals=5)
    plan = plan_next_search_round(
        state,
        _residuals(),
        (),
        SearchBudget(max_rounds=2, max_candidate_proposals=5, max_tasks_per_round=2),
    )
    assert plan.verdict is SearchLoopVerdict.RESOURCE_BLOCK_NONTERMINAL
    assert plan.budget_renewal_required


def test_goal_achieved_stops_search():
    state = SearchLoopState("s", latest_goal_verdict=GoalAssessmentVerdict.GOAL_ACHIEVED)
    plan = plan_next_search_round(state, _residuals(), (), SearchBudget(10, 100, 4))
    assert plan.verdict is SearchLoopVerdict.GOAL_ACHIEVED
