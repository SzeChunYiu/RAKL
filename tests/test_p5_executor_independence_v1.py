from __future__ import annotations
from dataclasses import replace
from rakl.math_research_assurance import FormalizationWitness, MathClaimStage, MathResearchRecord, NoveltyCertificate, ProofReceipt
from rakl.math_research_assurance_v2 import AssuranceIdentityBundle, IndependentReviewReceipt, NoveltyReviewReceipt, VerifierTrustReceiptV2, checker_identity_digest, classify_math_record_v2, novelty_world_digest

MANIFEST="lit-world-1"

def _record(*, neighboring=False, rediscovery=False):
    return MathResearchRecord(
        claim_id="artifact-exact",
        interestingness_screened=True,
        external_mathematical_review=True,
        formalization=FormalizationWitness("informal","formal",True,True,True,1),
        proof=ProofReceipt("T","neighbor" if neighboring else "formal","lean","4.32.1",True,(),"comparator","pinned",True,True,"proof-src"),
        novelty=NoveltyCertificate("2026-08-15",("registered",),("exact","structural"),"fingerprint",rediscovery,("known-parent",) if rediscovery else (),1),
    )

def _ids(record, proposer):
    reviewer="reviewer-independent"
    formal=IndependentReviewReceipt("f-review","formal","formal-procedure",reviewer,proposer,True,True)
    cert=record.novelty; assert cert is not None
    nr=IndependentReviewReceipt("n-review",cert.canonical_fingerprint,"novelty-procedure",reviewer,proposer,True,True)
    novel=NoveltyReviewReceipt(nr,novelty_world_digest(cert,literature_manifest_hash=MANIFEST))
    value=IndependentReviewReceipt("v-review","formal","value-criteria-v1",reviewer,proposer,True,True)
    trust=VerifierTrustReceiptV2("trust","proof-src",checker_identity_digest(record),"checker-manifest",True)
    return AssuranceIdentityBundle(formal,novel,value,trust)

def _stage(record, proposer):
    return classify_math_record_v2(record,proposer_identity_hash=proposer,identities=_ids(record,proposer),literature_manifest_hash=MANIFEST)

def test_same_valid_artifact_has_same_authority_under_symbolic_and_llm_proposers():
    record=_record(); a=_stage(record,"symbolic-enumerator"); b=_stage(record,"llm-proposer")
    assert a.stage is b.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE

def test_neighboring_statement_is_blocked_regardless_of_executor_class():
    record=_record(neighboring=True); a=_stage(record,"symbolic-enumerator"); b=_stage(record,"llm-proposer")
    assert a.stage is b.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE

def test_rediscovery_stage_is_executor_independent():
    record=_record(rediscovery=True); a=_stage(record,"symbolic-enumerator"); b=_stage(record,"llm-proposer")
    assert a.stage is b.stage is MathClaimStage.VERIFIED_REDISCOVERY

def test_self_review_is_blocked_not_relabelled_as_executor_independence():
    record=_record(); proposer="llm-proposer"; ids=_ids(record,proposer)
    bad_formal=replace(ids.formalization_review,reviewer_identity_hash=proposer)
    bad=replace(ids,formalization_review=bad_formal)
    report=classify_math_record_v2(record,proposer_identity_hash=proposer,identities=bad,literature_manifest_hash=MANIFEST)
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN
    assert "formalization_review_not_independent_of_proposer" in report.reasons
