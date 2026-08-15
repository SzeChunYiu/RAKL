from __future__ import annotations
from dataclasses import replace
import hashlib
import pytest
from rakl.math_research_assurance import FormalizationWitness, MathClaimStage, MathResearchRecord, NoveltyCertificate, ProofReceipt
from rakl.math_research_assurance_v2 import IndependentReviewReceipt, checker_identity_digest
from rakl.math_research_assurance_v3 import AssuranceIdentityBundleV3, NoveltyDossierReviewReceipt, VerifierTrustAttestationV3, formalization_pair_digest, novelty_dossier_digest
from rakl.math_research_assurance_v4 import classify_math_record_v4

def h(x): return hashlib.sha256(x.encode()).hexdigest()
PROP=h("proposer"); REVIEW=h("reviewer"); ATTEST=h("attestor"); LIT=h("literature-manifest")

def _record():
    informal=h("informal-claim"); formal=h("formal-statement"); proof=h("proof-source"); fp=h("theorem-fingerprint")
    return MathResearchRecord(claim_id="C",interestingness_screened=True,external_mathematical_review=True,
        formalization=FormalizationWitness(informal,formal,True,True,True,1),
        proof=ProofReceipt("T",formal,"lean","4.32.1",True,(),"comparator","pinned",True,True,proof),
        novelty=NoveltyCertificate("2026-08-15",("registered",),("exact","structural"),fp,False,(),1,("coverage",)))

def _review(subject, axis, proposer=PROP, reviewer=REVIEW, procedure=None):
    return IndependentReviewReceipt(h(axis+"-review"),subject,procedure or h(axis+"-procedure"),reviewer,proposer,True,True)

def _bundle(r, *, reviewer=REVIEW, verifier_manifest=None, trust_proposer=PROP):
    fd=formalization_pair_digest(r); nd=novelty_dossier_digest(r,literature_manifest_hash=LIT)
    assert r.formalization is not None and r.proof is not None
    return AssuranceIdentityBundleV3(
        _review(fd,"formal",reviewer=reviewer),
        NoveltyDossierReviewReceipt(_review(nd,"novelty",reviewer=reviewer),nd),
        _review(r.formalization.formal_statement_hash,"value",reviewer=reviewer),
        VerifierTrustAttestationV3(h("trust-receipt"),r.proof.source_hash or "",checker_identity_digest(r),verifier_manifest or h("verifier-manifest"),h("attest-procedure"),ATTEST,trust_proposer,True))

def test_exact_content_addressed_chain_may_enter_existing_gate():
    r=_record(); report=classify_math_record_v4(r,proposer_identity_hash=PROP,identities=_bundle(r),literature_manifest_hash=LIT)
    assert report.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE

def test_human_proposer_label_is_rejected():
    r=_record()
    with pytest.raises(ValueError,match="proposer_identity_hash.*SHA-256"):
        classify_math_record_v4(r,proposer_identity_hash="alice",identities=_bundle(r),literature_manifest_hash=LIT)

def test_human_reviewer_label_is_rejected():
    r=_record(); ids=_bundle(r)
    bad=replace(ids,formalization_review=replace(ids.formalization_review,reviewer_identity_hash="reviewer-B"))
    with pytest.raises(ValueError,match="reviewer_identity_hash.*SHA-256"):
        classify_math_record_v4(r,proposer_identity_hash=PROP,identities=bad,literature_manifest_hash=LIT)

def test_human_review_procedure_label_is_rejected():
    r=_record(); ids=_bundle(r)
    bad=replace(ids,value_review=replace(ids.value_review,procedure_hash="value-criteria-v1"))
    with pytest.raises(ValueError,match="procedure_hash.*SHA-256"):
        classify_math_record_v4(r,proposer_identity_hash=PROP,identities=bad,literature_manifest_hash=LIT)

def test_human_literature_manifest_label_is_rejected():
    r=_record()
    with pytest.raises(ValueError,match="literature_manifest_hash.*SHA-256"):
        classify_math_record_v4(r,proposer_identity_hash=PROP,identities=_bundle(r),literature_manifest_hash="latest-literature")

def test_human_verifier_manifest_label_is_rejected():
    r=_record(); ids=_bundle(r,verifier_manifest="lean-current")
    with pytest.raises(ValueError,match="verifier_manifest_hash.*SHA-256"):
        classify_math_record_v4(r,proposer_identity_hash=PROP,identities=ids,literature_manifest_hash=LIT)
