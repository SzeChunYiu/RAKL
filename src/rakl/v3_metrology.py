from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean
from typing import Iterable, Tuple

from .experience_substrate import SubstrateKind, SubstrateRelation
from .matched_microtrial import (
    MatchedModelConfig,
    TrialResourceCeiling,
    TrialResourceUsage,
    validate_resource_usage,
)
from .method_specs import METHOD_CONTRACTS
from .saturation_vector import SaturationAxis
from .v3_runtime import RAKLV3State, materialize_state_substrate, state_fingerprint


@dataclass(frozen=True)
class StateMetricSnapshot:
    """Read-only quantitative portrait of one frozen RAKL v3 state.

    Counts are descriptive. They do not imply that larger state is better.
    Retained novelty is reported separately from raw object growth.
    """

    state_hash: str
    substrate_hash: str
    node_counts: Tuple[Tuple[str, int], ...]
    edge_counts: Tuple[Tuple[str, int], ...]
    episode_count: int
    episode_outcome_counts: Tuple[Tuple[str, int], ...]
    lesson_count: int
    lesson_authority_counts: Tuple[Tuple[str, int], ...]
    tool_count: int
    tool_authority_counts: Tuple[Tuple[str, int], ...]
    failure_count: int
    failure_diagnosis_counts: Tuple[Tuple[str, int], ...]
    cumulative_retained_novelty: Tuple[Tuple[str, int], ...]
    evolution_variant_status_counts: Tuple[Tuple[str, int], ...]
    unresolved_link_count: int

    def novelty_for(self, axis: SaturationAxis) -> int:
        return dict(self.cumulative_retained_novelty).get(axis.value, 0)


@dataclass(frozen=True)
class StateGrowthDelta:
    before_state_hash: str
    after_state_hash: str
    node_deltas: Tuple[Tuple[str, int], ...]
    edge_deltas: Tuple[Tuple[str, int], ...]
    episode_delta: int
    lesson_delta: int
    tool_delta: int
    failure_delta: int
    retained_novelty_delta: Tuple[Tuple[str, int], ...]
    unresolved_link_delta: int

    @property
    def raw_object_delta(self) -> int:
        return self.episode_delta + self.lesson_delta + self.tool_delta + self.failure_delta

    @property
    def retained_novelty_total(self) -> int:
        return sum(value for _, value in self.retained_novelty_delta)


def _count(values: Iterable[str]) -> Tuple[Tuple[str, int], ...]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return tuple(sorted(result.items()))


def _delta_pairs(
    before: Tuple[Tuple[str, int], ...],
    after: Tuple[Tuple[str, int], ...],
    *,
    universe: Iterable[str] = (),
) -> Tuple[Tuple[str, int], ...]:
    left = dict(before)
    right = dict(after)
    keys = set(left) | set(right) | set(universe)
    return tuple(sorted((key, right.get(key, 0) - left.get(key, 0)) for key in keys))


def measure_state(state: RAKLV3State) -> StateMetricSnapshot:
    """Measure one state without changing it or granting authority."""

    substrate = materialize_state_substrate(state)
    novelty: dict[str, int] = {axis.value: 0 for axis in SaturationAxis}
    for round_ in state.saturation.rounds:
        for axis in SaturationAxis:
            novelty[axis.value] += round_.novelty_for(axis)

    evolution_counts: dict[str, int] = {}
    if state.evolution is not None:
        for variant in state.evolution.variants:
            key = variant.status.value
            evolution_counts[key] = evolution_counts.get(key, 0) + 1

    return StateMetricSnapshot(
        state_hash=state_fingerprint(state),
        substrate_hash=substrate.snapshot_hash,
        node_counts=_count(node.kind.value for node in substrate.nodes),
        edge_counts=_count(edge.relation.value for edge in substrate.edges),
        episode_count=len(state.experience.episodes),
        episode_outcome_counts=_count(item.outcome.value for item in state.experience.episodes),
        lesson_count=len(state.experience.lessons),
        lesson_authority_counts=_count(item.authority.value for item in state.experience.lessons),
        tool_count=len(state.tools.tools),
        tool_authority_counts=_count(item.authority.value for item in state.tools.tools),
        failure_count=len(state.failures.experiences),
        failure_diagnosis_counts=_count(item.diagnosis_status.value for item in state.failures.experiences),
        cumulative_retained_novelty=tuple(sorted(novelty.items())),
        evolution_variant_status_counts=tuple(sorted(evolution_counts.items())),
        unresolved_link_count=len(substrate.unresolved_links),
    )


