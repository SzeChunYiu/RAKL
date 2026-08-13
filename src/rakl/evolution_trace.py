from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping, Tuple


class MetricAuthority(str, Enum):
    DESCRIPTIVE = "DESCRIPTIVE"
    CONTROL_INPUT = "CONTROL_INPUT"
    EVOLUTION_EVIDENCE = "EVOLUTION_EVIDENCE"
    HARD_PROTECTED = "HARD_PROTECTED"


class MetricDirection(str, Enum):
    MAXIMIZE = "MAXIMIZE"
    MINIMIZE = "MINIMIZE"
    CONSTRAINT = "CONSTRAINT"


class DecisionStatus(str, Enum):
    SELECTED = "SELECTED"
    ABSTAIN = "ABSTAIN"
    BLOCKED = "BLOCKED"


class HardGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=lambda x: x.value if isinstance(x, Enum) else x)
    return sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class MetricDefinition:
    metric_name: str
    version: str
    unit: str
    direction: MetricDirection
    authority: MetricAuthority
    control_min: float | None = None
    control_max: float | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.metric_name or not self.version or not self.unit:
            raise ValueError("metric definition requires name/version/unit")
        if (self.control_min is None) != (self.control_max is None):
            raise ValueError("control normalization bounds must appear together")
        if self.control_min is not None and self.control_min >= self.control_max:
            raise ValueError("control_min must be < control_max")
        if self.authority is MetricAuthority.CONTROL_INPUT and self.control_min is None:
            raise ValueError("control-input metric requires frozen normalization bounds")

    @property
    def definition_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class MetricRegistry:
    registry_id: str
    definitions: Tuple[MetricDefinition, ...]

    def __post_init__(self) -> None:
        names = [d.metric_name for d in self.definitions]
        if not self.registry_id or len(names) != len(set(names)):
            raise ValueError("metric registry requires id and unique metric names")

    @property
    def registry_hash(self) -> str:
        return canonical_hash({"registry_id": self.registry_id, "definitions": [asdict(d) for d in self.definitions]})

    def by_name(self) -> Mapping[str, MetricDefinition]:
        return {d.metric_name: d for d in self.definitions}

    def validate_receipt(self, receipt: "MetricReceipt") -> None:
        definition = self.by_name().get(receipt.metric_name)
        if definition is None:
            raise ValueError("metric receipt references unregistered metric name")
        if receipt.definition_hash != definition.definition_hash:
            raise ValueError("metric receipt definition hash does not match frozen registry")
        if receipt.authority is not definition.authority:
            raise ValueError("metric receipt authority does not match frozen definition")
        if receipt.unit != definition.unit:
            raise ValueError("metric receipt unit does not match frozen definition")


@dataclass(frozen=True)
class EvaluationEpoch:
    epoch_id: str
    metric_registry_hash: str
    evaluator_hash: str
    benchmark_protocol_hash: str
    model_tool_harness_hash: str
    decision_policy_hash: str
    observatory_instrumentation_hash: str

    def __post_init__(self) -> None:
        if not self.epoch_id:
            raise ValueError("evaluation epoch requires id")
        for value in (
            self.metric_registry_hash,
            self.evaluator_hash,
            self.benchmark_protocol_hash,
            self.model_tool_harness_hash,
            self.decision_policy_hash,
            self.observatory_instrumentation_hash,
        ):
            if not _is_sha256(value):
                raise ValueError("evaluation epoch identities must be sha256")

    @property
    def epoch_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class GenomeSnapshot:
    variant_id: str
    genome_hash: str
    parent_ids: Tuple[str, ...]
    surfaces: Tuple[Tuple[str, str], ...]
    resource_profile: Tuple[Tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not self.variant_id or not _is_sha256(self.genome_hash):
            raise ValueError("genome snapshot requires id and sha256 genome_hash")
        names = [k for k, _ in self.surfaces]
        if len(names) != len(set(names)):
            raise ValueError("genome surface keys must be unique")


@dataclass(frozen=True)
class SelfModelSnapshot:
    self_model_hash: str
    genome_hash: str
    evaluation_epoch_id: str
    episode_cutoff_hash: str
    context_signature: Tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.self_model_hash, self.genome_hash, self.episode_cutoff_hash):
            if not _is_sha256(value):
                raise ValueError("self-model identities must be sha256")
        if not self.evaluation_epoch_id or not self.context_signature:
            raise ValueError("self-model must bind epoch and context")


