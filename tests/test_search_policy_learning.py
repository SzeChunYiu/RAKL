from dataclasses import replace

import pytest

from rakl.epistemic_search import (
    EvidenceStance,
    ScientificSearchQuestion,
    SearchCandidate,
    SearchFeedback,
    SearchIndexKind,
    SearchIntentKind,
    SearchRankVector,
    SearchVertical,
)
from rakl.search_policy_learning import (
    FailureDrivenUpdateVerdict,
    SearchFailureReceipt,
    SearchFailureSignature,
    SearchPolicy,
    compile_search_intents_with_policy,
    derive_search_policy_update,
    materialize_search_policy_challenger,
    search_feedback_value_with_policy,
    select_candidates_with_policy,
)


def _receipt(signature, **overrides):
    values = dict(
        failure_id="failure-1",
        question_id="q1",
        policy_version="search-v1",
        signature=signature,
        causal_evidence_ids=("trajectory-case-17", "failure-receipt-17"),
        observed_candidate_ids=("c1", "c2"),
        known_answer_validated=True,
        root_cause_confirmed=True,
        counterfactual_discriminator_passed=True,
        frozen_before_update=True,
    )
    values.update(overrides)
    return SearchFailureReceipt(**values)


def _derive(signature, policy=None, **receipt_overrides):
    incumbent = policy or SearchPolicy("search-v1")
    return derive_search_policy_update(
        _receipt(signature, **receipt_overrides),
        incumbent,
        update_id="upd-1",
        to_policy_version="search-v2",
    )


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
        mechanism_family="m1",
        stance=EvidenceStance.SUPPORT,
        substantive_match_score=0.8,
    )
    values.update(overrides)
    return SearchCandidate(candidate_id=candidate_id, **values)


def _question(**overrides):
    values = dict(
        question_id="q1",
        root_goal="Identify the mechanism behind the residual.",
        atom_id="atom-1",
        residual_terms=("residual", "mechanism"),
        structural_coordinates=(),
        unresolved_obligations=(),
        source_native_terms=(),
        semantic_expansions=tuple(f"semantic-{i}" for i in range(8)),
        candidate_mechanism=None,
    )
    values.update(overrides)
    return ScientificSearchQuestion(**values)


def _successor(signature, policy):
    assessment = _derive(signature, policy)
    assert assessment.verdict is FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED
    assert assessment.proposal is not None
    return assessment, materialize_search_policy_challenger(policy, assessment.proposal)


def test_failure_to_policy_update_is_deterministic_and_bounded():
    incumbent = SearchPolicy("search-v1", max_per_evidence_root=3)
    a = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, incumbent)
    b = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, incumbent)

    assert a.proposal == b.proposal
    assert a.proposal is not None
    assert [(d.parameter, d.old_value, d.new_value) for d in a.proposal.deltas] == [
        ("max_per_evidence_root", 3, 2)
    ]
    assert a.proposal.claims_policy_is_better is False
    assert a.proposal.eligible_for_canonical_promotion is False
    assert a.proposal.grants_scientific_authority is False


def test_no_caller_supplied_random_delta_surface_exists():
    assessment = _derive(
        SearchFailureSignature.QUERY_DRIFT,
        policy=SearchPolicy("search-v1", max_semantic_expansion_terms=8),
    )
    assert assessment.proposal is not None
    assert tuple(delta.parameter for delta in assessment.proposal.deltas) == (
        "max_semantic_expansion_terms",
    )
    with pytest.raises(TypeError):
        derive_search_policy_update(  # type: ignore[call-arg]
            _receipt(SearchFailureSignature.QUERY_DRIFT),
            SearchPolicy("search-v1"),
            update_id="upd",
            to_policy_version="search-v2",
            arbitrary_delta={"graph_centrality": 999},
        )


def test_unconfirmed_root_cause_does_not_generate_another_idea():
    result = _derive(
        SearchFailureSignature.OVERLY_NARROW_RECALL,
        root_cause_confirmed=False,
    )
    assert result.verdict is FailureDrivenUpdateVerdict.CANNOT_CHECK
    assert result.proposal is None


def test_counterfactual_discriminator_is_required_before_policy_learning():
    result = _derive(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        counterfactual_discriminator_passed=False,
    )
    assert result.verdict is FailureDrivenUpdateVerdict.CANNOT_CHECK
    assert result.proposal is None


