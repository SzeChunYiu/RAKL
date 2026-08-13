"""RSHEA Phase 2 adapter tests — enforce the v2 invariants structurally.

These tests are the gate for everything downstream (P3 shadow controller ... P7):
if an adapter mis-tags authority, infers normalization, or fabricates lineage, a
test here fails before any later phase can build on the defect.
"""
from types import SimpleNamespace

import pytest

from rakl.evolution import EvolutionTrial
from rakl.evolution_metrics import normalize_for_control
from rakl.evolution_trace import (
    HardGateObservation,
    HardGateStatus,
    MetricAuthority,
    MetricLedger,
    MetricRegistry,
    SelfModelSnapshot,
)
from rakl.meta_controller import (
    ActionEstimate,
    ComponentEstimate,
    DecisionPolicy,
    choose_meta_action,
)
from rakl.observability_adapters import (
    attribution_packet_to_epoch,
    attribution_validity_artifacts,
    bounded_saturation_artifacts,
    build_evaluation_epoch,
    evolution_trial_to_projection,
    paired_lift_to_receipt,
    process_outcome_gate,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
    saturation_to_self_model,
    task_episode_to_receipts,
)

_S = "a" * 64  # sha256-shaped identity


def _epoch():
    return build_evaluation_epoch(
        rakl_canonical_metrics,
        benchmark_protocol_hash="bench-proto",
        evaluator_hash="eval",
        model_tool_harness_hash="mth",
        decision_policy_hash="dp",
        observatory_instrumentation_hash="oi",
    )


def _process_telemetry(outcome="SUCCESS", cost=2500.0):
    return SimpleNamespace(
        invocation_id="inv1", process_surface="search", task_id="t1",
        output_state_hash="o1", outcome=SimpleNamespace(value=outcome),
        cost=cost, cost_policy_id="cp1",
        residual_before=("r1", "r2", "r3"), residual_after=("r1",),
        retained_novelty=(), raw_residual_contraction=2,
    )


# --- authority non-interchangeability ----------------------------------------
def test_process_telemetry_authority_tags_match_v2_invariant():
    cost, contraction, outcome = process_telemetry_to_receipts(
        _process_telemetry(), _epoch(), rakl_canonical_metrics, sequence_base=0
    )
    assert cost.authority is MetricAuthority.CONTROL_INPUT
    assert contraction.authority is MetricAuthority.CONTROL_INPUT
    assert outcome.authority is MetricAuthority.HARD_PROTECTED


def test_paired_lift_is_evidence_not_consumable_as_control_input():
    epoch = _epoch()
    pl = SimpleNamespace(point_estimate=0.42, ci_lo=0.1, ci_hi=0.7, n=30)
    lift = paired_lift_to_receipt(
        pl, epoch, rakl_canonical_metrics, sequence_index=0,
        candidate_hash="c", dataset_hash="d", evaluator_hash="e",
        resource_profile_hash="r",
    )
    assert lift.authority is MetricAuthority.EVOLUTION_EVIDENCE
    assert lift.ci_low == 0.1 and lift.ci_high == 0.7 and lift.sample_n == 30
    # Feeding an evidence receipt as a controller control-input must be rejected.
    ledger = MetricLedger((lift,))
    action = ActionEstimate(
        "ACT",
        (ComponentEstimate("paired_lift_estimate", 0.9, 0.05, lift.definition_hash, (lift.metric_id,)),),
        (),
    )
    policy = DecisionPolicy("p", epoch.epoch_id, (("paired_lift_estimate", 1.0),))
    sm = SelfModelSnapshot(_S, _S, epoch.epoch_id, _S, ("ctx",))
    with pytest.raises(ValueError, match="CONTROL_INPUT"):
        choose_meta_action(decision_id="d", self_model=sm, actions=(action,),
                           policy=policy, metric_ledger=ledger, metric_registry=rakl_canonical_metrics)


def test_development_gain_is_evidence_and_trial_round_trips_into_valid_ledger():
    epoch = _epoch()
    trial = EvolutionTrial("parent-v1", "child-v1", "dev-bench", {"qoi_a": 0.5, "qoi_b": -0.2})
    proj = evolution_trial_to_projection(trial, epoch, rakl_canonical_metrics, sequence_base=0)
    gains = [r for r in proj.receipts if r.metric_name == "development_gain"]
    assert len(gains) == 1  # only the positive-delta qoi_a
    assert gains[0].authority is MetricAuthority.EVOLUTION_EVIDENCE
    ledger = MetricLedger(proj.receipts)  # validates backward lineage + unique ids
    assert len(ledger.receipts) == len(proj.receipts)
    assert proj.trace.tournament_decision == "EVIDENCE_PROJECTED_NO_TOURNAMENT"
    assert proj.trace.archive_status == "projected_not_promoted"
    assert proj.trace.final_incumbent_id == "parent-v1"


# --- hard gates executed not logged ------------------------------------------
def test_blocking_failures_force_fail_gate_regardless_of_gain_magnitude():
    epoch = _epoch()
    trial = EvolutionTrial("p", "c", "dev", {"qoi_a": 5.0}, blocking_failures=("bad",))
    proj = evolution_trial_to_projection(trial, epoch, rakl_canonical_metrics, sequence_base=0)
    gates = {g.gate_id: g for g in proj.hard_gates}
    assert gates["trial_validity_gate"].status is HardGateStatus.FAIL
    tv = next(r for r in proj.receipts if r.metric_name == "trial_validity")
    assert tv.value == 1.0