@dataclass(frozen=True)
class MetricReceipt:
    metric_id: str
    metric_name: str
    definition_hash: str
    epoch_id: str
    value: float
    unit: str
    sample_n: int
    candidate_hash: str
    dataset_hash: str
    evaluator_hash: str
    resource_profile_hash: str
    authority: MetricAuthority
    sequence_index: int
    ci_low: float | None = None
    ci_high: float | None = None
    source_receipt_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.metric_id or not self.metric_name or not self.epoch_id or not self.unit:
            raise ValueError("metric receipt requires id/name/epoch/unit")
        if self.sample_n < 1 or self.sequence_index < 0:
            raise ValueError("sample_n must be positive and sequence_index non-negative")
        for value in (
            self.definition_hash,
            self.candidate_hash,
            self.dataset_hash,
            self.evaluator_hash,
            self.resource_profile_hash,
        ):
            if not _is_sha256(value):
                raise ValueError("metric lineage hashes must be sha256")
        if (self.ci_low is None) != (self.ci_high is None):
            raise ValueError("CI bounds must appear together")
        if self.ci_low is not None and self.ci_low > self.ci_high:
            raise ValueError("invalid CI")


@dataclass(frozen=True)
class MetricLedger:
    receipts: Tuple[MetricReceipt, ...]

    def __post_init__(self) -> None:
        ids = [r.metric_id for r in self.receipts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate metric receipt id")
        by_id: dict[str, MetricReceipt] = {}
        last_index = -1
        for receipt in self.receipts:
            if receipt.sequence_index <= last_index:
                raise ValueError("metric ledger sequence must be strictly increasing")
            for source_id in receipt.source_receipt_ids:
                source = by_id.get(source_id)
                if source is None:
                    raise ValueError("metric lineage may reference only earlier receipts")
                if source.sequence_index >= receipt.sequence_index:
                    raise ValueError("metric lineage must point backward")
                if receipt.authority is not MetricAuthority.DESCRIPTIVE and source.epoch_id != receipt.epoch_id:
                    raise ValueError("decision/evolution metric lineage may not silently cross evaluation epochs")
            by_id[receipt.metric_id] = receipt
            last_index = receipt.sequence_index

    def by_id(self) -> Mapping[str, MetricReceipt]:
        return {r.metric_id: r for r in self.receipts}


@dataclass(frozen=True)
class HardGateObservation:
    gate_id: str
    status: HardGateStatus
    metric_receipt_ids: Tuple[str, ...]
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.gate_id or not self.metric_receipt_ids:
            raise ValueError("hard gate requires id and protected metric receipt(s)")


@dataclass(frozen=True)
class DecisionComponent:
    name: str
    normalized_desirability: float
    uncertainty: float
    weight: float
    contribution: float
    normalization_definition_hash: str
    metric_receipt_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0.0 <= self.normalized_desirability <= 1.0:
            raise ValueError("normalized desirability must be in [0,1]")
        if self.uncertainty < 0:
            raise ValueError("uncertainty cannot be negative")
        if not _is_sha256(self.normalization_definition_hash):
            raise ValueError("normalization definition must be content identified")


@dataclass(frozen=True)
class MetaDecisionReceipt:
    decision_id: str
    self_model_hash: str
    evaluation_epoch_id: str
    candidate_actions: Tuple[str, ...]
    status: DecisionStatus
    selected_action: str | None
    components: Tuple[DecisionComponent, ...]
    total_expected_utility: float | None
    runner_up_action: str | None
    runner_up_utility: float | None
    hard_gate_observations: Tuple[HardGateObservation, ...]
    metric_receipt_ids: Tuple[str, ...]
    reasons: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.decision_id or not self.evaluation_epoch_id:
            raise ValueError("decision requires id and evaluation epoch")
        if self.selected_action is not None and self.selected_action not in self.candidate_actions:
            raise ValueError("selected action must be registered")
        if self.runner_up_action is not None and self.runner_up_action not in self.candidate_actions:
            raise ValueError("runner-up action must be registered")
        if self.status is DecisionStatus.SELECTED and self.selected_action is None:
            raise ValueError("SELECTED decision requires selected_action")
        if self.status is not DecisionStatus.SELECTED and self.selected_action is not None:
            raise ValueError("non-selected decision cannot carry selected_action")


@dataclass(frozen=True)
class EvolutionTrace:
    trace_id: str
    evaluation_epoch_id: str
    parent: GenomeSnapshot
    challenger: GenomeSnapshot
    triggering_episode_ids: Tuple[str, ...]
    root_cause_receipt_ids: Tuple[str, ...]
    changed_surfaces: Tuple[str, ...]
    prediction_metric_ids: Tuple[str, ...]
    development_metric_ids: Tuple[str, ...]
    assurance_metric_ids: Tuple[str, ...]
    attribution_metric_ids: Tuple[str, ...]
    decision_receipt_id: str
    tournament_decision: str
    archive_status: str
    final_incumbent_id: str
    rollback_variant_id: str
    metric_receipt_ids: Tuple[str, ...]

    @property
    def content_hash(self) -> str:
        return canonical_hash(asdict(self))
