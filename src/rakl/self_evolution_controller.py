"""Canonical current orchestration facade for RAKL self-evolution.

Historical ``meta_evolution*`` modules remain importable research/replay surfaces.
The current controller deliberately accepts only the strongest content-addressed
V4/V5 types and delegates all load-bearing semantics to ``meta_evolution_v5``.
It has no scientific-authority or auto-promotion operation.

Frozen contract:
``research/self_rakl_p4_p6_question_saturation_v7/STRICT_SELF_EVOLUTION_ENTRYPOINT_FREEZE.json``.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from .evolution import EvolutionVerdict
from .meta_evolution import EvolutionLayer, MutationGovernance, SelfEvolutionPlan
from .meta_evolution_v2 import ValidatedCandidateDelta
from .meta_evolution_v4 import CanonicalContextManifestV4, ContextTransportWitnessV4
from .meta_evolution_v5 import (
    StrictContextualMutationPolicyV5,
    StrictDiscriminatorDecisionReceiptV5,
    StrictEvaluatorEpochIdentityV5,
    StrictEvolutionPortraitV5,
    StrictOuterAssuranceBindingV5,
    assess_mutation_governance_v5,
    plan_self_evolution_v5,
    transported_weight_v5,
    update_contextual_mutation_policy_v5,
    validity_gated_pareto_frontier_v5,
)


def _require(value: object, typ: type, name: str):
    if not isinstance(value, typ):
        raise TypeError(f"{name} must be {typ.__name__} on the current strict controller")
    return value


@dataclass(frozen=True)
class SelfEvolutionController:
    """Non-sovereign controller for current strict self-evolution operations."""

    version: str = "SELF_EVOLUTION_CONTROLLER_STRICT_V5"

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def auto_promotes_methods(self) -> bool:
        return False

    def plan(
        self,
        portrait: StrictEvolutionPortraitV5,
        *,
        current_diagnosis_digest: str,
        discriminator_receipt: StrictDiscriminatorDecisionReceiptV5 | None = None,
    ) -> SelfEvolutionPlan:
        _require(portrait, StrictEvolutionPortraitV5, "portrait")
        if discriminator_receipt is not None:
            _require(discriminator_receipt, StrictDiscriminatorDecisionReceiptV5, "discriminator_receipt")
        return plan_self_evolution_v5(
            portrait,
            current_diagnosis_digest=current_diagnosis_digest,
            discriminator_receipt=discriminator_receipt,
        )

    def update_credit(
        self,
        policy: StrictContextualMutationPolicyV5,
        *,
        operator_contract_digest: str,
        target_layer: EvolutionLayer,
        context: CanonicalContextManifestV4,
        outcome: EvolutionVerdict,
    ) -> StrictContextualMutationPolicyV5:
        _require(policy, StrictContextualMutationPolicyV5, "policy")
        _require(context, CanonicalContextManifestV4, "context")
        return update_contextual_mutation_policy_v5(
            policy,
            operator_contract_digest=operator_contract_digest,
            target_layer=target_layer,
            context=context,
            outcome=outcome,
        )

    def transported_credit(
        self,
        policy: StrictContextualMutationPolicyV5,
        *,
        operator_contract_digest: str,
        target_layer: EvolutionLayer,
        source_context: CanonicalContextManifestV4,
        destination_context: CanonicalContextManifestV4,
        witness: ContextTransportWitnessV4 | None,
    ) -> float | None:
        _require(policy, StrictContextualMutationPolicyV5, "policy")
        _require(source_context, CanonicalContextManifestV4, "source_context")
        _require(destination_context, CanonicalContextManifestV4, "destination_context")
        if witness is not None:
            _require(witness, ContextTransportWitnessV4, "witness")
        return transported_weight_v5(
            policy,
            operator_contract_digest=operator_contract_digest,
            target_layer=target_layer,
            source_context=source_context,
            destination_context=destination_context,
            witness=witness,
        )

    def assess_governance(
        self,
        *,
        target_layer: EvolutionLayer,
        target_evaluator: StrictEvaluatorEpochIdentityV5,
        candidate_subject_sha: str,
        candidate_benchmark_digest: str,
        outer_assurance: StrictOuterAssuranceBindingV5 | None,
    ) -> MutationGovernance:
        _require(target_evaluator, StrictEvaluatorEpochIdentityV5, "target_evaluator")
        if outer_assurance is not None:
            _require(outer_assurance, StrictOuterAssuranceBindingV5, "outer_assurance")
        return assess_mutation_governance_v5(
            target_layer=target_layer,
            target_evaluator=target_evaluator,
            candidate_subject_sha=candidate_subject_sha,
            candidate_benchmark_digest=candidate_benchmark_digest,
            outer_assurance=outer_assurance,
        )

    def select_frontier(
        self,
        candidates: Iterable[ValidatedCandidateDelta],
    ) -> tuple[ValidatedCandidateDelta, ...]:
        items = tuple(candidates)
        for index, item in enumerate(items):
            _require(item, ValidatedCandidateDelta, f"candidates[{index}]")
        return validity_gated_pareto_frontier_v5(items)


CURRENT_SELF_EVOLUTION_CONTROLLER = SelfEvolutionController()

__all__ = ["CURRENT_SELF_EVOLUTION_CONTROLLER", "SelfEvolutionController"]
