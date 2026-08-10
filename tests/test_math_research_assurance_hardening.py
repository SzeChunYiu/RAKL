from __future__ import annotations

from rakl.math_research_assurance import (
    FormalizationWitness,
    MathClaimStage,
    MathResearchRecord,
    NoveltyCertificate,
    ProofReceipt,
    classify_math_record,
)


def _formalization() -> FormalizationWitness:
    return FormalizationWitness(
        informal_claim_hash="i",
        formal_statement_hash="f",
        accepted=True,
        roundtrip_checked=True,
        boundary_cases_checked=True,
        independent_reviewers=1,
    )


def _proof(**overrides) -> ProofReceipt:
    payload = dict(
        theorem_id="T",
        theorem_statement_hash="f",
        checker="lean",
        checker_version="4.32.1",
        accepted=True,
        axioms=(),
        independent_checker="comparator",
        independent_checker_version="pinned",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash="proof-hash",
    )
    payload.update(overrides)
    return ProofReceipt(**payload)


def test_missing_proof_source_identity_blocks_promotion() -> None:
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=_formalization(),
            proof=_proof(source_hash=None),
        )
    )
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "proof_source_hash_missing" in report.reasons


def test_missing_checker_version_blocks_promotion() -> None:
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=_formalization(),
            proof=_proof(checker_version=""),
        )
    )
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "primary_checker_version_missing" in report.reasons


def test_missing_independent_checker_version_blocks_strict_promotion() -> None:
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=_formalization(),
            proof=_proof(independent_checker_version=None),
        )
    )
    assert report.stage is MathClaimStage.BLOCKED_PROOF_ASSURANCE
    assert "independent_checker_version_missing" in report.reasons


def test_equivalent_prior_art_flag_without_identified_match_is_not_accepted() -> None:
    report = classify_math_record(
        MathResearchRecord(
            claim_id="C",
            formalization=_formalization(),
            proof=_proof(),
            novelty=NoveltyCertificate(
                corpus_cutoff="2026-08-10",
                corpora=("registered",),
                search_routes=("structural",),
                canonical_fingerprint="fp",
                equivalent_found=True,
                candidate_matches=(),
                independent_reviewers=1,
            ),
        )
    )
    assert report.stage is MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED
    assert "prior_equivalent_flag_has_no_candidate_match" in report.reasons
