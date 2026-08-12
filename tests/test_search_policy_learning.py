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
    CounterfactualSearchRun,
    FailureDrivenUpdateVerdict,
    RootCauseCertificationVerdict,
    SearchFailureSignature,
    SearchPolicy,
    SearchRootCauseDiagnostic,
    build_search_failure_receipt,
    certify_search_root_cause,
    compile_search_intents_with_policy,
    derive_search_policy_update,
    materialize_search_policy_challenger,
    propose_registered_counterfactual_policy,
    search_feedback_value_with_policy,
    select_candidates_with_policy,
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


def _run(run_id, policy, *, passed, context_suffix="same"):
    return CounterfactualSearchRun(
        run_id=run_id,
        policy=policy,
        evaluation_receipt_hash=f"eval-{run_id}",
        outcome_passed=passed,
        case_subject_hash=f"case-{context_suffix}",
        task_input_hash=f"task-{context_suffix}",
        candidate_pool_hash=f"pool-{context_suffix}",
        model_subject_hash=f"model-{context_suffix}",
        tool_contract_hash=f"tools-{context_suffix}",
        resource_contract_hash=f"resources-{context_suffix}",
    )


def _certify(
    signature,
    policy=None,
    *,
    counterfactual_passed=True,
    validated_signature=None,
    frozen=True,
    counterfactual_context_suffix="same",
    counterfactual_policy=None,
):
    incumbent = policy or SearchPolicy("search-v1")
    probe = counterfactual_policy or propose_registered_counterfactual_policy(
        incumbent,
        signature,
        to_policy_version="probe-v2",
    )
    diagnostic = SearchRootCauseDiagnostic(
        diagnostic_id="diag-1",
        certificate_id=f"root-cert-{signature.value}",
        failure_id="failure-1",
        question_id="q1",
        hypothesized_signature=signature,
        validated_reference_signature=(
            signature if validated_signature is None else validated_signature
        ),
        diagnosis_reference_receipt_hash="gold-diagnosis-receipt",
        causal_evidence_ids=("trajectory-case-17", "failure-receipt-17"),
        baseline=_run("baseline", incumbent, passed=False),
        counterfactual=_run(
            "counterfactual",
            probe,
            passed=counterfactual_passed,
            context_suffix=counterfactual_context_suffix,
        ),
        frozen_before_policy_update=frozen,
    )
    return incumbent, diagnostic, certify_search_root_cause(diagnostic)


def _receipt(signature, policy=None):
    incumbent, _, certified = _certify(signature, policy)
    assert certified.verdict is RootCauseCertificationVerdict.ROOT_CAUSE_CERTIFIED
    assert certified.certificate is not None
    return incumbent, build_search_failure_receipt(
        certified.certificate,
        observed_candidate_ids=("c1", "c2"),
    )


def _derive(signature, policy=None):
    incumbent, receipt = _receipt(signature, policy)
    result = derive_search_policy_update(
        receipt,
        incumbent,
        update_id="upd-1",
        to_policy_version="search-v2",
    )
    return incumbent, receipt, result


def _successor(signature, policy):
    incumbent, _, assessment = _derive(signature, policy)
    assert incumbent == policy
    assert assessment.verdict is FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED
    assert assessment.proposal is not None
    return assessment, materialize_search_policy_challenger(policy, assessment.proposal)


def test_matched_one_repair_counterfactual_certifies_root_cause_but_not_general_gain():
    policy = SearchPolicy("search-v1", max_per_evidence_root=3)
    _, diagnostic, result = _certify(
        SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION,
        policy,
    )
    assert result.verdict is RootCauseCertificationVerdict.ROOT_CAUSE_CERTIFIED
    assert result.certificate is not None
    assert result.certificate.signature is SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION
    assert result.certificate.intervention_parameters == ("max_per_evidence_root",)
    assert result.certificate.proves_general_policy_improvement is False
    assert result.certificate.grants_scientific_authority is False
    assert diagnostic.baseline.material_context_tuple == diagnostic.counterfactual.material_context_tuple


def test_counterfactual_that_does_not_rescue_cannot_authorize_policy_learning():
    _, _, result = _certify(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        SearchPolicy("search-v1", min_expected_information_gain=0.0),
        counterfactual_passed=False,
    )
    assert result.verdict is RootCauseCertificationVerdict.COUNTERFACTUAL_DID_NOT_RESCUE
    assert result.certificate is None


