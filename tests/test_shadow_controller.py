"""RSHEA Phase 3 shadow-controller tests.

Proves the shadow is a pure, side-effect-free projection: it runs the frozen
controller, stamps a receipt acted_upon=False, and never mutates its inputs or
reaches the live runtime. Controller success in shadow mode is observation, not
action.
"""
from types import SimpleNamespace

import pytest

from rakl.evolution_trace import DecisionStatus, HardGateStatus
from rakl.meta_controller import ActionEstimate, ComponentEstimate, DecisionPolicy
from rakl.observability_adapters import (
    build_evaluation_epoch,
    process_outcome_gate,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
    task_episode_to_receipts,
)
from rakl.shadow_controller import (
    ShadowDecision,
    ShadowLedger,
    build_status_quo_action,
    shadow_decide,
)
from rakl.evolution_trace import MetricLedger, SelfModelSnapshot

_S = "a" * 64


def _epoch():
    return build_evaluation_epoch(
        rakl_canonical_metrics,
        benchmark_protocol_hash="bench", evaluator_hash="eval",
        model_tool_harness_hash="mth", decision_policy_hash="dp",
        observatory_instrumentation_hash="oi",
    )


def _policy(epoch, weights=(("operator_cost", 1.0), ("residual_contraction", 0.0))):
    return DecisionPolicy("policy-1", epoch.epoch_id, tuple(weights))


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


def _episode(cost=2600.0):
    return SimpleNamespace(episode_id="e1", atom_id="a1", context_hash="ctx",
                           fibre_snapshot_hash="f", cost=cost, outcome=SimpleNamespace())


def _clean_setup():
    epoch = _epoch()
    cost, contraction, outcome = process_telemetry_to_receipts(
        _telemetry(), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost, contraction, outcome))
    gates = (process_outcome_gate(_telemetry(), process_outcome_receipt_id=outcome.metric_id),)
    return epoch, ledger, (cost, contraction), gates


# --- purity / never acts -----------------------------------------------------
def test_shadow_decide_does_not_mutate_inputs():
    epoch, ledger, control, gates = _clean_setup()
    policy, sm = _policy(epoch), _self_model(epoch)
    before = (len(ledger.receipts), rakl_canonical_metrics.registry_hash,
              epoch.epoch_id, policy.policy_hash, sm.self_model_hash)
    shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                  policy=policy, self_model=sm, control_receipts=control,
                  gates=gates, decision_id="d1")
    after = (len(ledger.receipts), rakl_canonical_metrics.registry_hash,
             epoch.epoch_id, policy.policy_hash, sm.self_model_hash)
    assert before == after


def test_shadow_decision_is_never_acted_upon_and_has_no_runtime_dependency():
    import rakl.shadow_controller as sc
    epoch, ledger, control, gates = _clean_setup()
    decision = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                             policy=_policy(epoch), self_model=_self_model(epoch),
                             control_receipts=control, gates=gates, decision_id="d1")
    assert decision.acted_upon is False
    assert decision.shadow_note == "shadow_mode_no_action"
    # Structural: the module never imports the live runtime (prose may mention it).
    assert not hasattr(sc, "self_hosting_runtime")
    import pathlib
    text = pathlib.Path(sc.__file__).read_text()
    import_lines = [ln for ln in text.splitlines() if ln.strip().startswith(("import ", "from "))]
    assert not any("runtime" in ln.lower() for ln in import_lines)


def test_shadow_decide_is_deterministic_for_identical_inputs():
    epoch, ledger, control, gates = _clean_setup()
    kw = dict(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
              policy=_policy(epoch), self_model=_self_model(epoch),
              control_receipts=control, gates=gates, decision_id="d1")
    d1 = shadow_decide(**kw)
    d2 = shadow_decide(**kw)
    assert d1 == d2  # frozen dataclass equality
    assert d1.input_content_hash == d2.input_content_hash