def test_unverified_precondition_blocks_via_unknown_gate():
    epoch = _epoch()
    trial = EvolutionTrial("p", "c", "dev", {"qoi_a": 1.0}, candidate_identity_verified=None)
    proj = evolution_trial_to_projection(trial, epoch, rakl_canonical_metrics, sequence_base=0)
    gates = {g.gate_id: g for g in proj.hard_gates}
    assert gates["candidate_identity_gate"].status is HardGateStatus.UNKNOWN


def test_process_outcome_gate_fails_on_failure():
    pt = _process_telemetry(outcome="FAILURE")
    cost, contraction, outcome = process_telemetry_to_receipts(
        pt, _epoch(), rakl_canonical_metrics, sequence_base=0)
    gate = process_outcome_gate(pt, process_outcome_receipt_id=outcome.metric_id)
    assert gate.status is HardGateStatus.FAIL


# --- frozen normalization ----------------------------------------------------
def test_operator_cost_normalization_uses_predeclared_bound_not_candidate_set():
    cost, _, _ = process_telemetry_to_receipts(
        _process_telemetry(cost=2500.0), _epoch(), rakl_canonical_metrics, sequence_base=0)
    definition = rakl_canonical_metrics.by_name()["operator_cost"]
    # 2500 of a [0, 10000] MINIMIZE bound -> desirability 0.75, frozen & versioned.
    assert normalize_for_control(cost.value, definition) == pytest.approx(0.75)


# --- append-only backward lineage -------------------------------------------
def test_ledger_rejects_non_backward_lineage_from_real_adapter_receipts():
    cost, contraction, outcome = process_telemetry_to_receipts(
        _process_telemetry(), _epoch(), rakl_canonical_metrics, sequence_base=0)
    MetricLedger((cost, contraction, outcome))  # valid: contraction@1 sources cost@0
    with pytest.raises(ValueError, match="earlier"):
        MetricLedger((contraction, cost))  # cost@0 appears after the receipt citing it


# --- epoch binding -----------------------------------------------------------
def test_every_adapter_receipt_binds_to_its_evaluation_epoch():
    epoch = _epoch()
    for r in process_telemetry_to_receipts(_process_telemetry(), epoch, rakl_canonical_metrics, sequence_base=0):
        assert r.epoch_id == epoch.epoch_id
    for r in task_episode_to_receipts(
        SimpleNamespace(episode_id="e", atom_id="a", context_hash="ctx",
                        fibre_snapshot_hash="f", cost=10.0, outcome=SimpleNamespace()),
        epoch, rakl_canonical_metrics, sequence_base=0):
        assert r.epoch_id == epoch.epoch_id
    for r in evolution_trial_to_projection(
        EvolutionTrial("p", "c", "d", {"q": 0.1}), epoch, rakl_canonical_metrics, sequence_base=0).receipts:
        assert r.epoch_id == epoch.epoch_id


# --- no absolute completeness ------------------------------------------------
def test_saturation_never_claims_absolute_completeness():
    epoch = _epoch()
    axis = SimpleNamespace(value="AX")
    report = SimpleNamespace(required_axes=(axis,), flat=lambda a: True,
                             bounded_saturated=True, grants_absolute_completeness=False)
    sm = saturation_to_self_model(report, genome_hash="g", episode_cutoff_hash="ec", epoch_id=epoch.epoch_id)
    assert all("absolute" not in sig for sig in sm.context_signature)
    receipt, gate = bounded_saturation_artifacts(
        report, epoch, rakl_canonical_metrics, sequence_index=0,
        candidate_hash="c", dataset_hash="d", evaluator_hash="e", resource_profile_hash="r")
    assert gate.status is HardGateStatus.PASS  # bounded saturation met ...
    assert "absolute_completeness=False" in gate.reason  # ... but never absolute


def test_attribution_validity_gate_fails_without_frozen_before_runs():
    packet = SimpleNamespace(
        benchmark_id="b1", rakl_protocol_hash="rph", evaluator_protocol_hash="eph",
        model_only_protocol_hash="moph", learned_state_hash="lsh", frozen_before_runs=False,
        model=SimpleNamespace())
    epoch = attribution_packet_to_epoch(packet, rakl_canonical_metrics,
                                        decision_policy_hash="dp", observatory_instrumentation_hash="oi")
    receipt, gate = attribution_validity_artifacts(packet, epoch, rakl_canonical_metrics, sequence_index=0)
    assert gate.status is HardGateStatus.FAIL
    assert receipt.authority is MetricAuthority.HARD_PROTECTED


def test_canonical_registry_is_frozen_and_self_consistent():
    assert rakl_canonical_metrics.registry_id == "rakl-canonical-v1"
    # registry_hash is stable and re-derivable from the versioned definitions
    again = MetricRegistry(rakl_canonical_metrics.registry_id, rakl_canonical_metrics.definitions)
    assert again.registry_hash == rakl_canonical_metrics.registry_hash
