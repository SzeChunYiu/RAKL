"""RSHEA Phase 7: runtime resumption - serialize/restore the controller epoch +
ledger across restarts, with content_hash tamper-evidence.

The self-hosting runtime is stateful: it carries a controller evaluation epoch
and the metric ledger the receipts were bound to. Across a restart that
resumption state must round-trip bit-for-bit AND be tamper-evident, so a restored
epoch+ledger that was corrupted (or silently drifted) is detected, not trusted.

This module is pure: it never mutates the archive, never licenses a promotion or
resume, and never reaches into ``self_hosting_runtime``'s mutation surface. It
only freezes epoch + ledger (+ optional controller decision receipt) into a JSON
envelope and rebuilds them. The authority boundary is unchanged on resumption:
promotion/resume authority stays with governance regardless of what is restored.

Each payload is sealed by the same ``canonical_hash(asdict(obj))`` the object uses
internally (so the epoch seal is exactly ``EvaluationEpoch.epoch_hash``). Restoring
recomputes each seal from the payload bytes and refuses on mismatch - the primary
tamper detector - then rebuilds the frozen dataclasses and cross-checks the
epoch's own ``epoch_hash`` so semantic integrity holds end to end, not just byte
integrity.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

from .evolution_trace import (
    DecisionComponent,
    DecisionStatus,
    EvaluationEpoch,
    HardGateObservation,
    HardGateStatus,
    MetaDecisionReceipt,
    MetricAuthority,
    MetricLedger,
    MetricReceipt,
    canonical_hash,
)

_SCHEMA_VERSION = "rakl-resumable-state-v1"


class ResumptionTamperError(ValueError):
    """A restored payload's recomputed content hash did not match its seal."""


@dataclass(frozen=True)
class ResumableStateEnvelope:
    """Frozen, self-describing carrier for serialized resumption state.

    Each payload is sealed by its own ``content_hash`` (the same
    ``canonical_hash(asdict(obj))`` the object uses internally). The envelope
    itself is sealed by ``content_hash`` over all its fields. Restoring
    recomputes each payload's hash from the payload and refuses on mismatch.
    """

    schema_version: str
    epoch_payload: str
    ledger_payload: str
    decision_receipt_payload: Optional[str]
    epoch_content_hash: str
    ledger_content_hash: str
    decision_receipt_content_hash: Optional[str]

    @property
    def content_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class RestoredState:
    """The faithfully rebuilt epoch + ledger (+ optional decision receipt)."""

    epoch: EvaluationEpoch
    ledger: MetricLedger
    decision_receipt: Optional[MetaDecisionReceipt]


# --- serialize ----------------------------------------------------------------
def serialize_resumable_state(
    *,
    epoch: EvaluationEpoch,
    ledger: MetricLedger,
    decision_receipt: Optional[MetaDecisionReceipt] = None,
) -> ResumableStateEnvelope:
    """Freeze epoch + ledger (+ optional decision receipt) into a sealed envelope.

    Pure: no mutation, no I/O. The seal of each component is
    ``canonical_hash(asdict(obj))`` - identical to what the object reports
    internally (e.g. ``epoch.epoch_hash``) - so a restored object that rebuilds
    faithfully hashes back to the same seal.
    """

    def _seal(obj: object) -> Tuple[str, str]:
        payload = json.dumps(asdict(obj), sort_keys=True, separators=(",", ":"))
        digest = canonical_hash(asdict(obj))
        return payload, digest

    epoch_payload, epoch_hash = _seal(epoch)
    ledger_payload, ledger_hash = _seal(ledger)
    if decision_receipt is not None:
        dr_payload, dr_hash = _seal(decision_receipt)
    else:
        dr_payload, dr_hash = None, None

    return ResumableStateEnvelope(
        schema_version=_SCHEMA_VERSION,
        epoch_payload=epoch_payload,
        ledger_payload=ledger_payload,
        decision_receipt_payload=dr_payload,
        epoch_content_hash=epoch_hash,
        ledger_content_hash=ledger_hash,
        decision_receipt_content_hash=dr_hash,
    )


# --- restore ------------------------------------------------------------------
def _verify_payload(payload: str, expected_hash: str, label: str) -> dict:
    """Parse a payload and refuse it unless it recomputes to its seal."""
    parsed = json.loads(payload)
    actual = canonical_hash(parsed)
    if actual != expected_hash:
        raise ResumptionTamperError(
            f"{label} content hash mismatch: expected {expected_hash}, got {actual}"
        )
    return parsed


def _restore_epoch(d: dict) -> EvaluationEpoch:
    return EvaluationEpoch(**d)  # all sha256 str fields