# --- controller outcomes surfaced through the shadow -------------------------
def test_shadow_selects_status_quo_on_clean_telemetry():
    epoch, ledger, control, gates = _clean_setup()
    decision = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                             policy=_policy(epoch), self_model=_self_model(epoch),
                             control_receipts=control, gates=gates, decision_id="d1")
    assert decision.receipt.status is DecisionStatus.SELECTED
    assert decision.receipt.selected_action == "status_quo"


def test_shadow_blocks_when_process_outcome_gate_fails():
    epoch = _epoch()
    cost, contraction, outcome = process_telemetry_to_receipts(
        _telemetry(outcome="FAILURE"), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost, contraction, outcome))
    gates = (process_outcome_gate(_telemetry(outcome="FAILURE"),
             process_outcome_receipt_id=outcome.metric_id),)
    decision = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                             policy=_policy(epoch), self_model=_self_model(epoch),
                             control_receipts=(cost, contraction), gates=gates, decision_id="d1")
    assert decision.receipt.status is DecisionStatus.BLOCKED
    assert decision.receipt.selected_action is None
    assert any("hard_gate_not_pass" in r for r in decision.receipt.reasons)


def test_shadow_abstains_when_alternative_is_within_utility_margin():
    epoch = _epoch()
    pt_cost, pt_cont, pt_out = process_telemetry_to_receipts(
        _telemetry(cost=2500.0), epoch, rakl_canonical_metrics, sequence_base=0)  # cost desirability 0.75
    (ep_cost,) = task_episode_to_receipts(_episode(cost=2600.0), epoch, rakl_canonical_metrics, sequence_base=3)  # -> 0.74
    ledger = MetricLedger((pt_cost, pt_cont, pt_out, ep_cost))
    gates = (process_outcome_gate(_telemetry(), process_outcome_receipt_id=pt_out.metric_id),)
    op_def_hash = rakl_canonical_metrics.by_name()["operator_cost"].definition_hash
    alt = ActionEstimate("alternative", (ComponentEstimate("operator_cost", 0.74, 0.0, op_def_hash, (ep_cost.metric_id,)),), ())
    decision = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                             policy=_policy(epoch), self_model=_self_model(epoch),
                             control_receipts=(pt_cost, pt_cont), gates=gates,
                             decision_id="d1", extra_actions=(alt,))
    assert decision.receipt.status is DecisionStatus.ABSTAIN
    assert decision.receipt.selected_action is None
    assert decision.receipt.runner_up_action == "alternative"


# --- authority boundary: evidence cannot enter a control decision -------------
def test_shadow_rejects_evidence_receipt_as_control_input():
    from rakl.observability_adapters import paired_lift_to_receipt
    epoch = _epoch()
    pl = SimpleNamespace(point_estimate=0.42, ci_lo=0.1, ci_hi=0.7, n=30)
    evidence = paired_lift_to_receipt(pl, epoch, rakl_canonical_metrics, sequence_index=0,
                                      candidate_hash="c", dataset_hash="d",
                                      evaluator_hash="e", resource_profile_hash="r")
    ledger = MetricLedger((evidence,))
    with pytest.raises(ValueError, match="CONTROL_INPUT"):
        shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                      policy=_policy(epoch), self_model=_self_model(epoch),
                      control_receipts=(evidence,), gates=(), decision_id="d1")


# --- append-only ledger ------------------------------------------------------
def test_shadow_ledger_is_append_only_and_original_unchanged():
    epoch, ledger, control, gates = _clean_setup()
    d1 = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                       policy=_policy(epoch), self_model=_self_model(epoch),
                       control_receipts=control, gates=gates, decision_id="d1")
    d2 = shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                       policy=_policy(epoch), self_model=_self_model(epoch),
                       control_receipts=control, gates=gates, decision_id="d2")
    empty = ShadowLedger()
    one = empty.record(d1)
    two = one.record(d2)
    assert empty.decisions == ()
    assert len(one.decisions) == 1 and one.decisions[0] is d1
    assert len(two.decisions) == 2
    assert empty.content_hash != one.content_hash != two.content_hash
