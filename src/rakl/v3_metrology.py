from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean
from typing import Iterable, Tuple

from .core import KnowledgeFiber
from .experience_substrate import SubstrateKind, SubstrateRelation
from .matched_microtrial import MatchedModelConfig, TrialResourceCeiling, TrialResourceUsage, validate_resource_usage
from .method_specs import METHOD_CONTRACTS
from .saturation_vector import SaturationAxis
from .unified_substrate import materialize_unified_substrate
from .v3_runtime import RAKLV3State, state_fingerprint


@dataclass(frozen=True)
class StateMetricSnapshot:
    """Read-only quantitative portrait of an explicitly bounded RAKL state."""

    state_hash: str
    substrate_hash: str
    measurement_scope: Tuple[str, ...]
    legacy_knowledge_fiber_count: int
    legacy_knowledge_projection_count: int
    node_counts: Tuple[Tuple[str, int], ...]
    edge_counts: Tuple[Tuple[str, int], ...]
    episode_count: int
    lesson_count: int
    tool_count: int
    failure_count: int
    cumulative_retained_novelty: Tuple[Tuple[str, int], ...]
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
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return tuple(sorted(counts.items()))


def _delta_pairs(before: Tuple[Tuple[str, int], ...], after: Tuple[Tuple[str, int], ...], *, universe: Iterable[str] = ()) -> Tuple[Tuple[str, int], ...]:
    left, right = dict(before), dict(after)
    keys = set(left) | set(right) | set(universe)
    return tuple(sorted((key, right.get(key, 0) - left.get(key, 0)) for key in keys))


def measure_state(state: RAKLV3State, *, legacy_knowledge_fibers: Iterable[KnowledgeFiber] = ()) -> StateMetricSnapshot:
    """Measure state without mutating it or granting authority."""

    legacy = tuple(legacy_knowledge_fibers)
    substrate = materialize_unified_substrate(
        experience=state.experience,
        tools=state.tools,
        failures=state.failures,
        legacy_knowledge_fibers=legacy,
        evolution=state.evolution,
    )
    novelty = {axis.value: 0 for axis in SaturationAxis}
    for round_ in state.saturation.rounds:
        for axis in SaturationAxis:
            novelty[axis.value] += round_.novelty_for(axis)
    return StateMetricSnapshot(
        state_hash=state_fingerprint(state),
        substrate_hash=substrate.snapshot_hash,
        measurement_scope=("V3_RUNTIME_STATE", "LEGACY_KNOWLEDGE_FIBERS_INCLUDED" if legacy else "NO_LEGACY_KNOWLEDGE_FIBERS_SUPPLIED"),
        legacy_knowledge_fiber_count=len(legacy),
        legacy_knowledge_projection_count=sum(len(fiber.projections) for fiber in legacy),
        node_counts=_count(node.kind.value for node in substrate.nodes),
        edge_counts=_count(edge.relation.value for edge in substrate.edges),
        episode_count=len(state.experience.episodes),
        lesson_count=len(state.experience.lessons),
        tool_count=len(state.tools.tools),
        failure_count=len(state.failures.experiences),
        cumulative_retained_novelty=tuple(sorted(novelty.items())),
        unresolved_link_count=len(substrate.unresolved_links),
    )


