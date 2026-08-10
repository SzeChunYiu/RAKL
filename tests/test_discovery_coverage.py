from __future__ import annotations

from rakl.discovery_coverage import (
    DiscoveryCoverageVerdict,
    DiscoveryRouteKind,
    DiscoveryRouteObservation,
    ExogenousCandidate,
    audit_exogenous_candidate,
    function_first_query_intents,
)


def _complete_routes(*, seen: tuple[str, ...] = ()) -> tuple[DiscoveryRouteObservation, ...]:
    return tuple(
        DiscoveryRouteObservation(
            route_id=f"route:{kind.value.lower()}",
            kind=kind,
            query_intent=f"probe {kind.value.lower()}",
            candidate_ids=(seen if kind is DiscoveryRouteKind.INTERACTION_ANALOG else ()),
        )
        for kind in DiscoveryRouteKind
    )


def test_missing_function_first_route_blocks_external_discovery_saturation():
    routes = tuple(
        route for route in _complete_routes()
        if route.kind is not DiscoveryRouteKind.FUNCTION_FIRST
    )
    candidate = ExogenousCandidate.from_facets(
        "note-graph-tool",
        "personal_knowledge_management",
        ("local graph", "backlinks"),
    )
    report = audit_exogenous_candidate(("local graph", "backlinks"), routes, candidate)

    assert report.verdict is DiscoveryCoverageVerdict.ROUTE_COVERAGE_INCOMPLETE
    assert "FUNCTION_FIRST" in report.missing_route_kinds
    assert not report.permits_external_discovery_saturation


def test_later_relevant_user_supplied_concept_is_counted_as_false_negative():
    candidate = ExogenousCandidate.from_facets(
        "obsidian",
        "personal_knowledge_management",
        ("global graph", "local graph", "backlinks", "bidirectional navigation"),
    )
    report = audit_exogenous_candidate(
        ("knowledge map", "local graph", "backlinks"),
        _complete_routes(),
        candidate,
    )

    assert report.verdict is DiscoveryCoverageVerdict.EXOGENOUS_CONCEPT_MISS
    assert report.overlapping_facets == ("backlinks", "local graph")
    assert not report.candidate_seen
    assert not report.permits_external_discovery_saturation


def test_candidate_seen_by_interaction_analogy_route_closes_regression():
    candidate = ExogenousCandidate.from_facets(
        "obsidian",
        "personal_knowledge_management",
        ("global graph", "local graph", "backlinks"),
    )
    report = audit_exogenous_candidate(
        ("local graph", "backlinks"),
        _complete_routes(seen=("obsidian",)),
        candidate,
    )

    assert report.verdict is DiscoveryCoverageVerdict.COVERAGE_COMPLETE_CANDIDATE_SEEN
    assert report.candidate_seen
    assert report.permits_external_discovery_saturation


def test_function_first_queries_do_not_require_prior_framework_name():
    intents = function_first_query_intents(("local graph", "backlinks", "typed relation navigation"))
    assert len(intents) == 4
    assert all("obsidian" not in intent.lower() for intent in intents)
    assert any("regardless of domain" in intent for intent in intents)
