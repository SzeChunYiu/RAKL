from __future__ import annotations

from dataclasses import dataclass
import json
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
_MAX_RAW_BYTES = 16_384
_MAX_RAW_DEPTH = 4


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


def _reject_nonfinite(value: str):
    raise ValueError(f"nonfinite_json_constant:{value}")


def _duplicate_safe_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate_json_key:{key}")
        out[key] = value
    return out


def _json_depth(value: Any) -> int:
    if isinstance(value, Mapping):
        return 1 + max((_json_depth(item) for item in value.values()), default=0)
    if isinstance(value, (list, tuple)):
        return 1 + max((_json_depth(item) for item in value), default=0)
    return 0


def parse_raw_untrusted_agent_authority_json(raw: str) -> AgentAuthorityProposalResult:
    """Parse raw model JSON without allowing parser ambiguity to mint authority.

    Duplicate keys are rejected instead of using last-key-wins semantics. BOM,
    NUL, non-finite constants, oversized/deep structures and non-object roots
    fail closed. The resulting object still traverses the stricter mapping-level
    gateway, so nested/lookalike/unknown fields cannot become a hidden control
    channel.
    """
    if not isinstance(raw, str):
        return AgentAuthorityProposalResult(None, ("agent_raw_payload_not_text",))
    if raw.startswith("\ufeff"):
        return AgentAuthorityProposalResult(None, ("agent_raw_payload_bom_forbidden",))
    if "\x00" in raw:
        return AgentAuthorityProposalResult(None, ("agent_raw_payload_nul_forbidden",))
    if len(raw.encode("utf-8")) > _MAX_RAW_BYTES:
        return AgentAuthorityProposalResult(None, ("agent_raw_payload_too_large",))
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_duplicate_safe_object,
            parse_constant=_reject_nonfinite,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        return AgentAuthorityProposalResult(None, (f"agent_raw_json_invalid:{exc}",))
    if not isinstance(value, Mapping):
        return AgentAuthorityProposalResult(None, ("agent_raw_json_root_not_object",))
    if _json_depth(value) > _MAX_RAW_DEPTH:
        return AgentAuthorityProposalResult(None, ("agent_raw_json_too_deep",))
    return parse_untrusted_agent_authority_payload(value)


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


def submit_raw_untrusted_agent_authority_json(
    state,
    raw: str,
    *,
    certificate_id: str,
    verification_outcome: VerificationOutcome,
    authority_context: ProtectedAuthorityContext | None = None,
    attestation_id: str | None = None,
) -> ScientificTransitionOutcome:
    """Raw-text sibling of :func:`submit_untrusted_agent_authority_payload`."""
    parsed = parse_raw_untrusted_agent_authority_json(raw)
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
