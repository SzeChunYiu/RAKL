from __future__ import annotations
from dataclasses import replace
from rakl.math_research_assurance import FormalizationWitness, MathClaimStage, MathResearchRecord, NoveltyCertificate, ProofReceipt
from rakl.math_research_assurance_v2 import IndependentReviewReceipt, checker_identity_digest
from rakl.math_research_assurance_v3 import AssuranceIdentityBundleV3, NoveltyDossierReviewReceipt, VerifierTrustAttestationV3, classify_math_record_v3, formalization_pair_digest, novelty_dossier_digest

PROP="proposer-A"; REVIEW="reviewer-B"; ATTEST="verifier-attestor-C"; LIT="lit-manifest-v1"

def _record(*, informal="informal-v1", equivalent=False):
    return MathResearchRecord(
        claim_id="C", interestingness_screened=True, external_mathematical_review=True,
        formalization=FormalizationWitness(informal,"formal-v1",True,True,True,1),
        proof=ProofReceipt("T","formal-v1","lean","4.32.1",True,(),"comparator","pinned",True,True,"proof-source-v1"),
        novelty=NoveltyCertificate("2026-08-15",("registered",),("exact","structural"),"fp-v1",equivalent,("known-parent",) if equivalent else (),1,("coverage-v1",)),
    )

def _review(subject, axis, proposer=PROP, reviewer=REVIEW):
    return IndependentReviewReceipt(f"{axis}-review",subject,f"{axis}-procedure",reviewer,proposer,True,True)

def _bundle(record=None, *, proposer=PROP, formal_subject=None, novelty_subject=None, novelty_digest=None, attestor=ATTEST, trust_proposer=None):
    record=record or _record(); n=record.novelty; assert n is not None
    fsubject=formal_subject or formalization_pair_digest(record)
    ndigest=novelty_digest or novelty_dossier_digest(record,literature_manifest_hash=LIT)
    nsubject=novelty_subject or ndigest
    return AssuranceIdentityBundleV3(
        formalization_review=_review(fsubject,"formal",proposer=proposer),
        novelty_review=NoveltyDossierReviewReceipt(_review(nsubject,"novelty",proposer=proposer),ndigest),
        value_review=_review("formal-v1","value",proposer=proposer),
        verifier_trust=VerifierTrustAttestationV3("trust","proof-source-v1",checker_identity_digest(record),"checker-manifest","trust-procedure",attestor,trust_proposer or proposer,True),
    )

def test_review_receipt_cannot_be_reused_by_different_current_proposer():
    r=_record(); ids=_bundle(r,proposer="proposer-A")
    report=classify_math_record_v3(r,proposer_identity_hash="proposer-B",identities=ids,literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN
    assert "formalization_review_proposer_mismatch" in report.reasons

def test_same_formal_statement_with_changed_informal_claim_needs_new_review():
    original=_record(informal="informal-A"); ids=_bundle(original)
    changed=_record(informal="informal-B")
    report=classify_math_record_v3(changed,proposer_identity_hash=PROP,identities=ids,literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN
    assert "formalization_review_subject_mismatch" in report.reasons

def test_novelty_result_flip_invalidates_old_dossier_review():
    before=_record(equivalent=False); ids=_bundle(before)
    after=_record(equivalent=True)
    ids=replace(ids,formalization_review=_review(formalization_pair_digest(after),"formal"),verifier_trust=VerifierTrustAttestationV3("trust","proof-source-v1",checker_identity_digest(after),"checker-manifest","trust-procedure",ATTEST,PROP,True))
    report=classify_math_record_v3(after,proposer_identity_hash=PROP,identities=ids,literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED
    assert "novelty_review_subject_mismatch" in report.reasons or "novelty_review_dossier_mismatch" in report.reasons

def test_verifier_self_attestation_is_rejected():
    r=_record(); ids=_bundle(r,attestor=PROP)
    report=classify_math_record_v3(r,proposer_identity_hash=PROP,identities=ids,literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "verifier_trust_attestor_not_independent" in report.reasons

def test_verifier_receipt_cannot_be_reused_by_new_proposer():
    r=_record(); ids=_bundle(r,proposer="proposer-B",trust_proposer="proposer-A")
    report=classify_math_record_v3(r,proposer_identity_hash="proposer-B",identities=ids,literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "verifier_trust_proposer_mismatch" in report.reasons

def test_exact_transitive_receipt_chain_reaches_existing_candidate_gate():
    r=_record(); report=classify_math_record_v3(r,proposer_identity_hash=PROP,identities=_bundle(r),literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    assert "v3_transitive_exact_receipt_chain_passed" in report.reasons
