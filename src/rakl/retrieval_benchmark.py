from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class BenchmarkVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


class RouteTrialVerdict(str, Enum):
    VALID = "VALID"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class RouteComparisonVerdict(str, Enum):
    MATCHED_SAME_RESOURCE = "MATCHED_SAME_RESOURCE"
    SYSTEM_LEVEL_WITH_RESOURCE_DELTA = "SYSTEM_LEVEL_WITH_RESOURCE_DELTA"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class GroundTruthLayer(str, Enum):
    RETRIEVAL_RELEVANCE = "RETRIEVAL_RELEVANCE"
    STRUCTURAL_WITNESS_VALIDITY = "STRUCTURAL_WITNESS_VALIDITY"
    TRANSFER_VALIDITY = "TRANSFER_VALIDITY"


@dataclass(frozen=True)
class CorpusArtifactIdentity:
    """Pinned identity for a benchmark artifact.

    A benchmark name or mutable viewer URL is not enough.  At least one immutable
    content identity must be available before the artifact can support a trial.
    """

    corpus_id: str
    source_id: str
    revision: str
    path: str
    content_sha: str
    size_bytes: int
    identity_observed: Optional[bool]


@dataclass(frozen=True)
class CorpusArtifactReport:
    verdict: BenchmarkVerdict
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class GroundTruthFactorization:
    """Separate authority for retrieval, structure and transfer labels."""

    retrieval_relevance_label_id: str
    structural_witness_label_id: Optional[str]
    transfer_validity_label_id: Optional[str]
    labels_collapsed_to_one_authority: bool


@dataclass(frozen=True)
class GroundTruthReport:
    verdict: BenchmarkVerdict
    available_layers: Tuple[GroundTruthLayer, ...]
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class RetrievalRouteTrial:
    """One evaluator-side observation of a frozen retrieval route.

    Gold IDs are evaluator-side state.  `hidden_labels_exposed=False` certifies
    that they were not visible to query generation or retrieval.
    """

    trial_id: str
    route_id: str
    corpus_id: str
    corpus_revision: str
    corpus_artifact_sha: str
    task_packet_id: str
    query_packet_id: str
    top_k: int
    base_model_id: str
    base_model_config_id: str
    output_contract_id: str
    evaluator_id: str
    resource_ids: Tuple[str, ...]
    resource_delta_declared: Optional[bool]
    hidden_labels_exposed: Optional[bool]
    query_frozen_before_labels: Optional[bool]
    execution_observed: Optional[bool]
    corpus_candidate_ids: Tuple[str, ...]
    designated_relevant_ids: Tuple[str, ...]
    retrieved_candidate_ids: Tuple[str, ...]


@dataclass(frozen=True)
class RetrievalRouteReport:
    verdict: RouteTrialVerdict
    corpus_coverage_rate: Optional[float]
    conditional_recall_at_k: Optional[float]
    mean_reciprocal_rank: Optional[float]
    covered_relevant_ids: Tuple[str, ...]
    absent_relevant_ids: Tuple[str, ...]
    retrieved_relevant_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def activates_retrieval_route(self) -> bool:
        return False


@dataclass(frozen=True)
class RouteComparisonReport:
    verdict: RouteComparisonVerdict
    route_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def establishes_model_improvement(self) -> bool:
        return False

    @property
    def activates_default(self) -> bool:
        return False


def validate_corpus_artifact(
    artifact: CorpusArtifactIdentity,
) -> CorpusArtifactReport:
    missing = tuple(
        f"{name}_missing"
        for name, value in (
            ("corpus_id", artifact.corpus_id),
            ("source_id", artifact.source_id),
            ("revision", artifact.revision),
            ("path", artifact.path),
            ("content_sha", artifact.content_sha),
        )
        if not value
    )
    if missing:
        return CorpusArtifactReport(BenchmarkVerdict.CANNOT_CHECK, missing)
    if artifact.size_bytes <= 0:
        return CorpusArtifactReport(
            BenchmarkVerdict.REJECT,
            ("artifact_size_must_be_positive",),
        )
    if artifact.identity_observed is None:
        return CorpusArtifactReport(
            BenchmarkVerdict.CANNOT_CHECK,
            ("artifact_identity_observation_unknown",),
        )
    if artifact.identity_observed is False:
        return CorpusArtifactReport(
            BenchmarkVerdict.CANNOT_CHECK,
            ("pinned_artifact_identity_not_observed",),
        )
    return CorpusArtifactReport(
        BenchmarkVerdict.VALID,
        ("source_revision_and_content_identity_pinned",),
    )


