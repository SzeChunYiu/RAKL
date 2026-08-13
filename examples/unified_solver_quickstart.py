"""Worked end-to-end quickstart for the eight unified problem-solving mechanics.

Run from the repository root:

    PYTHONPATH=src python examples/unified_solver_quickstart.py

Walks one synthetic solving episode through every registered mechanic:

    1. operational_map_belief          -- partial map, verified routes, coverage certificate
    2. mechanic_differential_diagnosis -- competing stall causes, discriminator demand
    3. verified_solver_compilation     -- representation/solver binding + preservation receipt
    4. path_cost_algebra               -- noncompensatory admissibility, Pareto frontier
    5. path_equivalence_concurrency    -- witness-gated (state-indexed) path quotienting
    6. navigation_quotient_validation  -- reachability obligations of a search quotient
    7. fieldability_and_geometry       -- geometry identity, amortization, cost geometry laws
    8. trajectory_to_certificate       -- discovery chronology vs dependency certificate
    9. registry audit                  -- every mechanic owned, proposal-only authority

HONESTY CONTRACT: everything below is proposal/search plumbing. No object printed
here grants scientific, theorem, or method-promotion authority; each step prints
its own authority projection to make that machine-checkable.
"""
from __future__ import annotations

from rakl.cost_geometry import OperatorCostGeometry, budget_indexed_triangle_counterexample
from rakl.fieldability import (
    FieldabilityProfile,
    GeometryArtifactIdentity,
    GeometryCertificationClass,
    amortization_break_even_queries,
)
from rakl.math_research_assurance import ProofReceipt
from rakl.mechanic_diagnosis import diagnose_mechanic_signals
from rakl.navigation_quotient import NavigationQuotientValidation
from rakl.operational_map import (
    CoverageCompletenessCertificate,
    MapEdgeStatus,
    OperationalEdge,
    OperationalMapReceipt,
    add_edge,
    canonical_edge_set_hash,
    verified_reachability,
)
from rakl.path_cost import (
    PathAdmissibility,
    PathCostVector,
    PathOption,
    admissible_pareto_frontier,
    explicit_lexicographic_select,
)
from rakl.path_equivalence import (
    TransitionIndependenceWitness,
    canonical_partial_order_trace,
    equivalent_under_declared_partial_order,
)
from rakl.proof_dag import ProofDAG, ProofEdge, ProofNode, ProofNodeKind, ProofNodeStatus, ProofRelation
from rakl.solution_assembly import (
    SolutionAssemblyReceipt,
    proof_dag_content_hash,
    validate_solution_assembly,
)
from rakl.solver_compilation import (
    CompilationStatus,
    PreservationValidationReceipt,
    SolverCompilationCandidate,
    TransformationEffect,
    compilation_break_even_uses,
)
from rakl.unified_solver_registry import validate_unified_solver_registry


def banner(step: str) -> None:
    print()
    print(f"=== {step} ===")


