"""RSHEA Phase 7 runtime-resumption tests.

Proves epoch + ledger (+ optional controller decision receipt) round-trip
bit-for-bit through serialize/restore, that the epoch seal is exactly
``EvaluationEpoch.epoch_hash`` (the object's own internal hash), and that any
tampered / corrupted / drifted payload is detected and refused on restore.
"""
import dataclasses
import json
from types import SimpleNamespace

import pytest

from rakl.evolution_trace import (
    DecisionStatus,
    MetricAuthority,
    MetricLedger,
    SelfModelSnapshot,
    canonical_hash,
)
from rakl.meta_controller import DecisionPolicy
from rakl.observability_adapters import (
    build_evaluation_epoch,
    process_outcome_gate,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
)
from rakl.runtime_resumption import (
    ResumableStateEnvelope,
    ResumptionTamperError,
    RestoredState,
    restore_resumable_state,
    serialize_resumable_state,
)
from rakl.shadow_controller import shadow_decide

_S = "a" * 64


def _epoch():
    return build_evaluation_epoch(
        rakl_canonical_metrics,
        benchmark_protocol_hash="bench", evaluator_hash="eval",
        model_tool_harness_hash="mth", decision_policy_hash="dp",
        observatory_instrumentation_hash="oi",
    )


def _policy(epoch):
    return DecisionPolicy(
        "policy-1", epoch.epoch_id, (("operator_cost", 1.0), ("residual_contraction", 0.0))
    )


def _self_model(epoch):
    return SelfModelSnapshot(_S, _S, epoch.epoch_id, _S, ("ctx",))


def _telemetry(cost=2500.0, outcome="SUCCESS"):
    return SimpleNamespace(
        invocation_id="inv1", process_surface="search", task_id="t1",
        output_state_hash="o1", outcome=SimpleNamespace(value=outcome),
        cost=cost, cost_policy_id="cp1",
        residual_before=("r1", "r2", "r3"), residual_after=("r1",),
        retained_novelty=(), raw_residual_contraction=2,
    )


def _setup(outcome="SUCCESS", cost=2500.0):
    epoch = _epoch()
    cost_r, contraction, out = process_telemetry_to_receipts(
        _telemetry(cost=cost, outcome=outcome), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost_r, contraction, out))
    gates = (process_outcome_gate(_telemetry(cost=cost, outcome=outcome),
             process_outcome_receipt_id=out.metric_id),)
    decision = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                             policy=_policy(epoch), self_model=_self_model(epoch),
                             control_receipts=(cost_r, contraction), gates=gates,
                             decision_id="d-sel")
    return epoch, ledger, decision


def _tamper(payload: str) -> str:
    """Return a syntactically-valid JSON payload with one string value altered,
    so its content hash diverges from the original."""
    obj = json.loads(payload)

    def _append(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str):
                    node[k] = v + "__tampered__"
                    return True
                if _append(v):
                    return True
        elif isinstance(node, list):
            for i, v in enumerate(node):
                if isinstance(v, str):
                    node[i] = v + "__tampered__"
                    return True
                if _append(v):
                    return True
        return False

    assert _append(obj), "tamper fixture found no string to alter"
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


# --- round-trip fidelity ------------------------------------------------------
def test_epoch_and_ledger_round_trip_bit_for_bit():
    epoch, ledger, decision = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger,
                                         decision_receipt=decision.receipt)
    restored = restore_resumable_state(envelope)
    assert isinstance(restored, RestoredState)
    assert restored.epoch == epoch
    assert restored.ledger == ledger
    assert restored.decision_receipt == decision.receipt


def test_restored_enums_and_tuples_preserve_identity_and_type():
    epoch, ledger, decision = _setup()
    restored = restore_resumable_state(
        serialize_resumable_state(epoch=epoch, ledger=ledger, decision_receipt=decision.receipt))
    # enums rebuild as members, not bare strings
    assert all(isinstance(r.authority, MetricAuthority) for r in restored.ledger.receipts)
    assert restored.decision_receipt.status is DecisionStatus.SELECTED
    # tuples rebuild as tuples (asdict/json had made them lists)
    assert isinstance(restored.ledger.receipts[0].source_receipt_ids, tuple)
    assert isinstance(restored.decision_receipt.components, tuple)
    assert isinstance(restored.decision_receipt.hard_gate_observations, tuple)
    assert isinstance(restored.decision_receipt.candidate_actions, tuple)


def test_epoch_seal_is_exactly_the_epoch_own_hash():
    epoch, ledger, _ = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger)
    # The seal is canonical_hash(asdict(epoch)) == EvaluationEpoch.epoch_hash.
    assert envelope.epoch_content_hash == epoch.epoch_hash


# --- tamper detection ---------------------------------------------------------
@pytest.mark.parametrize("field", ["epoch_payload", "ledger_payload", "decision_receipt_payload"])
def test_tampered_payload_is_refused(field):
    epoch, ledger, decision = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger,
                                         decision_receipt=decision.receipt)
    original = getattr(envelope, field)
    bad = dataclasses.replace(envelope, **{field: _tamper(original)})
    with pytest.raises(ResumptionTamperError):
        restore_resumable_state(bad)


def test_payload_present_without_seal_is_refused():
    epoch, ledger, decision = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger,
                                         decision_receipt=decision.receipt)
    bad = dataclasses.replace(envelope, decision_receipt_content_hash=None)
    with pytest.raises(ResumptionTamperError):
        restore_resumable_state(bad)


def test_unknown_schema_version_is_refused():
    epoch, ledger, _ = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger)
    bad = dataclasses.replace(envelope, schema_version="rakl-resumable-state-UNKNOWN")
    with pytest.raises(ValueError, match="schema"):
        restore_resumable_state(bad)


# --- purity / frozen / deterministic -----------------------------------------
def test_serialize_is_pure_inputs_unchanged():
    epoch, ledger, _ = _setup()
    before_epoch = (epoch.epoch_id, epoch.epoch_hash)
    before_ledger_ids = tuple(r.metric_id for r in ledger.receipts)
    serialize_resumable_state(epoch=epoch, ledger=ledger)
    assert (epoch.epoch_id, epoch.epoch_hash) == before_epoch
    assert tuple(r.metric_id for r in ledger.receipts) == before_ledger_ids


def test_envelope_and_restore_are_deterministic():
    epoch, ledger, decision = _setup()
    e1 = serialize_resumable_state(epoch=epoch, ledger=ledger, decision_receipt=decision.receipt)
    e2 = serialize_resumable_state(epoch=epoch, ledger=ledger, decision_receipt=decision.receipt)
    assert e1 == e2
    assert e1.content_hash == e2.content_hash
    assert restore_resumable_state(e1) == restore_resumable_state(e2)


def test_envelope_is_frozen_and_tamper_evident_at_envelope_level():
    epoch, ledger, _ = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger)
    assert dataclasses.is_dataclass(envelope) and getattr(envelope, "__dataclass_params__").frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        envelope.schema_version = "tamper"
    # content_hash seals every field: altering any one diverges it.
    tampered = dataclasses.replace(envelope, epoch_payload=_tamper(envelope.epoch_payload))
    assert tampered.content_hash != envelope.content_hash


# --- optional decision receipt -----------------------------------------------
def test_round_trip_without_decision_receipt():
    epoch, ledger, _ = _setup()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger)
    assert envelope.decision_receipt_payload is None
    assert envelope.decision_receipt_content_hash is None
    restored = restore_resumable_state(envelope)
    assert restored.decision_receipt is None
    assert restored.epoch == epoch
    assert restored.ledger == ledger