def validate_ground_truth_factorization(
    factorization: GroundTruthFactorization,
) -> GroundTruthReport:
    if not factorization.retrieval_relevance_label_id:
        return GroundTruthReport(
            BenchmarkVerdict.CANNOT_CHECK,
            (),
            ("retrieval_relevance_authority_missing",),
        )
    if factorization.labels_collapsed_to_one_authority:
        return GroundTruthReport(
            BenchmarkVerdict.REJECT,
            (),
            ("retrieval_structure_transfer_ground_truth_collapsed",),
        )

    layer_ids = [factorization.retrieval_relevance_label_id]
    available = [GroundTruthLayer.RETRIEVAL_RELEVANCE]
    if factorization.structural_witness_label_id:
        layer_ids.append(factorization.structural_witness_label_id)
        available.append(GroundTruthLayer.STRUCTURAL_WITNESS_VALIDITY)
    if factorization.transfer_validity_label_id:
        layer_ids.append(factorization.transfer_validity_label_id)
        available.append(GroundTruthLayer.TRANSFER_VALIDITY)

    if len(layer_ids) != len(set(layer_ids)):
        return GroundTruthReport(
            BenchmarkVerdict.REJECT,
            tuple(available),
            ("same_label_authority_reused_across_distinct_ground_truth_layers",),
        )

    reasons = ["retrieval_relevance_kept_distinct"]
    if GroundTruthLayer.STRUCTURAL_WITNESS_VALIDITY not in available:
        reasons.append("structural_ground_truth_unavailable_retrieval_only_scope")
    if GroundTruthLayer.TRANSFER_VALIDITY not in available:
        reasons.append("transfer_ground_truth_unavailable_no_transfer_claim")
    return GroundTruthReport(
        BenchmarkVerdict.VALID,
        tuple(available),
        tuple(reasons),
    )


def evaluate_retrieval_route_trial(
    trial: RetrievalRouteTrial,
) -> RetrievalRouteReport:
    required = (
        ("trial_id", trial.trial_id),
        ("route_id", trial.route_id),
        ("corpus_id", trial.corpus_id),
        ("corpus_revision", trial.corpus_revision),
        ("corpus_artifact_sha", trial.corpus_artifact_sha),
        ("task_packet_id", trial.task_packet_id),
        ("query_packet_id", trial.query_packet_id),
        ("base_model_id", trial.base_model_id),
        ("base_model_config_id", trial.base_model_config_id),
        ("output_contract_id", trial.output_contract_id),
        ("evaluator_id", trial.evaluator_id),
    )
    missing = tuple(f"{name}_missing" for name, value in required if not value)
    if missing:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            missing,
        )
    if trial.top_k <= 0:
        return RetrievalRouteReport(
            RouteTrialVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            (),
            (),
            (),
            ("top_k_must_be_positive",),
        )
    if trial.hidden_labels_exposed is None:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            ("hidden_label_exposure_status_unknown",),
        )
    if trial.hidden_labels_exposed:
        return RetrievalRouteReport(
            RouteTrialVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            (),
            (),
            (),
            ("hidden_relevance_labels_exposed",),
        )
    if trial.query_frozen_before_labels is None:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            ("query_freeze_chronology_unknown",),
        )
    if trial.query_frozen_before_labels is False:
        return RetrievalRouteReport(
            RouteTrialVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            (),
            (),
            (),
            ("posthoc_query_or_abstraction_modification",),
        )
    if trial.execution_observed is None:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            ("execution_observation_unknown",),
        )
    if trial.execution_observed is False:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            ("retrieval_route_not_executed",),
        )
    if trial.resource_delta_declared is None:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            ("resource_delta_declaration_unknown",),
        )
    if not trial.designated_relevant_ids:
        return RetrievalRouteReport(
            RouteTrialVerdict.CANNOT_CHECK,
            None,
            None,
            None,
            (),
            (),
            (),
            ("evaluator_relevance_labels_missing",),
        )
    if len(trial.retrieved_candidate_ids) > trial.top_k:
        return RetrievalRouteReport(
            RouteTrialVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            (),
            (),
            (),
            ("retrieved_candidate_count_exceeds_top_k",),
        )
    if len(trial.retrieved_candidate_ids) != len(set(trial.retrieved_candidate_ids)):
        return RetrievalRouteReport(
            RouteTrialVerdict.TRIAL_INVALID,
            None,
            None,
            None,
            (),
            (),
            (),
            ("duplicate_candidate_ids_in_ranked_output",),
        )

    corpus = set(trial.corpus_candidate_ids)
    relevant = tuple(dict.fromkeys(trial.designated_relevant_ids))
    covered = tuple(item for item in relevant if item in corpus)
    absent = tuple(item for item in relevant if item not in corpus)
    retrieved = tuple(item for item in relevant if item in trial.retrieved_candidate_ids)

    coverage_rate = len(covered) / len(relevant)
    conditional_recall: Optional[float]
    if covered:
        conditional_recall = sum(
            1 for item in covered if item in trial.retrieved_candidate_ids
        ) / len(covered)
    else:
        conditional_recall = None

    reciprocal_ranks = []
    rank_lookup = {
        candidate: index + 1
        for index, candidate in enumerate(trial.retrieved_candidate_ids)
    }
    for item in covered:
        reciprocal_ranks.append(1.0 / rank_lookup[item] if item in rank_lookup else 0.0)
    mrr = (
        sum(reciprocal_ranks) / len(reciprocal_ranks)
        if reciprocal_ranks
        else None
    )

    reasons = [
        "corpus_coverage_separated_from_retrieval_recall",
        "gold_labels_evaluator_side",
        "query_chronology_frozen",
    ]
    if absent:
        reasons.append("one_or_more_designated_sources_absent_from_corpus")
    if covered and not retrieved:
        reasons.append("covered_designated_sources_not_retrieved")

    return RetrievalRouteReport(
        RouteTrialVerdict.VALID,
        coverage_rate,
        conditional_recall,
        mrr,
        covered,
        absent,
        retrieved,
        tuple(reasons),
    )


