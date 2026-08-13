"""RSHEA Phase 3: shadow-mode meta-controller.

Runs the frozen meta-controller (``choose_meta_action``) over P2-adapted
observability and records the resulting ``MetaDecisionReceipt`` WITHOUT acting.

Shadow mode is a pure projection. Given an ``EvaluationEpoch``, a ``MetricLedger``
of P2-adapted receipts, the ``HARD_PROTECTED`` gates the adapters produced, and
the operator's frozen ``DecisionPolicy``, the shadow:

* builds a single honest ``status_quo`` ``ActionEstimate`` from the
  ``CONTROL_INPUT`` receipts (operator cost, residual contraction) and the hard
  gates — and ONLY those, respecting the authority boundary the controller
  itself enforces;
* runs ``choose_meta_action``, which returns whether status_quo (and any
  proposed alternatives) is SELECTED, ABSTAINED, or BLOCKED under the frozen
  policy;
* stamps the receipt into a ``ShadowDecision`` (``acted_upon=False``) and, if
  asked, appends it to an append-only ``ShadowLedger``.

It never mutates the ledger, registry, epoch, policy, or self-model; it never
imports or calls the live ``self_hosting_runtime``. Controller success in shadow
mode is NOT promotion and NOT action: P4/P5 are the only place a SELECTED
decision may, with governance, become action. The v2 invariant holds throughout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .evolution_metrics import normalize_for_control
from .evolution_trace import (
    EvaluationEpoch,
    HardGateObservation,
    MetaDecisionReceipt,
    MetricAuthority,
    MetricLedger,
    MetricReceipt,
    MetricRegistry,
    SelfModelSnapshot,
    canonical_hash,
)
from .meta_controller import (
    ActionEstimate,
    ComponentEstimate,
    DecisionPolicy,
    choose_meta_action,
)


def _component_for_receipt(
    receipt: MetricReceipt, registry: MetricRegistry
) -> ComponentEstimate:
    """Frozen-normalize one CONTROL_INPUT receipt into a controller component.

    Desirability comes from the versioned MetricDefinition bounds (never the
    candidate set). Uncertainty is half the CI width when a CI is present, else
    zero — a measured control input carries no speculative uncertainty.
    """
    definition = registry.by_name()[receipt.metric_name]
    desirability = normalize_for_control(receipt.value, definition)
    if receipt.ci_low is not None and receipt.ci_high is not None:
        uncertainty = max(0.0, (receipt.ci_high - receipt.ci_low) / 2.0)
    else:
        uncertainty = 0.0
    return ComponentEstimate(
        name=receipt.metric_name,
        normalized_desirability=desirability,
        uncertainty=uncertainty,
        normalization_definition_hash=definition.definition_hash,
        metric_receipt_ids=(receipt.metric_id,),
    )


def build_status_quo_action(
    control_receipts: Tuple[MetricReceipt, ...],
    gates: Tuple[HardGateObservation, ...],
    registry: MetricRegistry,
    *,
    action_name: str = "status_quo",
) -> ActionEstimate:
    """Build the single honest status-quo action from CONTROL_INPUT receipts + gates.

    Only CONTROL_INPUT receipts become utility components; only HARD_PROTECTED
    receipts back hard gates. Evidence receipts are deliberately excluded — the
    controller could not consume them anyway, and the shadow must not smuggle
    governance evidence into a control decision. (If an evidence receipt is
    passed here, ``choose_meta_action`` rejects it at its own authority boundary.)
    """
    if not control_receipts:
        raise ValueError("status-quo action requires at least one CONTROL_INPUT receipt")
    for r in control_receipts:
        if r.authority is not MetricAuthority.CONTROL_INPUT:
            raise ValueError(
                f"status-quo component must be CONTROL_INPUT, got {r.authority} ({r.metric_name})"
            )
    components = tuple(_component_for_receipt(r, registry) for r in control_receipts)
    return ActionEstimate(action_name, components, tuple(gates))


@dataclass(frozen=True)
class ShadowDecision:
    """A controller receipt observed in shadow mode — recorded, never acted on."""

    receipt: MetaDecisionReceipt
    input_content_hash: str
    acted_upon: bool = False
    shadow_note: str = "shadow_mode_no_action"


def shadow_decide(
    *,
    epoch: EvaluationEpoch,
    ledger: MetricLedger,
    registry: MetricRegistry,
    policy: DecisionPolicy,
    self_model: SelfModelSnapshot,
    control_receipts: Tuple[MetricReceipt, ...],
    gates: Tuple[HardGateObservation, ...],
    decision_id: str,
    action_name: str = "status_quo",
    extra_actions: Tuple[ActionEstimate, ...] = (),
) -> ShadowDecision:
    """Run the frozen controller over P2 telemetry and stamp the receipt WITHOUT acting.

    Pure: no mutation, no I/O, no runtime call. The returned ``ShadowDecision``
    is ``acted_upon=False`` by construction and carries a content hash of its
    inputs for tamper-evident provenance. ``extra_actions`` lets the shadow
    compare status-quo against proposed alternatives (so the ABSTAIN margin path
    is observable) without ever executing any of them.
    """
    if epoch.epoch_id != policy.evaluation_epoch_id:
        raise ValueError("shadow decide requires epoch and policy to share an evaluation epoch")
    if self_model.evaluation_epoch_id != policy.evaluation_epoch_id:
        raise ValueError("shadow decide requires self-model and policy to share an evaluation epoch")
    status_quo = build_status_quo_action(control_receipts, gates, registry, action_name=action_name)
    actions: Tuple[ActionEstimate, ...] = (status_quo,) + tuple(extra_actions)
    receipt = choose_meta_action(
        decision_id=decision_id,
        self_model=self_model,
        actions=actions,
        policy=policy,
        metric_ledger=ledger,
        metric_registry=registry,
    )
    input_content_hash = canonical_hash((
        epoch.epoch_id,
        registry.registry_hash,
        tuple(r.metric_id for r in ledger.receipts),
        policy.policy_hash,
        self_model.self_model_hash,
        tuple(a.action for a in actions),
    ))
    return ShadowDecision(receipt=receipt, input_content_hash=input_content_hash)


@dataclass(frozen=True)
class ShadowLedger:
    """Append-only log of shadow decisions (records receipts, never feeds them back)."""

    decisions: Tuple[ShadowDecision, ...] = ()

    def record(self, decision: ShadowDecision) -> "ShadowLedger":
        """Return a NEW ledger with ``decision`` appended (append-only, frozen)."""
        return ShadowLedger(self.decisions + (decision,))

    @property
    def content_hash(self) -> str:
        return canonical_hash(
            tuple((d.input_content_hash, d.receipt.decision_id, d.receipt.status.name) for d in self.decisions)
        )
