"""Regression tests for HOSTILE_MATH_AUDIT findings (research/unified_problem_solving_v1).

Each test replays the executed counterexample from the audit and asserts the
fixed, fail-closed behaviour. One test per fixed finding; the finding ID is
cited in each docstring.
"""
from __future__ import annotations

from math import inf, isinf

import pytest

from rakl.fieldability import amortization_break_even_queries, stability_adjusted_per_query_cost
from rakl.math_research_assurance import ProofReceipt
from rakl.mechanic_diagnosis import MechanicCause, MechanicDiagnosisReceipt, MechanicDiagnosisVerdict
from rakl.operational_map import (
    CoverageCompletenessCertificate,
    MapEdgeStatus,
    MapReachabilityVerdict,
    OperationalEdge,
    OperationalMapReceipt,
    add_edge,
    canonical_edge_set_hash,
    verified_reachability,
)
from rakl.path_congruence import TraceMonoid, congruence_certificate
from rakl.path_cost import (
    PathAdmissibility,
    PathCostVector,
    PathOption,
    admissible_pareto_frontier,
    dominates,
    explicit_lexicographic_select,
)
from rakl.path_equivalence import TransitionIndependenceWitness, equivalent_under_declared_partial_order
from rakl.proof_dag import ProofDAG, ProofEdge, ProofNode, ProofNodeKind, ProofNodeStatus, ProofRelation, dependency_closure
from rakl.solution_assembly import (
    AssemblyVerdict,
    SolutionAssemblyReceipt,
    proof_dag_content_hash,
    validate_solution_assembly,
)
from rakl.solver_compilation import SolverCompilationCandidate, TransformationEffect, compilation_break_even_uses


def test_u1_context_bound_witness_does_not_license_swaps_in_other_contexts():
    """Audit U1 (check G16): a witness bound to the empty-prefix context must not
    license an a,b swap that occurs after prefix p (a state where commutation was
    never certified); the context-free TraceMonoid must fail closed on real
    histories unless global independence is certified."""
    witness = TransitionIndependenceWitness(
        "w1", "a", "b", context_hash="state_after_EMPTY_prefix", verifier_ids=("verif1",)
    )
    # The audited counterexample: swap happens after "p", context never witnessed.
    assert not equivalent_under_declared_partial_order(
        ("p", "a", "b"),
        ("p", "b", "a"),
        independence_witnesses=(witness,),
        context_hash="state_after_EMPTY_prefix",
    )
    # Positive control: the swap at the witnessed (start/empty-prefix) context is licensed.
    assert equivalent_under_declared_partial_order(
        ("a", "b", "p"),
        ("b", "a", "p"),
        independence_witnesses=(witness,),
        context_hash="state_after_EMPTY_prefix",
    )
    # A resolver that names the swap-point state extends licensing soundly.
    after_p_witness = TransitionIndependenceWitness(
        "w2", "a", "b", context_hash="state_after_p", verifier_ids=("verif1",)
    )
    resolver = {(): "state_after_EMPTY_prefix", ("p",): "state_after_p"}.get
    assert equivalent_under_declared_partial_order(
        ("p", "a", "b"),
        ("p", "b", "a"),
        independence_witnesses=(after_p_witness,),
        context_hash="state_after_EMPTY_prefix",
        prefix_context_resolver=resolver,
    )
    # The certified-global escape hatch keeps the classical trace-monoid reading.
    assert equivalent_under_declared_partial_order(
        ("p", "a", "b"),
        ("p", "b", "a"),
        independence_witnesses=(witness,),
        context_hash="state_after_EMPTY_prefix",
        global_independence_certified=True,
    )
    # TraceMonoid: uncertified quotienting of real histories fails closed.
    uncertified = TraceMonoid.build(["a", "b", "p"], [("a", "b")])
    with pytest.raises(ValueError, match="global_independence_certified"):
        uncertified.history_equivalent(["p", "a", "b"], ["p", "b", "a"])
    certified = TraceMonoid.build(["a", "b", "p"], [("a", "b")], global_independence_certified=True)
    assert certified.history_equivalent(["p", "a", "b"], ["p", "b", "a"])
    cert = congruence_certificate(["a", "b"], [("a", "b")], sample_words=[["a"], ["b"]], sample_contexts=[([], [])])
    assert cert["licenses_real_history_quotient"] is False
    assert cert["grants_proof_authority"] is False


