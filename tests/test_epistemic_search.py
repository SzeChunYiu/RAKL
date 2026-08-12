from dataclasses import replace

import pytest

from rakl.epistemic_search import (
    EpistemicSpamFlag,
    EvidenceStance,
    ScientificSearchQuestion,
    SearchCandidate,
    SearchFeedback,
    SearchIndexKind,
    SearchRankVector,
    SearchVertical,
    bias_corrected_feedback_value,
    build_interaction_space,
    compile_search_intents,
    detect_epistemic_spam,
    diversify_candidates,
    dominates,
    pareto_front,
)


def _question(**overrides):
    values = dict(
        question_id="q1",
        root_goal="Determine whether mechanism M is identified in regime R.",
        atom_id="atom-1",
        residual_terms=("mechanism M", "regime R"),
        structural_coordinates=("observational_equivalence", "regime_shift"),
        unresolved_obligations=("find discriminating intervention",),
        source_native_terms=("identifiability",),
        semantic_expansions=("causal mechanism", "observationally equivalent"),
        candidate_mechanism="M",
    )
    values.update(overrides)
    return ScientificSearchQuestion(**values)


def _rank(**overrides):
    values = dict(
        query_relevance=0.8,
        root_obligation_relevance=0.8,
        expected_information_gain=0.7,
        structural_fit=0.7,
        context_alignment=0.8,
        source_authenticity=0.9,
        freshness=0.7,
        independent_root_contribution=0.7,
        contradiction_value=0.1,
        negative_result_value=0.1,
        novel_route_value=0.3,
        graph_centrality=0.5,
        retrieval_cost=1.0,
        verification_cost=1.0,
        failure_risk=0.1,
    )
    values.update(overrides)
    return SearchRankVector(**values)


def _candidate(candidate_id, **overrides):
    values = dict(
        vertical=SearchVertical.LITERATURE,
        index_kinds=(SearchIndexKind.LEXICAL, SearchIndexKind.SEMANTIC),
        rank=_rank(),
        evidence_root_id=f"root-{candidate_id}",
        canonical_content_id=f"content-{candidate_id}",
        mechanism_family="M",
        stance=EvidenceStance.SUPPORT,
    )
    values.update(overrides)
    return SearchCandidate(candidate_id=candidate_id, **values)


def test_query_compiler_keeps_every_expansion_bound_to_same_root_goal():
    question = _question()
    intents = compile_search_intents(question)
    assert len(intents) >= 10
    assert {item.root_goal_hash for item in intents} == {question.root_goal_hash}
    assert {item.atom_id for item in intents} == {question.atom_id}
    assert all(item.grants_scientific_authority is False for item in intents)


def test_all_query_term_fields_reject_blank_entries():
    for field in (
        "residual_terms",
        "structural_coordinates",
        "unresolved_obligations",
        "source_native_terms",
        "semantic_expansions",
    ):
        with pytest.raises(ValueError, match="blank search terms"):
            _question(**{field: ("valid", "   ")})
    with pytest.raises(ValueError, match="candidate_mechanism cannot be blank"):
        _question(candidate_mechanism="   ")


def test_pareto_dominance_is_routing_only_not_truth():
    strong = _candidate("strong", rank=_rank(query_relevance=0.9, retrieval_cost=0.5))
    weak = _candidate("weak", rank=_rank(query_relevance=0.5, retrieval_cost=2.0))
    assert dominates(strong, weak) is True
    assert pareto_front((strong, weak)) == (strong,)
    assert strong.grants_scientific_authority is False
    assert strong.grants_evidence_independence is False


def test_graph_centrality_is_not_a_pareto_benefit_coordinate():
    scientifically_better = _candidate(
        "better",
        rank=_rank(query_relevance=0.9, graph_centrality=0.01),
    )
    popular_but_weaker = _candidate(
        "popular",
        rank=_rank(query_relevance=0.5, graph_centrality=1.0),
    )
    assert dominates(scientifically_better, popular_but_weaker) is True
    assert pareto_front((scientifically_better, popular_but_weaker)) == (scientifically_better,)


def test_high_citation_centrality_cannot_beat_root_relevance_in_routing_tiebreak():
    popular_but_shallow = _candidate(
        "popular",
        rank=_rank(
            root_obligation_relevance=0.2,
            expected_information_gain=0.2,
            context_alignment=0.3,
            graph_centrality=1.0,
        ),
        mechanism_family="popular-family",
    )
    root_relevant = _candidate(
        "root-relevant",
        rank=_rank(
            root_obligation_relevance=0.95,
            expected_information_gain=0.9,
            context_alignment=0.9,
            graph_centrality=0.05,
        ),
        mechanism_family="root-family",
    )
    selected = diversify_candidates(
        (popular_but_shallow, root_relevant),
        limit=1,
        preserve_counterevidence=False,
    )
    assert selected == (root_relevant,)


