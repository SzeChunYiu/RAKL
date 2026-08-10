from rakl.open_world_discovery import (
    AssimilationStatus,
    CapabilityOwnerRecord,
    CapabilityRequirement,
    DiscoveryClosureStatus,
    DiscoveryRouteRecord,
    DiscoveryWorkspaceCandidate,
    DiscoveryWorkspacePartition,
    FunctionalSignature,
    HiddenNameBenchmark,
    MechanismCandidate,
    OWMDRouteKind,
    audit_bounded_discovery_closure,
    evaluate_hidden_name_benchmark,
    select_discovery_workspace,
)


def _signature() -> FunctionalSignature:
    return FunctionalSignature(
        inputs=("many parallel processes",),
        outputs=("small active subset shared downstream",),
        constraints=("bounded capacity",),
        relations=("competitive admission", "broad reuse"),
        dynamics=("maintenance", "displacement", "eviction"),
        failure_signatures=("prominence must not create truth",),
    )


def _requirement() -> CapabilityRequirement:
    return CapabilityRequirement(
        function_id="workspace-selection-broadcast",
        subsystem="research-cognition",
        description="select a bounded active subset and expose it to heterogeneous operators",
        impact="high",
        signature=_signature(),
        core_vocabulary=("knowledge lattice", "epistemic authority", "workspace"),
    )


def _owner() -> CapabilityOwnerRecord:
    return CapabilityOwnerRecord(
        function_id="workspace-selection-broadcast",
        mechanism_id="workspace-gate-v1",
        scope="proposal-only research cognition",
        preconditions=("typed candidates",),
        postconditions=("bounded workspace frame",),
        evidence_ids=("spec:workspace",),
        test_ids=("test_workspace_gate",),
        failure_semantics=("fail closed when reservations cannot be met",),
    )


def _routes():
    records = []
    for kind in OWMDRouteKind:
        if kind is OWMDRouteKind.CROSS_LANGUAGE:
            continue
        query = f"probe {kind.value.lower()} for bounded coordination mechanisms"
        records.append(
            DiscoveryRouteRecord(
                route_id=f"route:{kind.value.lower()}",
                kind=kind,
                query=query,
                completed=True,
                lexically_independent=(kind is OWMDRouteKind.FUNCTION_ONLY),
                stable=True,
                searched_through="2026-08-10" if kind is OWMDRouteKind.FRESHNESS else None,
            )
        )
    return tuple(records)


def test_owner_record_cannot_be_a_label_only():
    try:
        CapabilityOwnerRecord(
            function_id="f",
            mechanism_id="m",
            scope="scope",
            preconditions=(),
            postconditions=("out",),
            evidence_ids=("e",),
            test_ids=("t",),
            failure_semantics=("fail",),
        )
    except ValueError as error:
        assert "preconditions" in str(error)
    else:
        raise AssertionError("label-only owner record should fail")


def test_bounded_discovery_closure_requires_ontology_escape_and_freshness():
    routes = tuple(route for route in _routes() if route.kind is not OWMDRouteKind.FRESHNESS)
    routes = tuple(
        DiscoveryRouteRecord(
            route_id=route.route_id,
            kind=route.kind,
            query=route.query,
            completed=route.completed,
            candidate_ids=route.candidate_ids,
            lexically_independent=False,
            stable=route.stable,
            searched_through=route.searched_through,
        )
        for route in routes
    )
    report = audit_bounded_discovery_closure(
        _requirement(),
        routes,
        owner=_owner(),
        independent_omission_review=True,
        nearest_work_equivalence_audit=True,
        unresolved_preserved=True,
    )
    assert report.status is DiscoveryClosureStatus.OPEN
    assert "FRESHNESS" in report.missing_route_kinds
    assert not report.lexical_independence_passed
    assert "freshness_scan_missing" in report.reasons


def test_bounded_discovery_closure_can_close_with_owner_but_never_absolute():
    report = audit_bounded_discovery_closure(
        _requirement(),
        _routes(),
        owner=_owner(),
        independent_omission_review=True,
        nearest_work_equivalence_audit=True,
        unresolved_preserved=True,
    )
    assert report.status is DiscoveryClosureStatus.BOUNDED_CLOSED
    assert report.owner_mechanism_id == "workspace-gate-v1"
    assert report.freshness_cutoff == "2026-08-10"
    assert report.absolute_complete is False


