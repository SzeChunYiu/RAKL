"""RSHEA Phase 4: the governed bridge between the meta-controller and the
self-hosting runtime loop.

This module is the **single seam** where a frozen controller
``MetaDecisionReceipt`` (produced by the P3 shadow controller) is carried into
the self-hosting runtime's decision space. It is the only module that imports
*both* ``shadow_controller`` and ``self_hosting_runtime``: the shadow never
touches the runtime (P3 invariant), and the runtime never imports the controller.
The bridge sits between them.

Authority stays with governance throughout:

* the bridge never promotes a challenger, never mutates an ``EvolutionArchive``,
  never changes the governed incumbent, and never calls a mutating runtime
  function (``register_challenger`` / ``record_evolution_trial`` / …);
* the bridge never returns ``RESUME_WITH_INCUMBENT`` or
  ``GOVERNANCE_PROMOTION_REQUIRED`` from a controller receipt alone — object
  resumption is licensed exclusively by ``assess_resume_readiness``, which
  requires governance to have already changed the incumbent;
* a controller ``SELECTED`` endorses the current operator basis
  (``OBJECT_SEARCH_READY``) but is **not** promotion; a ``BLOCKED`` corroborates
  an *independently-licensed* escalation yet grants no escalation authority; an
  ``ABSTAIN`` is assurance-pending.

The bridge interprets; it does not act (``acted_upon=False``). A SELECTED
receipt only becomes a *governed proposal* in P5; resumption is restored in P7.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .evolution_trace import DecisionStatus, HardGateStatus, MetaDecisionReceipt
from .self_hosting_runtime import EscalationAssessment, SelfHostingDecision
from .shadow_controller import ShadowDecision

# The two runtime decisions that carry promotion/resume AUTHORITY. The bridge is
# structurally forbidden from emitting either from a controller receipt: emitting
# RESUME_WITH_INCUMBENT would bypass assess_resume_readiness, and emitting
# GOVERNANCE_PROMOTION_REQUIRED would let the controller nominate an incumbent.
_AUTHORITATIVE_RUNTIME_DECISIONS = frozenset(
    {SelfHostingDecision.RESUME_WITH_INCUMBENT, SelfHostingDecision.GOVERNANCE_PROMOTION_REQUIRED}
)


@dataclass(frozen=True)
class ControllerBridgeVerdict:
    """Frozen, authority-safe interpretation of one controller receipt for the runtime.

    Every field is read off the receipt; the bridge decides nothing and acts on
    nothing. ``runtime_decision`` is an *advisory* mapping — it never carries
    promotion/resume authority (see ``grants_authority``).
    """

    controller_decision_id: str
    evaluation_epoch_id: str
    runtime_decision: SelfHostingDecision
    controller_endorsed: bool
    corroborates_escalation: bool
    acted_upon: bool
    governance_required_for_promotion: bool
    reasons: Tuple[str, ...]

    @property
    def grants_authority(self) -> bool:
        """A controller receipt observed through the bridge grants no authority."""
        return self.runtime_decision in _AUTHORITATIVE_RUNTIME_DECISIONS


def _has_failed_hard_gate(receipt: MetaDecisionReceipt) -> bool:
    return any(gate.status is HardGateStatus.FAIL for gate in receipt.hard_gate_observations)


def interpret_controller_for_runtime(
    decision: ShadowDecision,
    *,
    escalation: Optional[EscalationAssessment] = None,
) -> ControllerBridgeVerdict:
    """Map a frozen controller receipt into a runtime-native, authority-safe verdict.

    Pure: no mutation, no I/O, no archive change. ``escalation`` (when supplied)
    is the runtime's OWN independent escalation assessment (from
    ``inspect_for_self_hosting``); the bridge reads it only to mark whether the
    controller's observation *corroborates* that escalation — it never licenses
    escalation from the controller side.
    """
    receipt: MetaDecisionReceipt = decision.receipt
    status = receipt.status
    escalation_licensed = (
        escalation is not None and escalation.decision is SelfHostingDecision.ESCALATION_REQUIRED
    )

    if status is DecisionStatus.SELECTED and not _has_failed_hard_gate(receipt):
        runtime_decision = SelfHostingDecision.OBJECT_SEARCH_READY
        controller_endorsed = True
        corroborates = False
        reasons = (
            "controller_selected_status_quo_no_hard_gate_failed",
            "controller_endorsement_is_not_promotion",
        )
    elif status is DecisionStatus.BLOCKED or _has_failed_hard_gate(receipt):
        runtime_decision = SelfHostingDecision.CANNOT_CHECK
        controller_endorsed = False
        corroborates = escalation_licensed
        reasons = ("controller_blocked_on_hard_gate", "bridge_grants_no_escalation_authority")
        if escalation_licensed:
            reasons = reasons + ("controller_block_corroborates_independently_licensed_escalation",)
    else:  # DecisionStatus.ABSTAIN
        runtime_decision = SelfHostingDecision.ASSURANCE_PENDING
        controller_endorsed = False
        corroborates = False
        reasons = ("controller_abstained_utility_margin", "assurance_pending_no_authority_change")

    verdict = ControllerBridgeVerdict(
        controller_decision_id=receipt.decision_id,
        evaluation_epoch_id=receipt.evaluation_epoch_id,
        runtime_decision=runtime_decision,
        controller_endorsed=controller_endorsed,
        corroborates_escalation=corroborates,
        acted_upon=False,
        governance_required_for_promotion=True,
        reasons=reasons,
    )
    # Structural guard: the mapping must never emit an authoritative decision.
    if verdict.grants_authority:
        raise AssertionError(
            "self-hosting bridge must not grant promotion/resume authority from a controller receipt"
        )
    return verdict


def annotate_resume_with_controller(
    governed_decision: SelfHostingDecision,
    governed_reasons: Tuple[str, ...],
    controller_verdict: ControllerBridgeVerdict,
) -> Tuple[SelfHostingDecision, Tuple[str, ...]]:
    """Attach the controller's observation to a governed resume decision (advisory).

    Governance is sovereign: this returns the **same** ``governed_decision`` it
    was given — it never overrides a governance verdict and never withholds a
    governed resume. The controller's observation is appended to the reasons so
    the runtime's resume record shows whether the controller corroborated; the
    actual governed-intervention behaviour (withholding/escalating on a controller
    block) belongs to P5.
    """
    if controller_verdict.corroborates_escalation:
        annotation = "controller_corroborates_escalation_no_authority_granted"
    elif controller_verdict.controller_endorsed:
        annotation = "controller_endorses_resume_no_authority_granted"
    else:
        annotation = "controller_observation_attached_governance_sovereign"
    return governed_decision, tuple(governed_reasons) + (annotation,)