def main() -> int:
    print(__doc__.splitlines()[0])
    print("honest-label: development walkthrough on a synthetic known world; "
          "no scientific/theorem/method authority is granted anywhere below")

    # ------------------------------------------------------------------
    banner("1. operational_map_belief: partial map != legality; UNKNOWN != BLOCKED")
    edges = (
        OperationalEdge("e1", "start", "mid", MapEdgeStatus.VERIFIED_TRANSITION,
                        scope="integer_case", verification_id="replay-001", operator_id="op.rewrite"),
        OperationalEdge("e2", "mid", "goal", MapEdgeStatus.VERIFIED_TRANSITION,
                        scope="integer_case", verification_id="replay-002", operator_id="op.induction"),
        OperationalEdge("e3", "start", "detour", MapEdgeStatus.CANDIDATE_UNVERIFIED,
                        scope="integer_case", operator_id="op.guess"),
        OperationalEdge("e4", "detour", "goal", MapEdgeStatus.REFUTED_IN_SCOPE,
                        scope="integer_case", failure_id="counterexample-007", operator_id="op.guess"),
    )
    partial_map = OperationalMapReceipt("map-demo", "problem-hash-1", "opbasis-v1", "chart-main", edges)
    route = verified_reachability(partial_map, start_state_id="start", target_state_id="goal")
    print(f"route verdict: {route.verdict.value}; edges: {route.route_edge_ids}")
    print(f"reasons: {route.reasons}")

    no_route = verified_reachability(partial_map, start_state_id="goal", target_state_id="start")
    print(f"reverse search: {no_route.verdict.value} (map still has CANDIDATE/UNKNOWN content)")
    print(f"  establishes_mathematical_impossibility={no_route.establishes_mathematical_impossibility}")

    # A coverage certificate must bind the CANONICAL HASH of the exact edge set.
    closed_edges = (
        OperationalEdge("c1", "a", "b", MapEdgeStatus.VERIFIED_TRANSITION,
                        scope="integer_case", verification_id="replay-101", operator_id="op.rewrite"),
    )
    certificate = CoverageCompletenessCertificate(
        "cover-1", "problem-hash-2", "opbasis-v1", "chart-main",
        closure_subject_hash=canonical_edge_set_hash(closed_edges),
        closure_verifier_id="closure-checker-v1",
    )
    certified_map = OperationalMapReceipt(
        "map-closed", "problem-hash-2", "opbasis-v1", "chart-main",
        closed_edges, coverage_certificate=certificate,
    )
    scoped = verified_reachability(certified_map, start_state_id="b", target_state_id="a")
    print(f"certified-map no-route: {scoped.verdict.value}")
    print(f"  scoped claim only: establishes_no_route_under_registered_map="
          f"{scoped.establishes_no_route_under_registered_map}; "
          f"impossibility authority={scoped.establishes_mathematical_impossibility}")
    mutated = add_edge(certified_map, OperationalEdge(
        "c2", "b", "a", MapEdgeStatus.CANDIDATE_UNVERIFIED, scope="integer_case", operator_id="op.new"))
    print(f"after add_edge the certificate is dropped: coverage_complete={mutated.coverage_complete} "
          "(a mutated enumeration is uncertified until re-closed)")

    # ------------------------------------------------------------------
    banner("2. mechanic_differential_diagnosis: represent competing stall causes")
    ambiguous = diagnose_mechanic_signals(
        diagnosis_id="diag-1", problem_state_id="start", atom_id="atom-demo",
        fibre_snapshot_hash="fibre-hash-1", residual_ids=("residual-1",),
        signals=("coverage_incomplete", "local_metric_descends_root_stalls"),
        discriminator_ids=("probe-coverage-vs-metric",),
    )
    print(f"signals -> verdict: {ambiguous.verdict.value}")
    print(f"candidate causes (set-valued, not forced to one): "
          f"{tuple(c.value for c in ambiguous.candidate_causes)}")
    identified = diagnose_mechanic_signals(
        diagnosis_id="diag-2", problem_state_id="start", atom_id="atom-demo",
        fibre_snapshot_hash="fibre-hash-1", residual_ids=("residual-1",),
        signals=("portal_roundtrip_failed",),
    )
    print(f"single-cause signals -> {identified.verdict.value}: "
          f"{tuple(c.value for c in identified.candidate_causes)}")
    print(f"  grants_method_promotion_authority={identified.grants_method_promotion_authority}")

    # ------------------------------------------------------------------
    banner("3. verified_solver_compilation: bind representation+solver+verifier")
    preservation = PreservationValidationReceipt(
        report_id="preserve-1", source_problem_hash="problem-hash-1",
        specification_hash="spec-hash-1", root_qoi="prove target theorem",
        representation_id="rep.graph", transform_id="tf.compile_to_sat",
        verifier_id="preservation-checker-v1", passed=True,
    )
    compilation = SolverCompilationCandidate(
        compilation_id="compile-1", source_problem_hash="problem-hash-1",
        specification_hash="spec-hash-1", root_qoi="prove target theorem",
        representation_id="rep.graph", transform_id="tf.compile_to_sat",
        solver_id="solver.sat", decoder_id="decode.model", verifier_id="verify.original-semantics",
        claimed_effects=(TransformationEffect.COMPILE_TO_SAT_SMT,),
        preservation_receipt=preservation,
        build_cost=40.0, execution_cost=2.0, decode_cost=1.0, verification_cost=2.0,
        expected_reuse=25.0, invalidation_hazard_per_use=0.02,
        status=CompilationStatus.VALIDATED_FOR_ROUTING,
    )
    print(f"compilation status: {compilation.status.value} "
          f"(requires a bound, passing preservation receipt: {compilation.preservation_report_id})")
    uses = compilation_break_even_uses(compilation, baseline_per_use_cost=9.0)
    print(f"hazard-consistent break-even uses vs baseline 9.0/use: {uses:.2f}")
    print(f"  grants_target_authority={compilation.grants_target_authority}")

    # ------------------------------------------------------------------
    banner("4. path_cost_algebra: hard admissibility BEFORE any cost comparison")
    ok = PathAdmissibility(True, True, True, True, True)
    unlicensed = PathAdmissibility(False, True, True, True, True)
    options = (
        PathOption("route-direct", PathCostVector(compute=8.0, verification=3.0), ok),
        PathOption("route-compiled", PathCostVector(compute=3.0, verification=6.0), ok),
        PathOption("route-cheap-but-unlicensed", PathCostVector(compute=0.5), unlicensed),
        PathOption("route-dominated", PathCostVector(compute=9.0, verification=4.0), ok),
    )
    frontier = admissible_pareto_frontier(options)
    print(f"admissible Pareto frontier: {tuple(o.path_id for o in frontier)}")
    print("  the cheapest option is EXCLUDED: an unlicensed assumption cannot be "
          "bought back by low compute (noncompensatory admissibility)")
    pick = explicit_lexicographic_select(options, coordinate_order=("verification", "compute"))
    print(f"explicit lexicographic pick (verification first): {pick.path_id}")

    # ------------------------------------------------------------------
    banner("5. path_equivalence_concurrency: quotient only witnessed redundancy")
    trace = canonical_partial_order_trace(("t.normalize", "t.rewrite", "t.check"),
                                          dependencies=(("t.rewrite", "t.check"),))
    print(f"partial-order trace layers: {trace.layers}")
    witness = TransitionIndependenceWitness(
        witness_id="w-1", left_transition_id="t.normalize", right_transition_id="t.rewrite",
        context_hash="state-hash-start", verifier_ids=("commutation-checker-v1",),
    )
    head_swap = equivalent_under_declared_partial_order(
        ("t.normalize", "t.rewrite", "t.check"), ("t.rewrite", "t.normalize", "t.check"),
        dependencies=(("t.rewrite", "t.check"),),
        independence_witnesses=(witness,), context_hash="state-hash-start",
    )
    print(f"witnessed head swap equivalent: {head_swap}")
    tail_witness = TransitionIndependenceWitness(
        witness_id="w-2", left_transition_id="t.rewrite", right_transition_id="t.check",
        context_hash="state-hash-start", verifier_ids=("commutation-checker-v1",),
    )
    interior_swap = equivalent_under_declared_partial_order(
        ("t.normalize", "t.rewrite", "t.check"), ("t.normalize", "t.check", "t.rewrite"),
        independence_witnesses=(tail_witness,), context_hash="state-hash-start",
    )
    print(f"unwitnessed interior swap (prefix state unnamed) fails closed: {interior_swap}")
    print("  witnesses are state-indexed: certifying commutation at the start state "
          "licenses no exchange after a prefix has executed")

    # ------------------------------------------------------------------
    banner("6. navigation_quotient_validation: a QoI quotient is not a search license")
    exact = NavigationQuotientValidation(
        validation_id="nq-1", quotient_id="quot.symmetry", semantic_validation_id="tcsq-77",
        source_subject_hash="subject-hash-1", abstract_subject_hash="abstract-hash-1",
        target_labels_preserved=True, forward_simulation_verified=True,
        route_lifting_verified=True, cost_relation_verified=True,
        verifier_ids=("quotient-checker-v1",),
    )
    overapprox = NavigationQuotientValidation(
        validation_id="nq-2", quotient_id="quot.coarse", semantic_validation_id="tcsq-78",
        source_subject_hash="subject-hash-1", abstract_subject_hash="abstract-hash-2",
        target_labels_preserved=True, forward_simulation_verified=True,
        route_lifting_verified=None, cost_relation_verified=None,
        verifier_ids=("quotient-checker-v1",),
    )
    print(f"fully validated quotient: {exact.verdict.value} "
          f"(requires_concrete_route_revalidation={exact.requires_concrete_route_revalidation})")
    print(f"over-approximation: {overapprox.verdict.value} "
          f"(requires_concrete_route_revalidation={overapprox.requires_concrete_route_revalidation})")
    print(f"  abstract route can mint solution authority: "
          f"{overapprox.abstract_route_can_mint_solution_authority}")

    # ------------------------------------------------------------------
    banner("7. fieldability + cost geometry: economics and laws, never truth")
    identity = GeometryArtifactIdentity(
        geometry_id="geom-1", specification_hash="spec-hash-1", root_qoi="prove target theorem",
        operator_basis_version="opbasis-v1", map_revision_hash=partial_map.content_hash,
        chart_id="chart-main", verifier_subject_hash="verifier-hash-1",
        cost_algebra_id="algebra.dev-numeric", construction_version="build-1",
        certification_class=GeometryCertificationClass.EMPIRICAL_RANKER,
    )
    profile = FieldabilityProfile(
        identity=identity, build_cost=100.0, baseline_per_query_cost=30.0,
        extraction_per_query_cost=10.0, invalidation_hazard_per_query=0.05,
        local_alignment=0.86, greedy_success=0.55, bounded_branch_success=0.97,
        route_stretch=1.1, false_descent_rate=0.14,
    )
    print(f"geometry certification class: {identity.certification_class.value} "
          f"(supports_exact_cost_claim={identity.supports_exact_cost_claim})")
    q_ok = amortization_break_even_queries(
        build_cost=100.0, extraction_per_query_cost=10.0,
        baseline_per_query_cost=30.0, invalidation_hazard_per_query=0.05)
    q_never = amortization_break_even_queries(
        build_cost=100.0, extraction_per_query_cost=10.0,
        baseline_per_query_cost=30.0, invalidation_hazard_per_query=0.25)
    print(f"hazard-adjusted break-even queries at h=0.05: {q_ok:.2f}; at h=0.25: {q_never} "
          "(the field never amortizes when hazard-priced rebuilds eat the advantage)")
    print(f"  fieldability grants_scientific_authority={profile.grants_scientific_authority}")

    geometry = OperatorCostGeometry([("x", "y", 3.0), ("y", "z", 3.0), ("x", "z", 7.0)])
    cert = geometry.certify_quasimetric()
    print(f"intrinsic cost geometry is a Lawvere quasimetric: {cert.is_lawvere_metric}")
    counter = budget_indexed_triangle_counterexample()
    print(f"budget-in-the-metric triangle violation reproduced: {counter['triangle_violated']} "
          "(budget lives in sublevel sets, not the metric)")

    # ------------------------------------------------------------------
    banner("8. trajectory_to_certificate: chronology != dependency certificate")
    dag = ProofDAG(
        nodes=(
            ProofNode("lemma-key", ProofNodeKind.LEMMA, "stmt-hash-lemma",
                      ProofNodeStatus.VERIFIED, "receipt-lemma"),
            ProofNode("target-theorem", ProofNodeKind.THEOREM, "stmt-hash-root",
                      ProofNodeStatus.VERIFIED, "receipt-root"),
            ProofNode("dead-end-idea", ProofNodeKind.CONJECTURE, "stmt-hash-dead",
                      ProofNodeStatus.PROPOSED),
        ),
        edges=(ProofEdge("lemma-key", "target-theorem", ProofRelation.REQUIRES),),
    )
    proof_receipt = ProofReceipt(
        theorem_id="target-theorem", theorem_statement_hash="stmt-hash-root",
        checker="lean-kernel", checker_version="4.x", accepted=True, axioms=(),
        independent_checker="lean-isolated", independent_checker_version="4.x",
        independent_accepted=True, isolated_recheck=True, source_hash="certificate-artifact-hash",
    )
    assembly = SolutionAssemblyReceipt(
        assembly_id="assembly-1", root_node_id="target-theorem",
        trajectory_episode_ids=("episode-dead-end", "episode-success"),
        selected_node_ids=("lemma-key", "target-theorem"),
        discarded_branch_ids=("dead-end-idea",),
        proof_dag_hash=proof_dag_content_hash(dag),
        certificate_artifact_hash="certificate-artifact-hash",
        proof_receipt=proof_receipt,
    )
    report = validate_solution_assembly(dag, assembly)
    print(f"assembly verdict: {report.verdict.value}")
    print("  the failed branch stays in the record (negative history is preserved); "
          "READY_FOR_EXTERNAL_AUTHORITY_GATE is the STRONGEST output this gate can emit")
    print(f"  grants_solution_authority={report.grants_solution_authority}")

    # ------------------------------------------------------------------
    banner("9. registry audit: every mechanic owned, proposal-only")
    registry = validate_unified_solver_registry()
    print(f"registry valid: {registry.valid}; mechanics: {len(registry.mechanic_ids)}")
    for mechanic_id in registry.mechanic_ids:
        print(f"  - {mechanic_id}")
    print(f"  grants_scientific_authority={registry.grants_scientific_authority}; "
          f"establishes_global_framework_completeness={registry.establishes_global_framework_completeness}")

    print()
    print("QUICKSTART_COMPLETE=true")
    print("AUTHORITY_GRANTED=false")
    print("METHOD_PROMOTION_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