def compare_state_metrics(before: StateMetricSnapshot, after: StateMetricSnapshot) -> StateGrowthDelta:
    return StateGrowthDelta(
        before_state_hash=before.state_hash,
        after_state_hash=after.state_hash,
        node_deltas=_delta_pairs(before.node_counts, after.node_counts, universe=(kind.value for kind in SubstrateKind)),
        edge_deltas=_delta_pairs(before.edge_counts, after.edge_counts, universe=(relation.value for relation in SubstrateRelation)),
        episode_delta=after.episode_count - before.episode_count,
        lesson_delta=after.lesson_count - before.lesson_count,
        tool_delta=after.tool_count - before.tool_count,
        failure_delta=after.failure_count - before.failure_count,
        retained_novelty_delta=_delta_pairs(
            before.cumulative_retained_novelty,
            after.cumulative_retained_novelty,
            universe=(axis.value for axis in SaturationAxis),
        ),
        unresolved_link_delta=after.unresolved_link_count - before.unresolved_link_count,
    )


class ProcessOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"
    BLOCKED = "BLOCKED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ProcessTelemetry:
    """Proposal-only measurement of one canonical RAKL process invocation."""

    invocation_id: str
    process_surface: str
    task_id: str
    episode_id: str
    input_state_hash: str
    output_state_hash: str
    input_fibre_hash: str
    output_hash: str
    outcome: ProcessOutcome
    cost: float
    cost_policy_id: str
    residual_before: Tuple[str, ...]
    residual_after: Tuple[str, ...]
    retained_novelty: Tuple[Tuple[SaturationAxis, int], ...]
    retrieved_ids: Tuple[str, ...] = ()
    selected_ids: Tuple[str, ...] = ()
    rejected_ids: Tuple[str, ...] = ()
    verification_ids: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.invocation_id or not self.process_surface or not self.task_id:
            raise ValueError("process telemetry requires invocation, process surface, and task id")
        if not self.cost_policy_id:
            raise ValueError("process telemetry requires a cost_policy_id")
        known_surfaces = {contract.surface for contract in METHOD_CONTRACTS}
        if self.process_surface not in known_surfaces:
            raise ValueError(f"unknown RAKL method surface: {self.process_surface}")
        if self.cost < 0:
            raise ValueError("process telemetry cost cannot be negative")
        axes = [axis for axis, _ in self.retained_novelty]
        if len(set(axes)) != len(axes):
            raise ValueError("retained_novelty axes must be unique")
        if any(value < 0 for _, value in self.retained_novelty):
            raise ValueError("retained novelty cannot be negative")

    @property
    def raw_residual_contraction(self) -> int:
        return len(self.residual_before) - len(self.residual_after)


@dataclass(frozen=True)
class ProcessAggregate:
    process_surface: str
    invocation_count: int
    success_count: int
    partial_success_count: int
    failure_count: int
    blocked_count: int
    cannot_check_count: int
    mean_cost: float
    cost_policy_ids: Tuple[str, ...]
    mean_raw_residual_contraction: float
    retained_novelty_totals: Tuple[Tuple[str, int], ...]
    retrieved_object_count: int
    selected_object_count: int
    rejected_object_count: int

    @property
    def valid_completion_rate(self) -> float:
        if not self.invocation_count:
            return 0.0
        return (self.success_count + self.partial_success_count) / self.invocation_count

    @property
    def costs_comparable(self) -> bool:
        return len(self.cost_policy_ids) <= 1


def aggregate_process_telemetry(records: Iterable[ProcessTelemetry]) -> Tuple[ProcessAggregate, ...]:
    grouped: dict[str, list[ProcessTelemetry]] = {}
    for record in records:
        grouped.setdefault(record.process_surface, []).append(record)

    reports: list[ProcessAggregate] = []
    for surface in sorted(grouped):
        items = grouped[surface]
        novelty = {axis.value: 0 for axis in SaturationAxis}
        for item in items:
            for axis, value in item.retained_novelty:
                novelty[axis.value] += value
        reports.append(
            ProcessAggregate(
                process_surface=surface,
                invocation_count=len(items),
                success_count=sum(item.outcome is ProcessOutcome.SUCCESS for item in items),
                partial_success_count=sum(item.outcome is ProcessOutcome.PARTIAL_SUCCESS for item in items),
                failure_count=sum(item.outcome is ProcessOutcome.FAILURE for item in items),
                blocked_count=sum(item.outcome is ProcessOutcome.BLOCKED for item in items),
                cannot_check_count=sum(item.outcome is ProcessOutcome.CANNOT_CHECK for item in items),
                mean_cost=mean(item.cost for item in items),
                cost_policy_ids=tuple(sorted({item.cost_policy_id for item in items})),
                mean_raw_residual_contraction=mean(item.raw_residual_contraction for item in items),
                retained_novelty_totals=tuple(sorted(novelty.items())),
                retrieved_object_count=sum(len(item.retrieved_ids) for item in items),
                selected_object_count=sum(len(item.selected_ids) for item in items),
                rejected_object_count=sum(len(item.rejected_ids) for item in items),
            )
        )
    return tuple(reports)


