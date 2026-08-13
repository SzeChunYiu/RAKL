from __future__ import annotations

from math import isinf

import pytest

from rakl.framework_closure import ClosureDisposition, ClosureIssue, ClosureLedger
from rakl.math_research_assurance import ProofReceipt
from rakl.vtg_hardening import (
    CertifiedNavigationBasin,
    GeometryConstructibilityClass,
    GeometryLearningReceipt,
    GeometryNontrivialityContract,
    GlobalAmalgamationReceipt,
    NavigationAbstractionKind,
    NavigationAbstractionReceipt,
    OperationalEdgeAssuranceClass,
    OperationalEdgeAssuranceReceipt,
    OperationalReplayEvidence,
    OperationalStateIdentity,
    ReachabilityClaimContract,
    ReachabilityQuantifier,
    ReplayVerdict,
)


def _state(state_id: str) -> OperationalStateIdentity:
    return OperationalStateIdentity(
        state_id=state_id,
        specification_hash="spec",
        root_qoi="prove theorem",
        environment_hash="env",
        verifier_subject_hash="lean-subject",
        local_context_hash=f"ctx-{state_id}",
        goals_hash=f"goals-{state_id}",
        metavariable_state_hash=f"mvars-{state_id}",
        options_hash="opts",
        operator_basis_version="ops",
        chart_id="chart",
        toolchain_hash="toolchain",
    )


def _local_proof_receipt(edge_id: str, statement_hash: str) -> ProofReceipt:
    return ProofReceipt(
        theorem_id=edge_id,
        theorem_statement_hash=statement_hash,
        checker="lean-kernel",
        checker_version="4.x",
        accepted=True,
        axioms=(),
        source_hash=f"proof-term-{edge_id}",
    )


def test_oracle_geometry_fails_nontriviality_claim_even_if_it_routes_perfectly():
    contract = GeometryNontrivialityContract(
        "c", "g", GeometryConstructibilityClass.ORACLE_EVALUATOR_ONLY,
        100, 64, 1000, 1, 1, True, False, True, 100, 0.0,
        fresh_subject_hashes=("fresh",), leakage_check_ids=("leak",),
    )
    assert contract.is_oracle_contaminated is True
    assert contract.supports_fresh_nontriviality_claim is False
    assert contract.grants_scientific_authority is False


def test_constructible_geometry_requires_fresh_and_leakage_bound_for_nontriviality_claim():
    contract = GeometryNontrivialityContract(
        "c", "g", GeometryConstructibilityClass.AMORTIZED_PRECOMPUTATION,
        100, 32, 1000, 2, 3, True, False, False, 50, 0.01,
        fresh_subject_hashes=("fresh",), leakage_check_ids=("leak",),
    )
    assert contract.supports_fresh_nontriviality_claim is True
    assert contract.estimated_total_cost(queries=10) == 150
    assert contract.estimated_break_even_queries(baseline_per_query_cost=25) == 5
    assert isinf(contract.estimated_break_even_queries(baseline_per_query_cost=5))


def test_replay_operational_edge_assurance_requires_exact_state_bound_replay_evidence():
    source = _state("s")
    target = _state("t")
    with pytest.raises(ValueError, match="replay evidence"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
            source, target, "lean-subject",
        )
    replay = OperationalReplayEvidence(
        "replay", "e", source.content_hash, target.content_hash, "action", "lean-tactic-replay", "4.x", "result", ReplayVerdict.PASS
    )
    receipt = OperationalEdgeAssuranceReceipt(
        "r", "e", OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
        source, target, "lean-subject", replay_evidence=replay,
    )
    assert receipt.supports_operational_reachability is True
    assert receipt.supports_local_logical_derivation_claim is False
    assert receipt.grants_root_theorem_authority is False


