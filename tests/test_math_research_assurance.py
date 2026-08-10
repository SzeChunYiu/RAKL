from rakl.math_research_assurance import (
    FormalizationWitness,
    MathClaimStage,
    MathResearchRecord,
    NoveltyCertificate,
    ProofReceipt,
    classify_math_record,
    update_novelty_certificate,
)


def aligned_statement() -> FormalizationWitness:
    return FormalizationWitness(
        informal_claim_hash="informal-v1",
        formal_statement_hash="formal-v1",
        accepted=True,
        roundtrip_checked=True,
        boundary_cases_checked=True,
        independent_reviewers=1,
    )


def trusted_proof(*, axioms=("propext", "Classical.choice", "Quot.sound")) -> ProofReceipt:
    return ProofReceipt(
        theorem_id="T",
        theorem_statement_hash="formal-v1",
        checker="lean",
        checker_version="4.32.1",
        accepted=True,
        axioms=axioms,
        independent_checker="comparator",
        independent_checker_version="pinned",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash="proof-source-v1",
    )


def bounded_novelty(*, equivalent_found=False) -> NoveltyCertificate:
    return NoveltyCertificate(
        corpus_cutoff="2026-08-10",
        corpora=("MathSciNet", "zbMATH", "arXiv", "journal-search"),
        search_routes=("exact", "notation-normalized", "structural", "citation-neighborhood"),
        canonical_fingerprint="canonical-theorem-v1",
        equivalent_found=equivalent_found,
        candidate_matches=("possible-prior-art",) if equivalent_found else (),
        independent_reviewers=1,
    )


def test_computation_never_promotes_to_theorem():
    report = classify_math_record(
        MathResearchRecord(claim_id="C", computational_support=True)
    )
    assert report.stage is MathClaimStage.COMPUTATIONALLY_SUPPORTED


def test_formal_statement_without_proof_stays_unproven():
    report = classify_math_record(
        MathResearchRecord(claim_id="C", formalization=aligned_statement())
    )
    assert report.stage is MathClaimStage.FORMALIZED_UNPROVEN


def test_sorry_dependency_blocks_proof_promotion():
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=aligned_statement(),
            proof=trusted_proof(axioms=("sorryAx",)),
        )
    )
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "proof_depends_on_sorryAx" in report.reasons


def test_native_or_compiler_trust_is_blocked_by_strict_profile():
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=aligned_statement(),
            proof=trusted_proof(axioms=("Lean.trustCompiler",)),
        )
    )
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE


def test_verified_proof_does_not_mint_novelty():
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=aligned_statement(),
            proof=trusted_proof(),
        )
    )
    assert report.stage is MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED


def test_prior_art_changes_novelty_not_truth():
    base = MathResearchRecord(
        claim_id="C",
        formalization=aligned_statement(),
        proof=trusted_proof(),
        novelty=bounded_novelty(equivalent_found=False),
    )
    assert classify_math_record(base).stage is MathClaimStage.BOUNDED_NOVEL_RESULT

    updated = update_novelty_certificate(
        base, bounded_novelty(equivalent_found=True)
    )
    report = classify_math_record(updated)
    assert report.stage is MathClaimStage.VERIFIED_REDISCOVERY
    assert updated.proof == base.proof


def test_new_math_candidate_requires_truth_novelty_and_research_value_gates():
    record = MathResearchRecord(
        claim_id="C",
        formalization=aligned_statement(),
        proof=trusted_proof(),
        novelty=bounded_novelty(equivalent_found=False),
        interestingness_screened=True,
        external_mathematical_review=True,
    )
    report = classify_math_record(record)
    assert report.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
