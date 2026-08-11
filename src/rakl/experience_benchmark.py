from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import Iterable, Tuple

from .v3_authority import (
    AttestationPurpose,
    ProtectedAuthorityContext,
    canonical_sha256,
    resolve_protected_attestation,
)

from .inference import InferenceStatus, paired_lift_verdict
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


def _timestamp(value: str) -> datetime | None:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


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
    output_artifact_id: str = ""
    executed_at: str = ""

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
    evaluator_artifact_id: str = ""
    tool_policy_artifact_id: str = ""
    output_schema_artifact_id: str = ""
    task_artifact_ids: Tuple[Tuple[str, str], ...] = ()
    packet_frozen_at: str = ""
    freeze_attestation_id: str | None = None
    match_attestation_id: str | None = None

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
        if len({task_id for task_id, _ in self.task_artifact_ids}) != len(self.task_artifact_ids):
            raise ValueError("benchmark task artifact bindings must be unique")


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
    # Inference fields for statistical verdicts
    transfer_success_inference_status: InferenceStatus | None = None
    transfer_success_excludes_null: bool | None = None
    transfer_score_inference_status: InferenceStatus | None = None
    transfer_score_excludes_null: bool | None = None

    @property
    def grants_global_capability_claim(self) -> bool:
        return False

    @property
    def transfer_gain_observed(self) -> bool:
        """True if either transfer metric has a statistically significant lift.

        Uses interval-excludes-null inference rather than point-estimate sign.
        Returns False for INSUFFICIENT_N or other indeterminate states.
        """
        if self.verdict is not ExperienceBenchmarkVerdict.VALID_MEASUREMENT:
            return False
        # Use interval-excludes-null verdict, not delta > 0
        success_ok = (
            self.transfer_success_excludes_null is True
            and self.transfer_success_inference_status == InferenceStatus.MEASURED_AND_DISTINGUISHABLE
        )
        score_ok = (
            self.transfer_score_excludes_null is True
            and self.transfer_score_inference_status == InferenceStatus.MEASURED_AND_DISTINGUISHABLE
        )
        return bool(success_ok or score_ok)


def _runs_by_task(packet: ExperienceBenchmarkPacket) -> dict[str, list[ExperienceBenchmarkRun]]:
    grouped: dict[str, list[ExperienceBenchmarkRun]] = {}
    for run in packet.runs:
        grouped.setdefault(run.task_id, []).append(run)
    return grouped


def benchmark_protocol_subject_hash(packet: ExperienceBenchmarkPacket) -> str:
    """Hash the pre-result benchmark packet, including exact artifact identities."""

    return canonical_sha256(
        {
            "benchmark_id": packet.benchmark_id,
            "model": repr(packet.model),
            "resource_ceiling": repr(packet.resource_ceiling),
            "tool_policy_id": packet.tool_policy_id,
            "output_schema_id": packet.output_schema_id,
            "evaluator_protocol_hash": packet.evaluator_protocol_hash,
            "initial_state_hash": packet.initial_state_hash,
            "development_task_ids": list(packet.development_task_ids),
            "transfer_task_ids": list(packet.transfer_task_ids),
            "evaluator_artifact_id": packet.evaluator_artifact_id,
            "tool_policy_artifact_id": packet.tool_policy_artifact_id,
            "output_schema_artifact_id": packet.output_schema_artifact_id,
            "task_artifact_ids": [list(item) for item in packet.task_artifact_ids],
            "packet_frozen_at": packet.packet_frozen_at,
        }
    )


def benchmark_result_subject_hash(packet: ExperienceBenchmarkPacket) -> str:
    return canonical_sha256(
        {
            "protocol_subject_hash": benchmark_protocol_subject_hash(packet),
            "learned_state_after_development_hash": packet.learned_state_after_development_hash,
            "runs": [
                {
                    "run_id": run.run_id,
                    "task_id": run.task_id,
                    "arm": run.arm.value,
                    "phase": run.phase.value,
                    "state_before_hash": run.state_before_hash,
                    "state_after_hash": run.state_after_hash,
                    "success": run.success,
                    "score": run.score,
                    "failure_signature": list(run.failure_signature),
                    "resource_usage": repr(run.resource_usage),
                    "output_hash": run.output_hash,
                    "output_artifact_id": run.output_artifact_id,
                    "executed_at": run.executed_at,
                }
                for run in packet.runs
            ],
        }
    )


