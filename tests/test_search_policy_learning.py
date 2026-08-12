from dataclasses import replace

import pytest

from rakl.epistemic_search import (
    EvidenceStance,
    SearchCandidate,
    SearchIndexKind,
    SearchRankVector,
    SearchVertical,
)
from rakl.search_policy_learning import (
    FailureDrivenUpdateVerdict,
    SearchFailureReceipt,
    SearchFailureSignature,
    SearchPolicy,
    derive_search_policy_update,
    materialize_search_policy_challenger,
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


def test_failure_to_policy_update_is_deterministic_and_bounded():
    incumbent = SearchPolicy("search-v1", max_per_evidence_root=3)
    a = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, incumbent)
    b = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, incumbent)

    assert a.verdict is FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED
    assert b.verdict is FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED
    assert a.proposal == b.proposal
    assert a.proposal is not None
    assert [(d.parameter, d.old_value, d.new_value) for d in a.proposal.deltas] == [
        ("max_per_evidence_root", 3, 2)
    ]
    assert a.proposal.claims_policy_is_better is False
    assert a.proposal.eligible_for_canonical_promotion is False
    assert a.proposal.grants_scientific_authority is False


def test_no_caller_supplied_random_delta_surface_exists():
    assessment = _derive(SearchFailureSignature.QUERY_DRIFT, policy=SearchPolicy("search-v1", require_root_goal_binding=False))
    assert assessment.proposal is not None
    assert tuple(delta.parameter for delta in assessment.proposal.deltas) == ("require_root_goal_binding",)
    # The public derivation API accepts diagnosis + incumbent only; arbitrary
    # parameter edits are not part of a failure-learning receipt.
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
    assert "search_root_cause_not_confirmed" in result.reasons


def test_counterfactual_discriminator_is_required_before_policy_learning():
    result = _derive(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        counterfactual_discriminator_passed=False,
    )
    assert result.verdict is FailureDrivenUpdateVerdict.CANNOT_CHECK
    assert result.proposal is None


def test_failure_receipt_must_be_frozen_before_update():
    unknown = _derive(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        frozen_before_update=None,
    )
    assert unknown.verdict is FailureDrivenUpdateVerdict.CANNOT_CHECK

    posthoc = _derive(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        frozen_before_update=False,
    )
    assert posthoc.verdict is FailureDrivenUpdateVerdict.INVALID


def test_failure_receipt_must_bind_exact_incumbent_policy():
    result = derive_search_policy_update(
        _receipt(SearchFailureSignature.LOW_INFORMATION_GAIN, policy_version="old-policy"),
        SearchPolicy("search-v1"),
        update_id="upd",
        to_policy_version="search-v2",
    )
    assert result.verdict is FailureDrivenUpdateVerdict.INVALID
    assert "failure_receipt_not_bound_to_incumbent_policy" in result.reasons


def test_saturated_registered_repair_returns_no_repair_not_random_idea():
    policy = SearchPolicy("search-v1", max_per_evidence_root=1)
    result = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, policy)
    assert result.verdict is FailureDrivenUpdateVerdict.NO_REGISTERED_POLICY_REPAIR
    assert result.proposal is None
    assert "do not substitute an unrelated random idea" in result.reasons[0]


def test_materialized_successor_is_challenger_only():
    incumbent = SearchPolicy("search-v1", require_structural_intent=False)
    assessment = _derive(SearchFailureSignature.SURFACE_MATCH_STRUCTURAL_MISS, incumbent)
    assert assessment.proposal is not None

    challenger = materialize_search_policy_challenger(incumbent, assessment.proposal)
    assert challenger.version == "search-v2"
    assert challenger.require_structural_intent is True
    assert challenger.grants_scientific_authority is False
    assert assessment.proposal.claims_policy_is_better is False


def test_stale_policy_delta_cannot_be_applied_to_different_incumbent():
    incumbent = SearchPolicy("search-v1", max_candidates=10)
    assessment = _derive(SearchFailureSignature.OVERLY_NARROW_RECALL, incumbent)
    assert assessment.proposal is not None

    mutated_incumbent = replace(incumbent, max_candidates=11)
    with pytest.raises(ValueError, match="stale policy delta"):
        materialize_search_policy_challenger(mutated_incumbent, assessment.proposal)


