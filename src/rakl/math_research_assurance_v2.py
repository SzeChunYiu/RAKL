"""Identity-bound successor to :mod:`rakl.math_research_assurance`.

The incumbent Paper-V state machine already separates specification, proof,
novelty and research value, but several review coordinates are represented as
counts/booleans.  V2 is a conservative wrapper: it may narrow an incumbent
promotion, never widen one.  Independent review becomes an exact-subject receipt
bound to reviewer/proposer identity and procedure; novelty additionally binds a
literature-world manifest; verifier trust binds the exact proof source and
checker manifest.

The frozen hostile cases live in
``research/self_rakl_p4_p6_question_saturation_v3/PAPER_V_REVIEW_IDENTITY_FREEZE.json``
and predate this implementation.  No object here grants scientific, theorem,
novelty, value, or publication authority by itself.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import hashlib, json
from .math_research_assurance import AssuranceReport, AssuranceVerdict, MathClaimStage, MathResearchRecord, NoveltyCertificate, classify_math_record


def _digest(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _need(value: str, name: str) -> str:
    if not value.strip(): raise ValueError(f"{name} cannot be blank")
    return value

@dataclass(frozen=True)
class IndependentReviewReceipt:
    review_id: str
    subject_hash: str
    procedure_hash: str
    reviewer_identity_hash: str
    proposer_identity_hash: str
    accepted: bool
    frozen_before_promotion_decision: bool
    def __post_init__(self):
        for n in ("review_id","subject_hash","procedure_hash","reviewer_identity_hash","proposer_identity_hash"):
            _need(getattr(self,n),n)
    @property
    def independent(self) -> bool: return self.reviewer_identity_hash != self.proposer_identity_hash
    @property
    def grants_scientific_authority(self) -> bool: return False

@dataclass(frozen=True)
class NoveltyReviewReceipt:
    review: IndependentReviewReceipt
    novelty_world_digest: str
    def __post_init__(self): _need(self.novelty_world_digest,"novelty_world_digest")
    @property
    def grants_scientific_authority(self) -> bool: return False

@dataclass(frozen=True)
class VerifierTrustReceiptV2:
    receipt_id: str
    proof_source_hash: str
    checker_identity_digest: str
    verifier_manifest_hash: str
    verified_before_promotion_decision: bool
    def __post_init__(self):
        for n in ("receipt_id","proof_source_hash","checker_identity_digest","verifier_manifest_hash"):
            _need(getattr(self,n),n)
    @property
    def grants_scientific_authority(self) -> bool: return False

@dataclass(frozen=True)
class AssuranceIdentityBundle:
    formalization_review: IndependentReviewReceipt | None = None
    novelty_review: NoveltyReviewReceipt | None = None
    value_review: IndependentReviewReceipt | None = None
    verifier_trust: VerifierTrustReceiptV2 | None = None
    @property
    def grants_scientific_authority(self) -> bool: return False
    @property
    def grants_publication_authority(self) -> bool: return False


def checker_identity_digest(record: MathResearchRecord) -> str:
    if record.proof is None: raise ValueError("proof receipt required")
    p=record.proof
    return _digest({"checker":p.checker,"checker_version":p.checker_version,"independent_checker":p.independent_checker,"independent_checker_version":p.independent_checker_version})


def novelty_world_digest(certificate: NoveltyCertificate, *, literature_manifest_hash: str) -> str:
    _need(literature_manifest_hash,"literature_manifest_hash")
    return _digest({"corpus_cutoff":certificate.corpus_cutoff,"corpora":sorted(certificate.corpora),"search_routes":sorted(certificate.search_routes),"canonical_fingerprint":certificate.canonical_fingerprint,"literature_manifest_hash":literature_manifest_hash})


def _audit_review(receipt: IndependentReviewReceipt | None, *, expected_subject_hash: str, axis: str) -> tuple[str, ...]:
    if receipt is None: return (f"{axis}_independent_review_receipt_missing",)
    reasons=[]
    if receipt.subject_hash != expected_subject_hash: reasons.append(f"{axis}_review_subject_mismatch")
    if not receipt.independent: reasons.append(f"{axis}_review_not_independent_of_proposer")
    if not receipt.accepted: reasons.append(f"{axis}_review_not_accepted")
    if receipt.frozen_before_promotion_decision is not True: reasons.append(f"{axis}_review_not_frozen_before_promotion_decision")
    return tuple(reasons)


def classify_math_record_v2(record: MathResearchRecord, *, proposer_identity_hash: str, identities: AssuranceIdentityBundle, literature_manifest_hash: str | None = None) -> AssuranceReport:
    """Apply exact-subject independent-review identity before incumbent promotion."""
    _need(proposer_identity_hash,"proposer_identity_hash")

    if record.formalization is not None:
        reasons=_audit_review(identities.formalization_review, expected_subject_hash=record.formalization.formal_statement_hash, axis="formalization")
        if reasons:
            return AssuranceReport(AssuranceVerdict.FAIL if identities.formalization_review is not None else AssuranceVerdict.CANNOT_CHECK, MathClaimStage.FORMALIZED_UNPROVEN, reasons)

    if record.proof is not None:
        trust=identities.verifier_trust
        if trust is None:
            return AssuranceReport(AssuranceVerdict.CANNOT_CHECK, MathClaimStage.BLOCKED_PROOF_ASSURANCE, ("verifier_trust_receipt_missing",))
        proof_source=record.proof.source_hash or ""
        reasons=[]
        if trust.proof_source_hash != proof_source: reasons.append("verifier_trust_proof_source_mismatch")
        if trust.checker_identity_digest != checker_identity_digest(record): reasons.append("verifier_trust_checker_identity_mismatch")
        if trust.verified_before_promotion_decision is not True: reasons.append("verifier_trust_not_frozen_before_promotion_decision")
        if reasons: return AssuranceReport(AssuranceVerdict.FAIL, MathClaimStage.BLOCKED_PROOF_ASSURANCE, tuple(reasons))

    if record.novelty is not None:
        if literature_manifest_hash is None or not literature_manifest_hash.strip():
            return AssuranceReport(AssuranceVerdict.CANNOT_CHECK, MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED, ("novelty_literature_manifest_missing",))
        nr=identities.novelty_review
        if nr is None:
            return AssuranceReport(AssuranceVerdict.CANNOT_CHECK, MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED, ("novelty_independent_review_receipt_missing",))
        review_reasons=_audit_review(nr.review, expected_subject_hash=record.novelty.canonical_fingerprint, axis="novelty")
        world=novelty_world_digest(record.novelty,literature_manifest_hash=literature_manifest_hash)
        reasons=list(review_reasons)
        if nr.novelty_world_digest != world: reasons.append("novelty_review_world_mismatch")
        if reasons: return AssuranceReport(AssuranceVerdict.CANNOT_CHECK, MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED, tuple(reasons))

    # Never let the incumbent boolean external-review field promote by itself.
    incumbent_input=replace(record, external_mathematical_review=False)
    base=classify_math_record(incumbent_input)
    if base.stage not in {MathClaimStage.BOUNDED_NOVEL_RESULT, MathClaimStage.NEW_MATHEMATICS_CANDIDATE}:
        return base

    # Research value remains a separate coordinate.  Missing/failed value review
    # does not demote theorem truth or bounded novelty; it only blocks the final
    # new-mathematics promotion.
    if record.interestingness_screened:
        expected=record.formalization.formal_statement_hash if record.formalization else ""
        reasons=_audit_review(identities.value_review, expected_subject_hash=expected, axis="value")
        if reasons:
            return AssuranceReport(AssuranceVerdict.PASS, MathClaimStage.BOUNDED_NOVEL_RESULT, base.reasons + reasons)
        assert identities.value_review is not None
        if not identities.value_review.procedure_hash.strip():
            return AssuranceReport(AssuranceVerdict.PASS, MathClaimStage.BOUNDED_NOVEL_RESULT, base.reasons + ("value_review_criteria_hash_missing",))
        promoted=classify_math_record(replace(record, external_mathematical_review=True))
        if promoted.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE:
            return AssuranceReport(promoted.verdict, promoted.stage, promoted.reasons + ("v2_exact_subject_independent_review_identity_passed",))
    return base