def test_u2_scope_heterogeneous_route_is_not_verified():
    """Audit U2 (check G1): a route composed of edges verified in incompatible
    scopes is not verified in any scope and must not be reported as a verified
    route; scope-uniform routes remain reachable."""
    receipt = OperationalMapReceipt(
        "m1", "psh", "obv1", "chart0",
        edges=(
            OperationalEdge("e1", "s", "a", MapEdgeStatus.VERIFIED_TRANSITION, scope="characteristic_zero", verification_id="v1"),
            OperationalEdge("e2", "a", "t", MapEdgeStatus.VERIFIED_TRANSITION, scope="characteristic_p_only", verification_id="v2"),
        ),
    )
    report = verified_reachability(receipt, start_state_id="s", target_state_id="t")
    assert report.verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_MAP_INCOMPLETE
    # Positive control: the same route within one scope is found and labelled.
    uniform = OperationalMapReceipt(
        "m1u", "psh", "obv1", "chart0",
        edges=(
            OperationalEdge("e1", "s", "a", MapEdgeStatus.VERIFIED_TRANSITION, scope="characteristic_zero", verification_id="v1"),
            OperationalEdge("e2", "a", "t", MapEdgeStatus.VERIFIED_TRANSITION, scope="characteristic_zero", verification_id="v2"),
        ),
    )
    uniform_report = verified_reachability(uniform, start_state_id="s", target_state_id="t")
    assert uniform_report.verdict is MapReachabilityVerdict.VERIFIED_ROUTE_FOUND
    assert uniform_report.route_edge_ids == ("e1", "e2")
    assert "route_scope_uniform:characteristic_zero" in uniform_report.reasons
    assert receipt.grants_scientific_authority is False


def test_u3_contradictory_statuses_on_same_transition_instance_fail_closed():
    """Audit U3 (check G2): the same (source, target, scope) key must not be
    simultaneously VERIFIED_TRANSITION and REFUTED_IN_SCOPE; anonymous operators
    cannot disambiguate contradiction from multi-operator, so they fail closed,
    while distinct operator_ids legitimately separate the claims."""
    with pytest.raises(ValueError, match="contradictory epistemic statuses"):
        OperationalMapReceipt(
            "m2", "psh", "obv1", "chart0",
            edges=(
                OperationalEdge("e1", "s", "t", MapEdgeStatus.VERIFIED_TRANSITION, scope="S", verification_id="v1"),
                OperationalEdge("e2", "s", "t", MapEdgeStatus.REFUTED_IN_SCOPE, scope="S", failure_id="f1"),
            ),
        )
    # Distinct operators are two different transition instances, not a contradiction.
    receipt = OperationalMapReceipt(
        "m2b", "psh", "obv1", "chart0",
        edges=(
            OperationalEdge("e1", "s", "t", MapEdgeStatus.VERIFIED_TRANSITION, scope="S", verification_id="v1", operator_id="op_A"),
            OperationalEdge("e2", "s", "t", MapEdgeStatus.REFUTED_IN_SCOPE, scope="S", failure_id="f1", operator_id="op_B"),
        ),
    )
    assert verified_reachability(receipt, start_state_id="s", target_state_id="t").verdict is MapReachabilityVerdict.VERIFIED_ROUTE_FOUND


