"""Failure-driven SearchPolicy evolution for RAKL (#433, #434).

This module makes the continual-improvement arrow executable::

    failure_t
      -> typed root-cause diagnosis_t
      -> bounded SearchPolicyDelta_t
      -> policy challenger_{t+1}
      -> fresh assurance

and explicitly rejects::

    failure_t -> another unconstrained idea

A failed trajectory cannot mutate search directly.  It must first yield a
frozen, known-answer-validated ``SearchFailureReceipt`` whose root cause survives
a counterfactual discriminator.  Each registered failure signature maps to an
allow-listed, *operational* policy repair: the successor changes query intent,
selection/diversification, exploration, or feedback learning on the next search.

The successor is still only a challenger.  The update function cannot claim it
is better; fresh held-out assurance and protected Self-RAKL governance own that
judgement and any later promotion.  Search/ranking feedback never mints
scientific authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
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
    "FailureDrivenUpdateAssessment",
    "FailureDrivenUpdateVerdict",
    "SearchFailureReceipt",
    "SearchFailureSignature",
    "SearchPolicy",
    "SearchPolicyDelta",
    "SearchPolicyUpdateProposal",
    "compile_search_intents_with_policy",
    "derive_search_policy_update",
    "materialize_search_policy_challenger",
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
class SearchFailureReceipt:
    """Frozen causal diagnosis of why one search trajectory failed."""

    failure_id: str
    question_id: str
    policy_version: str
    signature: SearchFailureSignature
    causal_evidence_ids: Tuple[str, ...]
    observed_candidate_ids: Tuple[str, ...] = ()
    known_answer_validated: bool | None = None
    root_cause_confirmed: bool | None = None
    counterfactual_discriminator_passed: bool | None = None
    frozen_before_update: bool | None = None

    def __post_init__(self) -> None:
        if not self.failure_id.strip() or not self.question_id.strip() or not self.policy_version.strip():
            raise ValueError("failure receipt requires failure/question/policy identities")
        if not self.causal_evidence_ids:
            raise ValueError("failure receipt requires causal evidence ids")
        if len(set(self.causal_evidence_ids)) != len(self.causal_evidence_ids):
            raise ValueError("causal evidence ids must be unique")

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
class SearchPolicyUpdateProposal:
    update_id: str
    failure_id: str
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


def _delta(parameter: str, old: object, new: object, rationale: str) -> Tuple[SearchPolicyDelta, ...]:
    if old == new:
        return ()
    return (SearchPolicyDelta(parameter, old, new, rationale),)


def _registered_repair(
    policy: SearchPolicy,
    signature: SearchFailureSignature,
) -> tuple[Tuple[SearchPolicyDelta, ...], str, str]:
    """Return the registered v1 policy repair for a confirmed search failure."""

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


def _proposal_hash(
    receipt: SearchFailureReceipt,
    policy: SearchPolicy,
    to_version: str,
    deltas: Sequence[SearchPolicyDelta],
) -> str:
    payload = repr(
        (
            "SEARCH_POLICY_FAILURE_UPDATE_V2",
            receipt.failure_id,
            receipt.question_id,
            receipt.policy_version,
            receipt.signature.value,
            tuple(sorted(receipt.causal_evidence_ids)),
            policy,
            to_version,
            tuple((item.parameter, item.old_value, item.new_value, item.rationale_code) for item in deltas),
        )
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def derive_search_policy_update(
    receipt: SearchFailureReceipt,
    policy: SearchPolicy,
    *,
    update_id: str,
    to_policy_version: str,
) -> FailureDrivenUpdateAssessment:
    """Map one validated failure to the registered bounded search-policy repair."""

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
    if receipt.known_answer_validated is not True:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.CANNOT_CHECK,
            ("failure_diagnosis_not_known_answer_validated",),
        )
    if receipt.root_cause_confirmed is not True:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.CANNOT_CHECK,
            ("search_root_cause_not_confirmed",),
        )
    if receipt.counterfactual_discriminator_passed is not True:
        return FailureDrivenUpdateAssessment(
            FailureDrivenUpdateVerdict.CANNOT_CHECK,
            ("root_cause_counterfactual_discriminator_not_passed",),
        )
    if receipt.frozen_before_update is not True:
        verdict = (
            FailureDrivenUpdateVerdict.CANNOT_CHECK
            if receipt.frozen_before_update is None
            else FailureDrivenUpdateVerdict.INVALID
        )
        return FailureDrivenUpdateAssessment(
            verdict,
            ("failure_receipt_not_frozen_before_policy_update",),
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

    proposal = SearchPolicyUpdateProposal(
        update_id=update_id,
        failure_id=receipt.failure_id,
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
    changes: dict[str, object] = {"version": proposal.to_policy_version}
    for delta in proposal.deltas:
        if not hasattr(incumbent, delta.parameter):
            raise ValueError(f"unknown search policy parameter: {delta.parameter}")
        if getattr(incumbent, delta.parameter) != delta.old_value:
            raise ValueError(f"stale policy delta for {delta.parameter}")
        changes[delta.parameter] = delta.new_value
    return replace(incumbent, **changes)


def _intent_terms(question: ScientificSearchQuestion) -> Tuple[str, ...]:
    for terms in (
        question.residual_terms,
        question.source_native_terms,
        question.semantic_expansions,
        question.structural_coordinates,
    ):
        cleaned = tuple(term.strip() for term in terms if term.strip())
        if cleaned:
            return cleaned
    return (question.root_goal,)


def _forced_intent(
    question: ScientificSearchQuestion,
    kind: SearchIntentKind,
    purpose: str,
) -> SearchIntent:
    return SearchIntent(
        intent_id=f"{question.question_id}:policy:{kind.value}",
        kind=kind,
        terms=_intent_terms(question),
        purpose=purpose,
        root_goal_hash=question.root_goal_hash,
        atom_id=question.atom_id,
    )


def compile_search_intents_with_policy(
    question: ScientificSearchQuestion,
    policy: SearchPolicy,
) -> Tuple[SearchIntent, ...]:
    """Compile next-iteration intents under a versioned learned search policy."""

    base = list(compile_search_intents(question))
    rewritten: list[SearchIntent] = []
    for intent in base:
        if intent.kind is SearchIntentKind.SEMANTIC_EXPANSION:
            terms = intent.terms[: policy.max_semantic_expansion_terms]
            if not terms:
                continue
            intent = replace(intent, terms=terms)
        rewritten.append(intent)

    present = {intent.kind for intent in rewritten}
    if policy.require_freshness_retraction_intent and SearchIntentKind.FRESHNESS_RETRACTION not in present:
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


def _can_add(candidate: SearchCandidate, selected: Sequence[SearchCandidate], policy: SearchPolicy) -> bool:
    if any(item.canonical_content_id == candidate.canonical_content_id for item in selected):
        return False
    if candidate.evidence_root_id:
        root_count = sum(item.evidence_root_id == candidate.evidence_root_id for item in selected)
        if root_count >= policy.max_per_evidence_root:
            return False
    if candidate.mechanism_family:
        mechanism_count = sum(item.mechanism_family == candidate.mechanism_family for item in selected)
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

    eligible = tuple(
        item
        for item in candidates
        if item.rank.root_obligation_relevance >= policy.min_root_obligation_relevance
        and item.rank.expected_information_gain >= policy.min_expected_information_gain
        and item.substantive_match_score >= policy.min_substantive_match_score
        and item.rank.verification_cost <= policy.max_verification_cost
    )
    if not eligible:
        return ()

    selected: list[SearchCandidate] = []
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
    if policy.exploration_fraction > 0:
        explore_slots = min(
            policy.max_candidates - len(selected),
            max(1, ceil(policy.max_candidates * policy.exploration_fraction)),
        )
    exploit_target = max(0, policy.max_candidates - len(selected) - explore_slots)

    exploit_order = diversify_candidates(
        eligible,
        limit=max(1, len(eligible)),
        max_per_evidence_root=policy.max_per_evidence_root,
        max_per_mechanism_family=policy.max_per_mechanism_family,
        preserve_counterevidence=policy.preserve_counterevidence,
    )
    for candidate in exploit_order:
        if len(selected) >= policy.max_candidates - explore_slots:
            break
        if candidate not in selected and _can_add(candidate, selected, policy):
            selected.append(candidate)
            if len(selected) >= exploit_target + (policy.max_candidates - explore_slots - exploit_target):
                break

    if explore_slots:
        added = 0
        for candidate in sorted(eligible, key=_explore_key):
            if added >= explore_slots or len(selected) >= policy.max_candidates:
                break
            if candidate not in selected and _can_add(candidate, selected, policy):
                selected.append(candidate)
                added += 1

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
