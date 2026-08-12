from rakl.authority_ledger import AuthorityAxis, AuthorityProposal
from rakl.claim_evidence import (
    ClaimAtom,
    ClaimEvidenceLink,
    EvidenceJudgment,
    EvidenceRelation,
    EvidenceReviewVerdict,
    TextSpanSelector,
    freeze_source_snapshot,
    validate_claim_evidence_link,
)
from rakl.epistemic_noninterference import EvidenceRootKind
from rakl.evidence_binding_certificate import (
    EvidenceBindingVerdict,
    ReviewedEvidenceBinding,
    evaluate_evidence_binding_for_promotion,
)
from rakl.v3_scientific_authority import ScientificEvidenceBinding


def test_review_contradiction_stays_conflict_not_invalid_exact_match_failure():
    claim = ClaimAtom("claim-contradiction", "Mechanism M explains the residual.", "regime-A")
    source = freeze_source_snapshot(
        "obs-contradiction",
        "paper://obs-contradiction",
        "The observation contradicts mechanism M in regime A.",
    )
    exact = "contradicts mechanism M"
    start = source.text.index(exact)
    link = ClaimEvidenceLink(
        link_id="link-contradiction",
        claim_id=claim.claim_id,
        source_id=source.source_id,
        source_sha256=source.sha256,
        selector=TextSpanSelector(start, start + len(exact), exact),
        proposed_relation=EvidenceRelation.SUPPORTS,
        selector_frozen_before_review=True,
    )
    judgment = EvidenceJudgment(
        judgment_id="judgment-contradiction",
        link_id=link.link_id,
        claim_id=claim.claim_id,
        scope=claim.scope,
        verdict=EvidenceReviewVerdict.REFUTES,
        known_answer_validated=True,
        frozen_before_synthesis=True,
    )
    report = validate_claim_evidence_link(claim, source, link, judgment)
    registration = ScientificEvidenceBinding(
        evidence_id="obs-contradiction",
        kind=EvidenceRootKind.EXTERNAL_OBSERVATION,
        content_sha256=source.sha256,
        supports_axes=(AuthorityAxis.MECHANISM,),
    )
    proposal = AuthorityProposal(
        proposal_id="proposal-contradiction",
        claim_id=claim.claim_id,
        axis=AuthorityAxis.MECHANISM,
        proposition="Mechanism M explains the residual.",
        scope_id=claim.scope,
        evidence_ids=(registration.evidence_id,),
    )

    result = evaluate_evidence_binding_for_promotion(
        claim,
        proposal,
        (ReviewedEvidenceBinding(registration.evidence_id, link, report),),
        {registration.evidence_id: registration},
        certificate_id="binding-contradiction",
        frozen_before_promotion=True,
    )

    assert result.verdict is EvidenceBindingVerdict.CONFLICT_REQUIRES_RESOLUTION
    assert "semantic_review_contradiction:obs-contradiction" in result.reasons
    assert "promotion_evidence_ids_do_not_exactly_match_reviewed_support_bindings" not in result.reasons