def test_counterfactual_must_hold_material_context_fixed():
    _, _, result = _certify(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        SearchPolicy("search-v1", min_expected_information_gain=0.0),
        counterfactual_context_suffix="different",
    )
    assert result.verdict is RootCauseCertificationVerdict.INVALID
    assert "counterfactual_search_probe_not_materially_matched" in result.reasons


def test_counterfactual_must_use_exact_registered_repair_and_no_extra_knob():
    policy = SearchPolicy("search-v1", min_expected_information_gain=0.0)
    registered = propose_registered_counterfactual_policy(
        policy,
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        to_policy_version="probe-v2",
    )
    contaminated = replace(registered, max_candidates=registered.max_candidates + 1)
    _, _, result = _certify(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        policy,
        counterfactual_policy=contaminated,
    )
    assert result.verdict is RootCauseCertificationVerdict.INVALID
    assert "counterfactual_policy_does_not_equal_exact_registered_repair" in result.reasons


def test_validated_reference_must_agree_with_hypothesized_failure_signature():
    _, _, result = _certify(
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        validated_signature=SearchFailureSignature.QUERY_DRIFT,
    )
    assert result.verdict is RootCauseCertificationVerdict.INVALID


def test_posthoc_or_unknown_root_cause_freeze_fails_closed():
    _, _, posthoc = _certify(SearchFailureSignature.LOW_INFORMATION_GAIN, frozen=False)
    assert posthoc.verdict is RootCauseCertificationVerdict.INVALID

    policy = SearchPolicy("search-v1")
    probe = propose_registered_counterfactual_policy(
        policy,
        SearchFailureSignature.LOW_INFORMATION_GAIN,
        to_policy_version="probe-v2",
    )
    diagnostic = SearchRootCauseDiagnostic(
        diagnostic_id="diag-unknown",
        certificate_id="cert-unknown",
        failure_id="failure-unknown",
        question_id="q1",
        hypothesized_signature=SearchFailureSignature.LOW_INFORMATION_GAIN,
        validated_reference_signature=SearchFailureSignature.LOW_INFORMATION_GAIN,
        diagnosis_reference_receipt_hash="gold",
        causal_evidence_ids=("case",),
        baseline=_run("base-u", policy, passed=False),
        counterfactual=_run("cf-u", probe, passed=True),
        frozen_before_policy_update=None,
    )
    unknown = certify_search_root_cause(diagnostic)
    assert unknown.verdict is RootCauseCertificationVerdict.CANNOT_CHECK


def test_failure_to_policy_update_is_deterministic_bounded_and_certificate_bound():
    policy = SearchPolicy("search-v1", max_per_evidence_root=3)
    incumbent_a, receipt_a, a = _derive(
        SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION,
        policy,
    )
    incumbent_b, receipt_b, b = _derive(
        SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION,
        policy,
    )
    assert incumbent_a == incumbent_b == policy
    assert a.proposal == b.proposal
    assert receipt_a.root_cause_certificate.subject_hash == receipt_b.root_cause_certificate.subject_hash
    assert a.proposal is not None
    assert [(d.parameter, d.old_value, d.new_value) for d in a.proposal.deltas] == [
        ("max_per_evidence_root", 3, 2)
    ]
    assert a.proposal.root_cause_certificate_id == "root-cert-SAME_ROOT_OVERCONCENTRATION"
    assert a.proposal.claims_policy_is_better is False
    assert a.proposal.eligible_for_canonical_promotion is False


def test_no_caller_supplied_random_delta_surface_exists():
    policy = SearchPolicy("search-v1", max_semantic_expansion_terms=8)
    _, receipt, assessment = _derive(SearchFailureSignature.QUERY_DRIFT, policy)
    assert assessment.proposal is not None
    assert tuple(delta.parameter for delta in assessment.proposal.deltas) == (
        "max_semantic_expansion_terms",
    )
    with pytest.raises(TypeError):
        derive_search_policy_update(  # type: ignore[call-arg]
            receipt,
            policy,
            update_id="upd",
            to_policy_version="search-v2",
            arbitrary_delta={"graph_centrality": 999},
        )


