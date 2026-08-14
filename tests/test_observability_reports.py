"""RSHEA Phase 6 observability-report tests.

Proves the report is a pure, frozen, tamper-evident, non-actionable projection
of the RSHEA artifacts: it observes the epoch's decision/gates/trace and the
control-vs-evidence authority split WITHOUT itself feeding back into control.
"""
import dataclasses
import pathlib
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from rakl.evolution import EvolutionTrial
from rakl.evolution_trace import (
    EvolutionTrace,
    MetricLedger,
    SelfModelSnapshot,
    canonical_hash,
)
from rakl.meta_controller import DecisionPolicy
from rakl.observability_adapters import (
    build_evaluation_epoch,
    evolution_trial_to_projection,
    paired_lift_to_receipt,
    process_outcome_gate,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
)
from rakl.observability_reports import ObservabilityReport, build_observability_report
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


def _clean_setup(cost=2500.0):
    epoch = _epoch()
    cost_r, contraction, outcome = process_telemetry_to_receipts(
        _telemetry(cost=cost), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost_r, contraction, outcome))
    gates = (process_outcome_gate(_telemetry(cost=cost), process_outcome_receipt_id=outcome.metric_id),)
    return epoch, ledger, (cost_r, contraction), gates


def _receipt_for(epoch, ledger, control, gates, decision_id="d1"):
    return shadow_decide(
        epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
        policy=_policy(epoch), self_model=_self_model(epoch),
        control_receipts=control, gates=gates, decision_id=decision_id,
    ).receipt


# --- purity / frozen / non-actionable ----------------------------------------
def test_report_does_not_mutate_inputs():
    epoch, ledger, control, gates = _clean_setup()
    receipt = _receipt_for(epoch, ledger, control, gates)
    before = (len(ledger.receipts), epoch.epoch_id, receipt.decision_id, receipt.status)
    build_observability_report(epoch=epoch, ledger=ledger, decision_receipt=receipt)
    after = (len(ledger.receipts), epoch.epoch_id, receipt.decision_id, receipt.status)
    assert before == after


def test_report_is_frozen_non_actionable_and_pure():
    import rakl.observability_reports as orm
    epoch, ledger, control, gates = _clean_setup()
    receipt = _receipt_for(epoch, ledger, control, gates)
    report = build_observability_report(epoch=epoch, ledger=ledger, decision_receipt=receipt)
    assert dataclasses.is_dataclass(report) and getattr(report, "__dataclass_params__").frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.decision_status = "TAMPER"
    assert report.is_actable is False
    assert report.schema_version == "rakl-observability-report-v1"
    # The module never imports the live runtime (prose may mention it).
    text = pathlib.Path(orm.__file__).read_text()
    import_lines = [ln for ln in text.splitlines() if ln.strip().startswith(("import ", "from "))]
    assert not any("runtime" in ln.lower() for ln in import_lines)


# --- deterministic + tamper-evident ------------------------------------------
def test_report_content_hash_is_deterministic_and_rederivable():
    epoch, ledger, control, gates = _clean_setup()
    receipt = _receipt_for(epoch, ledger, control, gates)
    r1 = build_observability_report(epoch=epoch, ledger=ledger, decision_receipt=receipt)
    r2 = build_observability_report(epoch=epoch, ledger=ledger, decision_receipt=receipt)
    assert r1 == r2
    assert r1.content_hash == r2.content_hash
    assert r1.source_content_hash == r2.source_content_hash
    # content_hash is literally the canonical hash of the report's own fields.
    assert canonical_hash(asdict(r1)) == r1.content_hash


def test_report_is_tamper_evident_across_different_sources():
    epoch = _epoch()
    # Variant A: cost 2500 (operator_cost desirability 0.75).
    eA, ledA, ctrlA, gatesA = _clean_setup(cost=2500.0)
    recA = _receipt_for(eA, ledA, ctrlA, gatesA)
    rA = build_observability_report(epoch=eA, ledger=ledA, decision_receipt=recA)
    # Variant B: cost 2600 (operator_cost desirability 0.74) -> different control receipt.
    eB, ledB, ctrlB, gatesB = _clean_setup(cost=2600.0)
    recB = _receipt_for(eB, ledB, ctrlB, gatesB)
    rB = build_observability_report(epoch=eB, ledger=ledB, decision_receipt=recB)
    assert rA.source_content_hash != rB.source_content_hash
    assert rA.content_hash != rB.content_hash


# --- decision + gate projection ----------------------------------------------
def test_report_projects_decision_status_and_selected_action():
    epoch, ledger, control, gates = _clean_setup()
    receipt = _receipt_for(epoch, ledger, control, gates)
    report = build_observability_report(epoch=epoch, ledger=ledger, decision_receipt=receipt)
    assert report.decision_status == "SELECTED"
    assert report.selected_action == "status_quo"
    assert report.decision_id == "d1"
    assert "status_quo" in report.candidate_actions
    assert any(c[0] == "operator_cost" for c in report.decision_component_summary)


