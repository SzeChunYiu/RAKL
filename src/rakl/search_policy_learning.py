"""Failure-driven search-policy evolution for RAKL (#433, #434).

The load-bearing continual-improvement contract is::

    failure_t
      -> typed root-cause hypothesis_t
      -> matched one-repair counterfactual probe_t
      -> root-cause certificate_t
      -> bounded SearchPolicyDelta_t
      -> policy challenger_{t+1}
      -> fresh assurance

not::

    failure_t -> another unconstrained idea

A failure cannot mutate search directly. A root-cause certificate is issued only
when the same frozen case is evaluated under the incumbent policy and exactly
one registered repair package, with task/candidate/model/tool/resource context
held fixed, the baseline failing, and the counterfactual succeeding.

The certificate is development/root-cause evidence only. It does **not** prove
that the successor policy is generally better. Fresh disjoint assurance and the
protected Self-RAKL governance path own that judgement and any later promotion.
Search/ranking feedback remains routing authority only and never mints
scientific authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from enum import Enum
from hashlib import sha256
from math import ceil
from typing import Callable, Sequence, Tuple

from .epistemic_search import (
    EvidenceStance,
    ScientificSearchQuestion,
    SearchCandidate,
    SearchFeedback,
    SearchIndexKind,
    SearchIntent,
    SearchIntentKind,
    SearchVertical,
    bias_corrected_feedback_value,
    compile_search_intents,
    diversify_candidates,
)

__all__ = [
    "CounterfactualSearchRun",
    "FailureDrivenUpdateAssessment",
    "FailureDrivenUpdateVerdict",
    "RootCauseCertificationAssessment",
    "RootCauseCertificationVerdict",
    "SearchFailureReceipt",
    "SearchFailureSignature",
    "SearchPolicy",
    "SearchPolicyDelta",
    "SearchPolicyUpdateProposal",
    "SearchRootCauseCertificate",
    "SearchRootCauseDiagnostic",
    "build_search_failure_receipt",
    "certify_search_root_cause",
    "compile_search_intents_with_policy",
    "derive_search_policy_update",
    "materialize_search_policy_challenger",
    "propose_registered_counterfactual_policy",
    "search_feedback_value_with_policy",
    "select_candidates_with_policy",
]


class SearchFailureSignature(str, Enum):
    MISSED_COUNTEREVIDENCE = "MISSED_COUNTEREVIDENCE"
    SAME_ROOT_OVERCONCENTRATION = "SAME_ROOT_OVERCONCENTRATION"
    MECHANISM_MONOCULTURE = "MECHANISM_MONOCULTURE"
    QUERY_DRIFT = "QUERY_DRIFT"
    MISSED_RETRACTION_OR_SUPERSESSION = "MISSED_RETRACTION_OR_SUPERSESSION"
    MISSED_NEGATIVE_RESULT = "MISSED_NEGATIVE_RESULT"
    SURFACE_MATCH_STRUCTURAL_MISS = "SURFACE_MATCH_STRUCTURAL_MISS"
    METHOD_OBLIGATION_UNSERVED = "METHOD_OBLIGATION_UNSERVED"
    LOW_INFORMATION_GAIN = "LOW_INFORMATION_GAIN"
    LOW_ROOT_OBLIGATION_RELEVANCE = "LOW_ROOT_OBLIGATION_RELEVANCE"
    KEYWORD_STUFFING_FALSE_POSITIVE = "KEYWORD_STUFFING_FALSE_POSITIVE"
    OVERLY_NARROW_RECALL = "OVERLY_NARROW_RECALL"
    OVERLY_BROAD_NOISE = "OVERLY_BROAD_NOISE"
    VERIFICATION_COST_OVERRUN = "VERIFICATION_COST_OVERRUN"
    POSITION_EXPOSURE_BIAS = "POSITION_EXPOSURE_BIAS"


class FailureDrivenUpdateVerdict(str, Enum):
    CHALLENGER_PROPOSED = "CHALLENGER_PROPOSED"
    NO_REGISTERED_POLICY_REPAIR = "NO_REGISTERED_POLICY_REPAIR"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


class RootCauseCertificationVerdict(str, Enum):
    ROOT_CAUSE_CERTIFIED = "ROOT_CAUSE_CERTIFIED"
    COUNTERFACTUAL_DID_NOT_RESCUE = "COUNTERFACTUAL_DID_NOT_RESCUE"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class SearchPolicy:
    """Versioned routing/search policy; no field is scientific authority."""

    version: str
    max_candidates: int = 12
    max_per_evidence_root: int = 1
    max_per_mechanism_family: int = 2
    preserve_counterevidence: bool = True
    min_root_obligation_relevance: float = 0.0
    min_expected_information_gain: float = 0.0
    min_substantive_match_score: float = 0.0
    max_verification_cost: float = 1.0e9
    exploration_fraction: float = 0.0
    max_semantic_expansion_terms: int = 8
    require_freshness_retraction_intent: bool = True
    require_negative_result_intent: bool = True
    preserve_retraction_slot: bool = False
    preserve_negative_result_slot: bool = False
    preserve_structural_slot: bool = False
    preserve_method_tool_slot: bool = False
    require_propensity_corrected_feedback: bool = True

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("search policy requires a version")
        if self.max_candidates < 1:
            raise ValueError("max_candidates must be positive")
        if self.max_per_evidence_root < 1 or self.max_per_mechanism_family < 1:
            raise ValueError("diversification limits must be positive")
        if self.max_semantic_expansion_terms < 0:
            raise ValueError("max_semantic_expansion_terms cannot be negative")
        for name in (
            "min_root_obligation_relevance",
            "min_expected_information_gain",
            "min_substantive_match_score",
            "exploration_fraction",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")
        if self.max_verification_cost < 0:
            raise ValueError("max_verification_cost cannot be negative")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SearchPolicyDelta:
    parameter: str
    old_value: object
    new_value: object
    rationale_code: str


@dataclass(frozen=True)
class CounterfactualSearchRun:
    """One exact run receipt in a matched root-cause discriminator."""

    run_id: str
    policy: SearchPolicy
    evaluation_receipt_hash: str
    outcome_passed: bool
    case_subject_hash: str
    task_input_hash: str
    candidate_pool_hash: str
    model_subject_hash: str
    tool_contract_hash: str
    resource_contract_hash: str

    def __post_init__(self) -> None:
        for name in (
            "run_id",
            "evaluation_receipt_hash",
            "case_subject_hash",
            "task_input_hash",
            "candidate_pool_hash",
            "model_subject_hash",
            "tool_contract_hash",
            "resource_contract_hash",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"counterfactual search run requires {name}")

    @property
    def material_context_tuple(self) -> tuple[str, ...]:
        return (
            self.case_subject_hash,
            self.task_input_hash,
            self.candidate_pool_hash,
            self.model_subject_hash,
            self.tool_contract_hash,
            self.resource_contract_hash,
        )


@dataclass(frozen=True)
class SearchRootCauseDiagnostic:
    """Frozen matched experiment for one hypothesized search failure cause."""

    diagnostic_id: str
    certificate_id: str
    failure_id: str
    question_id: str
    hypothesized_signature: SearchFailureSignature
    validated_reference_signature: SearchFailureSignature | None
    diagnosis_reference_receipt_hash: str | None
    causal_evidence_ids: Tuple[str, ...]
    baseline: CounterfactualSearchRun
    counterfactual: CounterfactualSearchRun
    frozen_before_policy_update: bool | None

    def __post_init__(self) -> None:
        for name in ("diagnostic_id", "certificate_id", "failure_id", "question_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"root-cause diagnostic requires {name}")
        if not self.causal_evidence_ids:
            raise ValueError("root-cause diagnostic requires causal evidence ids")
        if len(set(self.causal_evidence_ids)) != len(self.causal_evidence_ids):
            raise ValueError("causal evidence ids must be unique")


_ROOT_CAUSE_CERTIFICATE_ISSUER = object()
_FAILURE_RECEIPT_ISSUER = object()
_ISSUED_ROOT_CAUSE_RECORDS: dict[str, tuple[object, ...]] = {}


@dataclass(frozen=True)
class SearchRootCauseCertificate:
    certificate_id: str
    diagnostic_id: str
    failure_id: str
    question_id: str
    incumbent_policy_version: str
    counterfactual_policy_version: str
    signature: SearchFailureSignature
    intervention_parameters: Tuple[str, ...]
    baseline_run_id: str
    counterfactual_run_id: str
    baseline_evaluation_receipt_hash: str
    counterfactual_evaluation_receipt_hash: str
    matched_material_context_hash: str
    diagnosis_reference_receipt_hash: str
    causal_evidence_ids: Tuple[str, ...]
    subject_hash: str
    _issuer: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._issuer is not _ROOT_CAUSE_CERTIFICATE_ISSUER:
            raise ValueError("SearchRootCauseCertificate must be issued by certify_search_root_cause")
        issued = _ISSUED_ROOT_CAUSE_RECORDS.get(self.certificate_id)
        if issued != _certificate_record(self):
            raise ValueError("SearchRootCauseCertificate does not match its issued immutable record")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def proves_general_policy_improvement(self) -> bool:
        return False


@dataclass(frozen=True)
class RootCauseCertificationAssessment:
    verdict: RootCauseCertificationVerdict
    reasons: Tuple[str, ...] = ()
    certificate: SearchRootCauseCertificate | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SearchFailureReceipt:
    """Failure identity bound to a certified matched root-cause experiment."""

    failure_id: str
    question_id: str
    policy_version: str
    causal_evidence_ids: Tuple[str, ...]
    observed_candidate_ids: Tuple[str, ...]
    root_cause_certificate: SearchRootCauseCertificate
    _issuer: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._issuer is not _FAILURE_RECEIPT_ISSUER:
            raise ValueError("SearchFailureReceipt must be built by build_search_failure_receipt")
        certificate = self.root_cause_certificate
        if not _certificate_is_issued(certificate):
            raise ValueError("failure receipt references an unissued or mutated root-cause certificate")
        if self.failure_id != certificate.failure_id:
            raise ValueError("failure receipt/certificate failure identity mismatch")
        if self.question_id != certificate.question_id:
            raise ValueError("failure receipt/certificate question identity mismatch")
        if self.policy_version != certificate.incumbent_policy_version:
            raise ValueError("failure receipt/certificate incumbent policy mismatch")
        if tuple(sorted(self.causal_evidence_ids)) != tuple(sorted(certificate.causal_evidence_ids)):
            raise ValueError("failure receipt/certificate causal evidence mismatch")

    @property
    def signature(self) -> SearchFailureSignature:
        return self.root_cause_certificate.signature

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SearchPolicyUpdateProposal:
    update_id: str
    failure_id: str
    root_cause_certificate_id: str
    signature: SearchFailureSignature
    from_policy_version: str
    to_policy_version: str
    deltas: Tuple[SearchPolicyDelta, ...]
    expected_metric: str
    falsifier: str
    subject_hash: str

    @property
    def claims_policy_is_better(self) -> bool:
        return False

    @property
    def eligible_for_canonical_promotion(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class FailureDrivenUpdateAssessment:
    verdict: FailureDrivenUpdateVerdict
    reasons: Tuple[str, ...] = ()
    proposal: SearchPolicyUpdateProposal | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _certificate_record(certificate: SearchRootCauseCertificate) -> tuple[object, ...]:
    """Canonical public-field record used to make issued certificates immutable."""

    return (
        certificate.certificate_id,
        certificate.diagnostic_id,
        certificate.failure_id,
        certificate.question_id,
        certificate.incumbent_policy_version,
        certificate.counterfactual_policy_version,
        certificate.signature.value,
        tuple(certificate.intervention_parameters),
        certificate.baseline_run_id,
        certificate.counterfactual_run_id,
        certificate.baseline_evaluation_receipt_hash,
        certificate.counterfactual_evaluation_receipt_hash,
        certificate.matched_material_context_hash,
        certificate.diagnosis_reference_receipt_hash,
        tuple(certificate.causal_evidence_ids),
        certificate.subject_hash,
    )


def _certificate_record_values(
    *,
    certificate_id: str,
    diagnostic_id: str,
    failure_id: str,
    question_id: str,
    incumbent_policy_version: str,
    counterfactual_policy_version: str,
    signature: SearchFailureSignature,
    intervention_parameters: Sequence[str],
    baseline_run_id: str,
    counterfactual_run_id: str,
    baseline_evaluation_receipt_hash: str,
    counterfactual_evaluation_receipt_hash: str,
    matched_material_context_hash: str,
    diagnosis_reference_receipt_hash: str,
    causal_evidence_ids: Sequence[str],
    subject_hash: str,
) -> tuple[object, ...]:
    return (
        certificate_id,
        diagnostic_id,
        failure_id,
        question_id,
        incumbent_policy_version,
        counterfactual_policy_version,
        signature.value,
        tuple(intervention_parameters),
        baseline_run_id,
        counterfactual_run_id,
        baseline_evaluation_receipt_hash,
        counterfactual_evaluation_receipt_hash,
        matched_material_context_hash,
        diagnosis_reference_receipt_hash,
        tuple(causal_evidence_ids),
        subject_hash,
    )


def _certificate_is_issued(certificate: SearchRootCauseCertificate) -> bool:
    return (
        certificate._issuer is _ROOT_CAUSE_CERTIFICATE_ISSUER
        and _ISSUED_ROOT_CAUSE_RECORDS.get(certificate.certificate_id)
        == _certificate_record(certificate)
    )


def _policy_hash(policy: SearchPolicy) -> str:
    payload = tuple((item.name, getattr(policy, item.name)) for item in fields(policy))
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def _material_context_hash(run: CounterfactualSearchRun) -> str:
    return sha256(repr(run.material_context_tuple).encode("utf-8")).hexdigest()


def _delta(parameter: str, old: object, new: object, rationale: str) -> Tuple[SearchPolicyDelta, ...]:
    if old == new:
        return ()
    return (SearchPolicyDelta(parameter, old, new, rationale),)


def _registered_repair(
    policy: SearchPolicy,
    signature: SearchFailureSignature,
) -> tuple[Tuple[SearchPolicyDelta, ...], str, str]:
    """Return the registered repair for one confirmed search failure class."""

    if signature is SearchFailureSignature.MISSED_COUNTEREVIDENCE:
        return (
            _delta(
                "preserve_counterevidence",
                policy.preserve_counterevidence,
                True,
                "reserve_counterevidence_in_diversification",
            ),
            "counterevidence_recall",
            "fresh counterevidence recall does not improve without harming valid support retrieval",
        )
    if signature is SearchFailureSignature.SAME_ROOT_OVERCONCENTRATION:
        return (
            _delta(
                "max_per_evidence_root",
                policy.max_per_evidence_root,
                max(1, policy.max_per_evidence_root - 1),
                "reduce_same_root_echo_slots",
            ),
            "independent_root_coverage",
            "fresh independent-root coverage does not improve",
        )
    if signature is SearchFailureSignature.MECHANISM_MONOCULTURE:
        deltas = ()
        deltas += _delta(
            "max_per_mechanism_family",
            policy.max_per_mechanism_family,
            max(1, policy.max_per_mechanism_family - 1),
            "reduce_mechanism_family_monoculture",
        )
        deltas += _delta(
            "exploration_fraction",
            policy.exploration_fraction,
            min(1.0, round(policy.exploration_fraction + 0.05, 10)),
            "reserve_bounded_novel_route_exploration",
        )
        return deltas, "mechanism_family_coverage", "fresh mechanism-family coverage does not improve"
    if signature is SearchFailureSignature.QUERY_DRIFT:
        return (
            _delta(
                "max_semantic_expansion_terms",
                policy.max_semantic_expansion_terms,
                max(0, policy.max_semantic_expansion_terms - 2),
                "contract_semantic_expansion_after_confirmed_query_drift",
            ),
            "query_drift_rate",
            "fresh query-drift rate does not decrease without material recall loss",
        )
    if signature is SearchFailureSignature.MISSED_RETRACTION_OR_SUPERSESSION:
        deltas = ()
        deltas += _delta(
            "require_freshness_retraction_intent",
            policy.require_freshness_retraction_intent,
            True,
            "force_freshness_retraction_query_intent",
        )
        deltas += _delta(
            "preserve_retraction_slot",
            policy.preserve_retraction_slot,
            True,
            "reserve_retraction_or_correction_candidate_slot",
        )
        return deltas, "retraction_detection_recall", "fresh retraction/supersession recall does not improve"
    if signature is SearchFailureSignature.MISSED_NEGATIVE_RESULT:
        deltas = ()
        deltas += _delta(
            "require_negative_result_intent",
            policy.require_negative_result_intent,
            True,
            "force_negative_result_query_intent",
        )
        deltas += _delta(
            "preserve_negative_result_slot",
            policy.preserve_negative_result_slot,
            True,
            "reserve_negative_result_candidate_slot",
        )
        return deltas, "negative_result_recall", "fresh negative-result recall does not improve"
    if signature is SearchFailureSignature.SURFACE_MATCH_STRUCTURAL_MISS:
        return (
            _delta(
                "preserve_structural_slot",
                policy.preserve_structural_slot,
                True,
                "reserve_candidate_retrieved_from_structural_index",
            ),
            "structural_match_recall",
            "fresh structurally relevant retrieval does not improve",
        )
    if signature is SearchFailureSignature.METHOD_OBLIGATION_UNSERVED:
        return (
            _delta(
                "preserve_method_tool_slot",
                policy.preserve_method_tool_slot,
                True,
                "reserve_method_or_operator_candidate_slot",
            ),
            "obligation_discharge_route_recall",
            "fresh method/operator retrieval does not improve obligation discharge",
        )
    if signature is SearchFailureSignature.LOW_INFORMATION_GAIN:
        return (
            _delta(
                "min_expected_information_gain",
                policy.min_expected_information_gain,
                min(1.0, round(policy.min_expected_information_gain + 0.10, 10)),
                "raise_information_gain_floor",
            ),
            "information_gain_per_retrieval",
            "fresh information gain per retrieval does not improve",
        )
    if signature is SearchFailureSignature.LOW_ROOT_OBLIGATION_RELEVANCE:
        return (
            _delta(
                "min_root_obligation_relevance",
                policy.min_root_obligation_relevance,
                min(1.0, round(policy.min_root_obligation_relevance + 0.10, 10)),
                "raise_root_obligation_relevance_floor",
            ),
            "root_obligation_relevance",
            "fresh root-obligation relevance does not improve",
        )
    if signature is SearchFailureSignature.KEYWORD_STUFFING_FALSE_POSITIVE:
        return (
            _delta(
                "min_substantive_match_score",
                policy.min_substantive_match_score,
                min(1.0, round(policy.min_substantive_match_score + 0.10, 10)),
                "raise_substantive_match_floor_against_keyword_stuffing",
            ),
            "false_positive_rate",
            "fresh keyword-stuffing false positives do not decrease",
        )
    if signature is SearchFailureSignature.OVERLY_NARROW_RECALL:
        return (
            _delta(
                "max_candidates",
                policy.max_candidates,
                policy.max_candidates + 2,
                "expand_bounded_interaction_space_after_verified_recall_failure",
            ),
            "relevant_candidate_recall",
            "fresh relevant-candidate recall does not improve within the resource ceiling",
        )
    if signature is SearchFailureSignature.OVERLY_BROAD_NOISE:
        return (
            _delta(
                "max_candidates",
                policy.max_candidates,
                max(1, policy.max_candidates - 2),
                "shrink_interaction_space_after_verified_noise_failure",
            ),
            "precision_per_candidate",
            "fresh precision/cost does not improve without material recall loss",
        )
    if signature is SearchFailureSignature.VERIFICATION_COST_OVERRUN:
        return (
            _delta(
                "max_verification_cost",
                policy.max_verification_cost,
                round(policy.max_verification_cost * 0.8, 10),
                "tighten_verification_cost_ceiling",
            ),
            "verified_utility_per_cost",
            "fresh verified utility per cost does not improve",
        )
    if signature is SearchFailureSignature.POSITION_EXPOSURE_BIAS:
        deltas = ()
        deltas += _delta(
            "require_propensity_corrected_feedback",
            policy.require_propensity_corrected_feedback,
            True,
            "do_not_treat_rank_exposure_as_unbiased_relevance_feedback",
        )
        deltas += _delta(
            "exploration_fraction",
            policy.exploration_fraction,
            min(1.0, round(policy.exploration_fraction + 0.05, 10)),
            "collect_bounded_counterfactual_exposure",
        )
        return deltas, "bias_corrected_search_utility", "fresh bias-corrected utility does not improve"
    raise AssertionError(f"unhandled search failure signature: {signature}")


def _delta_rows(deltas: Sequence[SearchPolicyDelta]) -> tuple[tuple[str, object, object], ...]:
    return tuple(sorted((item.parameter, item.old_value, item.new_value) for item in deltas))


def _apply_deltas(
    policy: SearchPolicy,
    deltas: Sequence[SearchPolicyDelta],
    to_version: str,
) -> SearchPolicy:
    changes: dict[str, object] = {"version": to_version}
    for delta in deltas:
        if not hasattr(policy, delta.parameter):
            raise ValueError(f"unknown search policy parameter: {delta.parameter}")
        if getattr(policy, delta.parameter) != delta.old_value:
            raise ValueError(f"stale policy delta for {delta.parameter}")
        changes[delta.parameter] = delta.new_value
    return replace(policy, **changes)


def propose_registered_counterfactual_policy(
    incumbent: SearchPolicy,
    signature: SearchFailureSignature,
    *,
    to_policy_version: str,
) -> SearchPolicy:
    """Materialize the one registered repair package for a root-cause probe."""

    if not to_policy_version.strip() or to_policy_version == incumbent.version:
        raise ValueError("counterfactual policy requires a distinct successor version")
    deltas, _, _ = _registered_repair(incumbent, signature)
    if not deltas:
        raise ValueError("registered repair is already saturated for this failure signature")
    return _apply_deltas(incumbent, deltas, to_policy_version)


def _policy_differences(
    baseline: SearchPolicy,
    counterfactual: SearchPolicy,
) -> Tuple[SearchPolicyDelta, ...]:
    differences: list[SearchPolicyDelta] = []
    for item in fields(SearchPolicy):
        if item.name == "version":
            continue
        old = getattr(baseline, item.name)
        new = getattr(counterfactual, item.name)
        if old != new:
            differences.append(
                SearchPolicyDelta(item.name, old, new, "observed_counterfactual_difference")
            )
    return tuple(differences)


def _root_cause_subject_hash(
    *,
    certificate_id: str,
    diagnostic_id: str,
    failure_id: str,
    question_id: str,
    signature: SearchFailureSignature,
    baseline_run_id: str,
    counterfactual_run_id: str,
    baseline_evaluation_receipt_hash: str,
    counterfactual_evaluation_receipt_hash: str,
    baseline_policy_hash: str,
    counterfactual_policy_hash: str,
    matched_material_context_hash: str,
    diagnosis_reference_receipt_hash: str,
    causal_evidence_ids: Sequence[str],
    repair_rows: Sequence[tuple[str, object, object]],
) -> str:
    payload = (
        "SEARCH_ROOT_CAUSE_CERTIFICATE_V1",
        certificate_id,
        diagnostic_id,
        failure_id,
        question_id,
        signature.value,
        baseline_run_id,
        counterfactual_run_id,
        baseline_evaluation_receipt_hash,
        counterfactual_evaluation_receipt_hash,
        baseline_policy_hash,
        counterfactual_policy_hash,
        matched_material_context_hash,
        diagnosis_reference_receipt_hash,
        tuple(sorted(causal_evidence_ids)),
        tuple(repair_rows),
    )
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def certify_search_root_cause(
    diagnostic: SearchRootCauseDiagnostic,
) -> RootCauseCertificationAssessment:
    """Certify one frozen, matched, one-repair counterfactual root-cause probe."""

    if diagnostic.frozen_before_policy_update is None:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.CANNOT_CHECK,
            ("root_cause_diagnostic_freeze_chronology_unknown",),
        )
    if diagnostic.frozen_before_policy_update is False:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("root_cause_diagnostic_defined_posthoc",),
        )
    if diagnostic.validated_reference_signature is None or not diagnostic.diagnosis_reference_receipt_hash:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.CANNOT_CHECK,
            ("known_answer_root_cause_reference_missing",),
        )
    if diagnostic.validated_reference_signature is not diagnostic.hypothesized_signature:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("hypothesized_search_failure_signature_disagrees_with_validated_reference",),
        )

    baseline = diagnostic.baseline
    counterfactual = diagnostic.counterfactual
    if baseline.run_id == counterfactual.run_id:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("baseline_and_counterfactual_run_ids_must_differ",),
        )
    if baseline.evaluation_receipt_hash == counterfactual.evaluation_receipt_hash:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("baseline_and_counterfactual_evaluation_receipts_must_differ",),
        )
    if baseline.policy.version == counterfactual.policy.version:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("counterfactual_policy_version_must_differ",),
        )
    if baseline.material_context_tuple != counterfactual.material_context_tuple:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("counterfactual_search_probe_not_materially_matched",),
        )
    if baseline.outcome_passed:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("baseline_run_did_not_fail",),
        )
    if not counterfactual.outcome_passed:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.COUNTERFACTUAL_DID_NOT_RESCUE,
            ("registered_repair_did_not_rescue_the_frozen_failure_case",),
        )

    expected_deltas, _, _ = _registered_repair(
        baseline.policy,
        diagnostic.hypothesized_signature,
    )
    if not expected_deltas:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("registered_repair_already_saturated_in_baseline_policy",),
        )
    expected_rows = _delta_rows(expected_deltas)
    actual_rows = _delta_rows(_policy_differences(baseline.policy, counterfactual.policy))
    if actual_rows != expected_rows:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("counterfactual_policy_does_not_equal_exact_registered_repair",),
        )

    matched_context_hash = _material_context_hash(baseline)
    subject_hash = _root_cause_subject_hash(
        certificate_id=diagnostic.certificate_id,
        diagnostic_id=diagnostic.diagnostic_id,
        failure_id=diagnostic.failure_id,
        question_id=diagnostic.question_id,
        signature=diagnostic.hypothesized_signature,
        baseline_run_id=baseline.run_id,
        counterfactual_run_id=counterfactual.run_id,
        baseline_evaluation_receipt_hash=baseline.evaluation_receipt_hash,
        counterfactual_evaluation_receipt_hash=counterfactual.evaluation_receipt_hash,
        baseline_policy_hash=_policy_hash(baseline.policy),
        counterfactual_policy_hash=_policy_hash(counterfactual.policy),
        matched_material_context_hash=matched_context_hash,
        diagnosis_reference_receipt_hash=diagnostic.diagnosis_reference_receipt_hash,
        causal_evidence_ids=diagnostic.causal_evidence_ids,
        repair_rows=expected_rows,
    )
    record = _certificate_record_values(
        certificate_id=diagnostic.certificate_id,
        diagnostic_id=diagnostic.diagnostic_id,
        failure_id=diagnostic.failure_id,
        question_id=diagnostic.question_id,
        incumbent_policy_version=baseline.policy.version,
        counterfactual_policy_version=counterfactual.policy.version,
        signature=diagnostic.hypothesized_signature,
        intervention_parameters=tuple(sorted(item.parameter for item in expected_deltas)),
        baseline_run_id=baseline.run_id,
        counterfactual_run_id=counterfactual.run_id,
        baseline_evaluation_receipt_hash=baseline.evaluation_receipt_hash,
        counterfactual_evaluation_receipt_hash=counterfactual.evaluation_receipt_hash,
        matched_material_context_hash=matched_context_hash,
        diagnosis_reference_receipt_hash=diagnostic.diagnosis_reference_receipt_hash,
        causal_evidence_ids=tuple(sorted(diagnostic.causal_evidence_ids)),
        subject_hash=subject_hash,
    )
    existing = _ISSUED_ROOT_CAUSE_RECORDS.get(diagnostic.certificate_id)
    if existing is not None and existing != record:
        return RootCauseCertificationAssessment(
            RootCauseCertificationVerdict.INVALID,
            ("root_cause_certificate_id_collision_with_different_subject",),
        )
    _ISSUED_ROOT_CAUSE_RECORDS[diagnostic.certificate_id] = record
    certificate = SearchRootCauseCertificate(
        certificate_id=diagnostic.certificate_id,
        diagnostic_id=diagnostic.diagnostic_id,
        failure_id=diagnostic.failure_id,
        question_id=diagnostic.question_id,
        incumbent_policy_version=baseline.policy.version,
        counterfactual_policy_version=counterfactual.policy.version,
        signature=diagnostic.hypothesized_signature,
        intervention_parameters=tuple(sorted(item.parameter for item in expected_deltas)),
        baseline_run_id=baseline.run_id,
        counterfactual_run_id=counterfactual.run_id,
        baseline_evaluation_receipt_hash=baseline.evaluation_receipt_hash,
        counterfactual_evaluation_receipt_hash=counterfactual.evaluation_receipt_hash,
        matched_material_context_hash=matched_context_hash,
        diagnosis_reference_receipt_hash=diagnostic.diagnosis_reference_receipt_hash,
        causal_evidence_ids=tuple(sorted(diagnostic.causal_evidence_ids)),
        subject_hash=subject_hash,
        _issuer=_ROOT_CAUSE_CERTIFICATE_ISSUER,
    )
    return RootCauseCertificationAssessment(
        RootCauseCertificationVerdict.ROOT_CAUSE_CERTIFIED,
        (),
        certificate,
    )


def build_search_failure_receipt(
    certificate: SearchRootCauseCertificate,
    *,
    observed_candidate_ids: Sequence[str] = (),
) -> SearchFailureReceipt:
    """Bind an issued root-cause certificate into the only accepted failure receipt."""

    if not _certificate_is_issued(certificate):
        raise ValueError("unissued or mutated root-cause certificate")
    return SearchFailureReceipt(
        failure_id=certificate.failure_id,
        question_id=certificate.question_id,
        policy_version=certificate.incumbent_policy_version,
        causal_evidence_ids=certificate.causal_evidence_ids,
        observed_candidate_ids=tuple(observed_candidate_ids),
        root_cause_certificate=certificate,
        _issuer=_FAILURE_RECEIPT_ISSUER,
    )


def _proposal_hash(
    receipt: SearchFailureReceipt,
    policy: SearchPolicy,
    to_version: str,
    deltas: Sequence[SearchPolicyDelta],
) -> str:
    payload = (
        "SEARCH_POLICY_FAILURE_UPDATE_V4",
        receipt.failure_id,
        receipt.question_id,
        receipt.policy_version,
        receipt.signature.value,
        receipt.root_cause_certificate.certificate_id,
        receipt.root_cause_certificate.subject_hash,
        tuple(sorted(receipt.causal_evidence_ids)),
        _policy_hash(policy),
        to_version,
        tuple(
            (item.parameter, item.old_value, item.new_value, item.rationale_code)
            for item in deltas
        ),
    )
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def derive_search_policy_update(
    receipt: SearchFailureReceipt,
    policy: SearchPolicy,
    *,
    update_id: str,
    to_policy_version: str,
) -> FailureDrivenUpdateAssessment:
    """Map one certified failure to the *same repair* that rescued its frozen probe."""

    if receipt._issuer is not _FAILURE_RECEIPT_ISSUER:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("failure_receipt_not_issued_by_root_cause_certifier",),
        )
    certificate = receipt.root_cause_certificate
    if not _certificate_is_issued(certificate):
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("root_cause_certificate_not_currently_issued_or_was_mutated",),
        )
    if not update_id.strip() or not to_policy_version.strip():
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("update_and_successor_policy_identity_required",),
        )
    if to_policy_version == policy.version:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("successor_policy_version_must_differ",),
        )
    if receipt.policy_version != policy.version:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("failure_receipt_not_bound_to_incumbent_policy",),
        )

    deltas, expected_metric, falsifier = _registered_repair(policy, receipt.signature)
    if not deltas:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.NO_REGISTERED_POLICY_REPAIR,
            (
                "registered repair is already saturated at incumbent policy; "
                "do not substitute an unrelated random idea",
            ),
        )
    if tuple(sorted(item.parameter for item in deltas)) != certificate.intervention_parameters:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("certified_root_cause_intervention_no_longer_matches_registered_repair",),
        )

    # Reconstruct the exact certified counterfactual from the *current* incumbent.
    # This binds contents, not just the policy version and parameter names.
    try:
        reconstructed_counterfactual = _apply_deltas(
            policy,
            deltas,
            certificate.counterfactual_policy_version,
        )
    except ValueError:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("certified_root_cause_repair_is_stale_for_current_policy",),
        )
    expected_subject_hash = _root_cause_subject_hash(
        certificate_id=certificate.certificate_id,
        diagnostic_id=certificate.diagnostic_id,
        failure_id=certificate.failure_id,
        question_id=certificate.question_id,
        signature=certificate.signature,
        baseline_run_id=certificate.baseline_run_id,
        counterfactual_run_id=certificate.counterfactual_run_id,
        baseline_evaluation_receipt_hash=certificate.baseline_evaluation_receipt_hash,
        counterfactual_evaluation_receipt_hash=certificate.counterfactual_evaluation_receipt_hash,
        baseline_policy_hash=_policy_hash(policy),
        counterfactual_policy_hash=_policy_hash(reconstructed_counterfactual),
        matched_material_context_hash=certificate.matched_material_context_hash,
        diagnosis_reference_receipt_hash=certificate.diagnosis_reference_receipt_hash,
        causal_evidence_ids=certificate.causal_evidence_ids,
        repair_rows=_delta_rows(deltas),
    )
    if expected_subject_hash != certificate.subject_hash:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.INVALID,
            ("certified_root_cause_subject_not_valid_for_current_policy_repair",),
        )

    proposal = SearchPolicyUpdateProposal(
        update_id=update_id,
        failure_id=receipt.failure_id,
        root_cause_certificate_id=certificate.certificate_id,
        signature=receipt.signature,
        from_policy_version=policy.version,
        to_policy_version=to_policy_version,
        deltas=tuple(deltas),
        expected_metric=expected_metric,
        falsifier=falsifier,
        subject_hash=_proposal_hash(receipt, policy, to_policy_version, deltas),
    )
    return FailureDrivenUpdateAssessment(
        FailureDrivenUpdateVerdict.CHALLENGER_PROPOSED,
        (),
        proposal,
    )


def materialize_search_policy_challenger(
    incumbent: SearchPolicy,
    proposal: SearchPolicyUpdateProposal,
) -> SearchPolicy:
    """Materialize the exact proposal; this does not establish improvement."""

    if proposal.from_policy_version != incumbent.version:
        raise ValueError("proposal is not bound to incumbent policy version")
    return _apply_deltas(incumbent, proposal.deltas, proposal.to_policy_version)


def _root_bound_intent_terms(question: ScientificSearchQuestion) -> Tuple[str, ...]:
    residual = tuple(term.strip() for term in question.residual_terms if term.strip())
    return residual if residual else (question.root_goal,)


def _forced_intent(
    question: ScientificSearchQuestion,
    kind: SearchIntentKind,
    purpose: str,
) -> SearchIntent:
    return SearchIntent(
        intent_id=f"{question.question_id}:policy:{kind.value}",
        kind=kind,
        terms=_root_bound_intent_terms(question),
        purpose=purpose,
        root_goal_hash=question.root_goal_hash,
        atom_id=question.atom_id,
    )


def compile_search_intents_with_policy(
    question: ScientificSearchQuestion,
    policy: SearchPolicy,
) -> Tuple[SearchIntent, ...]:
    """Compile next-iteration intents under a versioned learned search policy."""

    rewritten: list[SearchIntent] = []
    for intent in compile_search_intents(question):
        if intent.kind is SearchIntentKind.SEMANTIC_EXPANSION:
            terms = intent.terms[: policy.max_semantic_expansion_terms]
            if not terms:
                continue
            intent = replace(intent, terms=terms)
        rewritten.append(intent)

    present = {intent.kind for intent in rewritten}
    if (
        policy.require_freshness_retraction_intent
        and SearchIntentKind.FRESHNESS_RETRACTION not in present
    ):
        rewritten.append(
            _forced_intent(
                question,
                SearchIntentKind.FRESHNESS_RETRACTION,
                "policy-required freshness/retraction check after prior search failure",
            )
        )
    if policy.require_negative_result_intent and SearchIntentKind.NEGATIVE_RESULT not in present:
        rewritten.append(
            _forced_intent(
                question,
                SearchIntentKind.NEGATIVE_RESULT,
                "policy-required negative-result search after prior search failure",
            )
        )
    return tuple(rewritten)


def _route_key(candidate: SearchCandidate) -> tuple[object, ...]:
    rank = candidate.rank
    return (
        -rank.root_obligation_relevance,
        -rank.expected_information_gain,
        -rank.context_alignment,
        -rank.structural_fit,
        -max(rank.contradiction_value, rank.negative_result_value),
        rank.failure_risk,
        rank.verification_cost + rank.retrieval_cost,
        candidate.candidate_id,
    )


def _explore_key(candidate: SearchCandidate) -> tuple[object, ...]:
    rank = candidate.rank
    return (
        -rank.novel_route_value,
        -rank.independent_root_contribution,
        -rank.structural_fit,
        candidate.candidate_id,
    )


def _can_add(
    candidate: SearchCandidate,
    selected: Sequence[SearchCandidate],
    policy: SearchPolicy,
) -> bool:
    if any(item.canonical_content_id == candidate.canonical_content_id for item in selected):
        return False
    if candidate.evidence_root_id:
        root_count = sum(
            item.evidence_root_id == candidate.evidence_root_id for item in selected
        )
        if root_count >= policy.max_per_evidence_root:
            return False
    if candidate.mechanism_family:
        mechanism_count = sum(
            item.mechanism_family == candidate.mechanism_family for item in selected
        )
        if mechanism_count >= policy.max_per_mechanism_family:
            return False
    return True


def _reserve_one(
    selected: list[SearchCandidate],
    candidates: Sequence[SearchCandidate],
    policy: SearchPolicy,
    predicate: Callable[[SearchCandidate], bool],
) -> None:
    if len(selected) >= policy.max_candidates:
        return
    for candidate in sorted((item for item in candidates if predicate(item)), key=_route_key):
        if candidate not in selected and _can_add(candidate, selected, policy):
            selected.append(candidate)
            return


def select_candidates_with_policy(
    candidates: Sequence[SearchCandidate],
    policy: SearchPolicy,
) -> Tuple[SearchCandidate, ...]:
    """Apply the learned policy to next-iteration candidate selection."""

    # Hard safety boundary: no learned policy can route benchmark-target leakage.
    eligible = tuple(
        item
        for item in candidates
        if not item.benchmark_target_leak
        and item.rank.root_obligation_relevance >= policy.min_root_obligation_relevance
        and item.rank.expected_information_gain >= policy.min_expected_information_gain
        and item.substantive_match_score >= policy.min_substantive_match_score
        and item.rank.verification_cost <= policy.max_verification_cost
    )
    if not eligible:
        return ()

    selected: list[SearchCandidate] = []
    # Counterevidence is load-bearing and reserves budget before specialized slots
    # and exploration.
    if policy.preserve_counterevidence:
        _reserve_one(
            selected,
            eligible,
            policy,
            lambda item: item.stance
            in {
                EvidenceStance.REFUTE,
                EvidenceStance.NEGATIVE_RESULT,
                EvidenceStance.RETRACTION_CORRECTION,
            },
        )
    if policy.preserve_retraction_slot:
        _reserve_one(
            selected,
            eligible,
            policy,
            lambda item: item.stance is EvidenceStance.RETRACTION_CORRECTION,
        )
    if policy.preserve_negative_result_slot:
        _reserve_one(
            selected,
            eligible,
            policy,
            lambda item: item.stance is EvidenceStance.NEGATIVE_RESULT,
        )
    if policy.preserve_structural_slot:
        _reserve_one(
            selected,
            eligible,
            policy,
            lambda item: SearchIndexKind.STRUCTURAL in item.index_kinds,
        )
    if policy.preserve_method_tool_slot:
        _reserve_one(
            selected,
            eligible,
            policy,
            lambda item: (
                item.vertical is SearchVertical.METHOD_TOOL
                or SearchIndexKind.METHOD_OPERATOR in item.index_kinds
            ),
        )

    explore_slots = 0
    if policy.exploration_fraction > 0 and len(selected) < policy.max_candidates:
        explore_slots = min(
            policy.max_candidates - len(selected),
            max(1, ceil(policy.max_candidates * policy.exploration_fraction)),
        )
    exploit_limit = policy.max_candidates - explore_slots

    exploit_order = diversify_candidates(
        eligible,
        limit=max(1, len(eligible)),
        max_per_evidence_root=policy.max_per_evidence_root,
        max_per_mechanism_family=policy.max_per_mechanism_family,
        preserve_counterevidence=policy.preserve_counterevidence,
    )
    for candidate in exploit_order:
        if len(selected) >= exploit_limit:
            break
        if candidate not in selected and _can_add(candidate, selected, policy):
            selected.append(candidate)

    if explore_slots:
        added = 0
        for candidate in sorted(eligible, key=_explore_key):
            if added >= explore_slots or len(selected) >= policy.max_candidates:
                break
            if candidate not in selected and _can_add(candidate, selected, policy):
                selected.append(candidate)
                added += 1

    # Diversity constraints can make an exploration reservation impossible; fill
    # any remaining safe slots from the exploitation order rather than underfill.
    if len(selected) < policy.max_candidates:
        for candidate in exploit_order:
            if len(selected) >= policy.max_candidates:
                break
            if candidate not in selected and _can_add(candidate, selected, policy):
                selected.append(candidate)

    return tuple(selected)


def search_feedback_value_with_policy(
    feedback: SearchFeedback,
    policy: SearchPolicy,
    *,
    max_weight: float = 10.0,
) -> float:
    """Convert observation feedback to a routing-learning signal under policy."""

    if feedback.verified_downstream_success is None or not feedback.inspected:
        return 0.0
    if policy.require_propensity_corrected_feedback:
        return bias_corrected_feedback_value(feedback, max_weight=max_weight)
    return 1.0 if feedback.verified_downstream_success else -1.0
