from rakl.formalism import VerificationReport, VerificationVerdict
from rakl.hard_gates import (
    HardGateObservation,
    HardGateState,
    evaluate_full_positive_goal,
    evaluate_hard_gates,
    polymarket_crypto_spot_gate_contract,
)
from rakl.invention import CandidateScore, GoalAssessmentVerdict, PositiveGoalContract


def _numeric_contract():
    return PositiveGoalContract(
        "goal",
        0.8,
        0.8,
        0.7,
        0.6,
        0.8,
        0.7,
        thresholds_frozen_before_results=True,
    )


def _score():
    return CandidateScore("c", 0.9, 0.9, 0.8, 0.8, 0.9, 0.85, 0.7, 2.0)


def _passing_observations():
    return tuple(
        HardGateObservation(
            requirement.gate_id,
            "c",
            HardGateState.PASS,
            evidence_ids=(f"receipt:{requirement.gate_id}",),
        )
        for requirement in polymarket_crypto_spot_gate_contract().requirements
    )


def test_missing_hard_gate_is_cannot_check():
    contract = polymarket_crypto_spot_gate_contract()
    report = evaluate_hard_gates(contract, (), candidate_id="c")
    assert report.state is HardGateState.CANNOT_CHECK
    assert set(report.unresolved_gate_ids) == {item.gate_id for item in contract.requirements}


def test_failed_hard_gate_blocks_candidate_success_but_continues_search():
    observations = list(_passing_observations())
    observations[0] = HardGateObservation(
        observations[0].gate_id,
        "c",
        HardGateState.FAIL,
        evidence_ids=("receipt:fail",),
        detail="typed candidate malformed",
    )
    report = evaluate_full_positive_goal(
        _numeric_contract(),
        polymarket_crypto_spot_gate_contract(),
        _score(),
        VerificationReport(VerificationVerdict.PASS, ("ok",)),
        tuple(observations),
    )
    assert report.verdict is GoalAssessmentVerdict.CANDIDATE_REJECTED_CONTINUE


def test_full_positive_goal_requires_all_exact_gates():
    report = evaluate_full_positive_goal(
        _numeric_contract(),
        polymarket_crypto_spot_gate_contract(),
        _score(),
        VerificationReport(VerificationVerdict.PASS, ("ok",)),
        _passing_observations(),
    )
    assert report.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
    assert report.goal_achieved
