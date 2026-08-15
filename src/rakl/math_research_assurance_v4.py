"""Final local content-identity wrapper for Paper V assurance.

V4 narrows v3 by requiring every load-bearing field represented as an identity
hash to actually be a lowercase SHA-256 content digest.  Display names remain
outside the authority path.  The mapping from an external actor/artifact to the
manifest bytes that are hashed is an explicit provenance trust-root assumption;
this wrapper does not self-certify that external fact.

Frozen hostile cases:
``research/self_rakl_p4_p6_question_saturation_v4/PAPER_V_CONTENT_IDENTITY_FREEZE.json``.
"""
from __future__ import annotations
import re
from .math_research_assurance import AssuranceReport, AssuranceVerdict, MathClaimStage, MathResearchRecord
from .math_research_assurance_v2 import IndependentReviewReceipt
from .math_research_assurance_v3 import AssuranceIdentityBundleV3, NoveltyDossierReviewReceipt, VerifierTrustAttestationV3, classify_math_record_v3

_HEX64=re.compile(r"^[0-9a-f]{64}$")

def _sha(value: str | None, name: str) -> str:
    if value is None or not _HEX64.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 content digest")
    return value

def _audit_review_content_identity(r: IndependentReviewReceipt | None, axis: str) -> None:
    if r is None: return
    _sha(r.subject_hash,f"{axis}.subject_hash")
    _sha(r.procedure_hash,f"{axis}.procedure_hash")
    _sha(r.reviewer_identity_hash,f"{axis}.reviewer_identity_hash")
    _sha(r.proposer_identity_hash,f"{axis}.proposer_identity_hash")

def classify_math_record_v4(record: MathResearchRecord, *, proposer_identity_hash: str, identities: AssuranceIdentityBundleV3, literature_manifest_hash: str | None=None) -> AssuranceReport:
    """Reject label-like identities before the v3 transitive receipt chain runs."""
    _sha(proposer_identity_hash,"proposer_identity_hash")
    if record.formalization is not None:
        _sha(record.formalization.informal_claim_hash,"formalization.informal_claim_hash")
        _sha(record.formalization.formal_statement_hash,"formalization.formal_statement_hash")
    if record.proof is not None:
        _sha(record.proof.theorem_statement_hash,"proof.theorem_statement_hash")
        _sha(record.proof.source_hash,"proof.source_hash")
    if record.novelty is not None:
        _sha(record.novelty.canonical_fingerprint,"novelty.canonical_fingerprint")
        _sha(literature_manifest_hash,"literature_manifest_hash")

    _audit_review_content_identity(identities.formalization_review,"formalization_review")
    _audit_review_content_identity(identities.value_review,"value_review")
    if identities.novelty_review is not None:
        _audit_review_content_identity(identities.novelty_review.review,"novelty_review")
        _sha(identities.novelty_review.dossier_digest,"novelty_review.dossier_digest")
    if identities.verifier_trust is not None:
        t=identities.verifier_trust
        _sha(t.proof_source_hash,"verifier_trust.proof_source_hash")
        _sha(t.checker_identity_digest,"verifier_trust.checker_identity_digest")
        _sha(t.verifier_manifest_hash,"verifier_trust.verifier_manifest_hash")
        _sha(t.attestation_procedure_hash,"verifier_trust.attestation_procedure_hash")
        _sha(t.attestor_identity_hash,"verifier_trust.attestor_identity_hash")
        _sha(t.proposer_identity_hash,"verifier_trust.proposer_identity_hash")

    return classify_math_record_v3(record,proposer_identity_hash=proposer_identity_hash,identities=identities,literature_manifest_hash=literature_manifest_hash)

__all__=["classify_math_record_v4"]
