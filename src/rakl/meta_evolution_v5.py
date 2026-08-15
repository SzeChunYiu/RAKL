"""Closure-eligible strict facade for recursive RAKL self-evolution.

Historical v1-v4 modules remain available for reproducibility and their frozen
benchmarks.  Current local closure uses this facade, which accepts only:

* v4 content-manifest mutation families and contexts;
* SHA-256 discriminator/evidence/context/operator identities;
* exact Git subject identities;
* SHA-256 evaluator/benchmark/environment/metric/dependency identities; and
* blocking validity before soft Pareto comparison.

Passing this facade only permits a challenger to enter the already-existing
protected method gate.  It grants no scientific or method-promotion authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable

from .evolution import EvolutionVerdict
from .mechanic_diagnosis import MechanicCause, MechanicDiagnosisVerdict
from .meta_evolution import EvolutionLayer, MutationGovernance, SelfEvolutionPlan
from .meta_evolution_v2 import DiagnosisBoundEvolutionPortrait, FailureEpochIdentity, ValidatedCandidateDelta
from .meta_evolution_v3 import DiscriminatorDecisionReceipt, EvaluatorEpochIdentity, OuterAssuranceBindingV3, assess_mutation_governance_v3, plan_self_evolution_v3, validity_gated_pareto_frontier_v3
from .meta_evolution_v4 import CanonicalContextManifestV4, ContextTransportWitnessV4, FailureEpochV4

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _sha(value: str, field: str) -> str:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 content digest")
    return value


def _git_sha(value: str, field: str) -> str:
    if not _GIT_OBJECT.fullmatch(value):
        raise ValueError(f"{field} must be an exact lowercase Git object hash")
    return value


@dataclass(frozen=True)
class StrictEvolutionPortraitV5:
    diagnosis_verdict: MechanicDiagnosisVerdict
    causes: tuple[MechanicCause, ...]
    discriminator_contract_digests: tuple[str, ...]
    stagnant: bool
    knowledge_gain_positive: bool = False
    failure_epochs: tuple[FailureEpochV4, ...] = ()
    current_topology_digest: str | None = None
    registered_topology_challenger_digests: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.causes)) != len(self.causes):
            raise ValueError("mechanic causes must be unique")
        for digest in self.discriminator_contract_digests:
            _sha(digest, "discriminator_contract_digest")
        if len(set(self.discriminator_contract_digests)) != len(self.discriminator_contract_digests):
            raise ValueError("discriminator contract digests must be unique")
        if self.current_topology_digest is not None:
            _sha(self.current_topology_digest, "current_topology_digest")
        for digest in self.registered_topology_challenger_digests:
            _sha(digest, "registered_topology_challenger_digest")
        if len(set(self.registered_topology_challenger_digests)) != len(self.registered_topology_challenger_digests):
            raise ValueError("topology challenger digests must be unique")
        if len({epoch.evidence_epoch_digest for epoch in self.failure_epochs}) != len(self.failure_epochs):
            raise ValueError("failure evidence epochs must be unique")

    def to_v2(self) -> DiagnosisBoundEvolutionPortrait:
        return DiagnosisBoundEvolutionPortrait(
            diagnosis_verdict=self.diagnosis_verdict,
            causes=self.causes,
            discriminator_ids=self.discriminator_contract_digests,
            stagnant=self.stagnant,
            knowledge_gain_positive=self.knowledge_gain_positive,
            failure_epochs=tuple(
                FailureEpochIdentity(
                    epoch_id=epoch.evidence_epoch_digest,
                    family_id=epoch.family.digest,
                )
                for epoch in self.failure_epochs
            ),
            current_topology=self.current_topology_digest,
            registered_topology_challengers=self.registered_topology_challenger_digests,
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class StrictDiscriminatorDecisionReceiptV5:
    receipt_digest: str
    diagnosis_before_digest: str
    diagnosis_after_digest: str
    discriminator_contract_digest: str
    evidence_epoch_digest: str
    total_cost: float
    resolved_target_layer: EvolutionLayer

    def __post_init__(self) -> None:
        for field in (
            "receipt_digest",
            "diagnosis_before_digest",
            "diagnosis_after_digest",
            "discriminator_contract_digest",
            "evidence_epoch_digest",
        ):
            _sha(getattr(self, field), field)
        if self.diagnosis_before_digest == self.diagnosis_after_digest:
            raise ValueError("decision-bearing discriminator must refine diagnosis state")
        if self.total_cost < 0:
            raise ValueError("discriminator cost cannot be negative")

    def to_v3(self) -> DiscriminatorDecisionReceipt:
        return DiscriminatorDecisionReceipt(
            receipt_id=self.receipt_digest,
            diagnosis_before_digest=self.diagnosis_before_digest,
            diagnosis_after_digest=self.diagnosis_after_digest,
            discriminator_id=self.discriminator_contract_digest,
            evidence_epoch_id=self.evidence_epoch_digest,
            total_cost=self.total_cost,
            resolved_target_layer=self.resolved_target_layer,
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def plan_self_evolution_v5(
    portrait: StrictEvolutionPortraitV5,
    *,
    current_diagnosis_digest: str,
    discriminator_receipt: StrictDiscriminatorDecisionReceiptV5 | None = None,
) -> SelfEvolutionPlan:
    _sha(current_diagnosis_digest, "current_diagnosis_digest")
    return plan_self_evolution_v3(
        portrait.to_v2(),
        current_diagnosis_digest=current_diagnosis_digest,
        discriminator_receipt=(
            discriminator_receipt.to_v3() if discriminator_receipt is not None else None
        ),
    )


@dataclass(frozen=True)
class StrictContextualMutationCreditV5:
    operator_contract_digest: str
    target_layer: EvolutionLayer
    context_digest: str
    weight: float

    def __post_init__(self) -> None:
        _sha(self.operator_contract_digest, "operator_contract_digest")
        _sha(self.context_digest, "context_digest")
        if self.weight <= 0:
            raise ValueError("contextual mutation weight must be positive")


@dataclass(frozen=True)
class StrictContextualMutationPolicyV5:
    entries: tuple[StrictContextualMutationCreditV5, ...]

    def __post_init__(self) -> None:
        if not self.entries:
            raise ValueError("strict contextual mutation policy requires entries")
        keys = [
            (entry.operator_contract_digest, entry.target_layer, entry.context_digest)
            for entry in self.entries
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("strict contextual mutation-policy keys must be unique")

    def weight_for(
        self,
        *,
        operator_contract_digest: str,
        target_layer: EvolutionLayer,
        context: CanonicalContextManifestV4,
    ) -> float:
        _sha(operator_contract_digest, "operator_contract_digest")
        for entry in self.entries:
            if (
                entry.operator_contract_digest == operator_contract_digest
                and entry.target_layer is target_layer
                and entry.context_digest == context.digest
            ):
                return entry.weight
        raise KeyError((operator_contract_digest, target_layer, context.digest))

    @property
    def grants_scientific_authority(self) -> bool:
        return False


_CREDIT_DELTA = {
    EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE: 0.25,
    EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED: 0.10,
    EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY: 0.05,
    EvolutionVerdict.META_OVERFIT: -0.25,
    EvolutionVerdict.NO_IMPROVEMENT: -0.10,
    EvolutionVerdict.BLOCKED: -0.05,
    EvolutionVerdict.CANNOT_CHECK: 0.0,
}


def update_contextual_mutation_policy_v5(
    policy: StrictContextualMutationPolicyV5,
    *,
    operator_contract_digest: str,
    target_layer: EvolutionLayer,
    context: CanonicalContextManifestV4,
    outcome: EvolutionVerdict,
) -> StrictContextualMutationPolicyV5:
    _sha(operator_contract_digest, "operator_contract_digest")
    found = False
    updated: list[StrictContextualMutationCreditV5] = []
    for entry in policy.entries:
        if (
            entry.operator_contract_digest == operator_contract_digest
            and entry.target_layer is target_layer
            and entry.context_digest == context.digest
        ):
            found = True
            updated.append(
                StrictContextualMutationCreditV5(
                    operator_contract_digest=entry.operator_contract_digest,
                    target_layer=entry.target_layer,
                    context_digest=entry.context_digest,
                    weight=max(0.05, entry.weight + _CREDIT_DELTA[outcome]),
                )
            )
        else:
            updated.append(entry)
    if not found:
        raise KeyError((operator_contract_digest, target_layer, context.digest))
    return StrictContextualMutationPolicyV5(tuple(updated))


def transported_weight_v5(
    policy: StrictContextualMutationPolicyV5,
    *,
    operator_contract_digest: str,
    target_layer: EvolutionLayer,
    source_context: CanonicalContextManifestV4,
    destination_context: CanonicalContextManifestV4,
    witness: ContextTransportWitnessV4 | None,
) -> float | None:
    try:
        source_weight = policy.weight_for(
            operator_contract_digest=operator_contract_digest,
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
        witness.operator_contract_digest != operator_contract_digest
        or witness.target_layer is not target_layer
        or witness.source_context_digest != source_context.digest
        or witness.destination_context_digest != destination_context.digest
    ):
        return None
    return source_weight


@dataclass(frozen=True)
class StrictEvaluatorEpochIdentityV5:
    evaluator_source_digest: str
    dependency_digest: str
    metric_semantics_digest: str
    benchmark_digest: str
    environment_digest: str
    cutoff_manifest_digest: str
    display_label: str = ""

    def __post_init__(self) -> None:
        for field in (
            "evaluator_source_digest",
            "dependency_digest",
            "metric_semantics_digest",
            "benchmark_digest",
            "environment_digest",
            "cutoff_manifest_digest",
        ):
            _sha(getattr(self, field), field)

    def to_v3(self) -> EvaluatorEpochIdentity:
        return EvaluatorEpochIdentity(
            display_id=self.display_label or self.epoch_digest,
            evaluator_source_digest=self.evaluator_source_digest,
            dependency_digest=self.dependency_digest,
            metric_semantics_digest=self.metric_semantics_digest,
            benchmark_digest=self.benchmark_digest,
            environment_digest=self.environment_digest,
            cutoff_id=self.cutoff_manifest_digest,
        )

    @property
    def epoch_digest(self) -> str:
        return self.to_v3().epoch_digest if self.display_label else EvaluatorEpochIdentity(
            display_id="strict-evaluator",
            evaluator_source_digest=self.evaluator_source_digest,
            dependency_digest=self.dependency_digest,
            metric_semantics_digest=self.metric_semantics_digest,
            benchmark_digest=self.benchmark_digest,
            environment_digest=self.environment_digest,
            cutoff_id=self.cutoff_manifest_digest,
        ).epoch_digest

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class StrictOuterAssuranceBindingV5:
    assurance_digest: str
    subject_git_sha: str
    outer_evaluator: StrictEvaluatorEpochIdentityV5
    frozen_before_candidate_outcome: bool | None
    candidate_outcomes_used_to_define_outer_evaluator: bool | None

    def __post_init__(self) -> None:
        _sha(self.assurance_digest, "assurance_digest")
        _git_sha(self.subject_git_sha, "subject_git_sha")

    def to_v3(self) -> OuterAssuranceBindingV3:
        return OuterAssuranceBindingV3(
            assurance_id=self.assurance_digest,
            subject_sha=self.subject_git_sha,
            outer_evaluator=self.outer_evaluator.to_v3(),
            frozen_before_candidate_outcome=self.frozen_before_candidate_outcome,
            candidate_outcomes_used_to_define_outer_evaluator=self.candidate_outcomes_used_to_define_outer_evaluator,
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_mutation_governance_v5(
    *,
    target_layer: EvolutionLayer,
    target_evaluator: StrictEvaluatorEpochIdentityV5,
    candidate_subject_sha: str,
    candidate_benchmark_digest: str,
    outer_assurance: StrictOuterAssuranceBindingV5 | None,
) -> MutationGovernance:
    _git_sha(candidate_subject_sha, "candidate_subject_sha")
    _sha(candidate_benchmark_digest, "candidate_benchmark_digest")
    if target_evaluator.benchmark_digest != candidate_benchmark_digest:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=target_layer in {
                EvolutionLayer.EVALUATOR,
                EvolutionLayer.META_POLICY,
                EvolutionLayer.MUTATION_LANGUAGE,
                EvolutionLayer.CONSTITUTION,
            },
            reasons=("target_evaluator_benchmark_mismatch",),
        )
    return assess_mutation_governance_v3(
        target_layer=target_layer,
        target_evaluator=target_evaluator.to_v3(),
        candidate_subject_sha=candidate_subject_sha,
        candidate_benchmark_digest=candidate_benchmark_digest,
        outer_assurance=outer_assurance.to_v3() if outer_assurance is not None else None,
    )


def validity_gated_pareto_frontier_v5(
    candidates: Iterable[ValidatedCandidateDelta],
) -> tuple[ValidatedCandidateDelta, ...]:
    return validity_gated_pareto_frontier_v3(candidates)


__all__ = [
    "StrictContextualMutationCreditV5",
    "StrictContextualMutationPolicyV5",
    "StrictDiscriminatorDecisionReceiptV5",
    "StrictEvaluatorEpochIdentityV5",
    "StrictEvolutionPortraitV5",
    "StrictOuterAssuranceBindingV5",
    "assess_mutation_governance_v5",
    "plan_self_evolution_v5",
    "transported_weight_v5",
    "update_contextual_mutation_policy_v5",
    "validity_gated_pareto_frontier_v5",
]
