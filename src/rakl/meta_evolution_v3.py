"""Research-only v3 controls for recursive RAKL self-evolution.

The governing adversarial packet is
``research/self_rakl_p4_p6_question_saturation_v3/META_EVOLUTION_V3_FROZEN_BENCHMARK.json``.
It was committed before this module.

V3 closes identity-gaming residuals left deliberately open by v2:

* contexts are canonical content-bound identities rather than opaque scope names;
* cross-context mutation credit requires an explicit transport witness;
* failed mutation-family diversity is content-bound rather than label-bound;
* outer evaluator independence is determined by content/dependency/metric/environment
  identity and chronology, not display-name inequality;
* an underidentified mutation may proceed only through a decision-bearing
  discriminator receipt owned by the existing diagnosis/VOI lane;
* blocking validity continues to precede every soft Pareto comparison.

This module does not implement a new discriminator-selection algorithm.  It
consumes receipts from the existing diagnosis controller.  No object here grants
scientific authority or method-promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from .evolution import EvolutionVerdict
from .meta_evolution import CandidateDelta, EvolutionLayer, MutationGovernance, SelfEvolutionAction, SelfEvolutionPlan
from .meta_evolution_v2 import (
    BlockingValidity,
    ContextualMutationCredit,
    ContextualMutationPolicy,
    DiagnosisBoundEvolutionPortrait,
    ValidatedCandidateDelta,
    plan_self_evolution_v2,
    validity_gated_pareto_frontier,
)


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _nonempty(value: str, *, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} cannot be blank")
    return value


@dataclass(frozen=True)
class CanonicalContextIdentity:
    """Content-bound context for mutation evidence.

    Human-readable aliases deliberately do not enter the digest.  Renaming a
    fibre/scope therefore cannot manufacture a new evidence context.
    """

    domain_id: str
    problem_family_id: str
    structural_substrate_digest: str
    evaluator_epoch_digest: str
    alias: str = ""

    def __post_init__(self) -> None:
        for field in (
            "domain_id",
            "problem_family_id",
            "structural_substrate_digest",
            "evaluator_epoch_digest",
        ):
            _nonempty(getattr(self, field), field=field)

    @property
    def digest(self) -> str:
        return _digest(
            {
                "domain_id": self.domain_id,
                "problem_family_id": self.problem_family_id,
                "structural_substrate_digest": self.structural_substrate_digest,
                "evaluator_epoch_digest": self.evaluator_epoch_digest,
            }
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ContextTransportWitness:
    witness_id: str
    operator_id: str
    target_layer: EvolutionLayer
    source_context_digest: str
    destination_context_digest: str
    evidence_epoch_id: str
    rationale: str

    def __post_init__(self) -> None:
        for field in (
            "witness_id",
            "operator_id",
            "source_context_digest",
            "destination_context_digest",
            "evidence_epoch_id",
            "rationale",
        ):
            _nonempty(getattr(self, field), field=field)
        if self.source_context_digest == self.destination_context_digest:
            raise ValueError("transport witness requires two distinct contexts")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ContextualMutationPolicyV3:
    """Mutation credit keyed by canonical context digest."""

    entries: tuple[ContextualMutationCredit, ...]

    def __post_init__(self) -> None:
        if not self.entries:
            raise ValueError("contextual mutation policy requires entries")
        keys = [(e.operator_id, e.target_layer, e.scope_key) for e in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("contextual mutation-policy keys must be unique")

    @classmethod
    def from_v2(cls, policy: ContextualMutationPolicy) -> "ContextualMutationPolicyV3":
        return cls(policy.entries)

    def weight_for(
        self,
        *,
        operator_id: str,
        target_layer: EvolutionLayer,
        context: CanonicalContextIdentity,
    ) -> float:
        for entry in self.entries:
            if (
                entry.operator_id == operator_id
                and entry.target_layer is target_layer
                and entry.scope_key == context.digest
            ):
                return entry.weight
        raise KeyError((operator_id, target_layer, context.digest))

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def transported_weight_v3(
    policy: ContextualMutationPolicyV3,
    *,
    operator_id: str,
    target_layer: EvolutionLayer,
    source_context: CanonicalContextIdentity,
    destination_context: CanonicalContextIdentity,
    witness: ContextTransportWitness | None,
) -> float | None:
    """Return earned source credit in a new context only under an exact witness.

    ``None`` means there is no licensed cross-context credit.  This function does
    not copy or promote the policy entry; it exposes a candidate prior to the
    surrounding protected method gate.
    """

    try:
        source_weight = policy.weight_for(
            operator_id=operator_id,
            target_layer=target_layer,
            context=source_context,
        )
    except KeyError:
        return None

    if source_context.digest == destination_context.digest:
        return source_weight
    if witness is None:
        return None
    if (
        witness.operator_id != operator_id
        or witness.target_layer is not target_layer
        or witness.source_context_digest != source_context.digest
        or witness.destination_context_digest != destination_context.digest
    ):
        return None
    return source_weight


@dataclass(frozen=True)
class MutationFamilyWitness:
    """Semantic identity of a mutation family for escalation accounting."""

    target_layer: EvolutionLayer
    precondition_ids: tuple[str, ...]
    effect_ids: tuple[str, ...]
    falsifier_ids: tuple[str, ...]
    mechanism_class_id: str
    alias: str = ""

    def __post_init__(self) -> None:
        _nonempty(self.mechanism_class_id, field="mechanism_class_id")
        for name, values in (
            ("precondition_ids", self.precondition_ids),
            ("effect_ids", self.effect_ids),
            ("falsifier_ids", self.falsifier_ids),
        ):
            if not values or any(not value.strip() for value in values):
                raise ValueError(f"{name} requires non-empty identities")

    @staticmethod
    def _normal(values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(values)))

    @property
    def digest(self) -> str:
        return _digest(
            {
                "target_layer": self.target_layer.value,
                "mechanism_class_id": self.mechanism_class_id,
                "precondition_ids": self._normal(self.precondition_ids),
                "effect_ids": self._normal(self.effect_ids),
                "falsifier_ids": self._normal(self.falsifier_ids),
            }
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class FailureEpochV3:
    epoch_id: str
    family: MutationFamilyWitness

    def __post_init__(self) -> None:
        _nonempty(self.epoch_id, field="epoch_id")


def distinct_failed_mutation_families_v3(epochs: Iterable[FailureEpochV3]) -> int:
    items = tuple(epochs)
    epoch_ids = [item.epoch_id for item in items]
    if len(epoch_ids) != len(set(epoch_ids)):
        raise ValueError("failure evidence epoch ids must be unique")
    return len({item.family.digest for item in items})


@dataclass(frozen=True)
class EvaluatorEpochIdentity:
    """Content identity of a research evaluator epoch.

    ``display_id`` is deliberately excluded from the content digest.  A renamed
    evaluator with identical rules is still the same evaluator for independence
    purposes.
    """

    display_id: str
    evaluator_source_digest: str
    dependency_digest: str
    metric_semantics_digest: str
    benchmark_digest: str
    environment_digest: str
    cutoff_id: str

    def __post_init__(self) -> None:
        for field in (
            "display_id",
            "evaluator_source_digest",
            "dependency_digest",
            "metric_semantics_digest",
            "benchmark_digest",
            "environment_digest",
            "cutoff_id",
        ):
            _nonempty(getattr(self, field), field=field)

    @property
    def evaluator_content_digest(self) -> str:
        return _digest(
            {
                "evaluator_source_digest": self.evaluator_source_digest,
                "dependency_digest": self.dependency_digest,
                "metric_semantics_digest": self.metric_semantics_digest,
                "environment_digest": self.environment_digest,
            }
        )

    @property
    def epoch_digest(self) -> str:
        return _digest(
            {
                "evaluator_content_digest": self.evaluator_content_digest,
                "benchmark_digest": self.benchmark_digest,
                "cutoff_id": self.cutoff_id,
            }
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class OuterAssuranceBindingV3:
    assurance_id: str
    subject_sha: str
    outer_evaluator: EvaluatorEpochIdentity
    frozen_before_candidate_outcome: bool | None
    candidate_outcomes_used_to_define_outer_evaluator: bool | None

    def __post_init__(self) -> None:
        _nonempty(self.assurance_id, field="assurance_id")
        _nonempty(self.subject_sha, field="subject_sha")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


_HIGHER_ORDER = {
    EvolutionLayer.EVALUATOR,
    EvolutionLayer.META_POLICY,
    EvolutionLayer.MUTATION_LANGUAGE,
}


def assess_mutation_governance_v3(
    *,
    target_layer: EvolutionLayer,
    target_evaluator: EvaluatorEpochIdentity,
    candidate_subject_sha: str,
    candidate_benchmark_digest: str,
    outer_assurance: OuterAssuranceBindingV3 | None,
) -> MutationGovernance:
    """Fail closed on naming-only or post-outcome outer assurance."""

    _nonempty(candidate_subject_sha, field="candidate_subject_sha")
    _nonempty(candidate_benchmark_digest, field="candidate_benchmark_digest")

    if target_layer is EvolutionLayer.CONSTITUTION:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("constitutional_change_requires_external_amendment_review",),
        )
    if target_layer not in _HIGHER_ORDER:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=True,
            requires_outer_assurance=False,
            reasons=("ordinary_mutation_may_enter_existing_protected_method_promotion_gate",),
        )
    if outer_assurance is None:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("higher_order_mutation_missing_outer_assurance",),
        )
    if outer_assurance.subject_sha != candidate_subject_sha:
        return MutationGovernance(True, False, True, ("outer_assurance_subject_mismatch",))
    if outer_assurance.outer_evaluator.benchmark_digest != candidate_benchmark_digest:
        return MutationGovernance(True, False, True, ("outer_assurance_benchmark_mismatch",))
    if outer_assurance.frozen_before_candidate_outcome is not True:
        return MutationGovernance(True, False, True, ("outer_assurance_not_preoutcome",))
    if outer_assurance.candidate_outcomes_used_to_define_outer_evaluator is not False:
        return MutationGovernance(True, False, True, ("outer_evaluator_conditioned_on_candidate_outcomes",))
    if outer_assurance.outer_evaluator.evaluator_content_digest == target_evaluator.evaluator_content_digest:
        return MutationGovernance(True, False, True, ("outer_evaluator_not_content_independent",))

    return MutationGovernance(
        proposal_allowed=True,
        eligible_for_auto_promotion=True,
        requires_outer_assurance=True,
        reasons=("content_bound_preoutcome_outer_assurance_allows_entry_to_protected_gate",),
    )


@dataclass(frozen=True)
class DiscriminatorDecisionReceipt:
    """Decision-bearing receipt produced by the existing diagnosis/VOI lane."""

    receipt_id: str
    diagnosis_before_digest: str
    diagnosis_after_digest: str
    discriminator_id: str
    evidence_epoch_id: str
    total_cost: float
    resolved_target_layer: EvolutionLayer

    def __post_init__(self) -> None:
        for field in (
            "receipt_id",
            "diagnosis_before_digest",
            "diagnosis_after_digest",
            "discriminator_id",
            "evidence_epoch_id",
        ):
            _nonempty(getattr(self, field), field=field)
        if self.total_cost < 0:
            raise ValueError("discriminator cost cannot be negative")
        if self.diagnosis_before_digest == self.diagnosis_after_digest:
            raise ValueError("decision-bearing discriminator must refine diagnosis state")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def plan_self_evolution_v3(
    portrait: DiagnosisBoundEvolutionPortrait,
    *,
    current_diagnosis_digest: str,
    discriminator_receipt: DiscriminatorDecisionReceipt | None = None,
) -> SelfEvolutionPlan:
    """Consume v2 routing, and only resolve an underidentified case by receipt."""

    _nonempty(current_diagnosis_digest, field="current_diagnosis_digest")
    baseline = plan_self_evolution_v2(portrait)
    if baseline.action is not SelfEvolutionAction.RUN_DISCRIMINATOR:
        if discriminator_receipt is not None:
            raise ValueError("discriminator receipt supplied when no discriminator is required")
        return baseline
    if discriminator_receipt is None:
        return baseline
    if discriminator_receipt.diagnosis_before_digest != current_diagnosis_digest:
        raise ValueError("discriminator receipt does not bind current diagnosis state")
    if discriminator_receipt.discriminator_id not in portrait.discriminator_ids:
        raise ValueError("discriminator receipt does not name a registered discriminator")

    target = discriminator_receipt.resolved_target_layer
    return SelfEvolutionPlan(
        action=SelfEvolutionAction.PROPOSE_MUTATION,
        target_layers=(target,),
        primary_layer=target,
        reasons=(
            "registered_discriminator_receipt_resolved_mutation_layer",
            f"evidence_epoch:{discriminator_receipt.evidence_epoch_id}",
        ),
        requires_outer_assurance=target in _HIGHER_ORDER,
        incumbent_topology_protected=False,
    )


def validity_gated_pareto_frontier_v3(
    candidates: Iterable[ValidatedCandidateDelta],
) -> tuple[ValidatedCandidateDelta, ...]:
    """Public v3 selection surface: hard validity first, soft Pareto second."""

    return validity_gated_pareto_frontier(candidates)


__all__ = [
    "BlockingValidity",
    "CandidateDelta",
    "CanonicalContextIdentity",
    "ContextTransportWitness",
    "ContextualMutationPolicyV3",
    "DiscriminatorDecisionReceipt",
    "EvaluatorEpochIdentity",
    "FailureEpochV3",
    "MutationFamilyWitness",
    "OuterAssuranceBindingV3",
    "ValidatedCandidateDelta",
    "assess_mutation_governance_v3",
    "distinct_failed_mutation_families_v3",
    "plan_self_evolution_v3",
    "transported_weight_v3",
    "validity_gated_pareto_frontier_v3",
]
