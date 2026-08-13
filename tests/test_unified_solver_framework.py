from __future__ import annotations

from math import isinf

import pytest

from rakl.fieldability import (
    FieldabilityProfile,
    GeometryArtifactIdentity,
    GeometryCertificationClass,
    amortization_break_even_queries,
    profile_supports_routing_claim,
    stability_adjusted_per_query_cost,
)
from rakl.math_research_assurance import ProofReceipt
from rakl.mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict, diagnose_mechanic_signals
from rakl.operational_map import (
    MapEdgeStatus,
    MapReachabilityVerdict,
    OperationalEdge,
    CoverageCompletenessCertificate,
    OperationalMapReceipt,
    verified_reachability,
)
from rakl.path_cost import PathAdmissibility, PathCostVector, PathOption, admissible_pareto_frontier, explicit_lexicographic_select
from rakl.path_equivalence import PathEquivalenceKind, PathEquivalenceWitness, TransitionIndependenceWitness, canonical_partial_order_trace, equivalent_under_declared_partial_order
from rakl.proof_dag import ProofDAG, ProofEdge, ProofNode, ProofNodeKind, ProofNodeStatus, ProofRelation
from rakl.solution_assembly import AssemblyVerdict, SolutionAssemblyReceipt, proof_dag_content_hash, validate_solution_assembly
from rakl.solver_compilation import CompilationStatus, PreservationValidationReceipt, SolverCompilationCandidate, TransformationEffect, compilation_break_even_uses
from rakl.vtg_hardening import OperationalEdgeAssuranceClass


def _edge(edge_id, source, target, status, *, verification_id=None, failure_id=None):
    assurance_class = None
    assurance_receipt_id = None
    if status is MapEdgeStatus.VERIFIED_TRANSITION:
        assurance_class = OperationalEdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL_EDGE
        assurance_receipt_id = f"assurance-{edge_id}"
    return OperationalEdge(
        edge_id,
        source,
        target,
        status,
        "fixed theorem",
        verification_id,
        failure_id,
        assurance_class=assurance_class,
        assurance_receipt_id=assurance_receipt_id,
    )


def test_unknown_map_content_never_becomes_impossibility():
    receipt = OperationalMapReceipt(
        "m", "p", "ops", "chart",
        edges=(
            _edge("sa", "s", "a", MapEdgeStatus.VERIFIED_TRANSITION, verification_id="v1"),
            _edge("ag?", "a", "g", MapEdgeStatus.UNKNOWN),
        ),
        unknown_coordinates=("bridge_to_goal",),
    )
    report = verified_reachability(receipt, start_state_id="s", target_state_id="g")
    assert report.verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_MAP_INCOMPLETE
    assert report.establishes_mathematical_impossibility is False
    assert receipt.grants_target_authority is False


def test_verified_operational_route_uses_verified_edges_only():
    receipt = OperationalMapReceipt(
        "m", "p", "ops", "chart",
        edges=(
            _edge("sa", "s", "a", MapEdgeStatus.VERIFIED_TRANSITION, verification_id="v1"),
            _edge("ag", "a", "g", MapEdgeStatus.VERIFIED_TRANSITION, verification_id="v2"),
        ),
    )
    report = verified_reachability(receipt, start_state_id="s", target_state_id="g")
    assert report.verdict is MapReachabilityVerdict.VERIFIED_ROUTE_FOUND
    assert report.route_edge_ids == ("sa", "ag")


def test_verified_transition_requires_assurance_class_and_receipt():
    with pytest.raises(ValueError, match="assurance"):
        OperationalEdge("sg", "s", "g", MapEdgeStatus.VERIFIED_TRANSITION, "scope", verification_id="v")


def test_complete_map_no_route_is_only_registered_basis_nonreachability():
    coverage = CoverageCompletenessCertificate("cover", "p", "ops", "chart", "enumerated-map-v1", "closure-checker")
    receipt = OperationalMapReceipt("m", "p", "ops", "chart", coverage_coordinates=("all_registered_states",), coverage_certificate=coverage)
    report = verified_reachability(receipt, start_state_id="s", target_state_id="g")
    assert report.verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_COVERAGE_COMPLETE
    assert report.establishes_no_route_under_registered_map is True
    assert report.establishes_mathematical_impossibility is False
    assert coverage.grants_mathematical_impossibility_authority is False
    assert receipt.grants_scientific_authority is False


def test_naked_coverage_claim_is_not_constructible():
    with pytest.raises(TypeError):
        OperationalMapReceipt("m", "p", "ops", "chart", coverage_complete=True)


def test_verified_applicability_is_not_a_verified_transition_edge():
    receipt = OperationalMapReceipt(
        "m", "p", "ops", "chart",
        edges=(_edge("sg", "s", "g", MapEdgeStatus.VERIFIED_APPLICABLE, verification_id="precondition-check"),),
    )
    report = verified_reachability(receipt, start_state_id="s", target_state_id="g")
    assert report.verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_MAP_INCOMPLETE