def test_explicit_open_fiber_preserves_unresolved_function_without_fake_owner():
    candidate = MechanismCandidate(
        candidate_id="remote-mechanism",
        mechanism_class="remote",
        source_ids=("paper:remote",),
        route_ids=("route:function_only",),
        functional_fit=0.8,
        structural_fit=0.4,
        evidence_quality=0.7,
        novelty_threat=0.5,
        transfer_cost=2.0,
        assimilation=AssimilationStatus.UNRESOLVED,
    )
    report = audit_bounded_discovery_closure(
        _requirement(),
        _routes(),
        explicit_open_fiber="fiber:workspace-selection-unresolved",
        candidates=(candidate,),
        independent_omission_review=True,
        nearest_work_equivalence_audit=True,
        unresolved_preserved=True,
    )
    assert report.status is DiscoveryClosureStatus.BOUNDED_CLOSED
    assert report.owner_mechanism_id is None
    assert report.explicit_open_fiber == "fiber:workspace-selection-unresolved"
    assert report.unresolved_candidate_ids == ("remote-mechanism",)


def test_discovery_workspace_reserves_remote_challenge_history_and_freshness():
    candidates = (
        DiscoveryWorkspaceCandidate("near-1", DiscoveryWorkspacePartition.NEAR, 100),
        DiscoveryWorkspaceCandidate("remote-1", DiscoveryWorkspacePartition.REMOTE, 5),
        DiscoveryWorkspaceCandidate("challenge-1", DiscoveryWorkspacePartition.CHALLENGE, 4),
        DiscoveryWorkspaceCandidate("history-1", DiscoveryWorkspacePartition.HISTORICAL, 3),
        DiscoveryWorkspaceCandidate("fresh-1", DiscoveryWorkspacePartition.FRESH, 2),
    )
    frame = select_discovery_workspace(candidates, capacity=5)
    assert set(frame.selected_candidate_ids) == {item.candidate_id for item in candidates}
    assert dict(frame.partition_counts)["REMOTE"] == 1
    assert dict(frame.partition_counts)["CHALLENGE"] == 1
    assert dict(frame.partition_counts)["HISTORICAL"] == 1
    assert dict(frame.partition_counts)["FRESH"] == 1


def _mechanism(candidate_id, mechanism_class, route_id):
    return MechanismCandidate(
        candidate_id=candidate_id,
        mechanism_class=mechanism_class,
        source_ids=(f"source:{candidate_id}",),
        route_ids=(route_id,),
        functional_fit=0.9,
        structural_fit=0.8,
        evidence_quality=0.8,
        novelty_threat=0.7,
        transfer_cost=1.0,
        assimilation=AssimilationStatus.COMPLEMENTARY,
    )


def test_gwt_omission_hidden_name_benchmark_requires_independent_retrieval_family():
    routes = (
        DiscoveryRouteRecord(
            "function",
            OWMDRouteKind.FUNCTION_ONLY,
            "systems selecting a bounded active subset from parallel processes for broad downstream reuse",
            True,
            lexically_independent=True,
        ),
    )
    candidates = (
        _mechanism("blackboard", "BLACKBOARD_ARCHITECTURE", "function"),
        _mechanism("gwt", "GLOBAL_WORKSPACE", "function"),
        _mechanism("prior", "CONSCIOUSNESS_PRIOR", "function"),
        _mechanism("shared", "SHARED_NEURAL_WORKSPACE", "function"),
        _mechanism("jspace", "J_SPACE", "function"),
    )
    benchmark = HiddenNameBenchmark(
        benchmark_id="GWT-OMISSION-01",
        withheld_terms=("global workspace", "consciousness", "J-space", "blackboard"),
        required_mechanism_classes=(
            "BLACKBOARD_ARCHITECTURE",
            "GLOBAL_WORKSPACE",
            "CONSCIOUSNESS_PRIOR",
            "SHARED_NEURAL_WORKSPACE",
            "J_SPACE",
        ),
    )
    report = evaluate_hidden_name_benchmark(benchmark, routes, candidates)
    assert report.passed
    assert not report.missing_mechanism_classes
    assert not report.leaked_route_ids


def test_hidden_name_benchmark_rejects_withheld_term_leak():
    routes = (
        DiscoveryRouteRecord(
            "bad-function",
            OWMDRouteKind.FUNCTION_ONLY,
            "find global workspace systems",
            True,
            lexically_independent=True,
        ),
    )
    benchmark = HiddenNameBenchmark(
        benchmark_id="GWT-OMISSION-01",
        withheld_terms=("global workspace",),
        required_mechanism_classes=("GLOBAL_WORKSPACE",),
    )
    report = evaluate_hidden_name_benchmark(
        benchmark,
        routes,
        (_mechanism("gwt", "GLOBAL_WORKSPACE", "bad-function"),),
    )
    assert not report.passed
    assert report.leaked_route_ids == ("bad-function",)
