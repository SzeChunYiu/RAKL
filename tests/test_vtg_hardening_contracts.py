from __future__ import annotations

from math import isinf

import pytest

from rakl.framework_closure import ClosureDisposition, ClosureIssue, ClosureLedger
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
    ReachabilityClaimContract,
    ReachabilityQuantifier,
)


def test_oracle_geometry_fails_nontriviality_claim_even_if_it_routes_perfectly():
    contract = GeometryNontrivialityContract(
        "c",
        "g",
        GeometryConstructibilityClass.ORACLE_EVALUATOR_ONLY,
        100,
        64,
        1000,
        1,
        1,
        True,
        False,
        True,
        100,
        0.0,
        fresh_subject_hashes=("fresh",),
        leakage_check_ids=("leak",),
    )
    assert contract.is_oracle_contaminated is True
    assert contract.supports_fresh_nontriviality_claim is False
    assert contract.grants_scientific_authority is False


def test_constructible_geometry_requires_fresh_and_leakage_bound_for_nontriviality_claim():
    contract = GeometryNontrivialityContract(
        "c",
        "g",
        GeometryConstructibilityClass.AMORTIZED_PRECOMPUTATION,
        100,
        32,
        1000,
        2,
        3,
        True,
        False,
        False,
        50,
        0.01,
        fresh_subject_hashes=("fresh",),
        leakage_check_ids=("leak",),
    )
    assert contract.supports_fresh_nontriviality_claim is True
    assert contract.estimated_total_cost(queries=10) == 150
    assert contract.estimated_break_even_queries(baseline_per_query_cost=25) == 5
    assert isinf(contract.estimated_break_even_queries(baseline_per_query_cost=5))


def test_replay_operational_edge_assurance_needs_snapshot_tool_and_replay_receipt():
    with pytest.raises(ValueError, match="snapshot/tool/replay"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE, "lean-env"
        )
    receipt = OperationalEdgeAssuranceReceipt(
        "r",
        "e",
        OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE,
        "lean-env",
        operational_snapshot_hash="snapshot",
        tool_version_hash="lean-tactic-v1",
        replay_receipt_id="replay",
    )
    assert receipt.supports_operational_reachability is True
    assert receipt.supports_local_logical_derivation_claim is False
    assert receipt.grants_root_theorem_authority is False


def test_kernel_edge_assurance_requires_proof_receipt_identity():
    with pytest.raises(ValueError, match="proof receipt"):
        OperationalEdgeAssuranceReceipt(
            "r", "e", OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE, "lean-kernel"
        )
    receipt = OperationalEdgeAssuranceReceipt(
        "r", "e", OperationalEdgeAssuranceClass.KERNEL_DERIVATION_EDGE, "lean-kernel", proof_receipt_id="proof"
    )
    assert receipt.supports_local_logical_derivation_claim is True
    assert receipt.grants_root_theorem_authority is False


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
        "a",
        "src",
        "abs",
        NavigationAbstractionKind.SOUND_OVERAPPROXIMATION,
        "alpha",
        "gamma",
        "sound",
        "target",
        refinement_operator_id="cegar-refine",
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
        "lr",
        "g",
        ("train-a", "train-b"),
        "behavior",
        "sampling",
        "verified-cost-labels",
        ("operators", "charts", "scales"),
        unseen_operator_ids=("new-op",),
        leakage_check_ids=("route-leak-check",),
        fresh_test_subject_hashes=("fresh",),
        ood_detector_id="ood",
        staleness_detector_id="stale",
    )
    assert receipt.has_known_support_gaps is True
    assert receipt.supports_fresh_empirical_geometry_claim is True
    assert receipt.supports_exact_global_geometry_claim is False


def test_amalgamation_requires_overlap_assumption_and_parent_checks_and_grants_no_authority():
    receipt = GlobalAmalgamationReceipt(
        "a",
        "root",
        ("child-a", "child-b"),
        ("overlap",),
        ("assumptions",),
        ("subst",),
        "parent-invariant",
        "final-verifier",
    )
    assert receipt.ready_for_solution_assembly is True
    assert receipt.grants_root_authority is False


def test_closure_ledger_rejects_boolean_style_closed_issue_without_evidence():
    issue = ClosureIssue(
        "i",
        "unsafe boolean closure",
        "routing",
        "blocking",
        "subject",
        ClosureDisposition.CLOSED_CODE_TEST,
    )
    ledger = ClosureLedger("l", "subject", (issue,), audit_context_ids=("same-context-review",))
    assert ledger.has_unowned_or_unclassified_issue is True
    assert "closed_or_rejected_issue_missing_evidence" in ledger.problems[0][1]
    assert ledger.establishes_no_hidden_issue_exists is False


def test_open_empirical_issue_must_have_falsifier_and_next_cut():
    issue = ClosureIssue(
        "i",
        "does geometry transfer",
        "routing",
        "research",
        "subject",
        ClosureDisposition.OPEN_EMPIRICAL,
        next_epistemic_cut="run held-out Lean family",
    )
    ledger = ClosureLedger("l", "subject", (issue,))
    assert ledger.registered_issues_all_owned is False
    assert "open_empirical_issue_missing_falsifier" in ledger.problems[0][1]


def test_provenance_bound_open_issue_is_owned_even_when_unresolved():
    issue = ClosureIssue(
        "i",
        "does geometry transfer",
        "routing",
        "research",
        "subject",
        ClosureDisposition.OPEN_EMPIRICAL,
        falsifier="no cost-adjusted gain over best-first on frozen fresh families",
        next_epistemic_cut="run held-out Lean family",
        reviewer_context_ids=("formal", "systems", "editorial"),
    )
    ledger = ClosureLedger("l", "subject", (issue,), audit_context_ids=("nature-skills-style-consistency-sweep",))
    assert ledger.registered_issues_all_owned is True
    assert ledger.establishes_no_hidden_issue_exists is False