def test_independent_reorderings_require_certified_commutation():
    deps = (("a", "c"), ("b", "c"))
    assert not equivalent_under_declared_partial_order(("a", "b", "c"), ("b", "a", "c"), deps)
    witness = TransitionIndependenceWitness("iab", "a", "b", "ctx", ("lean-replay",), ("disjoint obligations",))
    assert equivalent_under_declared_partial_order(
        ("a", "b", "c"), ("b", "a", "c"), deps, independence_witnesses=(witness,), context_hash="ctx"
    )
    assert not equivalent_under_declared_partial_order(("c", "a", "b"), ("a", "b", "c"), deps, independence_witnesses=(witness,), context_hash="ctx")
    with pytest.raises(ValueError, match="cycle"):
        canonical_partial_order_trace(("a", "b"), (("a", "b"), ("b", "a")))


def test_empty_dependency_list_does_not_identify_arbitrary_permutations():
    assert not equivalent_under_declared_partial_order(("a", "b"), ("b", "a"), ())


def test_nontrivial_path_equivalence_needs_replay_evidence_and_grants_no_proof():
    witness = PathEquivalenceWitness(
        "w", "s", "t", ("a", "b"), ("b", "a"), PathEquivalenceKind.COMMUTES_WITH_WITNESS,
        conditions=("independent obligations",), verifier_ids=("lean-replay",),
    )
    assert witness.grants_proof_authority is False


def test_invalid_cheap_path_cannot_buy_admissibility():
    valid = PathAdmissibility(True, True, True, True, True)
    invalid = PathAdmissibility(False, True, True, True, True)
    options = (
        PathOption("short-invalid", PathCostVector(compute=1), invalid),
        PathOption("valid", PathCostVector(compute=5, verification=1), valid),
    )
    selected = explicit_lexicographic_select(options, coordinate_order=("compute", "verification"))
    assert selected is not None and selected.path_id == "valid"


def test_path_cost_keeps_incomparable_pareto_routes():
    valid = PathAdmissibility(True, True, True, True, True)
    options = (
        PathOption("a", PathCostVector(compute=2, verification=8), valid),
        PathOption("b", PathCostVector(compute=8, verification=2), valid),
        PathOption("dominated", PathCostVector(compute=9, verification=9), valid),
    )
    assert {item.path_id for item in admissible_pareto_frontier(options)} == {"a", "b"}


def _geometry_identity():
    return GeometryArtifactIdentity(
        "g", "spec", "prove theorem", "ops", "map", "chart", "lean-env", "cost-v1", "geom-v1",
        GeometryCertificationClass.EMPIRICAL_RANKER,
    )


def test_fieldability_requires_closed_loop_evidence_not_local_alignment_only():
    profile = FieldabilityProfile(identity=_geometry_identity(), build_cost=1, local_alignment=0.99)
    assert not profile_supports_routing_claim(profile, min_bounded_branch_success=0.8, max_false_descent_rate=0.1)
    assert profile.grants_scientific_authority is False
    assert profile.identity.certification_class is GeometryCertificationClass.EMPIRICAL_RANKER
    assert profile.identity.supports_exact_cost_claim is False


def test_field_amortization_and_staleness_are_explicit():
    assert amortization_break_even_queries(build_cost=100, extraction_per_query_cost=10, baseline_per_query_cost=30) == 5
    assert isinf(amortization_break_even_queries(build_cost=100, extraction_per_query_cost=30, baseline_per_query_cost=30))
    assert stability_adjusted_per_query_cost(build_cost=100, extraction_per_query_cost=10, invalidation_hazard_per_query=0.1) == 20
    assert not _geometry_identity().matches(specification_hash="spec", root_qoi="prove theorem", operator_basis_version="ops-v2", map_revision_hash="map", chart_id="chart", verifier_subject_hash="lean-env", cost_algebra_id="cost-v1", construction_version="geom-v1")


def _diagnose(signals, discriminators=()):
    return diagnose_mechanic_signals(
        diagnosis_id="d", problem_state_id="p", atom_id="a", fibre_snapshot_hash="f",
        residual_ids=("r",), signals=signals, discriminator_ids=discriminators,
    )


def test_mechanic_diagnosis_preserves_ambiguity_and_authority_boundary():
    report = _diagnose(("local_metric_descends_root_stalls",), ("compare_best_first_on_same_map",))
    assert report.verdict is MechanicDiagnosisVerdict.DISCRIMINATOR_REQUIRED
    assert set(report.candidate_causes) == {MechanicCause.METRIC_FALSEHOOD, MechanicCause.LOCAL_MINIMUM_OR_DYNAMICS_GAP}
    assert report.grants_scientific_authority is False
    assert report.grants_method_promotion_authority is False


def test_unknown_diagnosis_signal_fails_closed():
    report = _diagnose(("mystery_signal",))
    assert report.verdict is MechanicDiagnosisVerdict.CANNOT_CHECK
    assert report.candidate_causes == (MechanicCause.UNKNOWN,)


