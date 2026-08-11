"""Freeze tests for the issue #141 hidden-path benchmark harness.

Every observation below is a hand-written FIXTURE.  None of it is an arm result:
no solver was run, no LLM was called, and the harness contains no code path that
could have produced these numbers itself.  The tests exercise the evaluator's
logic, not the extension's performance.
"""

from __future__ import annotations

import pytest

from rakl.backward_multiseed_benchmark import (
    ArmVerdict,
    ContaminationCeilings,
    FrozenBenchmarkSpec,
    HiddenPathCase,
    HiddenPathTaskFamily,
    MatchedBudget,
    SearchArm,
    TaskArmObservation,
    compare_arms,
    evaluate_arm,
)

FIXTURE_BUDGET = MatchedBudget(
    max_expansions=64,
    max_connection_tests=64,
    max_tool_calls=64,
    max_tokens=100_000,
    max_wall_clock_seconds=600.0,
)
FIXTURE_CEILINGS = ContaminationCeilings(
    max_false_root_progress_rate=0.10,
    min_connection_test_precision=0.90,
    max_repeated_known_failure_rate=0.25,
)


def _fixture_case(index: int, family: HiddenPathTaskFamily) -> HiddenPathCase:
    return HiddenPathCase(
        case_id=f"FIXTURE_CASE_{index}",
        family=family,
        root_goal_id=f"FIXTURE_ROOT_{index}",
        frozen_evidence_ids=(f"FIXTURE_EVIDENCE_{index}",),
        evaluator_knows_solution=True,
        gold_path_hidden_from_solver=True,
        evaluator_separate_from_solver=True,
    )


def _fixture_spec(
    *,
    arms: tuple[SearchArm, ...] = tuple(SearchArm),
    ceilings: ContaminationCeilings = FIXTURE_CEILINGS,
    n_cases: int = 4,
) -> FrozenBenchmarkSpec:
    families = tuple(HiddenPathTaskFamily)
    cases = tuple(_fixture_case(i, families[i % len(families)]) for i in range(n_cases))
    return FrozenBenchmarkSpec(
        benchmark_id="FIXTURE_BENCHMARK_141",
        cases=cases,
        arms=arms,
        budget=FIXTURE_BUDGET,
        ceilings=ceilings,
        minimum_cases_per_arm=1,
        frozen_before_any_arm_execution=True,
    )


def _fixture_observation(
    case_index: int,
    arm: SearchArm,
    *,
    solved: bool = False,
    emitted: int = 0,
    useful: int = 0,
    irrelevant: int = 0,
    claimed: int = 4,
    confirmed: int = 4,
    tests: int = 4,
    claims: int = 2,
    upheld: int = 2,
    retries: int = 0,
    tool_calls: int = 10,
    expansions: int = 10,
    declared: int = 2,
    closed: int = 1,
    gold_path_exposed: bool = False,
    budget_frozen: bool = True,
) -> TaskArmObservation:
    return TaskArmObservation(
        benchmark_id="FIXTURE_BENCHMARK_141",
        case_id=f"FIXTURE_CASE_{case_index}",
        arm=arm,
        verified_solved=solved,
        root_obligations_declared=declared,
        root_obligations_verified_closed=closed,
        waypoints_emitted=emitted,
        waypoints_used_in_verified_connection=useful,
        waypoints_judged_irrelevant_by_evaluator=irrelevant,
        connection_tests_run=tests,
        connection_tests_claimed_verified=claimed,
        connection_tests_confirmed_by_checker=confirmed,
        root_progress_claims=claims,
        root_progress_claims_upheld=upheld,
        repeated_known_failure_retries=retries,
        distinct_representations_used=2,
        forward_frontier_signature=("f1", "f2"),
        backward_frontier_signature=("f2", "b1"),
        expansions_used=expansions,
        tool_calls_used=tool_calls,
        tokens_used=1_000,
        wall_clock_seconds=5.0,
        verification_debt=0.5,
        gold_path_exposed=gold_path_exposed,
        budget_frozen_before_run=budget_frozen,
    )


def test_frozen_spec_covers_the_six_arms_and_nine_task_families() -> None:
    spec = _fixture_spec(n_cases=9)
    assert spec.covers_all_arms
    assert spec.covers_all_task_families
    assert len(SearchArm) == 6
    assert len(HiddenPathTaskFamily) == 9


def test_harness_returns_insufficient_history_when_no_arm_was_executed() -> None:
    """With no observations there is no result: the harness cannot invent one."""

    spec = _fixture_spec()
    report = evaluate_arm(spec, (), SearchArm.A_FORWARD_ONLY)
    assert report.verdict is ArmVerdict.INSUFFICIENT_HISTORY
    assert report.metrics is None
    assert "harness_does_not_generate_arm_results" in report.reasons

    comparison = compare_arms(spec, ())
    assert all(item.metrics is None for item in comparison.ranked)
    assert "no_observations_supplied" in comparison.reasons
    assert comparison.establishes_extension_benefit is False