def test_report_projects_failed_hard_gates():
    epoch = _epoch()
    cost, contraction, outcome = process_telemetry_to_receipts(
        _telemetry(outcome="FAILURE"), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost, contraction, outcome))
    gates = (process_outcome_gate(_telemetry(outcome="FAILURE"),
             process_outcome_receipt_id=outcome.metric_id),)
    receipt = shadow_decide(
        epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
        policy=_policy(epoch), self_model=_self_model(epoch),
        control_receipts=(cost, contraction), gates=gates, decision_id="d1").receipt
    report = build_observability_report(epoch=epoch, ledger=ledger, decision_receipt=receipt)
    assert report.decision_status == "BLOCKED"
    assert report.failed_gate_ids  # at least one failed gate surfaced
    assert any(status == "FAIL" for _gid, status in report.hard_gate_summary)


# --- authority separation projection -----------------------------------------
def test_report_authority_tally_keeps_control_and_evidence_separate():
    epoch, ledger, control, gates = _clean_setup()
    # Add an EVOLUTION_EVIDENCE receipt (paired lift) to the same ledger.
    evidence = paired_lift_to_receipt(
        SimpleNamespace(point_estimate=0.42, ci_lo=0.1, ci_hi=0.7, n=30),
        epoch, rakl_canonical_metrics, sequence_index=3,
        candidate_hash=_S, dataset_hash=_S, evaluator_hash=_S, resource_profile_hash=_S)
    mixed = MetricLedger(ledger.receipts + (evidence,))
    report = build_observability_report(epoch=epoch, ledger=mixed)
    # Control inputs (operator_cost, residual_contraction) and the protected
    # process_outcome present; the paired-lift evidence counted separately.
    assert report.control_input_count == 2
    assert report.evolution_evidence_count == 1
    assert report.hard_protected_count == 1
    total = report.control_input_count + report.evolution_evidence_count + report.hard_protected_count + report.descriptive_count
    assert total == len(mixed.receipts)


# --- evolution trace projection ----------------------------------------------
def test_report_projects_evolution_trace_fields():
    epoch, ledger, _control, _gates = _clean_setup()
    proj = evolution_trial_to_projection(
        EvolutionTrial("parent-v1", "child-v1", "dev-bench", {"qoi_a": 0.5, "qoi_b": -0.2}),
        epoch, rakl_canonical_metrics, sequence_base=4)
    trace = proj.trace
    assert isinstance(trace, EvolutionTrace)
    report = build_observability_report(
        epoch=epoch, ledger=ledger, evolution_trace=trace)
    assert report.tournament_decision == trace.tournament_decision
    assert report.archive_status == trace.archive_status
    assert report.final_incumbent_id == trace.final_incumbent_id
    assert report.changed_surfaces == trace.changed_surfaces
    assert report.trace_metric_receipt_count == len(trace.metric_receipt_ids)


# --- epoch binding -----------------------------------------------------------
def test_report_enforces_epoch_binding():
    epoch_a, ledger_a, control_a, gates_a = _clean_setup()
    receipt = _receipt_for(epoch_a, ledger_a, control_a, gates_a)
    # A different epoch (different instrumentation hash).
    epoch_b = build_evaluation_epoch(
        rakl_canonical_metrics, benchmark_protocol_hash="bench", evaluator_hash="eval",
        model_tool_harness_hash="mth", decision_policy_hash="dp",
        observatory_instrumentation_hash="DIFFERENT")
    assert epoch_b.epoch_id != epoch_a.epoch_id
    with pytest.raises(ValueError, match="epoch"):
        build_observability_report(epoch=epoch_b, ledger=ledger_a, decision_receipt=receipt)


# --- graceful absence of decision / trace ------------------------------------
def test_report_without_decision_or_trace_is_still_valid_and_bound():
    epoch, ledger, _control, _gates = _clean_setup()
    report = build_observability_report(epoch=epoch, ledger=ledger)
    assert report.decision_status is None and report.selected_action is None
    assert report.decision_component_summary == () and report.failed_gate_ids == ()
    assert report.tournament_decision is None and report.final_incumbent_id is None
    assert report.trace_metric_receipt_count == 0
    # Epoch binding, authority tally, and seals are still present and stable.
    assert report.evaluation_epoch_id == epoch.epoch_id
    assert report.control_input_count == 2  # operator_cost + residual_contraction
    assert report.is_actable is False
    assert report.source_content_hash and report.content_hash
    again = build_observability_report(epoch=epoch, ledger=ledger)
    assert again.content_hash == report.content_hash