def compare_state_metrics(before: StateMetricSnapshot, after: StateMetricSnapshot) -> StateGrowthDelta:
    if before.measurement_scope != after.measurement_scope:
        raise ValueError("state metric snapshots have different measurement scopes")
    if before.legacy_knowledge_fiber_count != after.legacy_knowledge_fiber_count:
        raise ValueError("state metric snapshots have different legacy knowledge fibre counts")
    return StateGrowthDelta(
        before_state_hash=before.state_hash,
        after_state_hash=after.state_hash,
        node_deltas=_delta_pairs(before.node_counts, after.node_counts, universe=(kind.value for kind in SubstrateKind)),
        edge_deltas=_delta_pairs(before.edge_counts, after.edge_counts, universe=(relation.value for relation in SubstrateRelation)),
        episode_delta=after.episode_count - before.episode_count,
        lesson_delta=after.lesson_count - before.lesson_count,
        tool_delta=after.tool_count - before.tool_count,
        failure_delta=after.failure_count - before.failure_count,
        retained_novelty_delta=_delta_pairs(before.cumulative_retained_novelty, after.cumulative_retained_novelty, universe=(axis.value for axis in SaturationAxis)),
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
    """Measurement-only record for one canonical RAKL process invocation."""

    invocation_id: str
    process_surface: str
    task_id: str
    input_state_hash: str
    output_state_hash: str
    outcome: ProcessOutcome
    cost: float
    cost_policy_id: str
    residual_before: Tuple[str, ...]
    residual_after: Tuple[str, ...]
    retained_novelty: Tuple[Tuple[SaturationAxis, int], ...]
    episode_id: str = ""
    input_fibre_hash: str = ""
    output_hash: str = ""
    retrieved_ids: Tuple[str, ...] = ()
    selected_ids: Tuple[str, ...] = ()
    rejected_ids: Tuple[str, ...] = ()
    verification_ids: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.invocation_id or not self.process_surface or not self.task_id:
            raise ValueError("process telemetry requires invocation, process surface and task id")
        if not self.cost_policy_id:
            raise ValueError("process telemetry requires cost_policy_id")
        if self.process_surface not in {contract.surface for contract in METHOD_CONTRACTS}:
            raise ValueError(f"unknown RAKL method surface: {self.process_surface}")
        if self.cost < 0:
            raise ValueError("process telemetry cost cannot be negative")
        axes = [axis for axis, _ in self.retained_novelty]
        if len(set(axes)) != len(axes) or any(value < 0 for _, value in self.retained_novelty):
            raise ValueError("retained novelty must use unique axes and non-negative counts")

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

    @property
    def costs_comparable(self) -> bool:
        return len(self.cost_policy_ids) <= 1


def aggregate_process_telemetry(records: Iterable[ProcessTelemetry]) -> Tuple[ProcessAggregate, ...]:
    grouped: dict[str, list[ProcessTelemetry]] = {}
    for record in records:
        grouped.setdefault(record.process_surface, []).append(record)
    result: list[ProcessAggregate] = []
    for surface in sorted(grouped):
        items = grouped[surface]
        novelty = {axis.value: 0 for axis in SaturationAxis}
        for item in items:
            for axis, count in item.retained_novelty:
                novelty[axis.value] += count
        result.append(ProcessAggregate(
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
        ))
    return tuple(result)


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
        if not self.run_id or not self.task_id or not self.output_hash or not self.state_before_hash or not self.state_after_hash:
            raise ValueError("attribution run identities and before/after state hashes are required")
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
        if not self.benchmark_id or not self.task_ids or len(set(self.task_ids)) != len(self.task_ids):
            raise ValueError("attribution packet requires a benchmark id and unique tasks")
        values = (self.model_only_protocol_hash, self.rakl_protocol_hash, self.model_only_state_hash, self.reset_state_hash, self.sham_state_hash, self.sham_policy_hash, self.learned_state_hash, self.evaluator_protocol_hash)
        if any(not value for value in values):
            raise ValueError("attribution protocol/state identities cannot be empty")
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


def _expected_state(packet: AttributionPacket, arm: AttributionArm) -> str:
    return {
        AttributionArm.MODEL_ONLY: packet.model_only_state_hash,
        AttributionArm.RAKL_RESET: packet.reset_state_hash,
        AttributionArm.RAKL_SHAM_MEMORY: packet.sham_state_hash,
        AttributionArm.RAKL_LEARNING: packet.learned_state_hash,
    }[arm]


def validate_attribution_packet(packet: AttributionPacket) -> AttributionValidation:
    problems: list[str] = []
    if not packet.frozen_before_runs:
        problems.append("attribution_packet_not_frozen_before_runs")
    if packet.resource_ceiling.max_model_output_tokens != packet.model.max_output_tokens:
        problems.append("model_output_tokens_do_not_match_resource_ceiling")
    grouped: dict[tuple[str, AttributionArm], list[AttributionRun]] = {}
    for run in packet.runs:
        grouped.setdefault((run.task_id, run.arm), []).append(run)
        resource = validate_resource_usage(run.resource_usage, packet.resource_ceiling)
        problems.extend(f"{run.run_id}:{item}" for item in resource.problems)
        expected = _expected_state(packet, run.arm)
        if run.state_before_hash != expected:
            problems.append(f"wrong_start_state:{run.run_id}")
        if run.state_after_hash != expected:
            problems.append(f"state_leakage:{run.run_id}")
    required = {(task, arm) for task in packet.task_ids for arm in AttributionArm}
    for key in required:
        if len(grouped.get(key, ())) != 1:
            problems.append(f"run_count:{key[0]}:{key[1].value}:{len(grouped.get(key, ()))}")
    if any(task not in packet.task_ids for task, _ in grouped):
        problems.append("unexpected_task_present")
    if len({run.run_id for run in packet.runs}) != len(packet.runs):
        problems.append("duplicate_run_id")
    return AttributionValidation(not problems, tuple(problems))


def _arm_metrics(packet: AttributionPacket, arm: AttributionArm) -> AttributionArmMetrics:
    runs = tuple(run for run in packet.runs if run.arm is arm and run.task_id in packet.task_ids)
    if not runs:
        return AttributionArmMetrics(arm, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return AttributionArmMetrics(
        arm=arm,
        task_count=len(runs),
        success_rate=sum(run.success for run in runs) / len(runs),
        mean_score=mean(run.score for run in runs),
        validity_failure_rate=sum(bool(run.validity_failures) for run in runs) / len(runs),
        mean_model_tokens=mean(run.resource_usage.model_input_tokens + run.resource_usage.model_output_tokens for run in runs),
        mean_tool_calls=mean(run.resource_usage.preprocessing_tool_calls for run in runs),
        mean_retrieval_calls=mean(run.resource_usage.external_retrieval_calls for run in runs),
        mean_wall_time_ms=mean(run.resource_usage.wall_time_ms for run in runs),
    )


def _paired_outcomes(packet: AttributionPacket) -> PairedOutcomeCounts:
    by = {(run.task_id, run.arm): run for run in packet.runs}
    both = rakl_only = baseline_only = both_fail = 0
    for task in packet.task_ids:
        base = by[(task, AttributionArm.MODEL_ONLY)].success
        learn = by[(task, AttributionArm.RAKL_LEARNING)].success
        if base and learn:
            both += 1
        elif learn:
            rakl_only += 1
        elif base:
            baseline_only += 1
        else:
            both_fail += 1
    return PairedOutcomeCounts(both, rakl_only, baseline_only, both_fail)


def assess_attribution(packet: AttributionPacket) -> AttributionReport:
    validation = validate_attribution_packet(packet)
    if not validation.matched:
        return AttributionReport(validation, (), None, None, None, None, None, None, None, None, None)
    metrics = tuple(_arm_metrics(packet, arm) for arm in AttributionArm)
    m = {item.arm: item for item in metrics}
    model, reset, sham, learning = (m[AttributionArm.MODEL_ONLY], m[AttributionArm.RAKL_RESET], m[AttributionArm.RAKL_SHAM_MEMORY], m[AttributionArm.RAKL_LEARNING])
    return AttributionReport(
        validation,
        metrics,
        reset.success_rate - model.success_rate,
        learning.success_rate - reset.success_rate,
        learning.success_rate - sham.success_rate,
        learning.success_rate - model.success_rate,
        reset.mean_score - model.mean_score,
        learning.mean_score - reset.mean_score,
        learning.mean_score - sham.mean_score,
        learning.mean_score - model.mean_score,
        _paired_outcomes(packet),
    )
