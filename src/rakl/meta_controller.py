from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple

from .evolution_trace import (
    DecisionComponent,
    DecisionStatus,
    HardGateObservation,
    HardGateStatus,
    MetaDecisionReceipt,
    MetricAuthority,
    MetricLedger,
    MetricRegistry,
    SelfModelSnapshot,
    canonical_hash,
)


@dataclass(frozen=True)
class ComponentEstimate:
    name: str
    normalized_desirability: float
    uncertainty: float
    normalization_definition_hash: str
    metric_receipt_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name or not 0.0 <= self.normalized_desirability <= 1.0:
            raise ValueError("component requires name and normalized desirability in [0,1]")
        if self.uncertainty < 0:
            raise ValueError("component uncertainty cannot be negative")


@dataclass(frozen=True)
class ActionEstimate:
    action: str
    components: Tuple[ComponentEstimate, ...]
    hard_gates: Tuple[HardGateObservation, ...]

    def __post_init__(self) -> None:
        if not self.action or not self.components:
            raise ValueError("action estimate requires action and components")
        names = [c.name for c in self.components]
        if len(names) != len(set(names)):
            raise ValueError("action component names must be unique")


@dataclass(frozen=True)
class DecisionPolicy:
    policy_id: str
    evaluation_epoch_id: str
    weights: Tuple[Tuple[str, float], ...]
    uncertainty_penalty: float = 1.0
    max_component_uncertainty: float = 0.35
    minimum_utility_margin: float = 0.02

    def __post_init__(self) -> None:
        if not self.policy_id or not self.evaluation_epoch_id:
            raise ValueError("decision policy requires id and evaluation epoch")
        names = [name for name, _ in self.weights]
        if len(names) != len(set(names)) or any(w < 0 for _, w in self.weights):
            raise ValueError("decision policy weights must be unique and non-negative")
        if self.uncertainty_penalty < 0 or self.max_component_uncertainty < 0 or self.minimum_utility_margin < 0:
            raise ValueError("decision policy thresholds cannot be negative")

    @property
    def policy_hash(self) -> str:
        return canonical_hash({
            "policy_id": self.policy_id,
            "evaluation_epoch_id": self.evaluation_epoch_id,
            "weights": self.weights,
            "uncertainty_penalty": self.uncertainty_penalty,
            "max_component_uncertainty": self.max_component_uncertainty,
            "minimum_utility_margin": self.minimum_utility_margin,
        })


def _validate_receipt_boundary(
    action: ActionEstimate,
    ledger: MetricLedger,
    registry: MetricRegistry,
    *,
    epoch_id: str,
) -> None:
    by_id = ledger.by_id()
    for component in action.components:
        for receipt_id in component.metric_receipt_ids:
            receipt = by_id.get(receipt_id)
            if receipt is None:
                raise ValueError(f"unknown control metric receipt: {receipt_id}")
            registry.validate_receipt(receipt)
            if receipt.authority is not MetricAuthority.CONTROL_INPUT:
                raise ValueError("utility may consume CONTROL_INPUT receipts only")
            if receipt.epoch_id != epoch_id:
                raise ValueError("control metric receipt belongs to a different evaluation epoch")
    for gate in action.hard_gates:
        for receipt_id in gate.metric_receipt_ids:
            receipt = by_id.get(receipt_id)
            if receipt is None:
                raise ValueError(f"unknown hard-gate metric receipt: {receipt_id}")
            registry.validate_receipt(receipt)
            if receipt.authority is not MetricAuthority.HARD_PROTECTED:
                raise ValueError("hard gates require HARD_PROTECTED metric receipts")
            if receipt.epoch_id != epoch_id:
                raise ValueError("hard-gate receipt belongs to a different evaluation epoch")


def action_utility(action: ActionEstimate, policy: DecisionPolicy) -> tuple[float, Tuple[DecisionComponent, ...]]:
    weights = dict(policy.weights)
    unknown = set(c.name for c in action.components) - set(weights)
    if unknown:
        raise ValueError("missing frozen weight for component(s): " + ",".join(sorted(unknown)))
    components = tuple(
        DecisionComponent(
            name=c.name,
            normalized_desirability=c.normalized_desirability,
            uncertainty=c.uncertainty,
            weight=weights[c.name],
            contribution=weights[c.name] * (c.normalized_desirability - policy.uncertainty_penalty * c.uncertainty),
            normalization_definition_hash=c.normalization_definition_hash,
            metric_receipt_ids=c.metric_receipt_ids,
        )
        for c in action.components
    )
    return sum(c.contribution for c in components), components


