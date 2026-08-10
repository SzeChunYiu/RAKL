from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Tuple


class AssuranceVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


class MathClaimStage(str, Enum):
    CONJECTURE = "CONJECTURE"
    COMPUTATIONALLY_SUPPORTED = "COMPUTATIONALLY_SUPPORTED"
    FORMALIZED_UNPROVEN = "FORMALIZED_UNPROVEN"
    BLOCKED_PROOF_ASSURANCE = "BLOCKED_PROOF_ASSURANCE"
    MACHINE_PROVEN = "MACHINE_PROVEN"
    VERIFIED_REDISCOVERY = "VERIFIED_REDISCOVERY"
    MACHINE_PROVEN_NOVELTY_UNRESOLVED = "MACHINE_PROVEN_NOVELTY_UNRESOLVED"
    BOUNDED_NOVEL_RESULT = "BOUNDED_NOVEL_RESULT"
    NEW_MATHEMATICS_CANDIDATE = "NEW_MATHEMATICS_CANDIDATE"


LEAN_BUILTIN_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})


@dataclass(frozen=True)
class FormalizationWitness:
    """Evidence that the formal statement matches the intended informal claim.

    Formal proof checking establishes a theorem about the formal statement, not by
    itself that the statement is the one the researcher intended.  This witness is
    therefore a separate gate.
    """

    informal_claim_hash: str
    formal_statement_hash: str
    accepted: bool
    roundtrip_checked: bool = False
    boundary_cases_checked: bool = False
    independent_reviewers: int = 0
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ProofReceipt:
    theorem_id: str
    theorem_statement_hash: str
    checker: str
    checker_version: str
    accepted: bool
    axioms: Tuple[str, ...] = ()
    independent_checker: str | None = None
    independent_checker_version: str | None = None
    independent_accepted: bool = False
    isolated_recheck: bool = False
    source_hash: str | None = None


@dataclass(frozen=True)
class NoveltyCertificate:
    """A bounded, defeasible novelty certificate relative to a corpus snapshot."""

    corpus_cutoff: str
    corpora: Tuple[str, ...]
    search_routes: Tuple[str, ...]
    canonical_fingerprint: str
    equivalent_found: bool
    candidate_matches: Tuple[str, ...] = ()
    independent_reviewers: int = 0
    coverage_notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MathResearchRecord:
    claim_id: str
    computational_support: bool = False
    formalization: FormalizationWitness | None = None
    proof: ProofReceipt | None = None
    novelty: NoveltyCertificate | None = None
    interestingness_screened: bool = False
    external_mathematical_review: bool = False


@dataclass(frozen=True)
class AssuranceReport:
    verdict: AssuranceVerdict
    stage: MathClaimStage
    reasons: Tuple[str, ...]


def audit_formalization(witness: FormalizationWitness | None) -> AssuranceReport:
    if witness is None:
        return AssuranceReport(
            AssuranceVerdict.CANNOT_CHECK,
            MathClaimStage.CONJECTURE,
            ("formal_statement_not_bound_to_informal_claim",),
        )
    reasons: list[str] = []
    if not witness.accepted:
        reasons.append("formalization_not_accepted")
    if not witness.roundtrip_checked:
        reasons.append("formalization_roundtrip_not_checked")
    if not witness.boundary_cases_checked:
        reasons.append("formalization_boundary_cases_not_checked")
    if witness.independent_reviewers < 1:
        reasons.append("formalization_has_no_independent_reviewer")
    if reasons:
        return AssuranceReport(
            AssuranceVerdict.FAIL,
            MathClaimStage.FORMALIZED_UNPROVEN,
            tuple(reasons),
        )
    return AssuranceReport(
        AssuranceVerdict.PASS,
        MathClaimStage.FORMALIZED_UNPROVEN,
        ("formalization_alignment_witness_passed",),
    )


def _is_native_or_compiler_axiom(name: str) -> bool:
    return (
        name == "Lean.trustCompiler"
        or "native_decide" in name
        or "bv_decide" in name
        or name.startswith("Lean.ofReduce")
    )


