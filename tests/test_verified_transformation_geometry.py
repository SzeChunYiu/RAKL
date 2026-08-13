import pytest
from rakl.verified_transformation_geometry import *


def subject(**overrides):
    d = dict(
        environment_hash="env", logic_or_kernel_version="lean", elaborator_or_tool_version="tool",
        options_hash="opt", operator_basis_hash="ops", transition_semantics_hash="trans",
        operational_map_revision_hash="map", chart_catalog_hash="charts", cost_model_hash="cost",
    )
    d.update(overrides)
    return OperationalSubject(**d)


def test_candidate_edge_does_not_support_operational_navigation():
    edge = EdgeAssuranceReceipt("e", subject(), "a", "b", EdgeAssuranceClass.CANDIDATE_OPERATIONAL, None)
    assert not edge.declares_validated_operational_edge
    assert not edge_ready_for_navigation(edge, ())
    assert not edge.grants_theorem_authority


def test_named_replay_receipt_must_be_resolved_for_navigation():
    sub = subject()
    edge = EdgeAssuranceReceipt("e", sub, "a", "b", EdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL, "r")
    assert edge.declares_validated_operational_edge
    assert not edge_ready_for_navigation(edge, ())
    resolution = ResolvedOperationalReceipt("r", sub, "replay", "artifact", True)
    assert edge_ready_for_navigation(edge, (resolution,))


def test_validated_edge_requires_receipt():
    with pytest.raises(ValueError):
        EdgeAssuranceReceipt("e", subject(), "a", "b", EdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL, None)


def test_reachability_quantifier_is_not_implicit():
    with pytest.raises(ValueError):
        ReachabilityClaim("r", subject(), "s", "t", ReachabilityQuantifier.ALMOST_SURE)
    r = ReachabilityClaim("r", subject(), "s", "t", ReachabilityQuantifier.PROBABILITY_AT_LEAST, "p", .9)
    assert not r.grants_target_authority


def test_exact_quotient_needs_two_way_semantics():
    with pytest.raises(ValueError):
        NavigationAbstractionContract("a", subject(), "c", "q", "map", "conc", AbstractionClass.EXACT_QUOTIENT, "fwd")


def test_geometry_stales_when_operational_world_changes():
    g = GeometryArtifact("g", subject(), "learn", ConstructibilityClass.APPROXIMATE_LEARNED, CostVector(construction=1), 10, 10)
    assert not g.stale_for(subject())
    assert g.stale_for(subject(operator_basis_hash="ops2"))


def test_learning_receipt_fresh_claim_detects_leakage():
    base = dict(
        receipt_id="r", geometry_id="g", subject=subject(), training_subject_hashes=("s",),
        behavior_policy_ids=("p",), sampling_process_id="sam", label_source_id="verifier", code_hash="code",
        model_or_algorithm_hash="model", train_split_hash="tr", dev_split_hash="dev", fresh_split_hash="fresh",
        seen_operator_ids=("o",), seen_chart_ids=("c",), seen_scale_ids=("sc",), support_diagnostic_id="support",
        ood_detector_id="ood", exploration_reopen_policy_id="reopen", fresh_gold_distance_accessed=False,
        fresh_labels_accessed_during_selection=False,
    )
    clean = GeometryLearningReceipt(fresh_gold_route_accessed=False, **base)
    leaky = GeometryLearningReceipt(fresh_gold_route_accessed=True, **base)
    assert clean.leakage_free_for_fresh_claim
    assert not leaky.leakage_free_for_fresh_claim




def test_learned_geometry_needs_matching_clean_learning_receipt():
    sub = subject()
    receipt = GeometryLearningReceipt(
        receipt_id="lr", geometry_id="g", subject=sub, training_subject_hashes=("s",),
        behavior_policy_ids=("p",), sampling_process_id="sam", label_source_id="labels", code_hash="code",
        model_or_algorithm_hash="model", train_split_hash="tr", dev_split_hash="dev", fresh_split_hash="fresh",
        seen_operator_ids=("o",), seen_chart_ids=("c",), seen_scale_ids=("sc",), fresh_gold_route_accessed=False,
        fresh_gold_distance_accessed=False, fresh_labels_accessed_during_selection=False, support_diagnostic_id="support",
        ood_detector_id="ood", exploration_reopen_policy_id="reopen",
    )
    artifact = GeometryArtifact("g", sub, "lr", ConstructibilityClass.APPROXIMATE_LEARNED, CostVector(construction=1), 10, 10)
    assert assess_geometry_for_fresh_routing(artifact, current_subject=sub) is GeometryUseVerdict.CANNOT_CHECK
    assert assess_geometry_for_fresh_routing(artifact, current_subject=sub, learning_receipt=receipt) is GeometryUseVerdict.READY_FOR_FRESH_ROUTING_TEST


