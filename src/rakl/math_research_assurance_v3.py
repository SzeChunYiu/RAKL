"""Transitive receipt-binding successor for Paper V assurance.

V3 preserves every incumbent/v2 rejection and closes reuse attacks discovered
by hostile review after v2: a review receipt must bind the *current* proposer,
formalization review binds the informal/formal pair, novelty review binds the
complete dossier result and literature world, and verifier trust is independently
attested for the exact proposer/proof/checker chain.

Frozen hostile cases:
``research/self_rakl_p4_p6_question_saturation_v3/PAPER_V_TRANSITIVE_RECEIPT_BINDING_FREEZE.json``.
No object here grants theorem, novelty, scientific, value or publication authority.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import hashlib, json
from .math_research_assurance import AssuranceReport, AssuranceVerdict, MathClaimStage, MathResearchRecord, classify_math_record
from .math_research_assurance_v2 import IndependentReviewReceipt, checker_identity_digest


def _digest(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def _need(x: str, name: str) -> str:
    if not x.strip(): raise ValueError(f"{name} cannot be blank")
    return x


def formalization_pair_digest(record: MathResearchRecord) -> str:
    if record.formalization is None: raise ValueError("formalization witness required")
    f=record.formalization
    return _digest({"informal_claim_hash":f.informal_claim_hash,"formal_statement_hash":f.formal_statement_hash})


def novelty_dossier_digest(record: MathResearchRecord, *, literature_manifest_hash: str) -> str:
    _need(literature_manifest_hash,"literature_manifest_hash")
    if record.novelty is None: raise ValueError("novelty certificate required")
    n=record.novelty
    return _digest({
        "corpus_cutoff":n.corpus_cutoff,
        "corpora":sorted(n.corpora),
        "search_routes":sorted(n.search_routes),
        "canonical_fingerprint":n.canonical_fingerprint,
        "equivalent_found":n.equivalent_found,
        "candidate_matches":sorted(n.candidate_matches),
        "coverage_notes":n.coverage_notes,
        "literature_manifest_hash":literature_manifest_hash,
    })


@dataclass(frozen=True)
class NoveltyDossierReviewReceipt:
    review: IndependentReviewReceipt
    dossier_digest: str
    def __post_init__(self): _need(self.dossier_digest,"dossier_digest")
    @property
    def grants_scientific_authority(self): return False

@dataclass(frozen=True)
class VerifierTrustAttestationV3:
    receipt_id: str
    proof_source_hash: str
    checker_identity_digest: str
    verifier_manifest_hash: str
    attestation_procedure_hash: str
    attestor_identity_hash: str
    proposer_identity_hash: str
    verified_before_promotion_decision: bool
    def __post_init__(self):
        for n in ("receipt_id","proof_source_hash","checker_identity_digest","verifier_manifest_hash","attestation_procedure_hash","attestor_identity_hash","proposer_identity_hash"):
            _need(getattr(self,n),n)
    @property
    def independent(self): return self.attestor_identity_hash != self.proposer_identity_hash
    @property
    def grants_scientific_authority(self): return False

@dataclass(frozen=True)
class AssuranceIdentityBundleV3:
    formalization_review: IndependentReviewReceipt | None=None
    novelty_review: NoveltyDossierReviewReceipt | None=None
    value_review: IndependentReviewReceipt | None=None
    verifier_trust: VerifierTrustAttestationV3 | None=None
    @property
    def grants_scientific_authority(self): return False
    @property
    def grants_publication_authority(self): return False


def _review_reasons(receipt: IndependentReviewReceipt | None, *, expected_subject: str, current_proposer: str, axis: str) -> tuple[str,...]:
    if receipt is None: return (f"{axis}_independent_review_receipt_missing",)
    r=[]
    if receipt.subject_hash != expected_subject: r.append(f"{axis}_review_subject_mismatch")
    if receipt.proposer_identity_hash != current_proposer: r.append(f"{axis}_review_proposer_mismatch")
    if receipt.reviewer_identity_hash == current_proposer: r.append(f"{axis}_review_not_independent_of_current_proposer")
    if not receipt.independent: r.append(f"{axis}_review_not_independent_as_recorded")
    if not receipt.accepted: r.append(f"{axis}_review_not_accepted")
    if receipt.frozen_before_promotion_decision is not True: r.append(f"{axis}_review_not_frozen_before_promotion_decision")
    return tuple(r)


def classify_math_record_v3(record: MathResearchRecord, *, proposer_identity_hash: str, identities: AssuranceIdentityBundleV3, literature_manifest_hash: str | None=None) -> AssuranceReport:
    _need(proposer_identity_hash,"proposer_identity_hash")

    if record.formalization is not None:
        reasons=_review_reasons(identities.formalization_review, expected_subject=formalization_pair_digest(record), current_proposer=proposer_identity_hash, axis="formalization")
        if reasons:
            return AssuranceReport(AssuranceVerdict.FAIL if identities.formalization_review is not None else AssuranceVerdict.CANNOT_CHECK, MathClaimStage.FORMALIZED_UNPROVEN, reasons)

    if record.proof is not None:
        trust=identities.verifier_trust
        if trust is None:
            return AssuranceReport(AssuranceVerdict.CANNOT_CHECK,MathClaimStage.BLOCKED_PROOF_ASSURANCE,("verifier_trust_attestation_missing",))
        reasons=[]
        if trust.proposer_identity_hash != proposer_identity_hash: reasons.append("verifier_trust_proposer_mismatch")
        if trust.attestor_identity_hash == proposer_identity_hash or not trust.independent: reasons.append("verifier_trust_attestor_not_independent")
        if trust.proof_source_hash != (record.proof.source_hash or ""): reasons.append("verifier_trust_proof_source_mismatch")
        if trust.checker_identity_digest != checker_identity_digest(record): reasons.append("verifier_trust_checker_identity_mismatch")
        if trust.verified_before_promotion_decision is not True: reasons.append("verifier_trust_not_frozen_before_promotion_decision")
        if reasons: return AssuranceReport(AssuranceVerdict.FAIL,MathClaimStage.BLOCKED_PROOF_ASSURANCE,tuple(reasons))

    if record.novelty is not None:
        if literature_manifest_hash is None or not literature_manifest_hash.strip():
            return AssuranceReport(AssuranceVerdict.CANNOT_CHECK,MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED,("novelty_literature_manifest_missing",))
        nr=identities.novelty_review
        if nr is None:
            return AssuranceReport(AssuranceVerdict.CANNOT_CHECK,MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED,("novelty_independent_review_receipt_missing",))
        expected=novelty_dossier_digest(record,literature_manifest_hash=literature_manifest_hash)
        reasons=list(_review_reasons(nr.review,expected_subject=expected,current_proposer=proposer_identity_hash,axis="novelty"))
        if nr.dossier_digest != expected: reasons.append("novelty_review_dossier_mismatch")
        if reasons: return AssuranceReport(AssuranceVerdict.CANNOT_CHECK,MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED,tuple(reasons))

    # Disable the incumbent boolean final-review switch until exact value review passes.
    base=classify_math_record(replace(record,external_mathematical_review=False))
    if base.stage not in {MathClaimStage.BOUNDED_NOVEL_RESULT,MathClaimStage.NEW_MATHEMATICS_CANDIDATE}:
        return base

    if record.interestingness_screened:
        expected_value=record.formalization.formal_statement_hash if record.formalization else ""
        reasons=_review_reasons(identities.value_review,expected_subject=expected_value,current_proposer=proposer_identity_hash,axis="value")
        if reasons:
            return AssuranceReport(AssuranceVerdict.PASS,MathClaimStage.BOUNDED_NOVEL_RESULT,base.reasons+reasons)
        promoted=classify_math_record(replace(record,external_mathematical_review=True))
        if promoted.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE:
            return AssuranceReport(promoted.verdict,promoted.stage,promoted.reasons+("v3_transitive_exact_receipt_chain_passed",))
    return base
