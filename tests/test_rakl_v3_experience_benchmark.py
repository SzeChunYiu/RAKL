from __future__ import annotations

from dataclasses import replace

from rakl.experience_benchmark import (
    ExperienceBenchmarkArm,
    ExperienceBenchmarkPacket,
    ExperienceBenchmarkPhase,
    ExperienceBenchmarkRun,
    ExperienceBenchmarkVerdict,
    assess_experience_benchmark,
)
from rakl.matched_microtrial import MatchedModelConfig, TrialResourceCeiling, TrialResourceUsage


def _usage() -> TrialResourceUsage:
    return TrialResourceUsage(
        model_input_tokens=100,
        model_output_tokens=20,
        preprocessing_model_tokens=40,
        preprocessing_tool_calls=2,
        external_retrieval_calls=1,
        wall_time_ms=1000,
    )


def _run(
    run_id: str,
    task_id: str,
    arm: ExperienceBenchmarkArm,
    phase: ExperienceBenchmarkPhase,
    before: str,
    after: str,
    *,
    success: bool,
    score: float,
    failure: tuple[str, ...] = (),
) -> ExperienceBenchmarkRun:
    return ExperienceBenchmarkRun(
        run_id=run_id,
        task_id=task_id,
        arm=arm,
        phase=phase,
        state_before_hash=before,
        state_after_hash=after,
        success=success,
        score=score,
        failure_signature=failure,
        resource_usage=_usage(),
        output_hash=f"sha256:{run_id}",
    )


def _packet() -> ExperienceBenchmarkPacket:
    model = MatchedModelConfig(
        model_id="model-x",
        model_revision="rev-1",
        temperature=0.0,
        max_output_tokens=100,
        seed=7,
        system_prompt="frozen prompt",
    )
    ceiling = TrialResourceCeiling(
        max_model_input_tokens=1000,
        max_model_output_tokens=100,
        max_preprocessing_model_tokens=1000,
        max_preprocessing_tool_calls=10,
        max_external_retrieval_calls=10,
        max_wall_time_ms=10000,
    )
    return ExperienceBenchmarkPacket(
        benchmark_id="experience-v3-1",
        model=model,
        resource_ceiling=ceiling,
        tool_policy_id="tools-frozen",
        output_schema_id="output-v1",
        evaluator_protocol_hash="eval-v1",
        initial_state_hash="S0",
        development_task_ids=("D1", "D2"),
        transfer_task_ids=("T1", "T2"),
        learned_state_after_development_hash="S2",
        frozen_before_runs=True,
        runs=(
            _run("b-d1", "D1", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S0", "S0", success=False, score=0.2, failure=("repeat",)),
            _run("l-d1", "D1", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S0", "S1", success=False, score=0.3, failure=("repeat",)),
            _run("b-d2", "D2", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S0", "S0", success=False, score=0.2, failure=("repeat",)),
            _run("l-d2", "D2", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S1", "S2", success=True, score=0.8),
            _run("b-t1", "T1", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S0", "S0", success=False, score=0.2, failure=("transfer-a",)),
            _run("l-t1", "T1", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S2", "T1-result", success=True, score=0.9),
            _run("b-t2", "T2", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S0", "S0", success=False, score=0.3, failure=("transfer-a",)),
            _run("l-t2", "T2", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S2", "T2-result", success=True, score=0.8),
        ),
    )


def test_matched_experience_benchmark_measures_learning_and_transfer() -> None:
    report = assess_experience_benchmark(_packet())
    assert report.verdict is ExperienceBenchmarkVerdict.VALID_MEASUREMENT
    assert report.validation.matched
    assert report.development_success_delta == 0.5
    assert report.transfer_success_delta == 1.0
    assert report.transfer_score_delta == 0.6
    assert report.transfer_repeat_failure_delta == -0.5
    assert report.transfer_gain_observed
    assert not report.grants_global_capability_claim


def test_fresh_transfer_cannot_learn_from_previous_transfer_case() -> None:
    packet = _packet()
    runs = tuple(
        replace(run, state_before_hash="T1-result")
        if run.run_id == "l-t2"
        else run
        for run in packet.runs
    )
    contaminated = replace(packet, runs=runs)
    report = assess_experience_benchmark(contaminated)
    assert report.verdict is ExperienceBenchmarkVerdict.INVALID
    assert not report.validation.matched
    assert any("fresh_transfer_not_started_from_frozen_learned_state:l-t2" == item for item in report.validation.problems)
