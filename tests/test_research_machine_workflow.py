import pytest

from rakl.research_machine_workflow import (
    KnowledgeAcquisitionRound,
    KnowledgeDecision,
    KnowledgeSaturationPolicy,
    KnowledgeSearchMode,
    assess_knowledge_saturation,
    knowledge_round_metrics,
)


def _round(
    rid,
    route,
    novelty=0,
    *,
    independent=True,
    mode=KnowledgeSearchMode.INITIAL_BROAD,
    residual_ids=(),
    sources=10,
    relevant=5,
    cost=10.0,
):
    semantic = tuple(f"{rid}-s{i}" for i in range(novelty))
    return KnowledgeAcquisitionRound(
        round_id=rid,
        route_family=route,
        mode=mode,
        independent_route=independent,
        query_ids=(f"q-{rid}",),
        source_ids=tuple(f"{rid}-p{i}" for i in range(sources)),
        relevant_source_ids=tuple(f"{rid}-p{i}" for i in range(relevant)),
        retained_semantic_ids=semantic,
        new_facet_ids=semantic[:1],
        new_mechanism_ids=semantic[1:2],
        cost_policy_id="cost-v1",
        cost=cost,
        evidence_pointers=(f"ev-{rid}",),
        residual_ids=residual_ids,
    )


def _policy():
    return KnowledgeSaturationPolicy(
        required_route_families=("foundational", "counterexample", "adjacent"),
        min_independent_flat_routes=3,
        window=3,
    )


def test_no_rounds_requires_search():
    result = assess_knowledge_saturation((), policy=_policy())
    assert result.decision is KnowledgeDecision.CONTINUE_SEARCH
    assert result.missing_route_families == ("foundational", "counterexample", "adjacent")


def test_new_semantic_objects_prevent_saturation():
    rounds = (
        _round("r1", "foundational", 0),
        _round("r2", "counterexample", 0),
        _round("r3", "adjacent", 1),
    )
    result = assess_knowledge_saturation(rounds, policy=_policy())
    assert result.decision is KnowledgeDecision.CONTINUE_SEARCH
    assert "KNOWLEDGE:recent_retained_novelty" in result.reasons


def test_flat_independent_routes_establish_bounded_saturation():
    rounds = (
        _round("r1", "foundational", 0),
        _round("r2", "counterexample", 0),
        _round("r3", "adjacent", 0),
    )
    result = assess_knowledge_saturation(rounds, policy=_policy())
    assert result.decision is KnowledgeDecision.PROCEED_OBJECT_WORK
    assert result.bounded_saturated is True


def test_many_duplicate_sources_do_not_substitute_for_route_coverage():
    rounds = (
        _round("r1", "foundational", 0, sources=100, relevant=80),
        _round("r2", "foundational", 0, sources=100, relevant=80),
        _round("r3", "foundational", 0, sources=100, relevant=80),
    )
    result = assess_knowledge_saturation(rounds, policy=_policy())
    assert result.decision is KnowledgeDecision.CONTINUE_SEARCH
    assert set(result.missing_route_families) == {"counterexample", "adjacent"}


def test_native_knowledge_residual_reopens_previously_flat_fiber():
    rounds = (
        _round("r1", "foundational", 0),
        _round("r2", "counterexample", 0),
        _round("r3", "adjacent", 0),
    )
    result = assess_knowledge_saturation(
        rounds,
        policy=_policy(),
        active_knowledge_residual_ids=("residual-new-coordinate",),
    )
    assert result.decision is KnowledgeDecision.TARGETED_REFRESH_REQUIRED


def test_freshness_event_reopens_without_erasing_prior_history():
    rounds = (
        _round("r1", "foundational", 0),
        _round("r2", "counterexample", 0),
        _round("r3", "adjacent", 0),
    )
    result = assess_knowledge_saturation(rounds, policy=_policy(), freshness_stale=True)
    assert result.decision is KnowledgeDecision.FRESHNESS_REFRESH_REQUIRED
    assert result.source_count == 30


def test_metrics_measure_semantic_yield_not_only_inventory():
    round_ = _round("r1", "foundational", 2, sources=20, relevant=10, cost=40.0)
    metrics = knowledge_round_metrics(round_)
    assert metrics["sources_processed"] == 20
    assert metrics["semantic_novelty"] == 2
    assert metrics["semantic_yield_per_source"] == pytest.approx(0.1)
    assert metrics["cost_per_semantic_object"] == pytest.approx(20.0)


def test_categorized_semantic_objects_must_be_retained():
    with pytest.raises(ValueError, match="categorized semantic objects"):
        KnowledgeAcquisitionRound(
            round_id="r1",
            route_family="foundational",
            mode=KnowledgeSearchMode.INITIAL_BROAD,
            independent_route=True,
            query_ids=("q",),
            source_ids=("p",),
            relevant_source_ids=("p",),
            retained_semantic_ids=(),
            new_facet_ids=("facet",),
            cost_policy_id="cost-v1",
        )


def test_relevant_sources_must_be_processed():
    with pytest.raises(ValueError, match="subset"):
        KnowledgeAcquisitionRound(
            round_id="r1",
            route_family="foundational",
            mode=KnowledgeSearchMode.INITIAL_BROAD,
            independent_route=True,
            query_ids=("q",),
            source_ids=("p1",),
            relevant_source_ids=("p2",),
            retained_semantic_ids=(),
            cost_policy_id="cost-v1",
        )
