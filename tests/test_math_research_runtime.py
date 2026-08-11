from __future__ import annotations

from rakl.math_context import ContextGateVerdict, MathContextFiber, MethodTransfer
from rakl.math_research_assurance import (
    FormalizationWitness,
    MathResearchRecord,
    NoveltyCertificate,
    ProofReceipt,
)
from rakl.math_research_runtime import plan_math_research, publication_ready
from rakl.problem_solving_algebra import ObstructionKind, ProblemSignature


def _signature() -> ProblemSignature:
    return ProblemSignature(
        objects=("claim",),
        domain="mathematics",
        goal_type="prove theorem",
    )


def _context() -> MathContextFiber:
    return MathContextFiber(
        atom_id="atom-C",
        object_context="one atomic mathematical obstruction",
        structural_coordinates=("symmetry", "composition law"),
        equivalent_formulations=("equivalent obstruction formulation",),
        solved_analogues=("solved sibling theorem",),
        method_transfers=(
            MethodTransfer(
                source_context="solved sibling theorem",
                method="transferable method",
                shared_structure=("shared invariant",),
                required_assumptions=("registered assumption",),
                disanalogies=("target lacks one source assumption",),
                repair_question="what weaker assumption makes the method survive?",
                source_anchors=("source:primary",),
            ),
        ),
        explicit_disanalogies=("source and target differ on the repair assumption",),
        source_anchors=("source:primary",),
        frozen_at="2026-08-11T04:00:00+00:00",
        first_candidate_at="2026-08-11T04:01:00+00:00",
        packet_hash="sha256:context",
    )


def _formalization() -> FormalizationWitness:
    return FormalizationWitness(
        informal_claim_hash="informal",
        formal_statement_hash="formal",
        accepted=True,
        roundtrip_checked=True,
        boundary_cases_checked=True,
        independent_reviewers=1,
    )


def _proof() -> ProofReceipt:
    return ProofReceipt(
        theorem_id="T",
        theorem_statement_hash="formal",
        checker="lean",
        checker_version="pinned",
        accepted=True,
        axioms=(),
        independent_checker="comparator",
        independent_checker_version="pinned",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash="proof-source",
    )


def _novelty() -> NoveltyCertificate:
    return NoveltyCertificate(
        corpus_cutoff="2026-08-10",
        corpora=("registered-corpus",),
        search_routes=("exact", "normalized", "structural"),
        canonical_fingerprint="fp",
        equivalent_found=False,
        independent_reviewers=1,
    )


def test_missing_context_blocks_candidate_generation_fail_closed() -> None:
    plan = plan_math_research(signature=_signature(), record=MathResearchRecord(claim_id="C"))
    assert plan.context_gate.verdict is ContextGateVerdict.CANNOT_CHECK
    assert not plan.candidate_generation_allowed
    assert not plan.candidate_paths
    assert "search_solved_and_near_solved_analogous_contexts" in plan.pre_candidate_actions


def test_context_complete_record_exposes_normal_research_blockers_and_paths() -> None:
    plan = plan_math_research(
        signature=_signature(),
        record=MathResearchRecord(claim_id="C"),
        context_fiber=_context(),
    )
    blockers = set(plan.next_blockers)
    assert ObstructionKind.FORMALIZATION_GAP in blockers
    assert ObstructionKind.FORMALIZATION_ALIGNMENT_GAP in blockers
    assert ObstructionKind.PROOF_GAP in blockers
    assert ObstructionKind.NOVELTY_GAP in blockers
    assert ObstructionKind.RESEARCH_VALUE_GAP in blockers
    assert plan.context_gate.verdict is ContextGateVerdict.PASS
    assert plan.candidate_generation_allowed
    assert plan.candidate_paths
    assert plan.pre_candidate_actions == ()


def test_verified_proof_removes_proof_blocker_but_not_novelty_or_value() -> None:
    record = MathResearchRecord(
        claim_id="C",
        formalization=_formalization(),
        proof=_proof(),
    )
    plan = plan_math_research(signature=_signature(), record=record, context_fiber=_context())
    blockers = set(plan.next_blockers)
    assert ObstructionKind.PROOF_GAP not in blockers
    assert ObstructionKind.NOVELTY_GAP in blockers
    assert ObstructionKind.RESEARCH_VALUE_GAP in blockers
    assert not publication_ready(record)


def test_only_all_noncompensatory_gates_make_record_publication_ready() -> None:
    record = MathResearchRecord(
        claim_id="C",
        formalization=_formalization(),
        proof=_proof(),
        novelty=_novelty(),
        interestingness_screened=True,
        external_mathematical_review=True,
    )
    plan = plan_math_research(signature=_signature(), record=record, context_fiber=_context())
    assert plan.next_blockers == ()
    assert publication_ready(record)


def test_rediscovery_is_not_publication_ready_as_new_mathematics() -> None:
    novelty = NoveltyCertificate(
        corpus_cutoff="2026-08-10",
        corpora=("registered-corpus",),
        search_routes=("structural",),
        canonical_fingerprint="fp",
        equivalent_found=True,
        candidate_matches=("known theorem",),
        independent_reviewers=1,
    )
    record = MathResearchRecord(
        claim_id="C",
        formalization=_formalization(),
        proof=_proof(),
        novelty=novelty,
        interestingness_screened=True,
        external_mathematical_review=True,
    )
    assert not publication_ready(record)