def choose_meta_action(
    *,
    decision_id: str,
    self_model: SelfModelSnapshot,
    actions: Sequence[ActionEstimate],
    policy: DecisionPolicy,
    metric_ledger: MetricLedger,
    metric_registry: MetricRegistry,
) -> MetaDecisionReceipt:
    if not actions:
        raise ValueError("at least one action required")
    if self_model.evaluation_epoch_id != policy.evaluation_epoch_id:
        raise ValueError("self-model and decision policy belong to different evaluation epochs")

    eligible: list[ActionEstimate] = []
    all_gate_observations: list[HardGateObservation] = []
    all_metric_ids: list[str] = []
    blocked_reasons: list[str] = []

    for action in actions:
        _validate_receipt_boundary(action, metric_ledger, metric_registry, epoch_id=policy.evaluation_epoch_id)
        all_gate_observations.extend(action.hard_gates)
        all_metric_ids.extend(mid for c in action.components for mid in c.metric_receipt_ids)
        all_metric_ids.extend(mid for g in action.hard_gates for mid in g.metric_receipt_ids)
        failing = tuple(g for g in action.hard_gates if g.status is not HardGateStatus.PASS)
        if failing:
            blocked_reasons.append(
                f"{action.action}:hard_gate_not_pass:" + ",".join(f"{g.gate_id}={g.status.value}" for g in failing)
            )
            continue
        if any(c.uncertainty > policy.max_component_uncertainty for c in action.components):
            blocked_reasons.append(f"{action.action}:component_uncertainty_above_policy_limit")
            continue
        eligible.append(action)

    if not eligible:
        return MetaDecisionReceipt(
            decision_id=decision_id,
            self_model_hash=self_model.self_model_hash,
            evaluation_epoch_id=policy.evaluation_epoch_id,
            candidate_actions=tuple(a.action for a in actions),
            status=DecisionStatus.BLOCKED,
            selected_action=None,
            components=(),
            total_expected_utility=None,
            runner_up_action=None,
            runner_up_utility=None,
            hard_gate_observations=tuple(all_gate_observations),
            metric_receipt_ids=tuple(dict.fromkeys(all_metric_ids)),
            reasons=tuple(blocked_reasons) or ("no_eligible_action",),
        )

    scored = sorted(
        ((action_utility(action, policy)[0], action) for action in eligible),
        key=lambda x: (x[0], x[1].action),
        reverse=True,
    )
    top_u, top = scored[0]
    _, components = action_utility(top, policy)
    runner = scored[1] if len(scored) > 1 else None
    if runner is not None and top_u - runner[0] < policy.minimum_utility_margin:
        return MetaDecisionReceipt(
            decision_id=decision_id,
            self_model_hash=self_model.self_model_hash,
            evaluation_epoch_id=policy.evaluation_epoch_id,
            candidate_actions=tuple(a.action for a in actions),
            status=DecisionStatus.ABSTAIN,
            selected_action=None,
            components=components,
            total_expected_utility=top_u,
            runner_up_action=runner[1].action,
            runner_up_utility=runner[0],
            hard_gate_observations=tuple(all_gate_observations),
            metric_receipt_ids=tuple(dict.fromkeys(all_metric_ids)),
            reasons=("top_action_margin_below_frozen_policy_threshold",),
        )

    return MetaDecisionReceipt(
        decision_id=decision_id,
        self_model_hash=self_model.self_model_hash,
        evaluation_epoch_id=policy.evaluation_epoch_id,
        candidate_actions=tuple(a.action for a in actions),
        status=DecisionStatus.SELECTED,
        selected_action=top.action,
        components=components,
        total_expected_utility=top_u,
        runner_up_action=None if runner is None else runner[1].action,
        runner_up_utility=None if runner is None else runner[0],
        hard_gate_observations=tuple(all_gate_observations),
        metric_receipt_ids=tuple(dict.fromkeys(all_metric_ids)),
        reasons=("selected_under_frozen_policy_after_hard_gate_and_uncertainty_checks",),
    )
