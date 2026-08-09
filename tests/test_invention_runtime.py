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
from rakl.hard_gates import HardGateObservation, HardGateState, polymarket_crypto_spot_gate_contract
from rakl.invention import CandidateScore, CandidateTheory, PositiveGoalContract, ResidualKind
from rakl.invention_runtime import InventionRuntime
from rakl.search_controller import SearchBudget, SearchLoopVerdict


def _candidate():
    x = FormalSymbol("x", SymbolRole.STATE, "real", units="return")
    eq = FormalEquation("eq", FormalExpression.sym("x"), FormalExpression.sym("x"), EquationKind.DEFINITION, unit_balance_passed=True)
    mechanism = MechanismGraph("m", (MechanismNode("nx", MechanismNodeKind.STATE, "x", symbol="x"),), ())
    return CandidateTheory("c", Formalism("f", "spot", (x,), (eq,), mechanism))


def _runtime():
    knowledge = ConstructiveKnowledgeState(KnowledgeFiber("fiber", "spot", "discover mechanism"))
    knowledge.set_goal_contract(
        PositiveGoalContract("goal", 0.8, 0.8, 0.7, 0.6, 0.8, 0.7, thresholds_frozen_before_results=True)
    )
    runtime = InventionRuntime.create(
        knowledge=knowledge,
        search_budget=SearchBudget(20, 200, 8),
        search_id="spot-search",
        hard_gate_contract=polymarket_crypto_spot_gate_contract(),
    )
    runtime.register_candidate(_candidate())
    return runtime


def _gate_observations(state=HardGateState.PASS):
    return tuple(
        HardGateObservation(req.gate_id, "c", state, evidence_ids=(f"receipt:{req.gate_id}",))
        for req in polymarket_crypto_spot_gate_contract().requirements
    )


def test_runtime_failed_candidate_spawns_residual_and_next_round():
    runtime = _runtime()
    runtime.register_score(CandidateScore("c", 0.9, 0.5, 0.2, 0.8, 0.9, 0.8, 0.7, 2.0))
    result = runtime.assess_candidate(
        "c",
        VerificationReport(VerificationVerdict.PASS, ("verified",)),
        hard_gate_observations=_gate_observations(),
        evidence_ids=("receipt:test",),
        implicated_fiber_ids=("fiber",),
    )
    assert result.spawned_residual is not None
    assert ResidualKind.PREDICTIVE in result.spawned_residual.kinds
    plan = runtime.plan_next_round()
    assert plan.verdict is SearchLoopVerdict.PLAN_READY
    assert plan.requests


def test_runtime_hard_gate_failure_spawns_typed_residual():
    runtime = _runtime()
    runtime.register_score(CandidateScore("c", 0.95, 0.95, 0.9, 0.9, 0.9, 0.9, 0.7, 2.0))
    observations = list(_gate_observations())
    for index, observation in enumerate(observations):
        if observation.gate_id == "TRANSPORT":
            observations[index] = HardGateObservation(
                "TRANSPORT", "c", HardGateState.FAIL, evidence_ids=("receipt:transport-fail",), detail="forward regime failed"
            )
    result = runtime.assess_candidate(
        "c",
        VerificationReport(VerificationVerdict.PASS, ("verified",)),
        hard_gate_observations=tuple(observations),
    )
    assert result.spawned_residual is not None
    assert ResidualKind.TRANSPORT in result.spawned_residual.kinds
    assert not runtime.goal_achieved


def test_runtime_closes_only_when_numeric_and_hard_gates_pass():
    runtime = _runtime()
    runtime.register_score(CandidateScore("c", 0.95, 0.95, 0.9, 0.9, 0.9, 0.9, 0.7, 2.0))
    result = runtime.assess_candidate(
        "c",
        VerificationReport(VerificationVerdict.PASS, ("verified",)),
        hard_gate_observations=_gate_observations(),
    )
    assert result.spawned_residual is None
    assert runtime.goal_achieved
    assert runtime.plan_next_round().verdict is SearchLoopVerdict.GOAL_ACHIEVED