def validate_experience_benchmark(
    packet: ExperienceBenchmarkPacket,
    authority_context: ProtectedAuthorityContext | None = None,
) -> ExperienceBenchmarkValidation:
    """Fail closed on chronology, state leakage, task mismatch, or resource mismatch."""

    problems: list[str] = []
    # The legacy boolean is not an authority input.  Protected content and
    # chronology receipts below decide whether the packet was actually frozen.
    if packet.resource_ceiling.max_model_output_tokens != packet.model.max_output_tokens:
        problems.append("model_output_tokens_do_not_match_registered_ceiling")

    expected_tasks = packet.development_task_ids + packet.transfer_task_ids
    expected_set = set(expected_tasks)
    grouped = _runs_by_task(packet)
    unexpected = set(grouped) - expected_set
    missing = expected_set - set(grouped)
    problems.extend(f"unexpected_task:{task_id}" for task_id in sorted(unexpected))
    problems.extend(f"missing_task:{task_id}" for task_id in sorted(missing))

    task_artifacts = dict(packet.task_artifact_ids)
    if set(task_artifacts) != expected_set:
        problems.append("task_artifact_bindings_do_not_match_registered_tasks")
    protocol_artifact_ids = tuple(
        item
        for item in (
            packet.evaluator_artifact_id,
            packet.tool_policy_artifact_id,
            packet.output_schema_artifact_id,
        )
        if item
    ) + tuple(task_artifacts.get(task_id, "") for task_id in expected_tasks)
    if not packet.packet_frozen_at or not packet.evaluator_artifact_id or not packet.tool_policy_artifact_id or not packet.output_schema_artifact_id:
        problems.append("benchmark_protocol_content_bindings_incomplete")
    freeze = resolve_protected_attestation(
        authority_context,
        packet.freeze_attestation_id,
        purpose=AttestationPurpose.BENCHMARK_FREEZE,
        subject_hash=benchmark_protocol_subject_hash(packet),
        required_artifact_ids=protocol_artifact_ids,
    )
    problems.extend(f"freeze:{reason}" for reason in freeze.reasons)

    artifacts = {item.artifact_id: item for item in authority_context.artifacts} if authority_context is not None else {}
    evaluator_artifact = artifacts.get(packet.evaluator_artifact_id)
    if evaluator_artifact is None or evaluator_artifact.payload_sha256 != packet.evaluator_protocol_hash:
        problems.append("evaluator_protocol_bytes_not_bound_to_declared_hash")
    freeze_attestation = None
    if authority_context is not None:
        freeze_attestation = next((item for item in authority_context.attestations if item.attestation_id == packet.freeze_attestation_id), None)
    packet_frozen = _timestamp(packet.packet_frozen_at)
    if packet_frozen is None:
        problems.append("benchmark_packet_frozen_at_invalid")
    if freeze_attestation is not None:
        freeze_subject_time = _timestamp(freeze_attestation.subject_frozen_at)
        if freeze_subject_time != packet_frozen:
            problems.append("freeze_attestation_subject_time_mismatch")
        for artifact_id in protocol_artifact_ids:
            artifact = artifacts.get(artifact_id)
            if artifact is not None and packet_frozen is not None:
                artifact_frozen = _timestamp(artifact.frozen_at)
                if artifact_frozen is None or artifact_frozen > packet_frozen:
                    problems.append(f"protocol_artifact_not_frozen_before_packet:{artifact_id}")

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
            output = artifacts.get(run.output_artifact_id)
            if not run.output_artifact_id or output is None:
                problems.append(f"run_output_artifact_unresolved:{run.run_id}")
            elif not output.content_valid or output.payload_sha256 != run.output_hash:
                problems.append(f"run_output_bytes_hash_mismatch:{run.run_id}")
            executed = _timestamp(run.executed_at)
            freeze_issued = _timestamp(freeze_attestation.issued_at) if freeze_attestation is not None else None
            if executed is None:
                problems.append(f"run_execution_chronology_missing:{run.run_id}")
            elif freeze_issued is not None and executed <= freeze_issued:
                problems.append(f"run_not_after_frozen_packet:{run.run_id}")
            if output is not None and executed is not None and _timestamp(output.frozen_at) != executed:
                problems.append(f"run_output_chronology_mismatch:{run.run_id}")

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

    output_ids = tuple(run.output_artifact_id for run in packet.runs if run.output_artifact_id)
    matched = resolve_protected_attestation(
        authority_context,
        packet.match_attestation_id,
        purpose=AttestationPurpose.BENCHMARK_MATCH,
        subject_hash=benchmark_result_subject_hash(packet),
        required_artifact_ids=protocol_artifact_ids + output_ids,
    )
    problems.extend(f"match:{reason}" for reason in matched.reasons)
    if authority_context is not None and packet.match_attestation_id:
        match_attestation = next((item for item in authority_context.attestations if item.attestation_id == packet.match_attestation_id), None)
        if match_attestation is not None:
            match_issued = _timestamp(match_attestation.issued_at)
            match_subject_frozen = _timestamp(match_attestation.subject_frozen_at)
            run_times = tuple(_timestamp(run.executed_at) for run in packet.runs)
            if match_issued is None or any(item is None or match_issued <= item for item in run_times):
                problems.append("match_attestation_not_after_all_runs")
            if match_subject_frozen is None or any(item is None or match_subject_frozen < item for item in run_times):
                problems.append("match_subject_not_frozen_after_all_runs")

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


