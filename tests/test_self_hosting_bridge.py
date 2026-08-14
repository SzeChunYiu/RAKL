"""RSHEA Phase 4 self-hosting bridge tests.

Proves the bridge is the single, authority-safe seam between the controller and
the runtime: it carries a frozen controller receipt into the runtime decision
space WITHOUT ever granting promotion/resume authority. Promotion authority stays
with governance (assess_resume_readiness); the bridge only interprets.
"""
import dataclasses
import pathlib
from types import SimpleNamespace

import pytest

from rakl.evolution_trace import MetricLedger, SelfModelSnapshot
from rakl.meta_controller import ActionEstimate, ComponentEstimate, DecisionPolicy
from rakl.observability_adapters import (
    build_evaluation_epoch,
    process_outcome_gate,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
)
from rakl.self_hosting_bridge import (
    ControllerBridgeVerdict,
    annotate_resume_with_controller,
    interpret_controller_for_runtime,
)
from rakl.self_hosting_runtime import EscalationAssessment, SelfHostingDecision
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


def _clean_setup(outcome="SUCCESS", cost=2500.0):
    epoch = _epoch()
    cost_r, contraction, out = process_telemetry_to_receipts(
        _telemetry(cost=cost, outcome=outcome), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost_r, contraction, out))
    gates = (process_outcome_gate(_telemetry(cost=cost, outcome=outcome),
             process_outcome_receipt_id=out.metric_id),)
    return epoch, ledger, (cost_r, contraction), gates


def _selected_decision():
    epoch, ledger, control, gates = _clean_setup()
    return shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                         policy=_policy(epoch), self_model=_self_model(epoch),
                         control_receipts=control, gates=gates, decision_id="d-sel")


def _blocked_decision():
    epoch, ledger, control, gates = _clean_setup(outcome="FAILURE")
    return shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                         policy=_policy(epoch), self_model=_self_model(epoch),
                         control_receipts=control, gates=gates, decision_id="d-blk")


def _abstain_decision():
    epoch, ledger, control, gates = _clean_setup()
    cost_r = control[0]
    op_def_hash = rakl_canonical_metrics.by_name()["operator_cost"].definition_hash
    alt = ActionEstimate("alternative",
                         (ComponentEstimate("operator_cost", 0.74, 0.0, op_def_hash, (cost_r.metric_id,)),), ())
    return shadow_decide(epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
                         policy=_policy(epoch), self_model=_self_model(epoch),
                         control_receipts=control, gates=gates, decision_id="d-abs",
                         extra_actions=(alt,))


def _escalation(decision=SelfHostingDecision.ESCALATION_REQUIRED):
    plan = SimpleNamespace(verdict="CANNOT_CHECK", reasons=("x",),
                           round_index=1, reopen_fiber_ids=())
    return EscalationAssessment(decision=decision, reasons=("r",), object_plan=plan)


# --- authority boundary (the core P4 invariant) ------------------------------
@pytest.mark.parametrize("build", [_selected_decision, _blocked_decision, _abstain_decision])
def test_bridge_never_grants_promotion_or_resume_authority(build):
    verdict = interpret_controller_for_runtime(build())
    assert verdict.acted_upon is False
    assert verdict.governance_required_for_promotion is True
    assert verdict.grants_authority is False
    assert verdict.runtime_decision not in (
        SelfHostingDecision.RESUME_WITH_INCUMBENT,
        SelfHostingDecision.GOVERNANCE_PROMOTION_REQUIRED,
    )


def test_bridge_imports_only_read_only_runtime_symbols():
    import ast
    import rakl.self_hosting_bridge as br
    text = pathlib.Path(br.__file__).read_text()
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("self_hosting_runtime"):
            imported |= {alias.name for alias in node.names}
    # The single seam may import only the non-mutating decision/assessment types;
    # it can never reach register_challenger / record_evolution_trial /
    # assess_resume_readiness, so it structurally cannot mutate the archive or
    # license a promotion/resume. (Call-site checks use the "(" so the docstring,
    # which names these as things the bridge must NOT call, does not match.)
    assert imported <= {"EscalationAssessment", "SelfHostingDecision"}
    for forbidden_call in ("register_challenger(", "record_evolution_trial(",
                           "assess_resume_readiness("):
        assert forbidden_call not in text, f"bridge must not call: {forbidden_call}"


