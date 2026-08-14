from hashlib import sha256

from hypothesis import given, strategies as st

from rakl.agent_authority_gateway import (
    parse_untrusted_agent_authority_payload,
    submit_untrusted_agent_authority_payload,
)
from rakl.authority_ledger import AuthorityAxis, VerificationOutcome
from rakl.claim_evidence import ClaimAtom
from rakl.epistemic_noninterference import EvidenceRootKind
from rakl.v3_runtime import RAKLV3State
from rakl.v3_scientific_authority import (
    ScientificEvidenceBinding,
    register_scientific_claim,
    register_scientific_evidence,
)

BASE = {
    "claim_id": "claim-agent-gateway",
    "axis": "R",
    "proposition": "the representation is supported in the registered scope",
    "scope_id": "scope-agent-gateway",
    "evidence_ids": ["ev-agent-gateway"],
}

FORBIDDEN = (
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
)


@given(st.sampled_from(FORBIDDEN), st.one_of(st.text(max_size=40), st.booleans(), st.integers()))
def test_agent_payload_cannot_smuggle_control_plane_fields(field, value):
    payload = dict(BASE)
    payload[field] = value
    result = parse_untrusted_agent_authority_payload(payload)
    assert not result.accepted_to_proposal_plane
    assert result.proposal is None
    assert result.grants_scientific_authority is False
    assert any("protected_control_fields" in reason for reason in result.reasons)


@given(
    st.text(min_size=1, max_size=24).filter(
        lambda key: key not in set(BASE) | set(FORBIDDEN) and key.strip() != ""
    )
)
def test_unknown_agent_fields_fail_closed(field):
    payload = dict(BASE)
    payload[field] = "candidate"
    result = parse_untrusted_agent_authority_payload(payload)
    assert not result.accepted_to_proposal_plane
    assert any("unknown_fields" in reason for reason in result.reasons)


def test_well_formed_agent_payload_creates_only_inert_typed_proposal():
    result = parse_untrusted_agent_authority_payload(BASE)
    assert result.accepted_to_proposal_plane
    assert result.proposal is not None
    assert result.proposal.axis is AuthorityAxis.REPRESENTATION
    assert result.proposal.evidence_ids == ("ev-agent-gateway",)
    assert result.grants_scientific_authority is False


def test_even_valid_registered_agent_proposal_cannot_mint_without_external_attestation():
    state = RAKLV3State()
    state = register_scientific_claim(
        state,
        ClaimAtom(
            claim_id="claim-agent-gateway",
            text="representation claim",
            scope="registered gateway scope",
        ),
    )
    state = register_scientific_evidence(
        state,
        ScientificEvidenceBinding(
            evidence_id="ev-agent-gateway",
            kind=EvidenceRootKind.EXTERNAL_OBSERVATION,
            content_sha256=sha256(b"external observation").hexdigest(),
            supports_axes=(AuthorityAxis.REPRESENTATION,),
        ),
    )
    before = state.scientific_authority
    outcome = submit_untrusted_agent_authority_payload(
        state,
        BASE,
        certificate_id="cert-agent-gateway",
        verification_outcome=VerificationOutcome.SUPPORTED,
        authority_context=None,
        attestation_id=None,
    )
    assert outcome.committed is False
    assert outcome.state.scientific_authority == before
    assert "resolved_protected_attestation_missing" in outcome.reasons