def assess_experience_benchmark(
    packet: ExperienceBenchmarkPacket,
    authority_context: ProtectedAuthorityContext | None = None,
) -> ExperienceBenchmarkReport:
    validation = validate_experience_benchmark(packet, authority_context)
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

    # Build paired differences for transfer tasks (per-task paired comparison)
    transfer_task_order = packet.transfer_task_ids
    success_diffs: list[float] = []
    score_diffs: list[float] = []
    for task_id in transfer_task_order:
        base_run = next(
            (run for run in packet.runs
             if run.task_id == task_id and run.arm == ExperienceBenchmarkArm.RESET_BASELINE
             and run.phase == ExperienceBenchmarkPhase.FRESH_TRANSFER),
            None,
        )
        learn_run = next(
            (run for run in packet.runs
             if run.task_id == task_id and run.arm == ExperienceBenchmarkArm.LEARNING_ENABLED
             and run.phase == ExperienceBenchmarkPhase.FRESH_TRANSFER),
            None,
        )
        if base_run is not None and learn_run is not None:
            success_diffs.append(1.0 if learn_run.success else 0.0 - (1.0 if base_run.success else 0.0))
            score_diffs.append(learn_run.score - base_run.score)

    # Compute statistical inference for transfer metrics
    success_verdict = paired_lift_verdict(success_diffs, alpha=0.05, n_boot=5000, n_perm=5000, seed=42) if success_diffs else None
    score_verdict = paired_lift_verdict(score_diffs, alpha=0.05, n_boot=5000, n_perm=5000, seed=43) if score_diffs else None

    return ExperienceBenchmarkReport(
        verdict=ExperienceBenchmarkVerdict.VALID_MEASUREMENT,
        validation=validation,
        metrics=metrics,
        development_success_delta=dev_learn.success_rate - dev_base.success_rate,
        development_score_delta=dev_learn.mean_score - dev_base.mean_score,
        transfer_success_delta=transfer_learn.success_rate - transfer_base.success_rate,
        transfer_score_delta=transfer_learn.mean_score - transfer_base.mean_score,
        transfer_repeat_failure_delta=transfer_learn.repeated_failure_rate - transfer_base.repeated_failure_rate,
        transfer_success_inference_status=success_verdict.status if success_verdict else None,
        transfer_success_excludes_null=success_verdict.excludes_null if success_verdict else None,
        transfer_score_inference_status=score_verdict.status if score_verdict else None,
        transfer_score_excludes_null=score_verdict.excludes_null if score_verdict else None,
    )
