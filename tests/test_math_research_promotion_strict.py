from __future__ import annotations

import hashlib

from rakl.math_research_assurance import FormalizationWitness, MathClaimStage, MathResearchRecord, NoveltyCertificate, ProofReceipt, classify_math_record
from rakl.math_research_assurance_v2 import IndependentReviewReceipt, checker_identity_digest
from rakl.math_research_assurance_v3 import AssuranceIdentityBundleV3, NoveltyDossierReviewReceipt, VerifierTrustAttestationV3, formalization_pair_digest, novelty_dossier_digest
from rakl.math_research_promotion_strict import strict_math_candidate
from rakl.proof_dag import ProofDAG, ProofEdge, ProofNode, ProofNodeKind, ProofRelation, add_edge
from rakl.proof_dag_v2 import DependencyManifestReceipt


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


PROP = h("proposer")
REVIEWER = h("reviewer")
ATTESTOR = h("attestor")
LITERATURE = h("literature-manifest")
FORMAL = h("formal-statement")
PROOF_SOURCE = h("proof-source")
DEPENDENCY = h("lemma-A")


def record() -> MathResearchRecord:
    return MathResearchRecord(
        claim_id="strict-candidate",
        interestingness_screened=True,
        external_mathematical_review=True,
        formalization=FormalizationWitness(h("informal-claim"), FORMAL, True, True, True, 1),
        proof=ProofReceipt("T", FORMAL, "lean", "4.32.1", True, (), "comparator", "pinned", True, True, PROOF_SOURCE),
        novelty=NoveltyCertificate("2026-08-15", ("registered",), ("exact", "structural"), h("theorem-fingerprint"), False, (), 1, ("coverage",)),
    )


def identities(r: MathResearchRecord) -> AssuranceIdentityBundleV3:
    formal_subject = formalization_pair_digest(r)
    dossier = novelty_dossier_digest(r, literature_manifest_hash=LITERATURE)
    assert r.formalization is not None and r.proof is not None
    return AssuranceIdentityBundleV3(
        formalization_review=IndependentReviewReceipt(h("formal-review"), formal_subject, h("formal-procedure"), REVIEWER, PROP, True, True),
        novelty_review=NoveltyDossierReviewReceipt(
            IndependentReviewReceipt(h("novelty-review"), dossier, h("novelty-procedure"), REVIEWER, PROP, True, True),
            dossier,
        ),
        value_review=IndependentReviewReceipt(h("value-review"), r.formalization.formal_statement_hash, h("value-procedure"), REVIEWER, PROP, True, True),
        verifier_trust=VerifierTrustAttestationV3(
            h("trust-receipt"),
            r.proof.source_hash or "",
            checker_identity_digest(r),
            h("verifier-manifest"),
            h("attestation-procedure"),
            ATTESTOR,
            PROP,
            True,
        ),
    )


def dag(include_dependency: bool = True) -> ProofDAG:
    nodes = (
        ProofNode("A", ProofNodeKind.LEMMA, DEPENDENCY),
        ProofNode("T", ProofNodeKind.THEOREM, FORMAL),
    )
    result = ProofDAG(nodes=nodes)
    if include_dependency:
        result = add_edge(result, ProofEdge("A", "T", ProofRelation.IMPLIES))
    return result


def manifest(*, dependencies=(DEPENDENCY,)) -> DependencyManifestReceipt:
    return DependencyManifestReceipt(
        h("dependency-manifest"),
        PROOF_SOURCE,
        FORMAL,
        dependencies,
        h("dependency-extractor"),
        True,
    )


def test_historical_classifier_positive_is_not_current_strict_eligibility_by_itself() -> None:
    r = record()
    assert classify_math_record(r).stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    decision = strict_math_candidate(
        r,
        proposer_identity_hash="alice",
        identities=identities(r),
        literature_manifest_hash=LITERATURE,
        dag=dag(),
        node_id="T",
        dependency_manifest=manifest(),
    )
    assert decision.eligible_new_mathematics_candidate is False
    assert any("strict_content_identity_failed" in reason for reason in decision.reasons)


def test_dependency_manifest_bypass_is_blocked_even_when_assurance_receipts_are_good() -> None:
    r = record()
    decision = strict_math_candidate(
        r,
        proposer_identity_hash=PROP,
        identities=identities(r),
        literature_manifest_hash=LITERATURE,
        dag=dag(include_dependency=False),
        node_id="T",
        dependency_manifest=manifest(),
    )
    assert decision.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert decision.checkpoint_verified is False
    assert decision.eligible_new_mathematics_candidate is False


def test_full_content_addressed_assurance_and_exact_dependency_path_is_candidate_eligible_only() -> None:
    r = record()
    decision = strict_math_candidate(
        r,
        proposer_identity_hash=PROP,
        identities=identities(r),
        literature_manifest_hash=LITERATURE,
        dag=dag(),
        node_id="T",
        dependency_manifest=manifest(),
    )
    assert decision.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    assert decision.checkpoint_verified is True
    assert decision.eligible_new_mathematics_candidate is True
    assert decision.grants_theorem_authority is False
    assert decision.grants_novelty_authority is False
    assert decision.grants_scientific_authority is False
    assert decision.grants_publication_authority is False