class AttributionArm(str, Enum):
    MODEL_ONLY = "MODEL_ONLY"
    RAKL_RESET = "RAKL_RESET"
    RAKL_SHAM_MEMORY = "RAKL_SHAM_MEMORY"
    RAKL_LEARNING = "RAKL_LEARNING"


@dataclass(frozen=True)
class AttributionRun:
    run_id: str
    task_id: str
    arm: AttributionArm
    state_before_hash: str
    state_after_hash: str
    success: bool
    score: float
    failure_signature: Tuple[str, ...]
    validity_failures: Tuple[str, ...]
    resource_usage: TrialResourceUsage
    output_hash: str

    def __post_init__(self) -> None:
        if not self.run_id or not self.task_id or not self.output_hash:
            raise ValueError("attribution run identifiers and output hash are required")
        if not self.state_before_hash or not self.state_after_hash:
            raise ValueError("attribution run requires before/after state identity")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("attribution score must be within [0, 1]")
        if not self.success and not self.failure_signature:
            raise ValueError("failed attribution run requires a failure signature")


@dataclass(frozen=True)
class AttributionPacket:
    benchmark_id: str
    model: MatchedModelConfig
    resource_ceiling: TrialResourceCeiling
    task_ids: Tuple[str, ...]
    model_only_protocol_hash: str
    rakl_protocol_hash: str
    model_only_state_hash: str
    reset_state_hash: str
    sham_state_hash: str
    sham_policy_hash: str
    learned_state_hash: str
    evaluator_protocol_hash: str
    runs: Tuple[AttributionRun, ...]
    frozen_before_runs: bool

    def __post_init__(self) -> None:
        if not self.benchmark_id or not self.task_ids:
            raise ValueError("attribution packet requires benchmark id and tasks")
        if len(set(self.task_ids)) != len(self.task_ids):
            raise ValueError("attribution task ids must be unique")
        required = (
            self.model_only_protocol_hash,
            self.rakl_protocol_hash,
            self.model_only_state_hash,
            self.reset_state_hash,
            self.sham_state_hash,
            self.sham_policy_hash,
            self.learned_state_hash,
            self.evaluator_protocol_hash,
        )
        if any(not value for value in required):
            raise ValueError("attribution protocol/state hashes cannot be empty")
        if self.sham_state_hash == self.learned_state_hash:
            raise ValueError("sham and learned state identities must differ")


@dataclass(frozen=True)
class AttributionValidation:
    matched: bool
    problems: Tuple[str, ...]


@dataclass(frozen=True)
class AttributionArmMetrics:
    arm: AttributionArm
    task_count: int
    success_rate: float
    mean_score: float
    validity_failure_rate: float
    mean_model_tokens: float
    mean_tool_calls: float
    mean_retrieval_calls: float
    mean_wall_time_ms: float


@dataclass(frozen=True)
class PairedOutcomeCounts:
    both_success: int
    rakl_only_success: int
    baseline_only_success: int
    both_fail: int


@dataclass(frozen=True)
class AttributionReport:
    validation: AttributionValidation
    metrics: Tuple[AttributionArmMetrics, ...]
    architecture_success_lift: float | None
    experience_success_lift: float | None
    content_specific_success_lift: float | None
    total_success_lift: float | None
    architecture_score_lift: float | None
    experience_score_lift: float | None
    content_specific_score_lift: float | None
    total_score_lift: float | None
    learning_vs_model_outcomes: PairedOutcomeCounts | None

    @property
    def grants_global_capability_claim(self) -> bool:
        return False

    @property
    def supports_scoped_assistance_measurement(self) -> bool:
        return self.validation.matched


def _expected_state_hash(packet: AttributionPacket, arm: AttributionArm) -> str:
    if arm is AttributionArm.MODEL_ONLY:
        return packet.model_only_state_hash
    if arm is AttributionArm.RAKL_RESET:
        return packet.reset_state_hash
    if arm is AttributionArm.RAKL_SHAM_MEMORY:
        return packet.sham_state_hash
    return packet.learned_state_hash