def test_failure_receipt_must_be_frozen_and_bound_to_exact_incumbent():
    unknown = _derive(SearchFailureSignature.LOW_INFORMATION_GAIN, frozen_before_update=None)
    assert unknown.verdict is FailureDrivenUpdateVerdict.CANNOT_CHECK

    posthoc = _derive(SearchFailureSignature.LOW_INFORMATION_GAIN, frozen_before_update=False)
    assert posthoc.verdict is FailureDrivenUpdateVerdict.INVALID

    wrong_policy = derive_search_policy_update(
        _receipt(SearchFailureSignature.LOW_INFORMATION_GAIN, policy_version="old-policy"),
        SearchPolicy("search-v1"),
        update_id="upd",
        to_policy_version="search-v2",
    )
    assert wrong_policy.verdict is FailureDrivenUpdateVerdict.INVALID


def test_saturated_registered_repair_returns_no_repair_not_random_idea():
    policy = SearchPolicy("search-v1", max_per_evidence_root=1)
    result = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, policy)
    assert result.verdict is FailureDrivenUpdateVerdict.NO_REGISTERED_POLICY_REPAIR
    assert result.proposal is None
    assert "do not substitute an unrelated random idea" in result.reasons[0]


def test_query_drift_failure_changes_next_query_expansion():
    policy_t = SearchPolicy("search-v1", max_semantic_expansion_terms=8)
    before = compile_search_intents_with_policy(_question(), policy_t)
    semantic_before = next(x for x in before if x.kind is SearchIntentKind.SEMANTIC_EXPANSION)
    assert len(semantic_before.terms) == 8

    _, policy_t1 = _successor(SearchFailureSignature.QUERY_DRIFT, policy_t)
    after = compile_search_intents_with_policy(_question(), policy_t1)
    semantic_after = next(x for x in after if x.kind is SearchIntentKind.SEMANTIC_EXPANSION)
    assert len(semantic_after.terms) == 6


def test_missed_retraction_failure_changes_next_selection():
    popular = _candidate("popular", rank=_rank(root_obligation_relevance=0.99), mechanism_family="m-pop")
    retraction = _candidate(
        "retraction",
        stance=EvidenceStance.RETRACTION_CORRECTION,
        rank=_rank(root_obligation_relevance=0.10),
        mechanism_family="m-ret",
    )
    policy_t = SearchPolicy(
        "search-v1",
        max_candidates=1,
        require_freshness_retraction_intent=False,
        preserve_retraction_slot=False,
    )
    assert select_candidates_with_policy((popular, retraction), policy_t) == (popular,)

    _, policy_t1 = _successor(SearchFailureSignature.MISSED_RETRACTION_OR_SUPERSESSION, policy_t)
    assert select_candidates_with_policy((popular, retraction), policy_t1) == (retraction,)
    intents = compile_search_intents_with_policy(_question(residual_terms=()), policy_t1)
    assert SearchIntentKind.FRESHNESS_RETRACTION in {x.kind for x in intents}


def test_missed_negative_result_failure_changes_next_selection():
    support = _candidate("support", rank=_rank(root_obligation_relevance=0.99), mechanism_family="m-s")
    negative = _candidate(
        "negative",
        stance=EvidenceStance.NEGATIVE_RESULT,
        rank=_rank(root_obligation_relevance=0.10),
        mechanism_family="m-n",
    )
    policy_t = SearchPolicy(
        "search-v1",
        max_candidates=1,
        require_negative_result_intent=False,
        preserve_negative_result_slot=False,
        preserve_counterevidence=False,
    )
    assert select_candidates_with_policy((support, negative), policy_t) == (support,)

    _, policy_t1 = _successor(SearchFailureSignature.MISSED_NEGATIVE_RESULT, policy_t)
    assert select_candidates_with_policy((support, negative), policy_t1) == (negative,)


def test_structural_miss_failure_reserves_structural_candidate_next_time():
    surface = _candidate("surface", rank=_rank(root_obligation_relevance=0.99), mechanism_family="m-surface")
    structural = _candidate(
        "structural",
        index_kinds=(SearchIndexKind.STRUCTURAL,),
        rank=_rank(root_obligation_relevance=0.10),
        mechanism_family="m-struct",
    )
    policy_t = SearchPolicy("search-v1", max_candidates=1, preserve_structural_slot=False)
    assert select_candidates_with_policy((surface, structural), policy_t) == (surface,)

    _, policy_t1 = _successor(SearchFailureSignature.SURFACE_MATCH_STRUCTURAL_MISS, policy_t)
    assert select_candidates_with_policy((surface, structural), policy_t1) == (structural,)