def audit_proof_receipt(
    receipt: ProofReceipt | None,
    *,
    allow_builtin_axioms: bool = True,
    allow_native_or_compiler_trust: bool = False,
    require_independent_recheck: bool = True,
) -> AssuranceReport:
    if receipt is None:
        return AssuranceReport(
            AssuranceVerdict.CANNOT_CHECK,
            MathClaimStage.FORMALIZED_UNPROVEN,
            ("proof_receipt_missing",),
        )
    reasons: list[str] = []
    if not receipt.accepted:
        reasons.append("primary_checker_rejected_or_incomplete")
    for axiom in receipt.axioms:
        if axiom == "sorryAx":
            reasons.append("proof_depends_on_sorryAx")
        elif _is_native_or_compiler_axiom(axiom) and not allow_native_or_compiler_trust:
            reasons.append(f"proof_depends_on_non_kernel_trust:{axiom}")
        elif axiom not in LEAN_BUILTIN_AXIOMS and not _is_native_or_compiler_axiom(axiom):
            reasons.append(f"proof_depends_on_custom_axiom:{axiom}")
        elif axiom in LEAN_BUILTIN_AXIOMS and not allow_builtin_axioms:
            reasons.append(f"builtin_axiom_disallowed_by_profile:{axiom}")
    if require_independent_recheck:
        if not receipt.independent_checker:
            reasons.append("independent_checker_missing")
        if not receipt.independent_accepted:
            reasons.append("independent_checker_did_not_accept")
        if not receipt.isolated_recheck:
            reasons.append("independent_recheck_not_isolated")
    if reasons:
        return AssuranceReport(
            AssuranceVerdict.FAIL,
            MathClaimStage.BLOCKED_PROOF_ASSURANCE,
            tuple(reasons),
        )
    return AssuranceReport(
        AssuranceVerdict.PASS,
        MathClaimStage.MACHINE_PROVEN,
        ("proof_receipt_and_trust_audit_passed",),
    )


def audit_novelty(certificate: NoveltyCertificate | None) -> AssuranceReport:
    if certificate is None:
        return AssuranceReport(
            AssuranceVerdict.CANNOT_CHECK,
            MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED,
            ("novelty_certificate_missing",),
        )
    if certificate.equivalent_found:
        return AssuranceReport(
            AssuranceVerdict.FAIL,
            MathClaimStage.VERIFIED_REDISCOVERY,
            ("prior_equivalent_result_found",),
        )
    reasons: list[str] = []
    if not certificate.corpus_cutoff:
        reasons.append("novelty_corpus_cutoff_missing")
    if not certificate.corpora:
        reasons.append("novelty_corpora_not_registered")
    if not certificate.search_routes:
        reasons.append("novelty_search_routes_not_registered")
    if not certificate.canonical_fingerprint:
        reasons.append("canonical_theorem_fingerprint_missing")
    if certificate.independent_reviewers < 1:
        reasons.append("novelty_has_no_independent_reviewer")
    if reasons:
        return AssuranceReport(
            AssuranceVerdict.CANNOT_CHECK,
            MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED,
            tuple(reasons),
        )
    return AssuranceReport(
        AssuranceVerdict.PASS,
        MathClaimStage.BOUNDED_NOVEL_RESULT,
        ("no_equivalent_found_within_registered_novelty_world",),
    )


def classify_math_record(record: MathResearchRecord) -> AssuranceReport:
    """Apply non-compensatory promotion gates to a mathematical research claim.

    Computation, model confidence, or absence of counterexamples can never bypass
    formalization alignment or proof assurance.  Likewise, proof validity cannot
    silently mint novelty authority.
    """

    if record.formalization is None:
        return AssuranceReport(
            AssuranceVerdict.CANNOT_CHECK,
            MathClaimStage.COMPUTATIONALLY_SUPPORTED
            if record.computational_support
            else MathClaimStage.CONJECTURE,
            (
                "computational_support_is_not_proof"
                if record.computational_support
                else "claim_is_conjectural",
            ),
        )

    formalization = audit_formalization(record.formalization)
    if formalization.verdict is not AssuranceVerdict.PASS:
        return formalization

    if record.proof is None:
        return AssuranceReport(
            AssuranceVerdict.CANNOT_CHECK,
            MathClaimStage.FORMALIZED_UNPROVEN,
            ("formal_statement_exists_but_no_trusted_proof_receipt",),
        )
    if record.proof.theorem_statement_hash != record.formalization.formal_statement_hash:
        return AssuranceReport(
            AssuranceVerdict.FAIL,
            MathClaimStage.BLOCKED_PROOF_ASSURANCE,
            ("proof_receipt_not_bound_to_formalization_hash",),
        )

    proof = audit_proof_receipt(record.proof)
    if proof.verdict is not AssuranceVerdict.PASS:
        return proof

    novelty = audit_novelty(record.novelty)
    if novelty.stage is MathClaimStage.VERIFIED_REDISCOVERY:
        return novelty
    if novelty.verdict is not AssuranceVerdict.PASS:
        return AssuranceReport(
            AssuranceVerdict.PASS,
            MathClaimStage.MACHINE_PROVEN_NOVELTY_UNRESOLVED,
            novelty.reasons,
        )

    if record.interestingness_screened and record.external_mathematical_review:
        return AssuranceReport(
            AssuranceVerdict.PASS,
            MathClaimStage.NEW_MATHEMATICS_CANDIDATE,
            (
                "proof_verified",
                "bounded_novelty_screen_passed",
                "interestingness_and_external_review_passed",
            ),
        )
    return novelty


def update_novelty_certificate(
    record: MathResearchRecord,
    certificate: NoveltyCertificate,
) -> MathResearchRecord:
    """Replace only novelty evidence; proof authority remains untouched.

    This encodes the fact that novelty is defeasible as the literature world expands,
    while a valid proof of the same fixed formal statement need not be demoted.
    """

    return replace(record, novelty=certificate)