def test_replay_edge_rejects_wrong_or_failed_replay_subject():
    source = _state("s")
    target = _state("t")
    bad = OperationalReplayEvidence(
        "replay", "e", source.content_hash, target.content_hash, "action", "lean-tactic-replay", "4.x", "result", ReplayVerdict.FAIL
    )
    with pytest.raises(ValueError, match="passing replay"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
            source, target, "lean-subject", replay_evidence=bad,
        )
    wrong_source = OperationalReplayEvidence(
        "replay", "e", "wrong", target.content_hash, "action", "lean-tactic-replay", "4.x", "result", ReplayVerdict.PASS
    )
    with pytest.raises(ValueError, match="source state"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
            source, target, "lean-subject", replay_evidence=wrong_source,
        )


def test_kernel_edge_assurance_requires_audited_proof_receipt_bound_to_edge():
    source = _state("s")
    target = _state("t")
    with pytest.raises(ValueError, match="proof receipt"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE,
            source, target, "lean-subject", derivation_statement_hash="stmt",
        )
    receipt = OperationalEdgeAssuranceReceipt(
        "r", "e", OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE,
        source, target, "lean-subject",
        derivation_statement_hash="stmt",
        proof_receipt=_local_proof_receipt("e", "stmt"),
    )
    assert receipt.supports_local_logical_derivation_claim is True
    assert receipt.grants_root_theorem_authority is False
    with pytest.raises(ValueError, match="theorem id"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE,
            source, target, "lean-subject",
            derivation_statement_hash="stmt",
            proof_receipt=_local_proof_receipt("other", "stmt"),
        )


def test_operational_states_must_share_frozen_subject_across_an_assured_edge():
    source = _state("s")
    target = OperationalStateIdentity(
        state_id="t", specification_hash="other-spec", root_qoi="prove theorem",
        environment_hash="env", verifier_subject_hash="lean-subject", local_context_hash="ctx-t",
        goals_hash="goals-t", metavariable_state_hash="mvars-t", options_hash="opts",
        operator_basis_version="ops", chart_id="chart", toolchain_hash="toolchain",
    )
    replay = OperationalReplayEvidence(
        "replay", "e", source.content_hash, target.content_hash, "action", "lean-tactic-replay", "4.x", "result", ReplayVerdict.PASS
    )
    with pytest.raises(ValueError, match="frozen operational subject"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
            source, target, "lean-subject", replay_evidence=replay,
        )


def test_reachability_quantifiers_cannot_be_silently_interchanged():
    exists = ReachabilityClaimContract("c1", "s", ReachabilityQuantifier.EXISTS_PATH)
    assert exists.policy_id is None
    with pytest.raises(ValueError, match="policy_id"):
        ReachabilityClaimContract("c2", "s", ReachabilityQuantifier.ALMOST_SURE)
    probabilistic = ReachabilityClaimContract(
        "c3", "s", ReachabilityQuantifier.PROBABILITY_AT_LEAST, policy_id="pi", probability_lower_bound=0.95
    )
    assert probabilistic.probability_lower_bound == 0.95
    assert probabilistic.grants_solution_authority is False


def test_overapproximation_requires_concretization_and_refinement():
    with pytest.raises(ValueError, match="overapproximation"):
        NavigationAbstractionReceipt(
            "a", "src", "abs", NavigationAbstractionKind.SOUND_OVERAPPROXIMATION, "alpha", None, "sound", "target"
        )
    receipt = NavigationAbstractionReceipt(
        "a", "src", "abs", NavigationAbstractionKind.SOUND_OVERAPPROXIMATION,
        "alpha", "gamma", "sound", "target", refinement_operator_id="cegar-refine",
    )
    assert receipt.abstract_route_requires_concrete_check is True
    assert receipt.abstract_no_route_can_mint_impossibility_authority is False