def test_specific_failures_map_to_specific_registered_repairs():
    cases = [
        (SearchFailureSignature.MISSED_COUNTEREVIDENCE, SearchPolicy("search-v1", preserve_counterevidence=False), "preserve_counterevidence"),
        (SearchFailureSignature.QUERY_DRIFT, SearchPolicy("search-v1", require_root_goal_binding=False), "require_root_goal_binding"),
        (SearchFailureSignature.MISSED_RETRACTION_OR_SUPERSESSION, SearchPolicy("search-v1", require_freshness_retraction_intent=False), "require_freshness_retraction_intent"),
        (SearchFailureSignature.MISSED_NEGATIVE_RESULT, SearchPolicy("search-v1", require_negative_result_intent=False), "require_negative_result_intent"),
        (SearchFailureSignature.METHOD_OBLIGATION_UNSERVED, SearchPolicy("search-v1", require_method_intent=False), "require_method_intent"),
        (SearchFailureSignature.KEYWORD_STUFFING_FALSE_POSITIVE, SearchPolicy("search-v1", min_substantive_match_score=0.2), "min_substantive_match_score"),
        (SearchFailureSignature.OVERLY_NARROW_RECALL, SearchPolicy("search-v1", max_candidates=8), "max_candidates"),
    ]
    for signature, policy, parameter in cases:
        result = _derive(signature, policy)
        assert result.verdict is FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED
        assert result.proposal is not None
        assert parameter in {delta.parameter for delta in result.proposal.deltas}


def test_position_bias_failure_updates_feedback_policy_not_truth_authority():
    policy = SearchPolicy(
        "search-v1",
        require_propensity_corrected_feedback=False,
        exploration_fraction=0.0,
    )
    result = _derive(SearchFailureSignature.POSITION_EXPOSURE_BIAS, policy)
    assert result.proposal is not None
    params = {delta.parameter for delta in result.proposal.deltas}
    assert params == {"require_propensity_corrected_feedback", "exploration_fraction"}
    assert result.grants_scientific_authority is False


def test_policy_thresholds_change_routing_selection_on_next_iteration():
    candidates = (
        _candidate("low-root", rank=_rank(root_obligation_relevance=0.2)),
        _candidate("low-info", rank=_rank(expected_information_gain=0.2), mechanism_family="m2"),
        _candidate("good", rank=_rank(root_obligation_relevance=0.9, expected_information_gain=0.9), mechanism_family="m3"),
    )
    policy_t = SearchPolicy("search-v1", min_root_obligation_relevance=0.0, min_expected_information_gain=0.0)
    selected_t = select_candidates_with_policy(candidates, policy_t)
    assert {item.candidate_id for item in selected_t} == {"low-root", "low-info", "good"}

    failure = _receipt(SearchFailureSignature.LOW_ROOT_OBLIGATION_RELEVANCE)
    update = derive_search_policy_update(
        failure,
        policy_t,
        update_id="upd-root",
        to_policy_version="search-v2",
    )
    assert update.proposal is not None
    policy_t1 = materialize_search_policy_challenger(policy_t, update.proposal)
    selected_t1 = select_candidates_with_policy(candidates, policy_t1)
    assert {item.candidate_id for item in selected_t1} == {"low-root", "low-info", "good"}  # 0.1 floor still admits all

    # Repeated independently diagnosed failures can move the same registered
    # parameter again; this is policy learning, but each step remains a challenger.
    failure_2 = replace(failure, failure_id="failure-2", policy_version="search-v2")
    update_2 = derive_search_policy_update(
        failure_2,
        policy_t1,
        update_id="upd-root-2",
        to_policy_version="search-v3",
    )
    assert update_2.proposal is not None
    policy_t2 = materialize_search_policy_challenger(policy_t1, update_2.proposal)
    assert policy_t2.min_root_obligation_relevance == 0.2
    assert policy_t2.grants_scientific_authority is False


def test_policy_can_make_same_root_failure_change_next_selection():
    same_a = _candidate("a", evidence_root_id="same", mechanism_family="m1")
    same_b = _candidate("b", evidence_root_id="same", mechanism_family="m2")
    independent = _candidate("c", evidence_root_id="independent", mechanism_family="m3")
    policy_t = SearchPolicy("search-v1", max_per_evidence_root=2)
    assert len([x for x in select_candidates_with_policy((same_a, same_b, independent), policy_t) if x.evidence_root_id == "same"]) == 2

    update = _derive(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, policy_t)
    assert update.proposal is not None
    policy_t1 = materialize_search_policy_challenger(policy_t, update.proposal)
    selected = select_candidates_with_policy((same_a, same_b, independent), policy_t1)
    assert len([x for x in selected if x.evidence_root_id == "same"]) == 1
    assert "c" in {x.candidate_id for x in selected}