def _restore_metric_receipt(d: dict) -> MetricReceipt:
    return MetricReceipt(
        metric_id=d["metric_id"],
        metric_name=d["metric_name"],
        definition_hash=d["definition_hash"],
        epoch_id=d["epoch_id"],
        value=d["value"],
        unit=d["unit"],
        sample_n=d["sample_n"],
        candidate_hash=d["candidate_hash"],
        dataset_hash=d["dataset_hash"],
        evaluator_hash=d["evaluator_hash"],
        resource_profile_hash=d["resource_profile_hash"],
        authority=MetricAuthority(d["authority"]),
        sequence_index=d["sequence_index"],
        ci_low=d["ci_low"],
        ci_high=d["ci_high"],
        source_receipt_ids=tuple(d.get("source_receipt_ids") or ()),
    )


def _restore_ledger(d: dict) -> MetricLedger:
    return MetricLedger(receipts=tuple(_restore_metric_receipt(r) for r in d["receipts"]))


def _restore_decision_component(d: dict) -> DecisionComponent:
    return DecisionComponent(
        name=d["name"],
        normalized_desirability=d["normalized_desirability"],
        uncertainty=d["uncertainty"],
        weight=d["weight"],
        contribution=d["contribution"],
        normalization_definition_hash=d["normalization_definition_hash"],
        metric_receipt_ids=tuple(d.get("metric_receipt_ids") or ()),
    )


def _restore_hard_gate(d: dict) -> HardGateObservation:
    return HardGateObservation(
        gate_id=d["gate_id"],
        status=HardGateStatus(d["status"]),
        metric_receipt_ids=tuple(d.get("metric_receipt_ids") or ()),
        reason=d.get("reason", ""),
    )


def _restore_decision_receipt(d: dict) -> MetaDecisionReceipt:
    return MetaDecisionReceipt(
        decision_id=d["decision_id"],
        self_model_hash=d["self_model_hash"],
        evaluation_epoch_id=d["evaluation_epoch_id"],
        candidate_actions=tuple(d["candidate_actions"]),
        status=DecisionStatus(d["status"]),
        selected_action=d["selected_action"],
        components=tuple(_restore_decision_component(c) for c in d["components"]),
        total_expected_utility=d["total_expected_utility"],
        runner_up_action=d["runner_up_action"],
        runner_up_utility=d["runner_up_utility"],
        hard_gate_observations=tuple(_restore_hard_gate(g) for g in d["hard_gate_observations"]),
        metric_receipt_ids=tuple(d["metric_receipt_ids"]),
        reasons=tuple(d.get("reasons") or ()),
    )


def restore_resumable_state(envelope: ResumableStateEnvelope) -> RestoredState:
    """Rebuild epoch + ledger (+ optional decision receipt) from an envelope.

    Each payload is verified against its sealed ``content_hash`` before it is
    trusted; a mismatch raises ``ResumptionTamperError`` (tamper / corruption /
    drift detected). The rebuilt epoch is then cross-checked against its own
    ``epoch_hash`` so semantic integrity holds, not just byte integrity.
    """
    if envelope.schema_version != _SCHEMA_VERSION:
        raise ValueError(f"unsupported resumable state schema: {envelope.schema_version}")

    epoch_d = _verify_payload(envelope.epoch_payload, envelope.epoch_content_hash, "epoch")
    ledger_d = _verify_payload(envelope.ledger_payload, envelope.ledger_content_hash, "ledger")

    epoch = _restore_epoch(epoch_d)
    ledger = _restore_ledger(ledger_d)

    # Semantic cross-check: the rebuilt epoch hashes to the SAME digest it was
    # sealed with (canonical_hash(asdict(...)) is what EvaluationEpoch.epoch_hash
    # uses). Catches a lossy reconstruction that a byte-level check would miss.
    if epoch.epoch_hash != envelope.epoch_content_hash:
        raise ResumptionTamperError("restored epoch hash diverged from its seal")
    if canonical_hash(asdict(ledger)) != envelope.ledger_content_hash:
        raise ResumptionTamperError("restored ledger hash diverged from its seal")

    decision_receipt: Optional[MetaDecisionReceipt] = None
    if envelope.decision_receipt_payload is not None:
        if envelope.decision_receipt_content_hash is None:
            raise ResumptionTamperError("decision receipt payload present without a seal")
        dr_d = _verify_payload(
            envelope.decision_receipt_payload,
            envelope.decision_receipt_content_hash,
            "decision_receipt",
        )
        decision_receipt = _restore_decision_receipt(dr_d)
        if canonical_hash(asdict(decision_receipt)) != envelope.decision_receipt_content_hash:
            raise ResumptionTamperError("restored decision receipt hash diverged from its seal")

    return RestoredState(epoch=epoch, ledger=ledger, decision_receipt=decision_receipt)
