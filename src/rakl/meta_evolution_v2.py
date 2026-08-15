"""Research-only successor controls for recursive RAKL self-evolution.

This module is a challenger to :mod:`rakl.meta_evolution`; it does not replace
or mutate the incumbent controller.  The frozen benchmark lives at
``research/self_rakl_p4_p6_question_saturation_v2/`` and predates this file.

The successor addresses five information-loss defects:

1. a diagnosis verdict must be consumed before mutation routing;
2. higher-order mutation needs a content-bound outer assurance object, not a
   boolean;
3. mutation-operator credit is scoped to the layer/fibre where evidence was
   earned;
4. escalation is driven by distinct failed mutation families, not raw attempt
   counts;
5. blocking validity precedes Pareto selection.

All objects here are proposal/method-control surfaces only.  They grant no
scientific authority and no method-promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from .evolution import EvolutionVerdict
from .mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict
from .meta_evolution import (
    CandidateDelta,
    EvolutionLayer,
    EvolutionPortrait,
    MutationGovernance,
    SelfEvolutionAction,
    SelfEvolutionPlan,
    pareto_frontier,
    plan_self_evolution,
)


@dataclass(frozen=True)
class FailureEpochIdentity:
    """One evidence epoch for a failed challenger family.

    Repeated seeds/reruns of the same mutation family do not automatically
    widen the architecture search space.  ``family_id`` is therefore the
    quantity used for escalation; ``epoch_id`` preserves provenance.
    """

    epoch_id: str
    family_id: str

    def __post_init__(self) -> None:
        if not self.epoch_id.strip() or not self.family_id.strip():
            raise ValueError("failure epoch requires non-empty epoch and family ids")


@dataclass(frozen=True)
class DiagnosisBoundEvolutionPortrait:
    diagnosis_verdict: MechanicDiagnosisVerdict
    causes: tuple[MechanicCause, ...]
    discriminator_ids: tuple[str, ...]
    stagnant: bool
    knowledge_gain_positive: bool = False
    failure_epochs: tuple[FailureEpochIdentity, ...] = ()
    current_topology: str | None = None
    registered_topology_challengers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.causes)) != len(self.causes):
            raise ValueError("mechanic causes must be unique")
        if len(set(self.discriminator_ids)) != len(self.discriminator_ids):
            raise ValueError("discriminator ids must be unique")
        if len({item.epoch_id for item in self.failure_epochs}) != len(self.failure_epochs):
            raise ValueError("failure epoch ids must be unique")
        if (
            self.diagnosis_verdict is MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
            and len(self.causes) != 1
        ):
            raise ValueError("identified diagnosis requires exactly one cause")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def distinct_failed_family_count(self) -> int:
        return len({item.family_id for item in self.failure_epochs})


def _baseline_layers(causes: tuple[MechanicCause, ...]) -> tuple[EvolutionLayer, ...]:
    """Ask the incumbent router which layers these causes imply before escalation."""

    if not causes:
        return ()
    plan = plan_self_evolution(
        EvolutionPortrait(
            causes=causes,
            stagnant=True,
            same_layer_failed_generations=0,
        )
    )
    return plan.target_layers


def plan_self_evolution_v2(portrait: DiagnosisBoundEvolutionPortrait) -> SelfEvolutionPlan:
    """Route self-evolution only after the diagnosis has enough information.

    A registered discriminator has priority over speculative mutation whenever
    the diagnosis state says it is still needed.  Once routing is justified,
    the incumbent layer-escalation logic is reused but receives the count of
    *distinct mutation families* rather than raw failed generations.
    """

    if portrait.diagnosis_verdict in {
        MechanicDiagnosisVerdict.CANNOT_CHECK,
        MechanicDiagnosisVerdict.DISCRIMINATOR_REQUIRED,
    }:
        reason = (
            "registered_discriminator_required_before_mutation"
            if portrait.discriminator_ids
            else "diagnosis_not_identified_register_discriminator_before_mutation"
        )
        return SelfEvolutionPlan(
            action=SelfEvolutionAction.RUN_DISCRIMINATOR,
            target_layers=(),
            primary_layer=None,
            reasons=(reason,),
        )

    if portrait.diagnosis_verdict is MechanicDiagnosisVerdict.NO_GAP:
        return SelfEvolutionPlan(
            action=SelfEvolutionAction.KEEP_INCUMBENT,
            target_layers=(),
            primary_layer=None,
            reasons=("diagnosis_reports_no_mechanic_gap",),
        )

    if MechanicCause.UNKNOWN in portrait.causes or not portrait.causes:
        return SelfEvolutionPlan(
            action=SelfEvolutionAction.RUN_DISCRIMINATOR,
            target_layers=(),
            primary_layer=None,
            reasons=("unknown_or_empty_cause_set_cannot_route_mutation",),
        )

    if portrait.diagnosis_verdict is MechanicDiagnosisVerdict.PARTIALLY_IDENTIFIED:
        layers = _baseline_layers(portrait.causes)
        if len(set(layers)) > 1:
            return SelfEvolutionPlan(
                action=SelfEvolutionAction.RUN_DISCRIMINATOR,
                target_layers=(),
                primary_layer=None,
                reasons=("partial_diagnosis_spans_multiple_mutation_layers",),
            )

    return plan_self_evolution(
        EvolutionPortrait(
            causes=portrait.causes,
            stagnant=portrait.stagnant,
            knowledge_gain_positive=portrait.knowledge_gain_positive,
            same_layer_failed_generations=portrait.distinct_failed_family_count,
            current_topology=portrait.current_topology,
            registered_topology_challengers=portrait.registered_topology_challengers,
        )
    )


@dataclass(frozen=True)
class OuterAssuranceBinding:
    assurance_id: str
    subject_sha: str
    evaluator_id: str
    benchmark_hash: str
    frozen_before_candidate_outcome: bool | None
    candidate_outcomes_used_to_define_evaluator: bool | None

    def __post_init__(self) -> None:
        for value in (
            self.assurance_id,
            self.subject_sha,
            self.evaluator_id,
            self.benchmark_hash,
        ):
            if not value.strip():
                raise ValueError("outer assurance identities cannot be blank")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


_HIGHER_ORDER = {
    EvolutionLayer.EVALUATOR,
    EvolutionLayer.META_POLICY,
    EvolutionLayer.MUTATION_LANGUAGE,
}


def assess_mutation_governance_v2(
    *,
    target_layer: EvolutionLayer,
    target_evaluator_id: str,
    candidate_subject_sha: str,
    outer_assurance: OuterAssuranceBinding | None,
) -> MutationGovernance:
    """Require identity/chronology separation for higher-order self-evolution."""

    if not target_evaluator_id.strip() or not candidate_subject_sha.strip():
        raise ValueError("target evaluator and candidate subject identities are required")

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
            reasons=("higher_order_mutation_missing_outer_assurance_binding",),
        )
    if outer_assurance.subject_sha != candidate_subject_sha:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("outer_assurance_subject_mismatch",),
        )
    if outer_assurance.frozen_before_candidate_outcome is not True:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("outer_assurance_not_frozen_before_candidate_outcome",),
        )
    if outer_assurance.candidate_outcomes_used_to_define_evaluator is not False:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("outer_evaluator_conditioned_on_candidate_outcomes",),
        )
    if outer_assurance.evaluator_id == target_evaluator_id:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("target_evaluator_cannot_be_its_own_outer_assurance",),
        )

    return MutationGovernance(
        proposal_allowed=True,
        eligible_for_auto_promotion=True,
        requires_outer_assurance=True,
        reasons=("identity_bound_preoutcome_outer_assurance_allows_entry_to_protected_gate",),
    )


@dataclass(frozen=True)
class ContextualMutationCredit:
    operator_id: str
    target_layer: EvolutionLayer
    scope_key: str
    weight: float

    def __post_init__(self) -> None:
        if not self.operator_id.strip() or not self.scope_key.strip():
            raise ValueError("contextual mutation credit requires operator and scope identity")
        if self.weight <= 0:
            raise ValueError("contextual mutation weight must be positive")


@dataclass(frozen=True)
class ContextualMutationPolicy:
    entries: tuple[ContextualMutationCredit, ...]

    def __post_init__(self) -> None:
        if not self.entries:
            raise ValueError("contextual mutation policy requires entries")
        keys = [
            (item.operator_id, item.target_layer, item.scope_key)
            for item in self.entries
        ]
        if len(set(keys)) != len(keys):
            raise ValueError("contextual mutation-policy keys must be unique")

    def weight_for(self, *, operator_id: str, target_layer: EvolutionLayer, scope_key: str) -> float:
        for item in self.entries:
            if (
                item.operator_id == operator_id
                and item.target_layer is target_layer
                and item.scope_key == scope_key
            ):
                return item.weight
        raise KeyError((operator_id, target_layer, scope_key))

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _credit_delta(outcome: EvolutionVerdict) -> float:
    return {
        EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE: 0.25,
        EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED: 0.10,
        EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY: 0.05,
        EvolutionVerdict.META_OVERFIT: -0.25,
        EvolutionVerdict.NO_IMPROVEMENT: -0.10,
        EvolutionVerdict.BLOCKED: -0.05,
        EvolutionVerdict.CANNOT_CHECK: 0.0,
    }[outcome]


def update_contextual_mutation_policy(
    policy: ContextualMutationPolicy,
    *,
    operator_id: str,
    target_layer: EvolutionLayer,
    scope_key: str,
    outcome: EvolutionVerdict,
) -> ContextualMutationPolicy:
    """Apply evidence only to the exact scope/layer that earned it."""

    found = False
    updated: list[ContextualMutationCredit] = []
    for item in policy.entries:
        if (
            item.operator_id == operator_id
            and item.target_layer is target_layer
            and item.scope_key == scope_key
        ):
            found = True
            updated.append(
                ContextualMutationCredit(
                    operator_id=item.operator_id,
                    target_layer=item.target_layer,
                    scope_key=item.scope_key,
                    weight=max(0.05, item.weight + _credit_delta(outcome)),
                )
            )
        else:
            updated.append(item)
    if not found:
        raise ValueError("mutation credit may update only a pre-registered contextual key")
    return ContextualMutationPolicy(tuple(updated))


class BlockingValidity(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ValidatedCandidateDelta:
    candidate: CandidateDelta
    blocking_validity: BlockingValidity
    blocking_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.blocking_validity is BlockingValidity.PASS and self.blocking_reasons:
            raise ValueError("PASS candidate cannot carry blocking failure reasons")
        if self.blocking_validity is not BlockingValidity.PASS and not self.blocking_reasons:
            raise ValueError("non-PASS candidate requires blocking reason")


def validity_gated_pareto_frontier(
    candidates: Iterable[ValidatedCandidateDelta],
) -> tuple[ValidatedCandidateDelta, ...]:
    """Apply noncompensatory validity before ordinary soft-QoI dominance."""

    items = tuple(candidates)
    ids = [item.candidate.candidate_id for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("candidate ids must be unique")
    valid = tuple(item for item in items if item.blocking_validity is BlockingValidity.PASS)
    if not valid:
        return ()
    frontier_ids = {
        item.candidate_id
        for item in pareto_frontier(entry.candidate for entry in valid)
    }
    return tuple(
        sorted(
            (entry for entry in valid if entry.candidate.candidate_id in frontier_ids),
            key=lambda entry: entry.candidate.candidate_id,
        )
    )