def test_u4_coverage_certificate_bound_to_edge_set_and_invalidated_on_mutation():
    """Audit U4 (checks G3/G3b): the coverage-completeness certificate must bind
    the canonical hash of the exact edge enumeration, and add_edge must drop the
    certificate (Moore-closure binding: a larger enumeration is uncertified)."""
    foreign = CoverageCompletenessCertificate(
        "c1", "psh", "obv1", "chart0",
        closure_subject_hash="hash_of_SOME_OTHER_edge_set",
        closure_verifier_id="closure_checker_1",
    )
    with pytest.raises(ValueError, match="canonical hash"):
        OperationalMapReceipt("mA", "psh", "obv1", "chart0", edges=(), coverage_certificate=foreign)
    edges = (OperationalEdge("e1", "s", "t", MapEdgeStatus.REFUTED_IN_SCOPE, scope="S", failure_id="f1"),)
    with pytest.raises(ValueError, match="canonical hash"):
        OperationalMapReceipt("mB", "psh", "obv1", "chart0", edges=edges, coverage_certificate=foreign)
    # A certificate bound to the actual enumeration still supports the scoped no-route verdict.
    bound = CoverageCompletenessCertificate(
        "c2", "psh", "obv1", "chart0",
        closure_subject_hash=canonical_edge_set_hash(edges),
        closure_verifier_id="closure_checker_1",
    )
    certified = OperationalMapReceipt("mC", "psh", "obv1", "chart0", edges=edges, coverage_certificate=bound)
    verdict = verified_reachability(certified, start_state_id="s", target_state_id="t").verdict
    assert verdict is MapReachabilityVerdict.NO_VERIFIED_ROUTE_COVERAGE_COMPLETE
    # G3b: mutation invalidates the closure certificate.
    mutated = add_edge(certified, OperationalEdge("e9", "q", "w", MapEdgeStatus.VERIFIED_TRANSITION, scope="S", verification_id="v9"))
    assert mutated.coverage_complete is False
    assert mutated.coverage_certificate is None
    assert bound.grants_mathematical_impossibility_authority is False


def _passing_proof_receipt(root_id: str, stmt_hash: str, src_hash: str) -> ProofReceipt:
    return ProofReceipt(
        theorem_id=root_id,
        theorem_statement_hash=stmt_hash,
        checker="lean4",
        checker_version="4.9.0",
        accepted=True,
        axioms=("propext",),
        independent_checker="lean4checker",
        independent_checker_version="4.9.0",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash=src_hash,
    )


def test_u5_refutes_conflict_blocks_ready_and_reduces_to_targets_are_premises():
    """Audit U5 (checks G4/G4b): (a) a VERIFIED node REFUTES-ing the VERIFIED root
    is an internal inconsistency and must REJECT, never READY; (b) under the
    natural encoding "X REDUCES_TO Y" the target Y is the premise, so a REFUTED
    reduction target blocks readiness."""
    # (a) conflict-freeness integrity constraint.
    root = ProofNode("root", ProofNodeKind.THEOREM, "h_root", ProofNodeStatus.VERIFIED, receipt_id="r1")
    cex = ProofNode("cex", ProofNodeKind.COUNTEREXAMPLE, "h_cex", ProofNodeStatus.VERIFIED, receipt_id="r2")
    dag = ProofDAG(nodes=(root, cex), edges=(ProofEdge("cex", "root", ProofRelation.REFUTES),))
    receipt = SolutionAssemblyReceipt(
        "as1", "root", ("ep1",), ("root", "cex"), (),
        proof_dag_content_hash(dag), "cert_hash",
        _passing_proof_receipt("root", "h_root", "cert_hash"),
    )
    report = validate_solution_assembly(dag, receipt)
    assert report.verdict is AssemblyVerdict.REJECT
    assert "verified_refutation_conflict" in report.reasons
    # (b) REDUCES_TO premise direction: the reduction target is inside the
    # dependency closure, and its refutation blocks readiness.
    root2 = ProofNode("root", ProofNodeKind.THEOREM, "h_root", ProofNodeStatus.VERIFIED, receipt_id="r1")
    lemma = ProofNode("lem", ProofNodeKind.LEMMA, "h_lem", ProofNodeStatus.REFUTED, receipt_id="ev1")
    dag2 = ProofDAG(nodes=(root2, lemma), edges=(ProofEdge("root", "lem", ProofRelation.REDUCES_TO),))
    assert dependency_closure(dag2, "root") == ("lem",)
    for selected in (("root",), ("root", "lem")):
        receipt2 = SolutionAssemblyReceipt(
            "as2", "root", ("ep1",), selected, (),
            proof_dag_content_hash(dag2), "cert_hash",
            _passing_proof_receipt("root", "h_root", "cert_hash"),
        )
        assert validate_solution_assembly(dag2, receipt2).verdict is not AssemblyVerdict.READY_FOR_EXTERNAL_AUTHORITY_GATE