def _compilation(**kwargs):
    values = dict(
        compilation_id="c", source_problem_hash="p", specification_hash="s", root_qoi="prove theorem",
        representation_id="r", transform_id="t", solver_id="solver", decoder_id="decode", verifier_id="lean",
        claimed_effects=(TransformationEffect.COMPILE_TO_FORMAL_PROVER,), build_cost=100, execution_cost=5, decode_cost=1, verification_cost=4,
    )
    values.update(kwargs)
    return SolverCompilationCandidate(**values)


def test_solver_compilation_accounts_for_build_decode_verify_and_never_mints_authority():
    candidate = _compilation(invalidation_hazard_per_use=0.1)
    assert candidate.one_shot_cost == 110
    assert candidate.amortized_per_use_cost(10) == 20
    assert candidate.stability_adjusted_per_use_cost == 20
    assert compilation_break_even_uses(candidate, baseline_per_use_cost=30) == 5
    assert candidate.grants_target_authority is False


def _preservation_receipt(**kwargs):
    values = dict(
        report_id="preserve", source_problem_hash="p", specification_hash="s", root_qoi="prove theorem",
        representation_id="r", transform_id="t", verifier_id="semantic-quotient-checker", passed=True,
    )
    values.update(kwargs)
    return PreservationValidationReceipt(**values)


def test_routing_validated_compilation_requires_bound_passing_preservation_receipt():
    with pytest.raises(ValueError, match="preservation"):
        _compilation(status=CompilationStatus.VALIDATED_FOR_ROUTING)
    candidate = _compilation(status=CompilationStatus.VALIDATED_FOR_ROUTING, preservation_receipt=_preservation_receipt())
    assert candidate.status is CompilationStatus.VALIDATED_FOR_ROUTING
    assert candidate.preservation_report_id == "preserve"
    with pytest.raises(ValueError, match="passing"):
        _compilation(status=CompilationStatus.VALIDATED_FOR_ROUTING, preservation_receipt=_preservation_receipt(passed=False))
    with pytest.raises(ValueError, match="does not match"):
        _compilation(status=CompilationStatus.VALIDATED_FOR_ROUTING, preservation_receipt=_preservation_receipt(transform_id="other"))


def _verified_dag():
    return ProofDAG(
        nodes=(
            ProofNode("lemma", ProofNodeKind.LEMMA, "h1", ProofNodeStatus.VERIFIED, "receipt-1"),
            ProofNode("root", ProofNodeKind.THEOREM, "h2", ProofNodeStatus.VERIFIED, "receipt-2"),
        ),
        edges=(ProofEdge("lemma", "root", ProofRelation.REQUIRES),),
    )


def _proof_receipt(**kwargs):
    values = dict(
        theorem_id="root",
        theorem_statement_hash="h2",
        checker="lean-kernel",
        checker_version="4.x",
        accepted=True,
        axioms=(),
        independent_checker="lean-isolated",
        independent_checker_version="4.x",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash="artifact",
    )
    values.update(kwargs)
    return ProofReceipt(**values)


def test_search_trajectory_and_final_certificate_are_separate():
    dag = _verified_dag()
    receipt = SolutionAssemblyReceipt(
        "assembly", "root", ("episode-dead", "episode-success"), ("lemma", "root"), ("dead-branch",),
        proof_dag_content_hash(dag), "artifact", _proof_receipt(),
    )
    report = validate_solution_assembly(dag, receipt)
    assert report.verdict is AssemblyVerdict.READY_FOR_EXTERNAL_AUTHORITY_GATE
    assert report.grants_solution_authority is False
    assert receipt.grants_solution_authority is False


def test_solution_assembly_requires_receipt_bound_to_root_and_artifact():
    dag = _verified_dag()
    missing = SolutionAssemblyReceipt("assembly", "root", (), ("lemma", "root"), (), proof_dag_content_hash(dag), "artifact", None)
    assert validate_solution_assembly(dag, missing).verdict is AssemblyVerdict.CANNOT_CHECK
    wrong_statement = SolutionAssemblyReceipt("assembly", "root", (), ("lemma", "root"), (), proof_dag_content_hash(dag), "artifact", _proof_receipt(theorem_statement_hash="other"))
    assert validate_solution_assembly(dag, wrong_statement).verdict is AssemblyVerdict.REJECT
    wrong_artifact = SolutionAssemblyReceipt("assembly", "root", (), ("lemma", "root"), (), proof_dag_content_hash(dag), "artifact", _proof_receipt(source_hash="other"))
    assert validate_solution_assembly(dag, wrong_artifact).verdict is AssemblyVerdict.REJECT


def test_solution_assembly_hash_mismatch_rejects():
    dag = _verified_dag()
    receipt = SolutionAssemblyReceipt("assembly", "root", (), ("lemma", "root"), (), "wrong", "artifact", _proof_receipt())
    assert validate_solution_assembly(dag, receipt).verdict is AssemblyVerdict.REJECT
