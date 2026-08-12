"""Failure-driven SearchPolicy evolution for RAKL (#433, #434).

This module encodes the central continual-improvement arrow explicitly::

    failure_t -> diagnosed search defect_t -> bounded policy challenger_{t+1}

not::

    failure_t -> another unconstrained idea

A failed trajectory does not directly mutate search behavior.  It must first
produce a frozen, known-answer-validated ``SearchFailureReceipt`` with a typed
root-cause signature.  That signature maps to an allow-listed search-policy
repair.  The resulting successor is a *challenger*, not a claim that the policy
is better.  Only fresh held-out assurance may establish improvement and only
Self-RAKL governance may promote a challenger.

The policy affects retrieval/routing only.  Failure frequency, ranking feedback,
policy updates, and successful fresh assurance never mint scientific authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Sequence, Tuple

from .epistemic_search import SearchCandidate, diversify_candidates

__all__ = [
    "FailureDrivenUpdateAssessment",
    "FailureDrivenUpdateVerdict",
    "SearchFailureReceipt",
    "SearchFailureSignature",
    "SearchPolicy",
    "SearchPolicyDelta",
    "SearchPolicyUpdateProposal",
    "derive_search_policy_update",
    "materialize_search_policy_challenger",
    "select_candidates_with_policy",
]


class SearchFailureSignature(str, Enum):
    """Search-layer root causes that have registered repair semantics."""

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
    """Versioned routing/search policy.  No coordinate is scientific authority."""

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
    require_root_goal_binding: bool = True
    require_freshness_retraction_intent: bool = True
    require_negative_result_intent: bool = True
    require_structural_intent: bool = False
    require_method_intent: bool = False
    require_propensity_corrected_feedback: bool = True

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("search policy requires a version")
        if self.max_candidates < 1:
            raise ValueError("max_candidates must be positive")
        if self.max_per_evidence_root < 1 or self.max_per_mechanism_family < 1:
            raise ValueError("diversification limits must be positive")
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
    """Frozen diagnosis of why a search trajectory failed."""

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
    """One failure-bound policy challenger proposal.

    ``expected_metric`` and ``falsifier`` state the hypothesis.  They do not
    assert improvement.  ``subject_hash`` binds the exact failure, incumbent and
    parameter changes for later fresh assurance.
    """

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
    """Return the only registered v1 repair family for a typed search failure."""

    if signature is SearchFailureSignature.MISSED_COUNTEREVIDENCE:
        return (
            _delta(
                "preserve_counterevidence",
                policy.preserve_counterevidence,
                True,
                "counterevidence_must_survive_diversification",
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
            "reserve_small_exploration_budget_for_alternative_mechanisms",
        )
        return deltas, "mechanism_family_coverage", "fresh mechanism-family coverage does not improve"
    if signature is SearchFailureSignature.QUERY_DRIFT:
        return (
            _delta(
                "require_root_goal_binding",
                policy.require_root_goal_binding,
                True,
                "bind_every_query_expansion_to_root_goal_and_atom",
            ),
            "query_drift_rate",
            "fresh query-drift rate does not decrease",
        )
    if signature is SearchFailureSignature.MISSED_RETRACTION_OR_SUPERSESSION:
        return (
            _delta(
                "require_freshness_retraction_intent",
                policy.require_freshness_retraction_intent,
                True,
                "force_freshness_retraction_search_intent",
            ),
            "retraction_detection_recall",
            "fresh retraction/supersession recall does not improve",
        )
    if signature is SearchFailureSignature.MISSED_NEGATIVE_RESULT:
        return (
            _delta(
                "require_negative_result_intent",
                policy.require_negative_result_intent,
                True,
                "force_negative_result_search_intent",
            ),
            "negative_result_recall",
            "fresh negative-result recall does not improve",
        )
    if signature is SearchFailureSignature.SURFACE_MATCH_STRUCTURAL_MISS:
        return (
            _delta(
                "require_structural_intent",
                policy.require_structural_intent,
                True,
                "require_structure_mechanism_search_not_only_surface_terms",
            ),
            "structural_match_recall",
            "fresh structurally relevant retrieval does not improve",
        )
    if signature is SearchFailureSignature.METHOD_OBLIGATION_UNSERVED:
        return (
            _delta(
                "require_method_intent",
                policy.require_method_intent,
                True,
                "require_method_operator_search_for_open_obligations",
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
            "collect_bounded_counterfactual_exposure_for_policy_learning",
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
            "SEARCH_POLICY_FAILURE_UPDATE_V1",
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
    """Map one validated failure to its registered bounded policy repair.

    There is intentionally no caller-supplied arbitrary delta argument.  If the
    diagnosed failure has no remaining registered repair at the current policy,
    the correct result is ``NO_REGISTERED_POLICY_REPAIR`` rather than inventing a
    random mechanism.
    """

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
    """Materialize the exact proposed policy as an experimental challenger."""

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


def select_candidates_with_policy(
    candidates: Sequence[SearchCandidate],
    policy: SearchPolicy,
) -> Tuple[SearchCandidate, ...]:
    """Apply policy thresholds/diversification to already-retrieved candidates.

    This is routing only.  Thresholds may change what is inspected next, but
    cannot upgrade evidence or scientific authority.
    """

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
    return diversify_candidates(
        eligible,
        limit=policy.max_candidates,
        max_per_evidence_root=policy.max_per_evidence_root,
        max_per_mechanism_family=policy.max_per_mechanism_family,
        preserve_counterevidence=policy.preserve_counterevidence,
    )