# --- faithful status -> runtime_decision mapping -----------------------------
def test_bridge_selected_maps_to_object_search_ready_not_promotion():
    verdict = interpret_controller_for_runtime(_selected_decision())
    assert verdict.runtime_decision is SelfHostingDecision.OBJECT_SEARCH_READY
    assert verdict.controller_endorsed is True
    assert verdict.corroborates_escalation is False


def test_bridge_blocked_maps_to_cannot_check_without_granting_escalation():
    # Without an independent escalation: the controller's block corroborates nothing.
    v0 = interpret_controller_for_runtime(_blocked_decision())
    assert v0.runtime_decision is SelfHostingDecision.CANNOT_CHECK
    assert v0.controller_endorsed is False
    assert v0.corroborates_escalation is False
    # With an independently-licensed escalation: the block corroborates, but the
    # bridge STILL grants no escalation authority (stays CANNOT_CHECK).
    v1 = interpret_controller_for_runtime(_blocked_decision(), escalation=_escalation())
    assert v1.runtime_decision is SelfHostingDecision.CANNOT_CHECK
    assert v1.corroborates_escalation is True
    assert v1.grants_authority is False


def test_bridge_abstain_maps_to_assurance_pending():
    verdict = interpret_controller_for_runtime(_abstain_decision())
    assert verdict.runtime_decision is SelfHostingDecision.ASSURANCE_PENDING
    assert verdict.controller_endorsed is False


# --- purity / frozen / deterministic / binding -------------------------------
def test_bridge_does_not_mutate_inputs_and_is_deterministic():
    decision = _selected_decision()
    before = (decision.receipt.decision_id, decision.receipt.status, decision.input_content_hash)
    v1 = interpret_controller_for_runtime(decision)
    v2 = interpret_controller_for_runtime(decision)
    after = (decision.receipt.decision_id, decision.receipt.status, decision.input_content_hash)
    assert before == after  # input receipt unchanged
    assert v1 == v2  # frozen-dataclass equality, deterministic
    assert dataclasses.is_dataclass(v1) and getattr(v1, "__dataclass_params__").frozen


def test_bridge_carries_epoch_binding_and_receipt_id():
    verdict = interpret_controller_for_runtime(_selected_decision())
    assert verdict.controller_decision_id == "d-sel"
    assert verdict.evaluation_epoch_id == _epoch().epoch_id


# --- governance sovereignty of the resume seam -------------------------------
def test_resume_annotation_never_overrides_governance():
    verdict = interpret_controller_for_runtime(_blocked_decision(), escalation=_escalation())
    # Governance returned RESUME_WITH_INCUMBENT on its own authority; the bridge
    # must NOT override it (even though the controller currently blocks).
    decision, reasons = annotate_resume_with_controller(
        SelfHostingDecision.RESUME_WITH_INCUMBENT, ("governed_incumbent_matches",), verdict)
    assert decision is SelfHostingDecision.RESUME_WITH_INCUMBENT  # sovereign, unchanged
    assert "governed_incumbent_matches" in reasons
    assert any("controller" in r for r in reasons)  # observation attached


def test_resume_annotation_attaches_endorsement_for_selected():
    verdict = interpret_controller_for_runtime(_selected_decision())
    decision, reasons = annotate_resume_with_controller(
        SelfHostingDecision.RESUME_WITH_INCUMBENT, ("governed_incumbent_matches",), verdict)
    assert decision is SelfHostingDecision.RESUME_WITH_INCUMBENT
    assert "controller_endorses_resume_no_authority_granted" in reasons
