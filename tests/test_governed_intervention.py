"""RSHEA Phase 5 governed-intervention tests.

Proves the controller's SELECTED only ever becomes a continuation PROPOSAL that
external governance must sign off on, and that ABSTAIN/BLOCKED never act. Even
when actionable, a proposal is object-search continuation, NEVER promotion/resume.
"""
import ast
import dataclasses
import pathlib
from types import SimpleNamespace

import pytest

from rakl.evolution_trace import MetricLedger, SelfModelSnapshot
from rakl.governed_intervention import (
    GovernedProposal,
    GovernanceSignOff,
    surface_governed_proposal,
)
from rakl.meta_controller import ActionEstimate, ComponentEstimate, DecisionPolicy
from rakl.observability_adapters import (
    build_evaluation_epoch,
    process_outcome_gate,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
)
from rakl.self_hosting_bridge import interpret_controller_for_runtime
from rakl.self_hosting_runtime import SelfHostingDecision
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


def _clean_setup(outcome="SUCCESS"):
    epoch = _epoch()
    cost_r, contraction, out = process_telemetry_to_receipts(
        _telemetry(outcome=outcome), epoch, rakl_canonical_metrics, sequence_base=0)
    ledger = MetricLedger((cost_r, contraction, out))
    gates = (process_outcome_gate(_telemetry(outcome=outcome),
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


def _verdict(decision):
    return interpret_controller_for_runtime(decision)


def _sign_off(epoch_id, proposal_id="p1", authorizes=True):
    return GovernanceSignOff(
        sign_off_id="so-1", evaluation_epoch_id=epoch_id, proposal_id=proposal_id,
        authorizes_continuation=authorizes,
        reasons=("governance_independent_review_complete",))


# --- ABSTAIN / BLOCKED never act ---------------------------------------------
def test_abstain_produces_no_proposal():
    assert surface_governed_proposal(_verdict(_abstain_decision()), proposal_id="p1") is None


def test_blocked_produces_no_proposal():
    assert surface_governed_proposal(_verdict(_blocked_decision()), proposal_id="p1") is None


# --- SELECTED -> proposal gated on external sign-off -------------------------
def test_selected_proposal_is_not_actionable_without_sign_off():
    proposal = surface_governed_proposal(_verdict(_selected_decision()), proposal_id="p1")
    assert isinstance(proposal, GovernedProposal)
    assert proposal.is_actionable is False
    assert proposal.is_signed_off is False


def test_selected_proposal_is_not_actionable_when_governance_denies():
    v = _verdict(_selected_decision())
    proposal = surface_governed_proposal(
        v, proposal_id="p1", sign_off=_sign_off(v.evaluation_epoch_id, authorizes=False))
    assert proposal.is_signed_off is False
    assert proposal.is_actionable is False


def test_selected_proposal_becomes_actionable_only_with_authorizing_sign_off():
    v = _verdict(_selected_decision())
    proposal = surface_governed_proposal(
        v, proposal_id="p1", sign_off=_sign_off(v.evaluation_epoch_id, authorizes=True))
    assert proposal.is_signed_off is True
    assert proposal.is_actionable is True


# --- the core invariant: actionable is continuation, NEVER promotion ---------
def test_actionable_proposal_never_grants_promotion_authority():
    v = _verdict(_selected_decision())
    proposal = surface_governed_proposal(
        v, proposal_id="p1", sign_off=_sign_off(v.evaluation_epoch_id, authorizes=True))
    assert proposal.is_actionable is True
    # Continuation of object search, not a promotion/resume decision.
    assert proposal.proposed_runtime_decision == SelfHostingDecision.OBJECT_SEARCH_READY.name
    assert proposal.proposed_decision_grants_authority is False
    assert proposal.proposed_runtime_decision not in {
        SelfHostingDecision.RESUME_WITH_INCUMBENT.name,
        SelfHostingDecision.GOVERNANCE_PROMOTION_REQUIRED.name,
    }


# --- no autonomous promotion: structural / source invariants -----------------
def test_module_cannot_autonomously_promote_or_sign_off():
    import rakl.governed_intervention as gi
    text = pathlib.Path(gi.__file__).read_text()
    tree = ast.parse(text)
    runtime_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("self_hosting_runtime"):
            runtime_imports |= {alias.name for alias in node.names}
    # P5 never imports the runtime directly; it learns the runtime decision only
    # through the P4 bridge verdict. (canonical_hash from evolution_trace is a
    # pure helper, used by P4/P6 too, and is permitted.)
    assert runtime_imports == set(), f"P5 must not import self_hosting_runtime: {runtime_imports}"
    # No mutating call sites and no self-issued sign-off.
    for forbidden in ("register_challenger(", "record_evolution_trial(",
                      "assess_resume_readiness(", "GovernanceSignOff("):
        assert forbidden not in text, f"P5 must not call/construct: {forbidden}"


def test_sign_off_is_distinct_authority_not_a_metric_receipt():
    from rakl.evolution_trace import MetricReceipt
    v = _verdict(_selected_decision())
    proposal = surface_governed_proposal(
        v, proposal_id="p1", sign_off=_sign_off(v.evaluation_epoch_id))
    assert not isinstance(proposal.sign_off, MetricReceipt)
    assert not isinstance(proposal, MetricReceipt)
    # A proposal/sign-off cannot be coerced into a ledger: no authority field.
    assert not hasattr(proposal, "authority")
    assert not hasattr(proposal.sign_off, "authority")


# --- sign-off epoch + proposal binding ---------------------------------------
def test_sign_off_must_be_epoch_and_proposal_bound():
    v = _verdict(_selected_decision())
    other_epoch = build_evaluation_epoch(
        rakl_canonical_metrics, benchmark_protocol_hash="bench", evaluator_hash="eval",
        model_tool_harness_hash="mth", decision_policy_hash="dp",
        observatory_instrumentation_hash="DIFFERENT")
    wrong_epoch = _sign_off(other_epoch.epoch_id)
    with pytest.raises(ValueError, match="epoch"):
        surface_governed_proposal(v, proposal_id="p1", sign_off=wrong_epoch)
    wrong_proposal = _sign_off(v.evaluation_epoch_id, proposal_id="OTHER")
    with pytest.raises(ValueError, match="proposal"):
        surface_governed_proposal(v, proposal_id="p1", sign_off=wrong_proposal)


# --- pure / frozen / deterministic / tamper-evident --------------------------
def test_proposal_is_pure_frozen_deterministic_and_tamper_evident():
    from rakl.evolution_trace import canonical_hash
    from dataclasses import asdict
    v = _verdict(_selected_decision())
    so = _sign_off(v.evaluation_epoch_id)
    p1 = surface_governed_proposal(v, proposal_id="p1", sign_off=so)
    p2 = surface_governed_proposal(v, proposal_id="p1", sign_off=so)
    assert dataclasses.is_dataclass(p1) and getattr(p1, "__dataclass_params__").frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        p1.proposal_id = "tamper"
    assert p1 == p2  # deterministic
    assert p1.content_hash == p2.content_hash
    assert canonical_hash(asdict(p1)) == p1.content_hash  # rederivable
    # A denied sign-off diverges the hash from an authorizing one (tamper-evident).
    p_denied = surface_governed_proposal(
        v, proposal_id="p1", sign_off=_sign_off(v.evaluation_epoch_id, authorizes=False))
    assert p_denied.content_hash != p1.content_hash


def test_proposal_carries_epoch_and_controller_binding():
    v = _verdict(_selected_decision())
    proposal = surface_governed_proposal(v, proposal_id="p1")
    assert proposal.controller_decision_id == "d-sel"
    assert proposal.evaluation_epoch_id == v.evaluation_epoch_id