def compare_retrieval_routes(
    trials: Tuple[RetrievalRouteTrial, ...],
) -> RouteComparisonReport:
    if len(trials) < 2:
        return RouteComparisonReport(
            RouteComparisonVerdict.CANNOT_CHECK,
            tuple(trial.route_id for trial in trials),
            ("at_least_two_routes_required",),
        )

    route_ids = tuple(trial.route_id for trial in trials)
    if len(route_ids) != len(set(route_ids)):
        return RouteComparisonReport(
            RouteComparisonVerdict.TRIAL_INVALID,
            route_ids,
            ("duplicate_route_id",),
        )

    reports = tuple(evaluate_retrieval_route_trial(trial) for trial in trials)
    if any(report.verdict is RouteTrialVerdict.TRIAL_INVALID for report in reports):
        return RouteComparisonReport(
            RouteComparisonVerdict.TRIAL_INVALID,
            route_ids,
            ("one_or_more_route_trials_invalid",),
        )
    if any(report.verdict is RouteTrialVerdict.CANNOT_CHECK for report in reports):
        return RouteComparisonReport(
            RouteComparisonVerdict.CANNOT_CHECK,
            route_ids,
            ("one_or_more_route_trials_incomplete",),
        )

    reference = trials[0]
    matched_fields = (
        "corpus_id",
        "corpus_revision",
        "corpus_artifact_sha",
        "task_packet_id",
        "query_packet_id",
        "top_k",
        "base_model_id",
        "base_model_config_id",
        "output_contract_id",
        "evaluator_id",
        "corpus_candidate_ids",
        "designated_relevant_ids",
    )
    mismatches = []
    for field in matched_fields:
        baseline = getattr(reference, field)
        if any(getattr(trial, field) != baseline for trial in trials[1:]):
            mismatches.append(f"matched_contract_mismatch:{field}")
    if mismatches:
        return RouteComparisonReport(
            RouteComparisonVerdict.TRIAL_INVALID,
            route_ids,
            tuple(mismatches),
        )

    resource_sets = tuple(frozenset(trial.resource_ids) for trial in trials)
    resources_differ = any(resources != resource_sets[0] for resources in resource_sets[1:])
    if resources_differ:
        if any(trial.resource_delta_declared is not True for trial in trials):
            return RouteComparisonReport(
                RouteComparisonVerdict.TRIAL_INVALID,
                route_ids,
                ("undeclared_resource_delta_between_routes",),
            )
        return RouteComparisonReport(
            RouteComparisonVerdict.SYSTEM_LEVEL_WITH_RESOURCE_DELTA,
            route_ids,
            (
                "matched_nonresource_contract",
                "resource_delta_explicit",
                "comparison_cannot_establish_pure_model_utilization_gain",
            ),
        )

    return RouteComparisonReport(
        RouteComparisonVerdict.MATCHED_SAME_RESOURCE,
        route_ids,
        (
            "matched_corpus_task_query_model_topk_and_evaluator",
            "same_resource_set",
            "no_automatic_route_activation",
        ),
    )