def test_diversification_preserves_counterevidence_and_limits_same_root_echoes():
    support_a = _candidate("support-a", evidence_root_id="shared-root")
    support_b = _candidate("support-b", evidence_root_id="shared-root")
    refute = _candidate(
        "refute",
        stance=EvidenceStance.REFUTE,
        mechanism_family="alternative",
        rank=_rank(contradiction_value=0.95),
    )
    selected = diversify_candidates((support_a, support_b, refute), limit=2)
    assert refute in selected
    same_root_selected = [item for item in selected if item.evidence_root_id == "shared-root"]
    assert len(same_root_selected) <= 1


def test_anti_epistemic_spam_flags_echoes_retractions_leaks_and_keyword_stuffing():
    echo_a = _candidate("a", evidence_root_id="same")
    echo_b = _candidate("b", evidence_root_id="same", synthetic_or_generated_echo=True)
    bad = _candidate(
        "bad",
        retracted_or_superseded=True,
        self_citation_loop=True,
        benchmark_target_leak=True,
        keyword_overlap_ratio=0.99,
        substantive_match_score=0.05,
    )
    by_id = {
        item.candidate_id: set(item.flags)
        for item in detect_epistemic_spam((echo_a, echo_b, bad))
    }
    assert EpistemicSpamFlag.SAME_ROOT_ECHO in by_id["a"]
    assert EpistemicSpamFlag.SAME_ROOT_ECHO in by_id["b"]
    assert EpistemicSpamFlag.SYNTHETIC_CONSENSUS in by_id["b"]
    assert EpistemicSpamFlag.RETRACTED_OR_SUPERSEDED in by_id["bad"]
    assert EpistemicSpamFlag.SELF_CITATION_LOOP in by_id["bad"]
    assert EpistemicSpamFlag.BENCHMARK_TARGET_LEAK in by_id["bad"]
    assert EpistemicSpamFlag.KEYWORD_STUFFING_SUSPECTED in by_id["bad"]


def test_benchmark_target_leak_is_excluded_from_interaction_space():
    leaked = _candidate(
        "leaked",
        benchmark_target_leak=True,
        rank=_rank(root_obligation_relevance=1.0),
    )
    clean = _candidate("clean")
    question = _question()
    space = build_interaction_space(
        question,
        compile_search_intents(question),
        (leaked, clean),
        space_id="space-1",
        max_candidates=2,
    )
    assert "leaked" not in space.candidate_ids
    assert "clean" in space.candidate_ids


def test_interaction_space_is_bounded_deterministic_and_problem_fibre_bindable():
    question = _question()
    intents = compile_search_intents(question)
    candidates = tuple(_candidate(f"c{i}", mechanism_family=f"m{i}") for i in range(4))
    a = build_interaction_space(
        question,
        intents,
        candidates,
        space_id="space",
        max_candidates=2,
        problem_fibre_snapshot_hash="fibre-hash",
        allowed_tool_ids=("tool-b", "tool-a"),
    )
    b = build_interaction_space(
        question,
        intents,
        candidates,
        space_id="space",
        max_candidates=2,
        problem_fibre_snapshot_hash="fibre-hash",
        allowed_tool_ids=("tool-a", "tool-b"),
    )
    assert len(a.candidate_ids) == 2
    assert a.snapshot_hash == b.snapshot_hash
    assert a.problem_fibre_snapshot_hash == "fibre-hash"
    assert a.allowed_tool_ids == ("tool-a", "tool-b")
    assert a.grants_scientific_authority is False


def test_query_drift_is_rejected_when_building_interaction_space():
    question = _question()
    intents = list(compile_search_intents(question))
    intents[0] = replace(intents[0], root_goal_hash="wrong")
    with pytest.raises(ValueError, match="query drift"):
        build_interaction_space(
            question,
            intents,
            (_candidate("c1"),),
            space_id="space",
            max_candidates=1,
        )


def test_search_feedback_is_propensity_corrected_routing_signal_only():
    feedback = SearchFeedback(
        question_id="q1",
        intent_id="intent-1",
        candidate_id="c1",
        rank_position=1,
        exposure_probability=0.25,
        inspected=True,
        changed_action=True,
        verified_downstream_success=True,
        cost=2.0,
    )
    assert bias_corrected_feedback_value(feedback) == 4.0
    assert feedback.grants_scientific_authority is False

    unseen = replace(feedback, inspected=False)
    assert bias_corrected_feedback_value(unseen) == 0.0


def test_duplicate_canonical_content_does_not_fill_interaction_space_twice():
    a = _candidate("a", canonical_content_id="same-content", mechanism_family="m1")
    b = _candidate("b", canonical_content_id="same-content", mechanism_family="m2")
    c = _candidate("c", mechanism_family="m3")
    selected = diversify_candidates((a, b, c), limit=3, preserve_counterevidence=False)
    assert len(
        [item for item in selected if item.canonical_content_id == "same-content"]
    ) == 1