def test_method_obligation_failure_reserves_method_candidate_next_time():
    literature = _candidate("paper", rank=_rank(root_obligation_relevance=0.99), mechanism_family="m-paper")
    method = _candidate(
        "method",
        vertical=SearchVertical.METHOD_TOOL,
        index_kinds=(SearchIndexKind.METHOD_OPERATOR,),
        rank=_rank(root_obligation_relevance=0.10),
        mechanism_family="m-method",
    )
    policy_t = SearchPolicy("search-v1", max_candidates=1, preserve_method_tool_slot=False)
    assert select_candidates_with_policy((literature, method), policy_t) == (literature,)

    _, policy_t1 = _successor(SearchFailureSignature.METHOD_OBLIGATION_UNSERVED, policy_t)
    assert select_candidates_with_policy((literature, method), policy_t1) == (method,)


def test_position_bias_failure_changes_feedback_learning_and_exploration():
    feedback = SearchFeedback(
        question_id="q1",
        intent_id="i1",
        candidate_id="c1",
        rank_position=1,
        exposure_probability=0.25,
        inspected=True,
        changed_action=True,
        verified_downstream_success=True,
        cost=1.0,
    )
    policy_t = SearchPolicy(
        "search-v1",
        max_candidates=2,
        require_propensity_corrected_feedback=False,
        exploration_fraction=0.0,
    )
    assert search_feedback_value_with_policy(feedback, policy_t) == 1.0

    _, policy_t1 = _successor(SearchFailureSignature.POSITION_EXPOSURE_BIAS, policy_t)
    assert search_feedback_value_with_policy(feedback, policy_t1) == 4.0

    exploit_a = _candidate("exploit-a", rank=_rank(root_obligation_relevance=0.99, novel_route_value=0.01), mechanism_family="m-a")
    exploit_b = _candidate("exploit-b", rank=_rank(root_obligation_relevance=0.98, novel_route_value=0.02), mechanism_family="m-b")
    explore = _candidate("explore", rank=_rank(root_obligation_relevance=0.20, novel_route_value=1.0), mechanism_family="m-c")
    before = select_candidates_with_policy((exploit_a, exploit_b, explore), policy_t)
    after = select_candidates_with_policy((exploit_a, exploit_b, explore), policy_t1)
    assert {x.candidate_id for x in before} == {"exploit-a", "exploit-b"}
    assert "explore" in {x.candidate_id for x in after}


def test_root_relevance_failure_filters_the_next_iteration():
    low = _candidate("low", rank=_rank(root_obligation_relevance=0.05), mechanism_family="m-low")
    good = _candidate("good", rank=_rank(root_obligation_relevance=0.90), mechanism_family="m-good")
    policy_t = SearchPolicy("search-v1", min_root_obligation_relevance=0.0)
    assert {x.candidate_id for x in select_candidates_with_policy((low, good), policy_t)} == {"low", "good"}

    _, policy_t1 = _successor(SearchFailureSignature.LOW_ROOT_OBLIGATION_RELEVANCE, policy_t)
    assert {x.candidate_id for x in select_candidates_with_policy((low, good), policy_t1)} == {"good"}


def test_same_root_failure_changes_next_selection():
    same_a = _candidate("a", evidence_root_id="same", mechanism_family="m1")
    same_b = _candidate("b", evidence_root_id="same", mechanism_family="m2")
    independent = _candidate("c", evidence_root_id="independent", mechanism_family="m3")
    policy_t = SearchPolicy("search-v1", max_per_evidence_root=2, max_candidates=3)
    assert len([x for x in select_candidates_with_policy((same_a, same_b, independent), policy_t) if x.evidence_root_id == "same"]) == 2

    _, policy_t1 = _successor(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, policy_t)
    selected = select_candidates_with_policy((same_a, same_b, independent), policy_t1)
    assert len([x for x in selected if x.evidence_root_id == "same"]) == 1
    assert "c" in {x.candidate_id for x in selected}


def test_materialized_successor_is_challenger_only_and_stale_delta_fails():
    incumbent = SearchPolicy("search-v1", max_candidates=10)
    assessment = _derive(SearchFailureSignature.OVERLY_NARROW_RECALL, incumbent)
    assert assessment.proposal is not None
    challenger = materialize_search_policy_challenger(incumbent, assessment.proposal)
    assert challenger.version == "search-v2"
    assert challenger.max_candidates == 12
    assert challenger.grants_scientific_authority is False
    assert assessment.proposal.claims_policy_is_better is False

    with pytest.raises(ValueError, match="stale policy delta"):
        materialize_search_policy_challenger(replace(incumbent, max_candidates=11), assessment.proposal)
