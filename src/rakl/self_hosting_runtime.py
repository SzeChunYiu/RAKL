"""Recursive self-hosting orchestration for RAKL.

This module intentionally owns *coordination*, not authority.  It connects the
existing object-level search controller, mechanic diagnosis, experience/evidence
lineage, governed framework tournament, and protected evolution archive into one
fail-closed loop:

    object search -> operator-basis dead end -> meta failure receipt
      -> typed framework challenger -> fresh tournament
      -> protected assurance archive -> governance promotion -> resume search

No function in this module grants scientific authority or bypasses the existing
protected attestation/governance paths.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Protocol, Tuple

from .epistemic_evolution import (
    EvolutionSurface,
    FrameworkVariantCard,
    TournamentAssessment,
    TournamentDecision,
    TournamentEvidence,
    assess_framework_challenger,
)
from .evolution_archive import (
    EvolutionArchive,
    EvolutionTrialAuthorityBindings,
    RAKLVariant,
    VariantStatus,
    record_evolution_trial,
    register_challenger,
)
from .mechanic_diagnosis import (
    MechanicCause,
    MechanicDiagnosisReceipt,
    MechanicDiagnosisVerdict,
    diagnose_mechanic_signals,
)
from .v3_authority import ProtectedAuthorityContext, canonical_sha256


class _SearchPlanLike(Protocol):
    verdict: object
    reasons: Tuple[str, ...]
    round_index: int
    reopen_fiber_ids: Tuple[str, ...]


class _ObjectRuntimeLike(Protocol):
    search_state: object

    def plan_next_round(self) -> _SearchPlanLike: ...

    def active_residuals(self) -> tuple[object, ...]: ...




_METHOD_OPERATOR_GAP_SURFACES = frozenset(
    {
        EvolutionSurface.PLANNING_SEARCH,
        EvolutionSurface.INTERACTION_SPACE,
        EvolutionSurface.SEARCH_FEEDBACK,
        EvolutionSurface.DIVERSIFICATION,
        EvolutionSurface.QUERY_COMPILATION,
        EvolutionSurface.RETRIEVAL_POLICY,
        EvolutionSurface.RANKING,
        EvolutionSurface.CRAWL_POLICY,
        EvolutionSurface.ANTI_EPISTEMIC_SPAM,
    }
)


def _is_sha256_hexdigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


class SelfHostingDecision(str, Enum):
    OBJECT_SEARCH_READY = "OBJECT_SEARCH_READY"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    CHALLENGER_REGISTERED = "CHALLENGER_REGISTERED"
    CHALLENGER_REJECTED = "CHALLENGER_REJECTED"
    ASSURANCE_PENDING = "ASSURANCE_PENDING"
    CHALLENGER_ASSURED = "CHALLENGER_ASSURED"
    GOVERNANCE_PROMOTION_REQUIRED = "GOVERNANCE_PROMOTION_REQUIRED"
    RESUME_WITH_INCUMBENT = "RESUME_WITH_INCUMBENT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MetaFailureReceipt:
    receipt_id: str
    receipt_hash: str
    search_id: str
    parent_variant_id: str
    residual_ids: Tuple[str, ...]
    reopen_fiber_ids: Tuple[str, ...]
    plan_reasons: Tuple[str, ...]
    triggering_episode_ids: Tuple[str, ...]
    diagnosis: MechanicDiagnosisReceipt

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.receipt_hash or not self.search_id:
            raise ValueError("meta failure receipt requires identity")
        if not self.parent_variant_id:
            raise ValueError("meta failure receipt requires parent variant identity")
        if not self.residual_ids:
            raise ValueError("meta failure receipt requires at least one residual")
        if not self.plan_reasons:
            raise ValueError("meta failure receipt requires object-search reasons")
        if self.diagnosis.verdict is not MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED:
            raise ValueError("meta failure receipt requires an identified mechanic gap")
        if self.diagnosis.candidate_causes != (MechanicCause.METHOD_OPERATOR_GAP,):
            raise ValueError("self-hosting escalation is restricted to METHOD_OPERATOR_GAP")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class EscalationAssessment:
    decision: SelfHostingDecision
    reasons: Tuple[str, ...]
    object_plan: _SearchPlanLike
    receipt: MetaFailureReceipt | None = None


@dataclass(frozen=True)
class MechanicMutationSpec:
    """Frozen typed declaration for one framework-level mutation.

    The actual implementation may be code/config/data, but the mutation is not
    admissible until exact identity, parentage, changed surface, falsifiers,
    protected invariants, resource delta and fresh evaluation cases are frozen.
    """

    mutation_id: str
    variant_id: str
    parent_variant_id: str
    method_hash: str
    surface: EvolutionSurface
    component_kind: str
    changed_component_ids: Tuple[str, ...]
    difference_witness_hash: str
    hypothesized_gain_qois: Tuple[str, ...]
    specific_falsifiers: Tuple[str, ...]
    protected_invariants: Tuple[str, ...]
    motivating_case_ids: Tuple[str, ...]
    development_case_ids: Tuple[str, ...]
    fresh_assurance_case_ids: Tuple[str, ...]
    capability_tags: Tuple[str, ...]
    resource_profile: Tuple[Tuple[str, float], ...]
    resource_delta: Tuple[Tuple[str, float], ...]
    external_inspirations: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()
    frozen_before_fresh_assurance: bool | None = True

    def __post_init__(self) -> None:
        for name in (
            "mutation_id",
            "variant_id",
            "parent_variant_id",
            "method_hash",
            "component_kind",
            "difference_witness_hash",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"mechanic mutation requires {name}")
        if self.variant_id == self.parent_variant_id:
            raise ValueError("mechanic mutation child must differ from parent")
        if not _is_sha256_hexdigest(self.method_hash):
            raise ValueError("mechanic mutation method_hash must be a lowercase sha256 hex digest")
        if not _is_sha256_hexdigest(self.difference_witness_hash):
            raise ValueError("mechanic mutation difference_witness_hash must be a lowercase sha256 hex digest")
        if self.surface not in _METHOD_OPERATOR_GAP_SURFACES:
            raise ValueError("METHOD_OPERATOR_GAP mutation must target a registered search-evolution surface")
        if not self.changed_component_ids:
            raise ValueError("mechanic mutation requires changed component ids")
        if len(set(self.changed_component_ids)) != len(self.changed_component_ids):
            raise ValueError("changed component ids must be unique")
        if not self.hypothesized_gain_qois:
            raise ValueError("mechanic mutation requires hypothesized gain QoIs")
        if not self.specific_falsifiers:
            raise ValueError("mechanic mutation requires predeclared falsifiers")
        if not self.protected_invariants:
            raise ValueError("mechanic mutation requires protected invariants")
        if not self.development_case_ids or not self.fresh_assurance_case_ids:
            raise ValueError("mechanic mutation requires development and fresh assurance cases")
        if len(set(self.development_case_ids)) != len(self.development_case_ids):
            raise ValueError("development case ids must be unique")
        if len(set(self.fresh_assurance_case_ids)) != len(self.fresh_assurance_case_ids):
            raise ValueError("fresh assurance case ids must be unique")
        exposed = set(self.motivating_case_ids) | set(self.development_case_ids)
        if exposed & set(self.fresh_assurance_case_ids):
            raise ValueError("fresh assurance cases must be disjoint from exposed cases")
        if any(value < 0 for _, value in self.resource_profile):
            raise ValueError("resource profile values cannot be negative")


@dataclass(frozen=True)
class RegisteredMutation:
    spec: MechanicMutationSpec
    root_cause_receipt: MetaFailureReceipt
    variant_card: FrameworkVariantCard
    archive: EvolutionArchive


@dataclass(frozen=True)
class MutationEvaluation:
    decision: SelfHostingDecision
    reasons: Tuple[str, ...]
    tournament: TournamentAssessment
    archive: EvolutionArchive
    evolution_verdict: str | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def promotes_incumbent(self) -> bool:
        return False


def _enum_value(value: object) -> str:
    candidate = getattr(value, "value", value)
    return str(candidate)


def _residual_id(item: object) -> str:
    value = getattr(item, "residual_id", None)
    if not value:
        raise ValueError("active residual is missing residual_id")
    return str(value)


def _search_id(runtime: _ObjectRuntimeLike) -> str:
    value = getattr(runtime.search_state, "search_id", None)
    if not value:
        raise ValueError("object runtime search_state is missing search_id")
    return str(value)


def inspect_for_self_hosting(
    runtime: _ObjectRuntimeLike,
    *,
    parent_variant_id: str,
    triggering_episode_ids: Tuple[str, ...] = (),
) -> EscalationAssessment:
    """Inspect one object-search planning boundary and fail closed on ambiguity.

    Escalation is intentionally narrow.  Resource exhaustion, missing residuals,
    ordinary candidate failure, or arbitrary ``CANNOT_CHECK`` states do *not*
    authorize framework mutation.  The current controller must specifically
    report operator-basis exhaustion.
    """

    if not parent_variant_id:
        raise ValueError("parent_variant_id is required")

    plan = runtime.plan_next_round()
    verdict = _enum_value(plan.verdict)
    if verdict in {"PLAN_READY", "GOAL_ACHIEVED"}:
        return EscalationAssessment(
            SelfHostingDecision.OBJECT_SEARCH_READY,
            ("object_search_has_a_registered_next_step",),
            plan,
        )

    operator_basis_exhausted = (
        verdict == "CANNOT_CHECK"
        and "all_registered_residual_operator_routes_exhausted_under_current_operator_basis"
        in tuple(plan.reasons)
    )
    if not operator_basis_exhausted:
        return EscalationAssessment(
            SelfHostingDecision.CANNOT_CHECK,
            (
                "self_hosting_escalation_not_licensed_by_current_object_state",
                *tuple(plan.reasons),
            ),
            plan,
        )

    residual_ids = tuple(dict.fromkeys(_residual_id(item) for item in runtime.active_residuals()))
    if not residual_ids:
        return EscalationAssessment(
            SelfHostingDecision.CANNOT_CHECK,
            ("operator_basis_exhausted_but_no_active_residual_identity_is_available",),
            plan,
        )

    search_id = _search_id(runtime)
    seed_payload = {
        "search_id": search_id,
        "parent_variant_id": parent_variant_id,
        "residual_ids": list(residual_ids),
        "reopen_fiber_ids": list(getattr(plan, "reopen_fiber_ids", ())),
        "plan_reasons": list(plan.reasons),
        "triggering_episode_ids": list(triggering_episode_ids),
    }
    seed_hash = canonical_sha256(seed_payload)
    diagnosis = diagnose_mechanic_signals(
        diagnosis_id=f"self-host:{search_id}:{seed_hash[:16]}",
        problem_state_id=search_id,
        atom_id=residual_ids[0],
        fibre_snapshot_hash=canonical_sha256(
            {"reopen_fiber_ids": list(getattr(plan, "reopen_fiber_ids", ())) }
        ),
        residual_ids=residual_ids,
        signals=("target_unreachable_current_operator_basis",),
    )
    receipt_payload = {
        **seed_payload,
        "diagnosis_id": diagnosis.diagnosis_id,
        "diagnosis_verdict": diagnosis.verdict.value,
        "candidate_causes": [cause.value for cause in diagnosis.candidate_causes],
    }
    receipt_hash = canonical_sha256(receipt_payload)
    receipt = MetaFailureReceipt(
        receipt_id=f"meta-failure:{search_id}:{receipt_hash[:16]}",
        receipt_hash=receipt_hash,
        search_id=search_id,
        parent_variant_id=parent_variant_id,
        residual_ids=residual_ids,
        reopen_fiber_ids=tuple(getattr(plan, "reopen_fiber_ids", ())),
        plan_reasons=tuple(plan.reasons),
        triggering_episode_ids=tuple(dict.fromkeys(triggering_episode_ids)),
        diagnosis=diagnosis,
    )
    return EscalationAssessment(
        SelfHostingDecision.ESCALATION_REQUIRED,
        (
            "object_operator_basis_exhausted",
            "mechanic_diagnosis_identified_METHOD_OPERATOR_GAP",
            "framework_mutation_may_be_proposed_but_has_no_authority_yet",
        ),
        plan,
        receipt,
    )


def register_mechanic_mutation(
    archive: EvolutionArchive,
    receipt: MetaFailureReceipt,
    spec: MechanicMutationSpec,
) -> RegisteredMutation:
    """Bind a typed challenger to the exact meta-failure that motivated it."""

    if archive.incumbent_id != receipt.parent_variant_id:
        raise ValueError("meta-failure receipt parent is stale relative to current incumbent")
    if spec.parent_variant_id != archive.incumbent_id:
        raise ValueError("mechanic mutation parent is stale relative to current incumbent")
    if spec.parent_variant_id != receipt.parent_variant_id:
        raise ValueError("mechanic mutation parent does not match root-cause receipt")

    card = FrameworkVariantCard(
        variant_id=spec.variant_id,
        parent_version=spec.parent_variant_id,
        surfaces_changed=(spec.surface,),
        triggering_evidence_ids=tuple(
            dict.fromkeys(receipt.triggering_episode_ids + (receipt.receipt_id,))
        ),
        root_cause_receipt_ids=(receipt.receipt_id,),
        external_inspirations=spec.external_inspirations,
        difference_witness_hash=spec.difference_witness_hash,
        hypothesized_gain_qois=spec.hypothesized_gain_qois,
        specific_falsifiers=spec.specific_falsifiers,
        protected_invariants=spec.protected_invariants,
        motivating_case_ids=spec.motivating_case_ids,
        development_case_ids=spec.development_case_ids,
        fresh_assurance_case_ids=spec.fresh_assurance_case_ids,
        rollback_variant_id=spec.parent_variant_id,
        failure_driven_update_ids=(receipt.receipt_id,),
        resource_delta=spec.resource_delta,
        frozen_before_fresh_assurance=spec.frozen_before_fresh_assurance,
    )
    variant = RAKLVariant(
        variant_id=spec.variant_id,
        method_hash=spec.method_hash,
        parent_ids=(spec.parent_variant_id,),
        capability_tags=tuple(dict.fromkeys(spec.capability_tags + (spec.component_kind,))),
        resource_profile=spec.resource_profile,
        created_by_episode_ids=receipt.triggering_episode_ids,
        status=VariantStatus.CHALLENGER,
        notes=tuple(
            dict.fromkeys(
                spec.notes
                + (
                    f"self_hosting_mutation_id:{spec.mutation_id}",
                    f"root_cause_receipt:{receipt.receipt_id}",
                    f"root_cause_hash:{receipt.receipt_hash}",
                )
            )
        ),
    )
    next_archive = register_challenger(archive, variant)
    return RegisteredMutation(spec, receipt, card, next_archive)


def _mark_rejected(archive: EvolutionArchive, variant_id: str, reasons: Tuple[str, ...] = ()) -> EvolutionArchive:
    if variant_id == archive.incumbent_id:
        raise ValueError("cannot reject the current incumbent through challenger evaluation")
    found = False
    variants = []
    for variant in archive.variants:
        if variant.variant_id == variant_id:
            found = True
            variants.append(
                replace(
                    variant,
                    status=VariantStatus.REJECTED,
                    notes=tuple(dict.fromkeys(variant.notes + tuple(f"tournament_rejection:{reason}" for reason in reasons))),
                )
            )
        else:
            variants.append(variant)
    if not found:
        raise ValueError("challenger variant is not registered")
    return EvolutionArchive(tuple(variants), archive.edges, archive.incumbent_id)


def evaluate_mechanic_mutation(
    registered: RegisteredMutation,
    evidence: TournamentEvidence,
    *,
    trial_id: str,
    authority_context: ProtectedAuthorityContext | None = None,
    assurance_attestation_id: str | None = None,
    authority_bindings: EvolutionTrialAuthorityBindings | None = None,
) -> MutationEvaluation:
    """Run the existing framework tournament, then the protected archive gate.

    Tournament eligibility is necessary but insufficient.  Only if it passes do
    we submit the exact trial to :func:`record_evolution_trial`; that function
    remains the sole assurance-status writer and can still return CANNOT_CHECK
    when protected attestations/bindings are absent or invalid.
    """

    trial = evidence.trial
    if trial.parent_version != registered.spec.parent_variant_id:
        raise ValueError("trial parent does not match registered mutation")
    if trial.child_version != registered.spec.variant_id:
        raise ValueError("trial child does not match registered mutation")

    tournament = assess_framework_challenger(registered.variant_card, evidence)
    if not tournament.promotion_eligible:
        rejected = _mark_rejected(registered.archive, registered.spec.variant_id, tournament.reasons)
        return MutationEvaluation(
            SelfHostingDecision.CHALLENGER_REJECTED,
            ("framework_tournament_did_not_grant_promotion_eligibility",) + tournament.reasons,
            tournament,
            rejected,
            tournament.underlying_evolution_verdict.value
            if tournament.underlying_evolution_verdict is not None
            else None,
        )

    archive, assessment = record_evolution_trial(
        registered.archive,
        trial_id=trial_id,
        child_variant_id=registered.spec.variant_id,
        trial=trial,
        authority_context=authority_context,
        assurance_attestation_id=assurance_attestation_id,
        authority_bindings=authority_bindings,
    )
    child = next(item for item in archive.variants if item.variant_id == registered.spec.variant_id)
    if child.status is VariantStatus.ASSURED:
        decision = SelfHostingDecision.GOVERNANCE_PROMOTION_REQUIRED
        reasons = (
            "challenger_passed_framework_tournament_and_protected_assurance",
            "protected_governance_promotion_is_still_required_before_runtime_switch",
        )
    else:
        decision = SelfHostingDecision.ASSURANCE_PENDING
        reasons = (
            "framework_tournament_is_promotion_eligible_but_protected_assurance_is_not_resolved",
            *assessment.reasons,
        )
    return MutationEvaluation(
        decision,
        reasons,
        tournament,
        archive,
        assessment.verdict.value,
    )


def assess_resume_readiness(
    archive: EvolutionArchive,
    *,
    expected_variant_id: str,
) -> tuple[SelfHostingDecision, Tuple[str, ...]]:
    """Allow object-level resumption only after governance changed the incumbent."""

    if not expected_variant_id:
        raise ValueError("expected_variant_id is required")
    target = next((item for item in archive.variants if item.variant_id == expected_variant_id), None)
    if target is None:
        return SelfHostingDecision.CANNOT_CHECK, ("expected_variant_is_not_registered",)
    if archive.incumbent_id != expected_variant_id or target.status is not VariantStatus.INCUMBENT:
        return (
            SelfHostingDecision.GOVERNANCE_PROMOTION_REQUIRED,
            ("challenger_is_not_the_governed_incumbent",),
        )
    return (
        SelfHostingDecision.RESUME_WITH_INCUMBENT,
        ("governed_incumbent_identity_matches_expected_self_hosted_variant",),
    )


__all__ = [
    "EscalationAssessment",
    "MechanicMutationSpec",
    "MetaFailureReceipt",
    "MutationEvaluation",
    "RegisteredMutation",
    "SelfHostingDecision",
    "assess_resume_readiness",
    "evaluate_mechanic_mutation",
    "inspect_for_self_hosting",
    "register_mechanic_mutation",
]