def test_degenerate_always_seed_arm_does_not_outrank_a_quiet_arm() -> None:
    """A seeder emitting a thousand irrelevant waypoints must score badly.

    The two arms are matched on solve rate, cost, budget and every integrity
    coordinate; they differ only in waypoint noise.  The noisy arm is also
    alphabetically *earlier*, so the enum tie-break would rank it first if
    ``irrelevant_waypoint_rate`` were not actually read by the ranking.
    """

    spec = _fixture_spec(arms=(SearchArm.C_FORWARD_BACKWARD, SearchArm.D_FORWARD_SEEDS))
    noisy = SearchArm.C_FORWARD_BACKWARD
    quiet = SearchArm.D_FORWARD_SEEDS
    observations = []
    for index in range(4):
        solved = index < 2
        observations.append(
            _fixture_observation(index, noisy, solved=solved, emitted=1_000, useful=2, irrelevant=998)
        )
        observations.append(
            _fixture_observation(index, quiet, solved=solved, emitted=2, useful=2, irrelevant=0)
        )

    comparison = compare_arms(spec, observations)
    noisy_report = evaluate_arm(spec, observations, noisy)
    quiet_report = evaluate_arm(spec, observations, quiet)

    assert noisy_report.metrics is not None and quiet_report.metrics is not None
    assert noisy_report.metrics.verified_solve_rate == quiet_report.metrics.verified_solve_rate
    assert noisy_report.metrics.cost_per_verified_solve == quiet_report.metrics.cost_per_verified_solve
    assert noisy_report.metrics.irrelevant_waypoint_rate == pytest.approx(0.998)
    assert quiet_report.metrics.irrelevant_waypoint_rate == pytest.approx(0.0)
    assert comparison.rank_of(quiet) < comparison.rank_of(noisy)


def test_emitting_more_waypoints_cannot_improve_rank() -> None:
    """Idea count is never scored: same useful yield, more noise, worse rank."""

    spec = _fixture_spec(arms=(SearchArm.C_FORWARD_BACKWARD, SearchArm.D_FORWARD_SEEDS))
    prolific = SearchArm.C_FORWARD_BACKWARD
    frugal = SearchArm.D_FORWARD_SEEDS
    observations = []
    for index in range(4):
        solved = index < 2
        observations.append(
            _fixture_observation(index, prolific, solved=solved, emitted=1_000, useful=10, irrelevant=990)
        )
        observations.append(
            _fixture_observation(index, frugal, solved=solved, emitted=10, useful=10, irrelevant=0)
        )

    prolific_report = evaluate_arm(spec, observations, prolific)
    frugal_report = evaluate_arm(spec, observations, frugal)
    assert prolific_report.metrics is not None and frugal_report.metrics is not None
    # Identical useful waypoint counts; only the noise differs.
    assert prolific_report.metrics.useful_waypoint_rate == pytest.approx(0.01)
    assert frugal_report.metrics.useful_waypoint_rate == pytest.approx(1.0)

    comparison = compare_arms(spec, observations)
    assert comparison.rank_of(frugal) < comparison.rank_of(prolific)


def test_false_root_progress_contaminates_an_arm_with_the_highest_solve_rate() -> None:
    """LOCAL_WAYPOINT_AS_ROOT_PROGRESS: solving more does not buy back credibility."""

    spec = _fixture_spec(arms=(SearchArm.A_FORWARD_ONLY, SearchArm.B_BACKWARD_ONLY))
    observations = []
    for index in range(4):
        observations.append(
            _fixture_observation(index, SearchArm.A_FORWARD_ONLY, solved=index < 1)
        )
        observations.append(
            _fixture_observation(
                index,
                SearchArm.B_BACKWARD_ONLY,
                solved=True,
                claims=4,
                upheld=1,
            )
        )

    honest = evaluate_arm(spec, observations, SearchArm.A_FORWARD_ONLY)
    contaminated = evaluate_arm(spec, observations, SearchArm.B_BACKWARD_ONLY)
    assert honest.verdict is ArmVerdict.ARM_ADMISSIBLE
    assert contaminated.verdict is ArmVerdict.ARM_CONTAMINATED
    assert contaminated.metrics is not None and honest.metrics is not None
    assert contaminated.metrics.verified_solve_rate > honest.metrics.verified_solve_rate
    assert any("LOCAL_WAYPOINT_AS_ROOT_PROGRESS" in reason for reason in contaminated.reasons)

    comparison = compare_arms(spec, observations)
    assert comparison.rank_of(SearchArm.A_FORWARD_ONLY) < comparison.rank_of(SearchArm.B_BACKWARD_ONLY)