def test_u6_break_even_prices_invalidation_hazard():
    """Audit U6 (checks G7/G7b): the break-even law must use renewal-reward
    accounting consistent with the module's own hazard model. With build=100,
    baseline=30, extraction=10, hazard=0.25 the hazard-adjusted per-query cost
    (35) exceeds baseline, so amortization never occurs (was: 5 queries)."""
    assert stability_adjusted_per_query_cost(build_cost=100, extraction_per_query_cost=10, invalidation_hazard_per_query=0.25) == 35.0
    assert amortization_break_even_queries(
        build_cost=100, extraction_per_query_cost=10, baseline_per_query_cost=30,
        invalidation_hazard_per_query=0.25,
    ) == inf
    # h=0 remains the special case of the one law.
    assert amortization_break_even_queries(build_cost=100, extraction_per_query_cost=10, baseline_per_query_cost=30) == 5.0
    # Positive-advantage hazard case: advantage = 30 - 10 - 0.05*100 = 15.
    assert amortization_break_even_queries(
        build_cost=100, extraction_per_query_cost=10, baseline_per_query_cost=30,
        invalidation_hazard_per_query=0.05,
    ) == pytest.approx(100 / 15)
    candidate = SolverCompilationCandidate(
        "c1", "sph", "spec", "qoi", "rep", "tr", "sol", None, "ver",
        (TransformationEffect.RELAX,), build_cost=100, execution_cost=10,
        invalidation_hazard_per_use=0.25,
    )
    assert candidate.stability_adjusted_per_use_cost == 35.0
    assert isinf(compilation_break_even_uses(candidate, baseline_per_use_cost=30))
    assert candidate.grants_scientific_authority is False


def test_i1_nan_and_nonfinite_costs_fail_closed():
    """Audit I1 (checks G5/G5b): NaN vacuously passed the `< 0` guard, making
    dominance undecidable and lexicographic selection input-order-dependent.
    Cost coordinates must be finite and nonnegative."""
    with pytest.raises(ValueError, match="finite"):
        PathCostVector(compute=float("nan"))
    with pytest.raises(ValueError, match="finite"):
        PathCostVector(compute=float("inf"))
    with pytest.raises(ValueError):
        PathCostVector(compute=-1.0)
    # With the finiteness axiom enforced, selection is a function of the option set.
    ok = PathAdmissibility(True, True, True, True, True)
    p1 = PathOption("p1", PathCostVector(compute=1.0), ok)
    p5 = PathOption("p5", PathCostVector(compute=5.0), ok)
    assert explicit_lexicographic_select([p1, p5], coordinate_order=("compute",)) == explicit_lexicographic_select([p5, p1], coordinate_order=("compute",))
    assert dominates(p1.cost, p5.cost)


def test_i2_duplicate_path_id_fails_closed():
    """Audit I2 (check G6): duplicate path_ids disabled dominance pruning, so a
    strictly dominated option survived the "Pareto frontier"; path_id is a key
    and duplicates must be rejected."""
    ok = PathAdmissibility(True, True, True, True, True)
    a = PathOption("p", PathCostVector(compute=1.0), ok)
    b = PathOption("p", PathCostVector(compute=2.0), ok)
    assert dominates(a.cost, b.cost)
    with pytest.raises(ValueError, match="unique"):
        admissible_pareto_frontier([a, b])
    with pytest.raises(ValueError, match="unique"):
        explicit_lexicographic_select([a, b], coordinate_order=("compute",))
    # Unique ids: the frontier is a genuine Pareto frontier.
    c = PathOption("q", PathCostVector(compute=2.0), ok)
    assert admissible_pareto_frontier([a, c]) == (a,)


def test_i3_unknown_is_not_an_identifiable_mechanic_cause():
    """Audit I3(a) (check G9): UNKNOWN is the epistemic bottom, not a fault
    hypothesis; a receipt claiming the uniquely identified mechanic gap is
    UNKNOWN must not construct."""
    with pytest.raises(ValueError, match="UNKNOWN"):
        MechanicDiagnosisReceipt(
            "d1", "ps", "atom", "fibre", (), ("sig",),
            (MechanicCause.UNKNOWN,),
            verdict=MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED,
        )
    # CANNOT_CHECK with UNKNOWN remains the correct fail-closed representation.
    receipt = MechanicDiagnosisReceipt(
        "d2", "ps", "atom", "fibre", (), ("mystery_signal",),
        (MechanicCause.UNKNOWN,),
        verdict=MechanicDiagnosisVerdict.CANNOT_CHECK,
    )
    assert receipt.grants_scientific_authority is False
