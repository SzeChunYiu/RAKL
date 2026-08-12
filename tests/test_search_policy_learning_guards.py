from rakl.epistemic_search import (
    EvidenceStance,
    ScientificSearchQuestion,
    SearchCandidate,
    SearchIndexKind,
    SearchIntentKind,
    SearchRankVector,
    SearchVertical,
)
from rakl.search_policy_learning import (
    SearchFailureSignature,
    SearchPolicy,
    compile_search_intents_with_policy,
    derive_search_policy_update,
    materialize_search_policy_challenger,
    select_candidates_with_policy,
)
from rakl.search_policy_learning import SearchFailureReceipt


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
        index_kinds=(SearchIndexKind.LEXICAL,),
        rank=_rank(),
        evidence_root_id=f"root-{candidate_id}",
        canonical_content_id=f"content-{candidate_id}",
        mechanism_family=f"m-{candidate_id}",
        stance=EvidenceStance.SUPPORT,
        substantive_match_score=0.8,
    )
    values.update(overrides)
    return SearchCandidate(candidate_id=candidate_id, **values)


def _failure(signature, policy_version="p1"):
    return SearchFailureReceipt(
        failure_id="f1",
        question_id="q1",
        policy_version=policy_version,
        signature=signature,
        causal_evidence_ids=("case-1",),
        known_answer_validated=True,
        root_cause_confirmed=True,
        counterfactual_discriminator_passed=True,
        frozen_before_update=True,
    )


def test_benchmark_target_leak_is_excluded_even_from_reserved_slot():
    leaked_retraction = _candidate(
        "leaked",
        stance=EvidenceStance.RETRACTION_CORRECTION,
        benchmark_target_leak=True,
        rank=_rank(root_obligation_relevance=1.0),
    )
    clean = _candidate("clean", rank=_rank(root_obligation_relevance=0.1))
    policy = SearchPolicy(
        "p1",
        max_candidates=1,
        preserve_retraction_slot=True,
        preserve_counterevidence=True,
    )
    selected = select_candidates_with_policy((leaked_retraction, clean), policy)
    assert selected == (clean,)


def test_benchmark_target_leak_is_excluded_even_from_exploration():
    exploit = _candidate("exploit", rank=_rank(root_obligation_relevance=0.99, novel_route_value=0.0))
    leaked_novel = _candidate(
        "leaked-novel",
        benchmark_target_leak=True,
        rank=_rank(root_obligation_relevance=0.1, novel_route_value=1.0),
    )
    clean_novel = _candidate(
        "clean-novel",
        rank=_rank(root_obligation_relevance=0.2, novel_route_value=0.9),
    )
    policy = SearchPolicy("p1", max_candidates=2, exploration_fraction=0.5, preserve_counterevidence=False)
    selected = select_candidates_with_policy((exploit, leaked_novel, clean_novel), policy)
    ids = {item.candidate_id for item in selected}
    assert "leaked-novel" not in ids
    assert ids == {"exploit", "clean-novel"}


def test_counterevidence_reserves_budget_before_exploration_and_other_slots():
    support = _candidate("support", rank=_rank(root_obligation_relevance=1.0, novel_route_value=1.0))
    structural = _candidate(
        "structural",
        index_kinds=(SearchIndexKind.STRUCTURAL,),
        rank=_rank(root_obligation_relevance=0.9, novel_route_value=0.9),
    )
    refute = _candidate(
        "refute",
        stance=EvidenceStance.REFUTE,
        rank=_rank(root_obligation_relevance=0.1, novel_route_value=0.0),
    )
    policy = SearchPolicy(
        "p1",
        max_candidates=1,
        preserve_counterevidence=True,
        preserve_structural_slot=True,
        exploration_fraction=1.0,
    )
    selected = select_candidates_with_policy((support, structural, refute), policy)
    assert selected == (refute,)


def test_forced_corrective_intent_uses_root_goal_not_semantic_expansion_when_residual_empty():
    question = ScientificSearchQuestion(
        question_id="q1",
        root_goal="Find whether the claimed mechanism survives the regime shift.",
        atom_id="a1",
        residual_terms=(),
        structural_coordinates=(),
        semantic_expansions=("paraphrase one", "paraphrase two"),
    )
    policy = SearchPolicy(
        "p1",
        require_freshness_retraction_intent=True,
        require_negative_result_intent=True,
    )
    intents = compile_search_intents_with_policy(question, policy)
    forced = [
        item
        for item in intents
        if item.kind in {SearchIntentKind.FRESHNESS_RETRACTION, SearchIntentKind.NEGATIVE_RESULT}
    ]
    assert len(forced) == 2
    assert all(item.terms == (question.root_goal,) for item in forced)
    assert all("paraphrase" not in " ".join(item.terms) for item in forced)


def test_confirmed_missed_counterevidence_changes_next_budget_allocation():
    support = _candidate("support", rank=_rank(root_obligation_relevance=1.0))
    refute = _candidate("refute", stance=EvidenceStance.REFUTE, rank=_rank(root_obligation_relevance=0.1))
    incumbent = SearchPolicy("p1", max_candidates=1, preserve_counterevidence=False)
    assert select_candidates_with_policy((support, refute), incumbent) == (support,)

    assessment = derive_search_policy_update(
        _failure(SearchFailureSignature.MISSED_COUNTEREVIDENCE),
        incumbent,
        update_id="u1",
        to_policy_version="p2",
    )
    assert assessment.proposal is not None
    challenger = materialize_search_policy_challenger(incumbent, assessment.proposal)
    assert select_candidates_with_policy((support, refute), challenger) == (refute,)
