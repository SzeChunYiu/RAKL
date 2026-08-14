"""RSHEA Phase 5: governed intervention - the surface that turns a controller
SELECTED into an external governance sign-off proposal, and enforces that
controller ABSTAIN / BLOCKED never act.

Phase 4's bridge carries a frozen controller receipt into the runtime decision
space WITHOUT acting (acted_upon=False). Phase 5 is the one place a controller
SELECTED *could* become a continuation - but only as a proposal that external
governance must independently sign off. Until sign-off, nothing happens; with
sign-off, the runtime may continue object search. Promotion and resume authority
are never granted here: sign-off authorizes CONTINUATION, never promotion, and
the proposal's proposed decision is always a non-authoritative runtime decision.

Authority non-interchangeability holds throughout. A controller SELECTED is
CONTROL_INPUT *evidence for* the proposal (it endorses the current operator
basis); a GovernanceSignOff is GOVERNANCE *authority for* the action. The two
are not interchangeable: a sign-off is not a metric receipt, cannot be entered
into a ledger, cannot back evolution evidence, and cannot be substituted for a
control input. Nothing in the controller/runtime loop constructs a sign-off -
governance is sovereign and external.

This module never imports the live self_hosting_runtime (it learns the runtime
decision only through the P4 bridge verdict) and never calls a mutating runtime
function, so it structurally cannot promote a challenger, change an incumbent,
or license a resume.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional, Tuple

from .evolution_trace import canonical_hash
from .self_hosting_bridge import ControllerBridgeVerdict


@dataclass(frozen=True)
class GovernanceSignOff:
    """Frozen, external governance authorization for one governed proposal.

    Governance is sovereign and external: no code in the controller/runtime loop
    constructs this. ``authorizes_continuation`` is governance's independent
    decision to let the runtime proceed with object search on the
    controller-endorsed basis; it is NEVER a promotion or incumbent change. A
    sign-off is GOVERNANCE authority, distinct from a CONTROL_INPUT receipt.
    """

    sign_off_id: str
    evaluation_epoch_id: str
    proposal_id: str
    authorizes_continuation: bool
    reasons: Tuple[str, ...]

    @property
    def content_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class GovernedProposal:
    """A controller SELECTED surfaced as a proposal needing governance sign-off.

    Never actionable until an external GovernanceSignOff authorizes
    continuation, and even then ``is_actionable`` only means the runtime may
    continue object search - it is NEVER promotion/resume authority
    (``proposed_decision_grants_authority`` is False by construction).
    """

    proposal_id: str
    evaluation_epoch_id: str
    controller_decision_id: str
    proposed_runtime_decision: str
    proposed_decision_grants_authority: bool
    sign_off: Optional[GovernanceSignOff]
    reasons: Tuple[str, ...]

    @property
    def is_signed_off(self) -> bool:
        return (
            self.sign_off is not None
            and self.sign_off.authorizes_continuation
        )

    @property
    def is_actionable(self) -> bool:
        """Actionable iff governance signed off AND the proposed decision grants
        no promotion/resume authority (continuation only, never promotion)."""
        return self.is_signed_off and not self.proposed_decision_grants_authority

    @property
    def content_hash(self) -> str:
        return canonical_hash(asdict(self))


def surface_governed_proposal(
    bridge_verdict: ControllerBridgeVerdict,
    *,
    proposal_id: str,
    sign_off: Optional[GovernanceSignOff] = None,
) -> Optional[GovernedProposal]:
    """Surface a controller SELECTED as a governance sign-off proposal.

    Returns None for ABSTAIN/BLOCKED controller observations - they never
    produce a proposal and never act. For a SELECTED (bridge
    OBJECT_SEARCH_READY), returns a GovernedProposal that is not actionable
    until external governance signs off; sign-off authorizes object-search
    continuation, NEVER promotion/resume. Pure: no mutation, no I/O, and it
    never constructs a sign-off itself (governance is sovereign and external).
    """
    # ABSTAIN/BLOCKED never act: the controller did not endorse a continuation.
    if not bridge_verdict.controller_endorsed:
        return None

    if sign_off is not None:
        if sign_off.evaluation_epoch_id != bridge_verdict.evaluation_epoch_id:
            raise ValueError(
                "governance sign-off must be bound to the proposal's evaluation epoch"
            )
        if sign_off.proposal_id != proposal_id:
            raise ValueError("governance sign-off must reference this proposal")

    proposal = GovernedProposal(
        proposal_id=proposal_id,
        evaluation_epoch_id=bridge_verdict.evaluation_epoch_id,
        controller_decision_id=bridge_verdict.controller_decision_id,
        proposed_runtime_decision=bridge_verdict.runtime_decision.name,
        proposed_decision_grants_authority=bridge_verdict.grants_authority,
        sign_off=sign_off,
        reasons=bridge_verdict.reasons
        + ("controller_selected_surfaces_as_governance_proposal",),
    )
    # Defense in depth: a proposal must never embed an authoritative decision.
    if proposal.proposed_decision_grants_authority:
        raise AssertionError(
            "governed proposal must never embed a promotion/resume-authoritative decision"
        )
    return proposal
