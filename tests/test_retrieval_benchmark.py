from dataclasses import FrozenInstanceError

import pytest

from rakl.retrieval_benchmark import (
    BenchmarkVerdict,
    CorpusArtifactIdentity,
    GroundTruthFactorization,
    GroundTruthLayer,
    RetrievalRouteTrial,
    RouteComparisonVerdict,
    RouteTrialVerdict,
    compare_retrieval_routes,
    evaluate_retrieval_route_trial,
    validate_corpus_artifact,
    validate_ground_truth_factorization,
)


def _artifact(**overrides) -> CorpusArtifactIdentity:
    values = dict(
        corpus_id="MIR-test",
        source_id="Anikethh/Methodology-Inspiration-Retrieval",
        revision="dc0545adffad7cd15c730f4a7bb9388d6440a47c",
        path="data/test_chronological_df.csv",
        content_sha="ae1d293db3dd755232e527c3f8d58800ba7e06ad",
        size_bytes=5169467,
        identity_observed=True,
    )
    values.update(overrides)
    return CorpusArtifactIdentity(**values)


def _trial(**overrides) -> RetrievalRouteTrial:
    values = dict(
        trial_id="trial-lexical",
        route_id="LEXICAL",
        corpus_id="MIR-test",
        corpus_revision="dc0545adffad7cd15c730f4a7bb9388d6440a47c",
        corpus_artifact_sha="ae1d293db3dd755232e527c3f8d58800ba7e06ad",
        task_packet_id="mir-eval-packet-v1",
        query_packet_id="query-v1",
        top_k=3,
        base_model_id="same-model",
        base_model_config_id="temperature-0",
        output_contract_id="ranked-paper-ids-v1",
        evaluator_id="mir-evaluator-v1",
        resource_ids=("paper-index",),
        resource_delta_declared=False,
        hidden_labels_exposed=False,
        query_frozen_before_labels=True,
        execution_observed=True,
        corpus_candidate_ids=("surface", "gold-A", "gold-B", "other"),
        designated_relevant_ids=("gold-A", "gold-B"),
        retrieved_candidate_ids=("surface", "gold-A", "other"),
    )
    values.update(overrides)
    return RetrievalRouteTrial(**values)


def test_pinned_corpus_artifact_is_valid():
    report = validate_corpus_artifact(_artifact())
    assert report.verdict is BenchmarkVerdict.VALID


def test_unpinned_revision_cannot_support_benchmark():
    report = validate_corpus_artifact(_artifact(revision=""))
    assert report.verdict is BenchmarkVerdict.CANNOT_CHECK
    assert "revision_missing" in report.reasons


def test_unobserved_pinned_identity_is_cannot_check_not_success():
    report = validate_corpus_artifact(_artifact(identity_observed=False))
    assert report.verdict is BenchmarkVerdict.CANNOT_CHECK


def test_retrieval_structure_transfer_ground_truth_cannot_be_collapsed():
    report = validate_ground_truth_factorization(
        GroundTruthFactorization(
            retrieval_relevance_label_id="mir-gold",
            structural_witness_label_id="mir-gold",
            transfer_validity_label_id="mir-gold",
            labels_collapsed_to_one_authority=True,
        )
    )
    assert report.verdict is BenchmarkVerdict.REJECT


def test_retrieval_only_ground_truth_is_valid_but_scoped():
    report = validate_ground_truth_factorization(
        GroundTruthFactorization(
            retrieval_relevance_label_id="mir-gold",
            structural_witness_label_id=None,
            transfer_validity_label_id=None,
            labels_collapsed_to_one_authority=False,
        )
    )
    assert report.verdict is BenchmarkVerdict.VALID
    assert report.available_layers == (GroundTruthLayer.RETRIEVAL_RELEVANCE,)
    assert "structural_ground_truth_unavailable_retrieval_only_scope" in report.reasons


def test_same_label_authority_cannot_silently_cover_retrieval_and_structure():
    report = validate_ground_truth_factorization(
        GroundTruthFactorization(
            retrieval_relevance_label_id="one-label",
            structural_witness_label_id="one-label",
            transfer_validity_label_id=None,
            labels_collapsed_to_one_authority=False,
        )
    )
    assert report.verdict is BenchmarkVerdict.REJECT


def test_route_trial_separates_corpus_coverage_from_retrieval_recall():
    report = evaluate_retrieval_route_trial(
        _trial(
            corpus_candidate_ids=("surface", "gold-A", "other"),
            designated_relevant_ids=("gold-A", "gold-B"),
            retrieved_candidate_ids=("surface", "gold-A", "other"),
        )
    )
    assert report.verdict is RouteTrialVerdict.VALID
    assert report.corpus_coverage_rate == 0.5
    assert report.conditional_recall_at_k == 1.0
    assert report.absent_relevant_ids == ("gold-B",)


