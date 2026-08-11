from rakl.experience_substrate import EpisodeOutcome, TaskEpisode
from rakl.matched_microtrial import MatchedModelConfig, TrialResourceCeiling, TrialResourceUsage
from rakl.saturation_vector import NoveltyRound, SaturationAxis
from rakl.v3_metrology import (
    AttributionArm,
    AttributionPacket,
    AttributionRun,
    ProcessOutcome,
    ProcessTelemetry,
    aggregate_process_telemetry,
    assess_attribution,
    compare_state_metrics,
    measure_state,
)
from rakl.v3_runtime import RAKLV3State, record_saturation_round, record_task_episode


def _usage(tokens: int = 20) -> TrialResourceUsage:
    return TrialResourceUsage(
        model_input_tokens=tokens,
        model_output_tokens=10,
        preprocessing_model_tokens=5,
        preprocessing_tool_calls=2,
        external_retrieval_calls=1,
        wall_time_ms=100,
    )


def test_state_metrology_separates_raw_growth_from_retained_novelty():
    before_state = RAKLV3State()
    before = measure_state(before_state)

    episode = TaskEpisode(
        episode_id="ep-1",
        task_id="task-1",
        atom_id="atom-1",
        context_hash="ctx",
        problem_signature=("test",),
        fibre_snapshot_hash="fiber",
        operator_ids=("op-1",),
        action_trace=("try op-1",),
        observation_ids=("obs-1",),
        verification_ids=("verify-1",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("evidence://1",),
        artifact_hash="hash-ep-1",
        timestamp="2026-08-11T10:00:00+00:00",
        cost=1.0,
    )
    after_state = record_task_episode(before_state, episode)
    after_state = record_saturation_round(
        after_state,
        NoveltyRound(
            round_id="round-1",
            route_family="route-A",
            independent_route=True,
            retained_novelty=(
                (SaturationAxis.EXPERIENCE_PATTERN, 1),
                (SaturationAxis.PATH, 1),
            ),
        ),
    )
    after = measure_state(after_state)
    delta = compare_state_metrics(before, after)

    assert delta.episode_delta == 1
    assert dict(delta.retained_novelty_delta)[SaturationAxis.EXPERIENCE_PATTERN.value] == 1
    assert dict(delta.retained_novelty_delta)[SaturationAxis.PATH.value] == 1
    assert delta.retained_novelty_total == 2
    assert after.episode_count == 1


def test_process_telemetry_aggregates_by_method_surface():
    records = (
        ProcessTelemetry(
            invocation_id="p1",
            process_surface="routing",
            task_id="task-1",
            episode_id="ep-1",
            input_state_hash="s0",
            output_state_hash="s1",
            input_fibre_hash="f0",
            output_hash="o1",
            outcome=ProcessOutcome.SUCCESS,
            cost=2.0,
            residual_before=("a", "b"),
            residual_after=("b",),
            retained_novelty=((SaturationAxis.PATH, 1),),
            retrieved_ids=("tool-1", "failure-1"),
            selected_ids=("tool-1",),
            rejected_ids=("failure-1",),
        ),
        ProcessTelemetry(
            invocation_id="p2",
            process_surface="routing",
            task_id="task-2",
            episode_id="ep-2",
            input_state_hash="s1",
            output_state_hash="s2",
            input_fibre_hash="f1",
            output_hash="o2",
            outcome=ProcessOutcome.BLOCKED,
            cost=4.0,
            residual_before=("c",),
            residual_after=("c",),
            retained_novelty=((SaturationAxis.OBSTRUCTION, 1),),
        ),
    )

    (report,) = aggregate_process_telemetry(records)
    assert report.process_surface == "routing"
    assert report.invocation_count == 2
    assert report.success_count == 1
    assert report.blocked_count == 1
    assert report.mean_cost == 3.0
    assert report.mean_raw_residual_contraction == 0.5
    assert dict(report.retained_novelty_totals)[SaturationAxis.PATH.value] == 1
    assert dict(report.retained_novelty_totals)[SaturationAxis.OBSTRUCTION.value] == 1


def test_four_arm_attribution_separates_architecture_experience_and_memory_content_lift():
    model = MatchedModelConfig(
        model_id="model",
        model_revision="rev",
        temperature=0.0,
        max_output_tokens=100,
        seed=7,
        system_prompt="frozen",
    )
    ceiling = TrialResourceCeiling(
        max_model_input_tokens=100,
        max_model_output_tokens=100,
        max_preprocessing_model_tokens=100,
        max_preprocessing_tool_calls=10,
        max_external_retrieval_calls=10,
        max_wall_time_ms=1000,
    )

    outcomes = {
        "t1": {
            AttributionArm.MODEL_ONLY: (False, 0.2),
            AttributionArm.RAKL_RESET: (False, 0.3),
            AttributionArm.RAKL_SHAM_MEMORY: (False, 0.3),
            AttributionArm.RAKL_LEARNING: (True, 0.9),
        },
        "t2": {
            AttributionArm.MODEL_ONLY: (True, 0.8),
            AttributionArm.RAKL_RESET: (True, 0.8),
            AttributionArm.RAKL_SHAM_MEMORY: (True, 0.7),
            AttributionArm.RAKL_LEARNING: (True, 0.9),
        },
    }
    runs = []
    for task_id, task_outcomes in outcomes.items():
        for arm, (success, score) in task_outcomes.items():
            runs.append(
                AttributionRun(
                    run_id=f"{task_id}-{arm.value}",
                    task_id=task_id,
                    arm=arm,
                    success=success,
                    score=score,
                    failure_signature=() if success else ("not_solved",),
                    validity_failures=(),
                    resource_usage=_usage(),
                    output_hash=f"hash-{task_id}-{arm.value}",
                )
            )

    packet = AttributionPacket(
        benchmark_id="attr-1",
        model=model,
        resource_ceiling=ceiling,
        task_ids=("t1", "t2"),
        model_only_protocol_hash="model-only",
        rakl_protocol_hash="rakl",
        reset_state_hash="reset",
        sham_state_hash="sham",
        learned_state_hash="learned",
        evaluator_protocol_hash="eval",
        runs=tuple(runs),
        frozen_before_runs=True,
    )
    report = assess_attribution(packet)

    assert report.validation.matched
    assert report.total_success_lift == 0.5
    assert report.experience_success_lift == 0.5
    assert report.content_specific_success_lift == 0.5
    assert report.learning_vs_model_outcomes is not None
    assert report.learning_vs_model_outcomes.rakl_only_success == 1
    assert report.learning_vs_model_outcomes.baseline_only_success == 0
    assert report.grants_global_capability_claim is False