def test_total_cost_gain_requires_accounting_receipt():
    sub = subject()
    a = GeometryArtifact("g", sub, None, ConstructibilityClass.EXACT_FINITE_ENUMERATION, CostVector(construction=5), 10, 10, 100, 90)
    assert not a.demonstrates_net_cost_gain
    b = GeometryArtifact("g", sub, None, ConstructibilityClass.EXACT_FINITE_ENUMERATION, CostVector(construction=5), 10, 10, 100, 90, "accounting")
    assert b.demonstrates_net_cost_gain


def test_basin_fails_if_candidate_edges_are_admitted():
    with pytest.raises(ValueError):
        NavigationBasinCertificate("b", subject(), "h", "mem", "mem-proof", "prog", "prog-proof", "rank", "goal", "boundary", "boundary-proof", EdgeAssuranceClass.CANDIDATE_OPERATIONAL)


def test_basin_theorem_receipts_must_resolve():
    sub = subject()
    basin = NavigationBasinCertificate("b", sub, "h", "mem", "mem-proof", "prog", "prog-proof", "rank", "goal", "boundary", "boundary-proof", EdgeAssuranceClass.REPLAY_VALIDATED_OPERATIONAL)
    assert not navigation_basin_ready_for_use(basin, ())
    rs = tuple(
        ResolvedOperationalReceipt(rid, sub, "verifier", f"art:{rid}", True)
        for rid in ("mem-proof", "prog-proof", "rank", "goal", "boundary-proof")
    )
    assert navigation_basin_ready_for_use(basin, rs)


def test_portal_non_preservation_is_load_bearing_and_receipts_resolve():
    sub = subject()
    p = PortalWitness("p", sub, "a", "b", "s", "t", frozenset({"mass"}), frozenset({"phase"}), ("bound",), "verify")
    assert p.declares_preservation_for(frozenset({"mass"}))
    assert not p.declares_preservation_for(frozenset({"phase"}))
    assert not portal_ready_for_use(p, frozenset({"mass"}), ())
    resolutions = (
        ResolvedOperationalReceipt("verify", sub, "verifier", "v-art", True),
        ResolvedOperationalReceipt("bound", sub, "verifier", "b-art", True),
    )
    assert portal_ready_for_use(p, frozenset({"mass"}), resolutions)


def test_search_path_is_not_proof_constellation():
    sub = subject()
    t = SearchTrajectoryReceipt("t", sub, "s", "x", ("e",), "policy", "terminal-check")
    assert t.declares_verified_terminal
    assert not trajectory_terminal_is_resolved(t, ())
    assert trajectory_terminal_is_resolved(
        t, (ResolvedOperationalReceipt("terminal-check", sub, "verifier", "artifact", True),)
    )
    assert not t.is_proof_certificate
    c = SolutionConstellationBinding("c", "root", "dag", "root-check", ("t",))
    assert c.proof_dag_hash == "dag"


def test_amalgamation_requires_joint_obligations_and_root_replay():
    incomplete = AmalgamationReceipt("a", "root", ("c1",), ("overlap",), "subst", ("assump",), ("repr",), (), "parent", "root-v")
    assert incomplete.verdict is AmalgamationVerdict.INCOMPLETE
    ready = AmalgamationReceipt("a", "root", ("c1",), ("overlap",), "subst", ("assump",), ("repr",), ("joint",), "parent", "root-v")
    assert ready.verdict is AmalgamationVerdict.READY_FOR_ROOT_AUTHORITY_GATE
    assert not amalgamation_ready_for_root_gate(ready, subject(), ())
    ids = ("overlap", "subst", "assump", "repr", "joint", "parent", "root-v")
    rs = tuple(ResolvedOperationalReceipt(r, subject(), "verifier", f"art:{r}", True) for r in ids)
    assert amalgamation_ready_for_root_gate(ready, subject(), rs)
    assert not ready.grants_authority


def test_solve_projection_never_mints_authority():
    s = SolveProjection("p", subject(), "problem", "assumptions", "target", (), None, (), None, True)
    assert not s.grants_scientific_authority and not s.grants_proof_authority
