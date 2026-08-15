from __future__ import annotations
import pytest
from rakl.math_research_assurance import FormalizationWitness, MathClaimStage, MathResearchRecord, NoveltyCertificate, ProofReceipt, classify_math_record
from rakl.math_research_assurance_v2 import AssuranceIdentityBundle, IndependentReviewReceipt, NoveltyReviewReceipt, VerifierTrustReceiptV2, checker_identity_digest, classify_math_record_v2, novelty_world_digest

PROPOSER="proposer-A"; REVIEWER="reviewer-B"; MANIFEST="literature-manifest-v1"

def _record():
    return MathResearchRecord(
        claim_id="C",
        interestingness_screened=True,
        external_mathematical_review=True,
        formalization=FormalizationWitness("informal-v1","formal-v1",True,True,True,1),
        proof=ProofReceipt("T","formal-v1","lean","4.32.1",True,(),"comparator","pinned",True,True,"proof-source-v1"),
        novelty=NoveltyCertificate("2026-08-15",("MathSciNet","arXiv"),("exact","structural"),"fp-v1",False,(),1),
    )

def _review(subject, axis, *, reviewer=REVIEWER, proposer=PROPOSER):
    return IndependentReviewReceipt(f"review-{axis}",subject,f"procedure-{axis}",reviewer,proposer,True,True)

def _bundle(record=None, *, reviewer=REVIEWER, formal_subject="formal-v1", novelty_world=None, verifier_source="proof-source-v1", checker_digest=None, value=True):
    record=record or _record(); cert=record.novelty; assert cert is not None
    formal=_review(formal_subject,"formal",reviewer=reviewer)
    nreview=_review(cert.canonical_fingerprint,"novelty",reviewer=reviewer)
    world=novelty_world_digest(cert,literature_manifest_hash=MANIFEST) if novelty_world is None else novelty_world
    vreview=_review("formal-v1","value",reviewer=reviewer) if value else None
    trust=VerifierTrustReceiptV2("trust",verifier_source,checker_digest or checker_identity_digest(record),"lean-manifest-v1",True)
    return AssuranceIdentityBundle(formal,NoveltyReviewReceipt(nreview,world),vreview,trust)

def test_v1_boolean_review_can_look_promotable_but_v2_blocks_self_review():
    record=_record()
    assert classify_math_record(record).stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    report=classify_math_record_v2(record,proposer_identity_hash=PROPOSER,identities=_bundle(record,reviewer=PROPOSER),literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN
    assert "formalization_review_not_independent_of_proposer" in report.reasons

def test_review_for_neighboring_statement_cannot_be_reused():
    report=classify_math_record_v2(_record(),proposer_identity_hash=PROPOSER,identities=_bundle(formal_subject="formal-other"),literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN
    assert "formalization_review_subject_mismatch" in report.reasons

def test_novelty_review_must_bind_exact_literature_world():
    report=classify_math_record_v2(_record(),proposer_identity_hash=PROPOSER,identities=_bundle(novelty_world="wrong-world"),literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED
    assert "novelty_review_world_mismatch" in report.reasons

def test_missing_value_review_preserves_truth_and_novelty_but_blocks_new_math_promotion():
    report=classify_math_record_v2(_record(),proposer_identity_hash=PROPOSER,identities=_bundle(value=False),literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.BOUNDED_NOVEL_RESULT
    assert "value_independent_review_receipt_missing" in report.reasons

def test_value_review_requires_nonempty_frozen_criteria_identity():
    with pytest.raises(ValueError,match="procedure_hash"):
        IndependentReviewReceipt("r","formal-v1","",REVIEWER,PROPOSER,True,True)

def test_verifier_trust_must_bind_exact_proof_source_and_checker_manifest():
    report=classify_math_record_v2(_record(),proposer_identity_hash=PROPOSER,identities=_bundle(verifier_source="other-proof"),literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "verifier_trust_proof_source_mismatch" in report.reasons
    report2=classify_math_record_v2(_record(),proposer_identity_hash=PROPOSER,identities=_bundle(checker_digest="wrong-checker"),literature_manifest_hash=MANIFEST)
    assert "verifier_trust_checker_identity_mismatch" in report2.reasons

def test_exact_subject_independent_reviews_may_enter_existing_candidate_gate():
    record=_record(); bundle=_bundle(record)
    report=classify_math_record_v2(record,proposer_identity_hash=PROPOSER,identities=bundle,literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    assert "v2_exact_subject_independent_review_identity_passed" in report.reasons
    assert bundle.grants_scientific_authority is False and bundle.grants_publication_authority is False
