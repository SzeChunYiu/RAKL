from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean
from typing import Iterable, Tuple

from .matched_microtrial import (
    MatchedModelConfig,
    TrialResourceCeiling,
    TrialResourceUsage,
    validate_resource_usage,
)


class ExperienceBenchmarkArm(str, Enum):
    RESET_BASELINE = "RESET_BASELINE"
    LEARNING_ENABLED = "LEARNING_ENABLED"


class ExperienceBenchmarkPhase(str, Enum):
    DEVELOPMENT_SEQUENCE = "DEVELOPMENT_SEQUENCE"
    FRESH_TRANSFER = "FRESH_TRANSFER"


class ExperienceBenchmarkVerdict(str, Enum):
    VALID_MEASUREMENT = "VALID_MEASUREMENT"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ExperienceBenchmarkRun:
    run_id: str
    task_id: str
    arm: ExperienceBenchmarkArm
    phase: ExperienceBenchmarkPhase
    state_before_hash: str
    state_after_hash: str
    success: bool
    score: float
    failure_signature: Tuple[str, ...]
    resource_usage: TrialResourceUsage
    output_hash: str

    def __post_init__(self) -> None:
        if not self.run_id or not self.task_id or not self.state_before_hash or not self.state_after_hash or not self.output_hash:
            raise ValueError("experience benchmark run identifiers and state/output hashes are required")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("experience benchmark score must be within [0, 1]")
        if not self.success and not self.failure_signature:
            raise ValueError("failed benchmark run requires a failure signature")


@dataclass(frozen=True)
class ExperienceBenchmarkPacket:
    benchmark_id: str
    model: MatchedModelConfig
    resource_ceiling: TrialResourceCeiling
    tool_policy_id: str
    output_schema_id: str
    evaluator_protocol_hash: str
    initial_state_hash: str
    development_task_ids: Tuple[str, ...]
    transfer_task_ids: Tuple[str, ...]
    learned_state_after_development_hash: str
    runs: Tuple[ExperienceBenchmarkRun, ...]
    frozen_before_runs: bool

    def __post_init__(self) -> None:
        required = (
            self.benchmark_id,
            self.tool_policy_id,
            self.output_schema_id,
            self.evaluator_protocol_hash,
            self.initial_state_hash,
            self.learned_state_after_development_hash,
        )
        if any(not value for value in required):
            raise ValueError("experience benchmark protocol identifiers cannot be empty")
        if not self.development_task_ids:
            raise ValueError("experience benchmark requires at least one development task")
        if not self.transfer_task_ids:
            raise ValueError("experience benchmark requires at least one fresh transfer task")
        if set(self.development_task_ids) & set(self.transfer_task_ids):
            raise ValueError("development and fresh-transfer tasks must be disjoint")
        expected = self.development_task_ids + self.transfer_task_ids
        if len(set(expected)) != len(expected):
            raise ValueError("benchmark task ids must be unique")


@dataclass(frozen=True)
class ExperienceBenchmarkValidation:
    matched: bool
    problems: Tuple[str, ...]


@dataclass(frozen=True)
class ArmPhaseMetrics:
    arm: ExperienceBenchmarkArm
    phase: ExperienceBenchmarkPhase
    task_count: int
    success_rate: float
    mean_score: float
    repeated_failure_rate: float
    total_model_tokens: int
    total_preprocessing_model_tokens: int
    total_tool_calls: int
    total_retrieval_calls: int
    total_wall_time_ms: int


@dataclass(frozen=True)
class ExperienceBenchmarkReport:
    verdict: ExperienceBenchmarkVerdict
    validation: ExperienceBenchmarkValidation
    metrics: Tuple[ArmPhaseMetrics, ...]
    development_success_delta: float | None
    development_score_delta: float | None
    transfer_success_delta: float | None
    transfer_score_delta: float | None
    transfer_repeat_failure_delta: float | None

    @property
    def grants_global_capability_claim(self) -> bool:
        return False

    @property
    def transfer_gain_observed(self) -> bool:
        if self.verdict is not ExperienceBenchmarkVerdict.VALID_MEASUREMENT:
            return False
        return bool(
            (self.transfer_success_delta is not None and self.transfer_success_delta > 0)
            or (self.transfer_score_delta is not None and self.transfer_score_delta > 0)
        )


def _runs_by_task(packet: ExperienceBenchmarkPacket) -> dict[str, list[ExperienceBenchmarkRun]]:
    grouped: dict[str, list[ExperienceBenchmarkRun]] = {}
    for run in packet.runs:
        grouped.setdefault(run.task_id, []).append(run)
    return grouped


