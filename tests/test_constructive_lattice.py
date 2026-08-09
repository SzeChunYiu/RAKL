from rakl.constructive_lattice import ConstructiveKnowledgeState
from rakl.core import KnowledgeFiber
from rakl.formalism import (
    EquationKind,
    FormalEquation,
    FormalExpression,
    FormalSymbol,
    Formalism,
    MechanismGraph,
    MechanismNode,
    MechanismNodeKind,
    SymbolRole,
    VerificationReport,
    VerificationVerdict,
)
from rakl.invention import (
    CandidateScore,
    CandidateTheory,
    GoalAssessmentVerdict,
    PositiveGoalContract,
    ResidualKind,
    ResidualSignature,
)


def _candidate() -> CandidateTheory:
    x = FormalSymbol("x", SymbolRole.STATE, domain="real", units="return")
    equation = FormalEquation(
        "eq_x",
        FormalExpression.sym("x"),
        FormalExpression.sym("x"),
        EquationKind.DEFINITION,
        unit_balance_passed=True,
    )
    mechanism = MechanismGraph(
        "m",
        (MechanismNode("n_x", MechanismNodeKind.STATE, "x", symbol="x"),),
        (),
    )
    return CandidateTheory("c", Formalism("f", "spot", (x,), (equation,), mechanism))


def _contract() -> PositiveGoalContract:
    return PositiveGoalContract(
        "goal",
        min_descriptive_coverage=0.8,
        min_residual_closure=0.8,
        min_predictive_value=0.7,
        min_identification=0.6,
        min_falsifiability=0.8,
        min_robustness=0.7,
        thresholds_frozen_before_results=True,
    )


def test_constructive_state_registers_invention_objects_into_fiber_dimensions():
    state = ConstructiveKnowledgeState(KnowledgeFiber("fiber", "spot", "explain spot"))
    residual = ResidualSignature(
        "r",
        (ResidualKind.REGIME,),
        "hidden regime structure remains",
    )
    state.register_residual(residual)
    state.register_candidate(_candidate())
    state.set_goal_contract(_contract())
    assert state.fiber.dimensions["residual_signatures"] == {"r"}
    assert state.fiber.dimensions["formalism_candidates"] == {"c"}
    assert state.fiber.dimensions["goal_contracts"] == {"goal"}


def test_constructive_state_refuses_goal_closure_for_weak_candidate():
    state = ConstructiveKnowledgeState(KnowledgeFiber("fiber", "spot", "explain spot"))
    state.register_candidate(_candidate())
    state.set_goal_contract(_contract())
    state.register_score(CandidateScore("c", 0.9, 0.4, 0.2, 0.8, 0.9, 0.8, 0.5, 1.0))
    result = state.evaluate_candidate(
        "c",
        VerificationReport(VerificationVerdict.PASS, ("verified",)),
    )
    assert result.verdict is GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE
    assert state.continuation_required


def test_constructive_state_can_close_only_after_positive_goal():
    state = ConstructiveKnowledgeState(KnowledgeFiber("fiber", "spot", "explain spot"))
    state.register_candidate(_candidate())
    state.set_goal_contract(_contract())
    state.register_score(CandidateScore("c", 0.95, 0.9, 0.8, 0.8, 0.9, 0.85, 0.7, 1.0))
    result = state.evaluate_candidate(
        "c",
        VerificationReport(VerificationVerdict.PASS, ("verified",)),
    )
    assert result.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
    assert state.goal_achieved
    assert not state.continuation_required
