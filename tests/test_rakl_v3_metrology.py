from __future__ import annotations

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
    validate_attribution_packet,
)
from rakl.v3_runtime import RAKLV3State, record_saturation_round


def test_state_growth_counts_retained_semantic_novelty_not_repo_growth() -> None:
    before_state = RAKLV3State()
    after_state = record_saturation_round(
        before_state,
        NoveltyRound(
            round_id="r1",
            route_family="independent-source-audit",
            independent_route=True,
            retained_novelty=((SaturationAxis.KNOWLEDGE, 1), (SaturationAxis.RELATION, 2)),
        ),
    )
    before = measure_state(before_state)
    after = measure_state(after_state)
    delta = compare_state_metrics(before, after)
    assert dict(delta.retained_novelty_delta)["KNOWLEDGE"] == 1
    assert dict(delta.retained_novelty_delta)["RELATION"] == 2
    assert delta.raw_object_delta == 0


def test_process_telemetry_requires_canonical_surface_and_cost_policy() -> None:
    record = ProcessTelemetry(
        invocation_id="i1",
        process_surface="routing",
        task_id="t1",
        input_state_hash="s0",
        output_state_hash="s0",
        outcome=ProcessOutcome.SUCCESS,
        cost=2.0,
        cost_policy_id="tokens-plus-tools-v1",
        residual_before=("gap-a", "gap-b"),
        residual_after=("gap-b",),
        retained_novelty=((SaturationAxis.PATH, 1),),
        retrieved_ids=("tool-a", "failure-a"),
        selected_ids=("tool-a",),
        rejected_ids=("failure-a",),
    )
    aggregate = aggregate_process_telemetry((record,))[0]
    assert aggregate.process_surface == "routing"
    assert aggregate.invocation_count == 1
    assert aggregate.mean_raw_residual_contraction == 1
    assert aggregate.costs_comparable
    assert dict(aggregate.retained_novelty_totals)["PATH"] == 1


def _resource() -> TrialResourceUsage:
    return TrialResourceUsage(
        model_input_tokens=100,
        model_output_tokens=20,
        preprocessing_model_tokens=0,
        preprocessing_tool_calls=2,
        external_retrieval_calls=1,
        wall_time_ms=1000,
    )


def _run(task: str, arm: AttributionArm, state: str, *, success: bool, score: float) -> AttributionRun:
    return AttributionRun(
        run_id=f"{task}-{arm.value}",
        task_id=task,
        arm=arm,
        state_before_hash=state,
        state_after_hash=state,
        success=success,
        score=score,
        failure_signature=() if success else ("not-solved",),
        validity_failures=(),
        resource_usage=_resource(),
        output_hash=f"out-{task}-{arm.value}",
    )


def _packet(*, leak_learning_state: bool = False) -> AttributionPacket:
    states = {
        AttributionArm.MODEL_ONLY: "model",
        AttributionArm.RAKL_RESET: "reset",
        AttributionArm.RAKL_SHAM_MEMORY: "sham",
        AttributionArm.RAKL_LEARNING: "learned",
    }
    runs = []
    scores = {
        AttributionArm.MODEL_ONLY: (False, 0.2),
        AttributionArm.RAKL_RESET: (False, 0.3),
        AttributionArm.RAKL_SHAM_MEMORY: (False, 0.35),
        AttributionArm.RAKL_LEARNING: (True, 0.7),
    }
    for arm in AttributionArm:
        run = _run("T1", arm, states[arm], success=scores[arm][0], score=scores[arm][1])
        if arm is AttributionArm.RAKL_LEARNING and leak_learning_state:
            run = AttributionRun(**{**run.__dict__, "state_after_hash": "learned-plus-T1"})
        runs.append(run)
    model = MatchedModelConfig(
        model_id="model",
        model_revision="rev",
        temperature=0.0,
        max_output_tokens=64,
        seed=1,
        system_prompt="fixed",
    )
    ceiling = TrialResourceCeiling(
        max_model_input_tokens=200,
        max_model_output_tokens=64,
        max_preprocessing_model_tokens=100,
        max_preprocessing_tool_calls=4,
        max_external_retrieval_calls=4,
        max_wall_time_ms=5000,
    )
    return AttributionPacket(
        benchmark_id="paper5-attribution-v1",
        model=model,
        resource_ceiling=ceiling,
        task_ids=("T1",),
        model_only_protocol_hash="p-model",
        rakl_protocol_hash="p-rakl",
        model_only_state_hash="model",
        reset_state_hash="reset",
        sham_state_hash="sham",
        sham_policy_hash="sham-policy-v1",
        learned_state_hash="learned",
        evaluator_protocol_hash="eval-v1",
        runs=tuple(runs),
        frozen_before_runs=True,
    )


def test_four_arm_attribution_separates_architecture_experience_and_content_lift() -> None:
    packet = _packet()
    validation = validate_attribution_packet(packet)
    assert validation.matched
    report = assess_attribution(packet)
    assert report.total_success_lift == 1.0
    assert report.experience_score_lift == 0.4
    assert report.content_specific_score_lift == 0.35
    assert report.learning_vs_model_outcomes is not None
    assert report.learning_vs_model_outcomes.rakl_only_success == 1
    assert not report.grants_global_capability_claim


def test_four_arm_attribution_fails_closed_on_transfer_state_leakage() -> None:
    validation = validate_attribution_packet(_packet(leak_learning_state=True))
    assert not validation.matched
    assert any(problem.startswith("state_leakage:") for problem in validation.problems)