def validate_experience_benchmark(packet: ExperienceBenchmarkPacket) -> ExperienceBenchmarkValidation:
    """Fail closed on chronology, state leakage, task mismatch, or resource mismatch."""

    problems: list[str] = []
    if not packet.frozen_before_runs:
        problems.append("benchmark_packet_not_frozen_before_runs")
    if packet.resource_ceiling.max_model_output_tokens != packet.model.max_output_tokens:
        problems.append("model_output_tokens_do_not_match_registered_ceiling")

    expected_tasks = packet.development_task_ids + packet.transfer_task_ids
    expected_set = set(expected_tasks)
    grouped = _runs_by_task(packet)
    unexpected = set(grouped) - expected_set
    missing = expected_set - set(grouped)
    problems.extend(f"unexpected_task:{task_id}" for task_id in sorted(unexpected))
    problems.extend(f"missing_task:{task_id}" for task_id in sorted(missing))

    for task_id in expected_tasks:
        task_runs = grouped.get(task_id, [])
        if len(task_runs) != 2:
            problems.append(f"task_run_count:{task_id}:{len(task_runs)}")
            continue
        arms = {run.arm for run in task_runs}
        if arms != {ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkArm.LEARNING_ENABLED}:
            problems.append(f"task_arms_invalid:{task_id}")
        expected_phase = (
            ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE
            if task_id in packet.development_task_ids
            else ExperienceBenchmarkPhase.FRESH_TRANSFER
        )
        for run in task_runs:
            if run.phase is not expected_phase:
                problems.append(f"task_phase_mismatch:{run.run_id}")
            resource_report = validate_resource_usage(run.resource_usage, packet.resource_ceiling)
            problems.extend(f"{run.run_id}:{problem}" for problem in resource_report.problems)

    baseline_runs = {
        run.task_id: run
        for run in packet.runs
        if run.arm is ExperienceBenchmarkArm.RESET_BASELINE and run.task_id in expected_set
    }
    for task_id, run in baseline_runs.items():
        if run.state_before_hash != packet.initial_state_hash:
            problems.append(f"baseline_state_not_reset_before:{task_id}")
        if run.state_after_hash != packet.initial_state_hash:
            problems.append(f"baseline_state_mutated:{task_id}")

    learning_dev = {
        run.task_id: run
        for run in packet.runs
        if run.arm is ExperienceBenchmarkArm.LEARNING_ENABLED
        and run.phase is ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE
    }
    previous_hash = packet.initial_state_hash
    for task_id in packet.development_task_ids:
        run = learning_dev.get(task_id)
        if run is None:
            continue
        if run.state_before_hash != previous_hash:
            problems.append(f"learning_state_chain_broken_before:{task_id}")
        previous_hash = run.state_after_hash
    if previous_hash != packet.learned_state_after_development_hash:
        problems.append("learned_state_after_development_hash_mismatch")

    for run in packet.runs:
        if run.arm is ExperienceBenchmarkArm.LEARNING_ENABLED and run.phase is ExperienceBenchmarkPhase.FRESH_TRANSFER:
            if run.state_before_hash != packet.learned_state_after_development_hash:
                problems.append(f"fresh_transfer_not_started_from_frozen_learned_state:{run.run_id}")

    if len({run.run_id for run in packet.runs}) != len(packet.runs):
        problems.append("duplicate_run_id")

    return ExperienceBenchmarkValidation(not problems, tuple(problems))


def _repeated_failure_rate(runs: Iterable[ExperienceBenchmarkRun]) -> float:
    ordered = tuple(runs)
    failures = 0
    repeats = 0
    seen: set[Tuple[str, ...]] = set()
    for run in ordered:
        if run.success:
            continue
        failures += 1
        signature = run.failure_signature
        if signature in seen:
            repeats += 1
        seen.add(signature)
    return repeats / failures if failures else 0.0


def _metrics(
    packet: ExperienceBenchmarkPacket,
    arm: ExperienceBenchmarkArm,
    phase: ExperienceBenchmarkPhase,
) -> ArmPhaseMetrics:
    task_order = packet.development_task_ids if phase is ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE else packet.transfer_task_ids
    by_task = {
        run.task_id: run
        for run in packet.runs
        if run.arm is arm and run.phase is phase
    }
    ordered = tuple(by_task[task_id] for task_id in task_order if task_id in by_task)
    if not ordered:
        return ArmPhaseMetrics(arm, phase, 0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0)
    return ArmPhaseMetrics(
        arm=arm,
        phase=phase,
        task_count=len(ordered),
        success_rate=sum(run.success for run in ordered) / len(ordered),
        mean_score=mean(run.score for run in ordered),
        repeated_failure_rate=_repeated_failure_rate(ordered),
        total_model_tokens=sum(run.resource_usage.model_input_tokens + run.resource_usage.model_output_tokens for run in ordered),
        total_preprocessing_model_tokens=sum(run.resource_usage.preprocessing_model_tokens for run in ordered),
        total_tool_calls=sum(run.resource_usage.preprocessing_tool_calls for run in ordered),
        total_retrieval_calls=sum(run.resource_usage.external_retrieval_calls for run in ordered),
        total_wall_time_ms=sum(run.resource_usage.wall_time_ms for run in ordered),
    )


def assess_experience_benchmark(packet: ExperienceBenchmarkPacket) -> ExperienceBenchmarkReport:
    validation = validate_experience_benchmark(packet)
    if not validation.matched:
        return ExperienceBenchmarkReport(
            verdict=ExperienceBenchmarkVerdict.INVALID,
            validation=validation,
            metrics=(),
            development_success_delta=None,
            development_score_delta=None,
            transfer_success_delta=None,
            transfer_score_delta=None,
            transfer_repeat_failure_delta=None,
        )

    metrics = tuple(
        _metrics(packet, arm, phase)
        for phase in (ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, ExperienceBenchmarkPhase.FRESH_TRANSFER)
        for arm in (ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkArm.LEARNING_ENABLED)
    )
    lookup = {(metric.arm, metric.phase): metric for metric in metrics}
    dev_base = lookup[(ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE)]
    dev_learn = lookup[(ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE)]
    transfer_base = lookup[(ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.FRESH_TRANSFER)]
    transfer_learn = lookup[(ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.FRESH_TRANSFER)]
    return ExperienceBenchmarkReport(
        verdict=ExperienceBenchmarkVerdict.VALID_MEASUREMENT,
        validation=validation,
        metrics=metrics,
        development_success_delta=dev_learn.success_rate - dev_base.success_rate,
        development_score_delta=dev_learn.mean_score - dev_base.mean_score,
        transfer_success_delta=transfer_learn.success_rate - transfer_base.success_rate,
        transfer_score_delta=transfer_learn.mean_score - transfer_base.mean_score,
        transfer_repeat_failure_delta=transfer_learn.repeated_failure_rate - transfer_base.repeated_failure_rate,
    )