def validate_attribution_packet(packet: AttributionPacket) -> AttributionValidation:
    """Fail closed on arm mismatch, state leakage, task mismatch, or resources."""

    problems: list[str] = []
    if not packet.frozen_before_runs:
        problems.append("attribution_packet_not_frozen_before_runs")
    if packet.resource_ceiling.max_model_output_tokens != packet.model.max_output_tokens:
        problems.append("model_output_tokens_do_not_match_registered_ceiling")

    by_task: dict[str, list[AttributionRun]] = {}
    for run in packet.runs:
        by_task.setdefault(run.task_id, []).append(run)
        resource_report = validate_resource_usage(run.resource_usage, packet.resource_ceiling)
        problems.extend(f"{run.run_id}:{problem}" for problem in resource_report.problems)

        expected_state = _expected_state_hash(packet, run.arm)
        if run.state_before_hash != expected_state:
            problems.append(f"{run.run_id}:unexpected_state_before:{run.arm.value}")
        if run.state_after_hash != expected_state:
            problems.append(f"{run.run_id}:state_mutated_or_leaked:{run.arm.value}")

    expected = set(packet.task_ids)
    problems.extend(f"unexpected_task:{task}" for task in sorted(set(by_task) - expected))
    problems.extend(f"missing_task:{task}" for task in sorted(expected - set(by_task)))

    all_arms = set(AttributionArm)
    for task_id in packet.task_ids:
        runs = by_task.get(task_id, [])
        if len(runs) != len(all_arms):
            problems.append(f"task_run_count:{task_id}:{len(runs)}")
            continue
        arms = {run.arm for run in runs}
        if arms != all_arms:
            problems.append(f"task_arms_invalid:{task_id}")

    if len({run.run_id for run in packet.runs}) != len(packet.runs):
        problems.append("duplicate_run_id")

    return AttributionValidation(not problems, tuple(problems))


def _arm_metrics(packet: AttributionPacket, arm: AttributionArm) -> AttributionArmMetrics:
    by_task = {run.task_id: run for run in packet.runs if run.arm is arm}
    ordered = tuple(by_task[task_id] for task_id in packet.task_ids if task_id in by_task)
    if not ordered:
        return AttributionArmMetrics(arm, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return AttributionArmMetrics(
        arm=arm,
        task_count=len(ordered),
        success_rate=sum(item.success for item in ordered) / len(ordered),
        mean_score=mean(item.score for item in ordered),
        validity_failure_rate=sum(bool(item.validity_failures) for item in ordered) / len(ordered),
        mean_model_tokens=mean(
            item.resource_usage.model_input_tokens + item.resource_usage.model_output_tokens
            for item in ordered
        ),
        mean_tool_calls=mean(item.resource_usage.preprocessing_tool_calls for item in ordered),
        mean_retrieval_calls=mean(item.resource_usage.external_retrieval_calls for item in ordered),
        mean_wall_time_ms=mean(item.resource_usage.wall_time_ms for item in ordered),
    )


def _paired_learning_vs_model(packet: AttributionPacket) -> PairedOutcomeCounts:
    model = {run.task_id: run for run in packet.runs if run.arm is AttributionArm.MODEL_ONLY}
    learning = {run.task_id: run for run in packet.runs if run.arm is AttributionArm.RAKL_LEARNING}
    both_success = rakl_only = baseline_only = both_fail = 0
    for task_id in packet.task_ids:
        b = model[task_id].success
        r = learning[task_id].success
        if b and r:
            both_success += 1
        elif r and not b:
            rakl_only += 1
        elif b and not r:
            baseline_only += 1
        else:
            both_fail += 1
    return PairedOutcomeCounts(both_success, rakl_only, baseline_only, both_fail)


def assess_attribution(packet: AttributionPacket) -> AttributionReport:
    validation = validate_attribution_packet(packet)
    if not validation.matched:
        return AttributionReport(
            validation=validation,
            metrics=(),
            architecture_success_lift=None,
            experience_success_lift=None,
            content_specific_success_lift=None,
            total_success_lift=None,
            architecture_score_lift=None,
            experience_score_lift=None,
            content_specific_score_lift=None,
            total_score_lift=None,
            learning_vs_model_outcomes=None,
        )

    metrics = tuple(_arm_metrics(packet, arm) for arm in AttributionArm)
    lookup = {item.arm: item for item in metrics}
    model = lookup[AttributionArm.MODEL_ONLY]
    reset = lookup[AttributionArm.RAKL_RESET]
    sham = lookup[AttributionArm.RAKL_SHAM_MEMORY]
    learning = lookup[AttributionArm.RAKL_LEARNING]
    return AttributionReport(
        validation=validation,
        metrics=metrics,
        architecture_success_lift=reset.success_rate - model.success_rate,
        experience_success_lift=learning.success_rate - reset.success_rate,
        content_specific_success_lift=learning.success_rate - sham.success_rate,
        total_success_lift=learning.success_rate - model.success_rate,
        architecture_score_lift=reset.mean_score - model.mean_score,
        experience_score_lift=learning.mean_score - reset.mean_score,
        content_specific_score_lift=learning.mean_score - sham.mean_score,
        total_score_lift=learning.mean_score - model.mean_score,
        learning_vs_model_outcomes=_paired_learning_vs_model(packet),
    )
