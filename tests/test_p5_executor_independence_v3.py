from __future__ import annotations
from dataclasses import replace
from rakl.math_research_assurance import FormalizationWitness, MathClaimStage, MathResearchRecord, NoveltyCertificate, ProofReceipt
from rakl.math_research_assurance_v2 import IndependentReviewReceipt, checker_identity_digest
from rakl.math_research_assurance_v3 import AssuranceIdentityBundleV3, NoveltyDossierReviewReceipt, VerifierTrustAttestationV3, classify_math_record_v3, formalization_pair_digest, novelty_dossier_digest

LIT="lit-manifest"; REVIEW="external-reviewer"; ATTEST="external-verifier-attestor"

def _record(*, neighboring=False, rediscovery=False):
    return MathResearchRecord("artifact",True,True,FormalizationWitness("informal","formal",True,True,True,1),ProofReceipt("T","neighbor" if neighboring else "formal","lean","4.32.1",True,(),"comparator","pinned",True,True,"proof-src"),NoveltyCertificate("2026-08-15",("registered",),("exact","structural"),"fp",rediscovery,("parent",) if rediscovery else (),1,"coverage"))

def _ids(r, proposer):
    fd=formalization_pair_digest(r); nd=novelty_dossier_digest(r,literature_manifest_hash=LIT)
    return AssuranceIdentityBundleV3(
        IndependentReviewReceipt("formal-review",fd,"formal-procedure",REVIEW,proposer,True,True),
        NoveltyDossierReviewReceipt(IndependentReviewReceipt("novel-review",nd,"novel-procedure",REVIEW,proposer,True,True),nd),
        IndependentReviewReceipt("value-review","formal","value-criteria",REVIEW,proposer,True,True),
        VerifierTrustAttestationV3("trust","proof-src",checker_identity_digest(r),"checker-manifest","attest-procedure",ATTEST,proposer,True),
    )

def _stage(r, proposer): return classify_math_record_v3(r,proposer_identity_hash=proposer,identities=_ids(r,proposer),literature_manifest_hash=LIT)

def test_v3_valid_artifact_stage_is_executor_independent():
    r=_record(); assert _stage(r,"symbolic-enumerator").stage is _stage(r,"llm-proposer").stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE

def test_v3_neighboring_statement_failure_is_executor_independent():
    r=_record(neighboring=True); assert _stage(r,"symbolic-enumerator").stage is _stage(r,"llm-proposer").stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE

def test_v3_rediscovery_is_executor_independent():
    r=_record(rediscovery=True); assert _stage(r,"symbolic-enumerator").stage is _stage(r,"llm-proposer").stage is MathClaimStage.VERIFIED_REDISCOVERY

def test_v3_self_review_remains_blocked():
    r=_record(); proposer="llm-proposer"; ids=_ids(r,proposer)
    bad=replace(ids,formalization_review=replace(ids.formalization_review,reviewer_identity_hash=proposer))
    report=classify_math_record_v3(r,proposer_identity_hash=proposer,identities=bad,literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN
    assert "formalization_review_not_independent_of_current_proposer" in report.reasons