def test_exact_abstraction_requires_two_way_validation():
    with pytest.raises(ValueError, match="exact navigation quotient"):
        NavigationAbstractionReceipt(
            "a", "src", "abs", NavigationAbstractionKind.EXACT_QUOTIENT, "q", "lift", "sound", "target"
        )
    receipt = NavigationAbstractionReceipt(
        "a", "src", "abs", NavigationAbstractionKind.EXACT_QUOTIENT, "q", "lift", "sound", "target", "two-way"
    )
    assert receipt.abstract_route_requires_concrete_check is False


def test_navigation_basin_is_scoped_not_global():
    basin = CertifiedNavigationBasin(
        "b", "g", "subject", "selector", "rank", "well-founded", "action-check", "minima-goal", "boundary"
    )
    assert basin.supports_scoped_termination_theorem is True
    assert basin.supports_global_navigation_claim is False


def test_learning_receipt_preserves_support_gaps_and_never_claims_exact_global_geometry():
    receipt = GeometryLearningReceipt(
        "lr", "g", ("train-a", "train-b"), "behavior", "sampling", "verified-cost-labels",
        ("operators", "charts", "scales"), unseen_operator_ids=("new-op",),
        leakage_check_ids=("route-leak-check",), fresh_test_subject_hashes=("fresh",),
        ood_detector_id="ood", staleness_detector_id="stale",
    )
    assert receipt.has_known_support_gaps is True
    assert receipt.supports_fresh_empirical_geometry_claim is True
    assert receipt.supports_exact_global_geometry_claim is False


def test_amalgamation_requires_overlap_assumption_and_parent_checks_and_grants_no_authority():
    receipt = GlobalAmalgamationReceipt(
        "a", "root", ("child-a", "child-b"), ("overlap",), ("assumptions",), ("subst",),
        "parent-invariant", "final-verifier",
    )
    assert receipt.ready_for_solution_assembly is True
    assert receipt.grants_root_authority is False


def test_closure_ledger_rejects_boolean_style_closed_issue_without_evidence():
    issue = ClosureIssue(
        "i", "unsafe boolean closure", "routing", "blocking", "subject", ClosureDisposition.CLOSED_CODE_TEST,
    )
    ledger = ClosureLedger("l", "subject", (issue,), audit_context_ids=("same-context-review",))
    assert ledger.has_unowned_or_unclassified_issue is True
    assert "closed_or_rejected_issue_missing_evidence" in ledger.problems[0][1]
    assert ledger.establishes_no_hidden_issue_exists is False


def test_closure_ledger_rejects_noncanonical_owner_surface():
    issue = ClosureIssue(
        "i", "vague ownership", "someone", "blocking", "subject",
        ClosureDisposition.CLOSED_THEOREM_OR_PROOF_OBLIGATION, evidence_ids=("theorem",),
    )
    ledger = ClosureLedger("l", "subject", (issue,))
    assert "owner_surface_not_canonical" in ledger.problems[0][1]


def test_open_empirical_issue_must_have_falsifier_and_next_cut():
    issue = ClosureIssue(
        "i", "does geometry transfer", "routing", "research", "subject", ClosureDisposition.OPEN_EMPIRICAL,
        next_epistemic_cut="run held-out Lean family",
    )
    ledger = ClosureLedger("l", "subject", (issue,))
    assert ledger.registered_issues_all_owned is False
    assert "open_empirical_issue_missing_falsifier" in ledger.problems[0][1]


def test_provenance_bound_open_issue_is_owned_even_when_unresolved():
    issue = ClosureIssue(
        "i", "does geometry transfer", "routing", "research", "subject", ClosureDisposition.OPEN_EMPIRICAL,
        falsifier="no cost-adjusted gain over best-first on frozen fresh families",
        next_epistemic_cut="run held-out Lean family",
        reviewer_context_ids=("formal", "systems", "editorial"),
    )
    ledger = ClosureLedger("l", "subject", (issue,), audit_context_ids=("nature-skills-style-consistency-sweep",))
    assert ledger.registered_issues_all_owned is True
    assert ledger.establishes_no_hidden_issue_exists is False