def test_route_trial_computes_conditional_recall_and_mrr():
    report = evaluate_retrieval_route_trial(_trial())
    assert report.verdict is RouteTrialVerdict.VALID
    assert report.corpus_coverage_rate == 1.0
    assert report.conditional_recall_at_k == 0.5
    assert report.mean_reciprocal_rank == pytest.approx(0.25)


def test_hidden_gold_exposure_invalidates_retrieval_trial():
    report = evaluate_retrieval_route_trial(_trial(hidden_labels_exposed=True))
    assert report.verdict is RouteTrialVerdict.TRIAL_INVALID


def test_posthoc_domain_stripping_invalidates_retrieval_trial():
    report = evaluate_retrieval_route_trial(_trial(query_frozen_before_labels=False))
    assert report.verdict is RouteTrialVerdict.TRIAL_INVALID


def test_unexecuted_route_is_cannot_check():
    report = evaluate_retrieval_route_trial(_trial(execution_observed=False))
    assert report.verdict is RouteTrialVerdict.CANNOT_CHECK


def test_route_output_cannot_exceed_frozen_top_k():
    report = evaluate_retrieval_route_trial(
        _trial(
            top_k=2,
            retrieved_candidate_ids=("surface", "gold-A", "other"),
        )
    )
    assert report.verdict is RouteTrialVerdict.TRIAL_INVALID


def test_duplicate_ranked_candidates_are_invalid():
    report = evaluate_retrieval_route_trial(
        _trial(retrieved_candidate_ids=("gold-A", "gold-A"))
    )
    assert report.verdict is RouteTrialVerdict.TRIAL_INVALID


def test_matched_same_resource_routes_are_comparable():
    lexical = _trial()
    relational = _trial(
        trial_id="trial-relational",
        route_id="DOMAIN_STRIPPED_RELATIONAL",
        retrieved_candidate_ids=("gold-B", "gold-A", "surface"),
    )
    report = compare_retrieval_routes((lexical, relational))
    assert report.verdict is RouteComparisonVerdict.MATCHED_SAME_RESOURCE
    assert report.activates_default is False
    assert report.establishes_model_improvement is False


def test_topk_mismatch_invalidates_route_comparison():
    lexical = _trial()
    graph = _trial(
        trial_id="trial-graph",
        route_id="GRAPH",
        top_k=5,
        retrieved_candidate_ids=("gold-A", "gold-B"),
    )
    report = compare_retrieval_routes((lexical, graph))
    assert report.verdict is RouteComparisonVerdict.TRIAL_INVALID
    assert "matched_contract_mismatch:top_k" in report.reasons


def test_model_mismatch_invalidates_route_comparison():
    lexical = _trial()
    embedding = _trial(
        trial_id="trial-embedding",
        route_id="EMBEDDING",
        base_model_id="stronger-model",
    )
    report = compare_retrieval_routes((lexical, embedding))
    assert report.verdict is RouteComparisonVerdict.TRIAL_INVALID


def test_corpus_revision_mismatch_invalidates_route_comparison():
    lexical = _trial()
    graph = _trial(
        trial_id="trial-graph",
        route_id="GRAPH",
        corpus_revision="floating-main",
    )
    report = compare_retrieval_routes((lexical, graph))
    assert report.verdict is RouteComparisonVerdict.TRIAL_INVALID


def test_undeclared_resource_delta_invalidates_comparison():
    lexical = _trial()
    graph = _trial(
        trial_id="trial-graph",
        route_id="GRAPH",
        resource_ids=("paper-index", "methodology-graph"),
        resource_delta_declared=False,
    )
    report = compare_retrieval_routes((lexical, graph))
    assert report.verdict is RouteComparisonVerdict.TRIAL_INVALID
    assert "undeclared_resource_delta_between_routes" in report.reasons


def test_declared_graph_resource_delta_is_system_level_comparison():
    lexical = _trial(resource_delta_declared=True)
    graph = _trial(
        trial_id="trial-graph",
        route_id="GRAPH",
        resource_ids=("paper-index", "methodology-graph"),
        resource_delta_declared=True,
        retrieved_candidate_ids=("gold-A", "gold-B", "surface"),
    )
    report = compare_retrieval_routes((lexical, graph))
    assert report.verdict is RouteComparisonVerdict.SYSTEM_LEVEL_WITH_RESOURCE_DELTA
    assert report.establishes_model_improvement is False


def test_corpus_artifact_contract_is_immutable():
    artifact = _artifact()
    with pytest.raises(FrozenInstanceError):
        artifact.revision = "changed"  # type: ignore[misc]