def test_saturated_registered_repair_has_no_counterfactual_instead_of_random_idea():
    policy = SearchPolicy("search-v1", max_per_evidence_root=1)
    with pytest.raises(ValueError, match="already saturated"):
        propose_registered_counterfactual_policy(
            policy,
            SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION,
            to_policy_version="probe-v2",
        )


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
        preserve_counterevidence=False,
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


def test_structural_and_method_failures_change_next_selection():
    surface = _candidate("surface", rank=_rank(root_obligation_relevance=0.99), mechanism_family="m-surface")
    structural = _candidate(
        "structural",
        index_kinds=(SearchIndexKind.STRUCTURAL,),
        rank=_rank(root_obligation_relevance=0.10),
        mechanism_family="m-struct",
    )
    policy_t = SearchPolicy("search-v1", max_candidates=1, preserve_structural_slot=False)
    assert select_candidates_with_policy((surface, structural), policy_t) == (surface,)
    _, structural_policy = _successor(SearchFailureSignature.SURFACE_MATCH_STRUCTURAL_MISS, policy_t)
    assert select_candidates_with_policy((surface, structural), structural_policy) == (structural,)

    literature = _candidate("paper", rank=_rank(root_obligation_relevance=0.99), mechanism_family="m-paper")
    method = _candidate(
        "method",
        vertical=SearchVertical.METHOD_TOOL,
        index_kinds=(SearchIndexKind.METHOD_OPERATOR,),
        rank=_rank(root_obligation_relevance=0.10),
        mechanism_family="m-method",
    )
    method_t = SearchPolicy("search-v1", max_candidates=1, preserve_method_tool_slot=False)
    assert select_candidates_with_policy((literature, method), method_t) == (literature,)
    _, method_t1 = _successor(SearchFailureSignature.METHOD_OBLIGATION_UNSERVED, method_t)
    assert select_candidates_with_policy((literature, method), method_t1) == (method,)


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
        preserve_counterevidence=False,
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


def test_root_relevance_and_same_root_failures_change_next_selection():
    low = _candidate("low", rank=_rank(root_obligation_relevance=0.05), mechanism_family="m-low")
    good = _candidate("good", rank=_rank(root_obligation_relevance=0.90), mechanism_family="m-good")
    policy_t = SearchPolicy("search-v1", min_root_obligation_relevance=0.0)
    assert {x.candidate_id for x in select_candidates_with_policy((low, good), policy_t)} == {"low", "good"}
    _, policy_t1 = _successor(SearchFailureSignature.LOW_ROOT_OBLIGATION_RELEVANCE, policy_t)
    assert {x.candidate_id for x in select_candidates_with_policy((low, good), policy_t1)} == {"good"}

    same_a = _candidate("a", evidence_root_id="same", mechanism_family="m1")
    same_b = _candidate("b", evidence_root_id="same", mechanism_family="m2")
    independent = _candidate("c", evidence_root_id="independent", mechanism_family="m3")
    root_t = SearchPolicy("search-v1", max_per_evidence_root=2, max_candidates=3)
    assert len([x for x in select_candidates_with_policy((same_a, same_b, independent), root_t) if x.evidence_root_id == "same"]) == 2
    _, root_t1 = _successor(SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION, root_t)
    selected = select_candidates_with_policy((same_a, same_b, independent), root_t1)
    assert len([x for x in selected if x.evidence_root_id == "same"]) == 1
    assert "c" in {x.candidate_id for x in selected}


def test_materialized_successor_is_challenger_only_and_stale_delta_fails():
    incumbent = SearchPolicy("search-v1", max_candidates=10)
    _, _, assessment = _derive(SearchFailureSignature.OVERLY_NARROW_RECALL, incumbent)
    assert assessment.proposal is not None
    challenger = materialize_search_policy_challenger(incumbent, assessment.proposal)
    assert challenger.version == "search-v2"
    assert challenger.max_candidates == 12
    assert challenger.grants_scientific_authority is False
    assert assessment.proposal.claims_policy_is_better is False

    with pytest.raises(ValueError, match="stale policy delta"):
        materialize_search_policy_challenger(replace(incumbent, max_candidates=11), assessment.proposal)