def test_unverified_connections_called_roads_contaminate_the_arm() -> None:
    spec = _fixture_spec(arms=(SearchArm.A_FORWARD_ONLY, SearchArm.B_BACKWARD_ONLY))
    observations = [
        _fixture_observation(index, SearchArm.B_BACKWARD_ONLY, solved=True, claimed=8, confirmed=2, tests=8)
        for index in range(4)
    ]
    report = evaluate_arm(spec, observations, SearchArm.B_BACKWARD_ONLY)
    assert report.verdict is ArmVerdict.ARM_CONTAMINATED
    assert any("UNVERIFIED_CONNECTION_AS_ROAD" in reason for reason in report.reasons)


def test_gold_path_exposure_invalidates_the_trial() -> None:
    spec = _fixture_spec()
    observations = [
        _fixture_observation(0, SearchArm.A_FORWARD_ONLY, solved=True, gold_path_exposed=True)
    ]
    report = evaluate_arm(spec, observations, SearchArm.A_FORWARD_ONLY)
    assert report.verdict is ArmVerdict.TRIAL_INVALID
    assert any("GOLD_PATH_LEAK" in reason for reason in report.reasons)


def test_budget_violation_invalidates_the_trial() -> None:
    """Seed volume is not free: exceeding the matched budget voids the arm."""

    spec = _fixture_spec()
    observations = [
        _fixture_observation(
            0,
            SearchArm.E_FORWARD_BACKWARD_SEEDS,
            solved=True,
            expansions=FIXTURE_BUDGET.max_expansions + 1,
        )
    ]
    report = evaluate_arm(spec, observations, SearchArm.E_FORWARD_BACKWARD_SEEDS)
    assert report.verdict is ArmVerdict.TRIAL_INVALID
    assert any("budget_violation_expansions" in reason for reason in report.reasons)


def test_unknown_chronology_is_cannot_check_and_never_a_pass() -> None:
    spec = _fixture_spec()
    observations = [
        TaskArmObservation(
            **{
                **_fixture_observation(0, SearchArm.A_FORWARD_ONLY, solved=True).__dict__,
                "gold_path_exposed": None,
            }
        )
    ]
    report = evaluate_arm(spec, observations, SearchArm.A_FORWARD_ONLY)
    assert report.verdict is ArmVerdict.CANNOT_CHECK
    assert report.metrics is None


def test_benchmark_frozen_after_execution_is_trial_invalid() -> None:
    spec = FrozenBenchmarkSpec(
        benchmark_id="FIXTURE_BENCHMARK_141",
        cases=(_fixture_case(0, HiddenPathTaskFamily.SHORT_DIRECT_FORWARD),),
        arms=tuple(SearchArm),
        budget=FIXTURE_BUDGET,
        ceilings=FIXTURE_CEILINGS,
        minimum_cases_per_arm=1,
        frozen_before_any_arm_execution=False,
    )
    report = evaluate_arm(
        spec,
        [_fixture_observation(0, SearchArm.A_FORWARD_ONLY, solved=True)],
        SearchArm.A_FORWARD_ONLY,
    )
    assert report.verdict is ArmVerdict.TRIAL_INVALID


def test_spec_hash_changes_when_a_threshold_is_retuned() -> None:
    """Freeze integrity: retuning a ceiling produces a different evaluator identity."""

    original = _fixture_spec()
    retuned = _fixture_spec(
        ceilings=ContaminationCeilings(
            max_false_root_progress_rate=0.90,
            min_connection_test_precision=0.10,
            max_repeated_known_failure_rate=0.90,
        )
    )
    assert original.spec_hash != retuned.spec_hash


def test_arm_metrics_and_comparison_grant_no_authority() -> None:
    spec = _fixture_spec()
    observations = [_fixture_observation(0, SearchArm.A_FORWARD_ONLY, solved=True)]
    report = evaluate_arm(spec, observations, SearchArm.A_FORWARD_ONLY)
    assert report.grants_scientific_authority is False
    assert report.metrics is not None
    assert report.metrics.grants_capability_claim is False
    comparison = compare_arms(spec, observations)
    assert comparison.grants_scientific_authority is False
    assert comparison.establishes_extension_benefit is False


def test_observation_rejects_impossible_counts() -> None:
    with pytest.raises(ValueError):
        _fixture_observation(0, SearchArm.A_FORWARD_ONLY, claimed=1, confirmed=5)
    with pytest.raises(ValueError):
        _fixture_observation(0, SearchArm.A_FORWARD_ONLY, emitted=2, useful=2, irrelevant=2)
    with pytest.raises(ValueError):
        _fixture_observation(0, SearchArm.A_FORWARD_ONLY, claims=1, upheld=3)
