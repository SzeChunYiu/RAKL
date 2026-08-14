from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from .authority_ledger import AuthorityAxis, AuthorityProposal, VerificationOutcome
from .v3_authority import ProtectedAuthorityContext
from .v3_scientific_authority import ScientificTransitionOutcome, promote_scientific_authority

_ALLOWED_FIELDS = frozenset({"claim_id", "axis", "proposition", "scope_id", "evidence_ids"})
_FORBIDDEN_CONTROL_FIELDS = frozenset({
    "verified",
    "verification_outcome",
    "outcome",
    "attestation_id",
    "authority_context",
    "signer_key",
    "signer_id",
    "certificate_id",
    "evaluator_artifact_id",
    "subject_hash",
    "grants_authority",
})


@dataclass(frozen=True)
class AgentAuthorityProposalResult:
    proposal: AuthorityProposal | None
    reasons: Tuple[str, ...]

    @property
    def accepted_to_proposal_plane(self) -> bool:
        return self.proposal is not None and not self.reasons

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def parse_untrusted_agent_authority_payload(
    payload: Mapping[str, Any],
) -> AgentAuthorityProposalResult:
    """Compile model/agent output into an inert typed proposal only.

    The payload may describe the scientific assertion it wants considered, but
    it may not carry any control-plane object or declaration that could be
    mistaken for verification/attestation/certificate authority. Unknown fields
    are rejected rather than ignored so a later schema extension cannot silently
    create a new authority channel.
    """
    keys = set(payload)
    dangerous = sorted(keys & _FORBIDDEN_CONTROL_FIELDS)
    unknown = sorted(keys - _ALLOWED_FIELDS - _FORBIDDEN_CONTROL_FIELDS)
    reasons: list[str] = []
    if dangerous:
        reasons.append("agent_payload_contains_protected_control_fields:" + ",".join(dangerous))
    if unknown:
        reasons.append("agent_payload_contains_unknown_fields:" + ",".join(unknown))
    missing = sorted(_ALLOWED_FIELDS - keys)
    if missing:
        reasons.append("agent_payload_missing_required_fields:" + ",".join(missing))
    if reasons:
        return AgentAuthorityProposalResult(None, tuple(reasons))

    try:
        axis = AuthorityAxis(str(payload["axis"]))
    except (TypeError, ValueError):
        return AgentAuthorityProposalResult(None, ("agent_payload_invalid_authority_axis",))

    evidence = payload["evidence_ids"]
    if not isinstance(evidence, (list, tuple)) or not evidence or any(
        not isinstance(item, str) or not item.strip() for item in evidence
    ):
        return AgentAuthorityProposalResult(None, ("agent_payload_invalid_evidence_ids",))

    values = {
        "claim_id": payload["claim_id"],
        "proposition": payload["proposition"],
        "scope_id": payload["scope_id"],
    }
    if any(not isinstance(value, str) or not value.strip() for value in values.values()):
        return AgentAuthorityProposalResult(None, ("agent_payload_blank_or_nonstring_claim_fields",))

    proposal = AuthorityProposal(
        proposal_id="agent-proposal:" + str(payload["claim_id"]),
        claim_id=str(payload["claim_id"]),
        axis=axis,
        proposition=str(payload["proposition"]),
        scope_id=str(payload["scope_id"]),
        evidence_ids=tuple(evidence),
    )
    return AgentAuthorityProposalResult(proposal, ())


def submit_untrusted_agent_authority_payload(
    state,
    payload: Mapping[str, Any],
    *,
    certificate_id: str,
    verification_outcome: VerificationOutcome,
    authority_context: ProtectedAuthorityContext | None = None,
    attestation_id: str | None = None,
) -> ScientificTransitionOutcome:
    """Submit an agent proposal through the existing protected runtime boundary.

    ``certificate_id``, ``verification_outcome``, ``authority_context`` and
    ``attestation_id`` are deliberately *not* read from the agent payload. The
    gateway cannot manufacture them. A valid payload therefore remains inert
    unless an external protected control plane separately supplies a matching
    attestation to :func:`promote_scientific_authority`.
    """
    parsed = parse_untrusted_agent_authority_payload(payload)
    if not parsed.accepted_to_proposal_plane or parsed.proposal is None:
        return ScientificTransitionOutcome(state, False, parsed.reasons)
    return promote_scientific_authority(
        state,
        parsed.proposal,
        certificate_id=certificate_id,
        outcome=verification_outcome,
        authority_context=authority_context,
        attestation_id=attestation_id,
    )
