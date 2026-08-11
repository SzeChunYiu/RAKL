from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Tuple

from .evolution import EvolutionAssessment, EvolutionTrial, EvolutionVerdict, SelfEvolutionAssessor


class VariantStatus(str, Enum):
    INCUMBENT = "INCUMBENT"
    CHALLENGER = "CHALLENGER"
    ASSURED = "ASSURED"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class RAKLVariant:
    variant_id: str
    method_hash: str
    parent_ids: Tuple[str, ...]
    capability_tags: Tuple[str, ...]
    resource_profile: Tuple[Tuple[str, float], ...]
    created_by_episode_ids: Tuple[str, ...]
    status: VariantStatus
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.variant_id or not self.method_hash:
            raise ValueError("RAKL variant requires variant_id and method_hash")
        names = [name for name, _ in self.resource_profile]
        if len(set(names)) != len(names):
            raise ValueError("resource profile keys must be unique")
        if any(value < 0 for _, value in self.resource_profile):
            raise ValueError("resource profile values cannot be negative")


@dataclass(frozen=True)
class EvolutionEdge:
    trial_id: str
    parent_id: str
    child_id: str
    verdict: EvolutionVerdict
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class EvolutionArchive:
    variants: Tuple[RAKLVariant, ...]
    edges: Tuple[EvolutionEdge, ...] = ()
    incumbent_id: str = ""


@dataclass(frozen=True)
class VariantSelection:
    variant_id: str
    matched_capability_tags: Tuple[str, ...]
    resource_cost: float
    status: VariantStatus


def initialize_evolution_archive(incumbent: RAKLVariant) -> EvolutionArchive:
    if incumbent.status is not VariantStatus.INCUMBENT:
        incumbent = replace(incumbent, status=VariantStatus.INCUMBENT)
    return EvolutionArchive((incumbent,), (), incumbent.variant_id)


def register_challenger(archive: EvolutionArchive, challenger: RAKLVariant) -> EvolutionArchive:
    if any(variant.variant_id == challenger.variant_id for variant in archive.variants):
        raise ValueError(f"duplicate RAKL variant id: {challenger.variant_id}")
    known = {variant.variant_id for variant in archive.variants}
    if not challenger.parent_ids or not set(challenger.parent_ids).issubset(known):
        raise ValueError("challenger must name existing parent variant(s)")
    return EvolutionArchive(
        archive.variants + (replace(challenger, status=VariantStatus.CHALLENGER),),
        archive.edges,
        archive.incumbent_id,
    )


def record_evolution_trial(
    archive: EvolutionArchive,
    *,
    trial_id: str,
    child_variant_id: str,
    trial: EvolutionTrial,
) -> tuple[EvolutionArchive, EvolutionAssessment]:
    """Record assurance evidence without automatically changing the incumbent."""

    if not trial_id:
        raise ValueError("trial_id is required")
    by_id = {variant.variant_id: variant for variant in archive.variants}
    child = by_id.get(child_variant_id)
    if child is None:
        raise ValueError("child variant is not registered")
    if trial.child_version != child_variant_id:
        raise ValueError("evolution trial child_version does not match registered variant")
    if trial.parent_version not in child.parent_ids:
        raise ValueError("evolution trial parent_version is not a registered parent of child")
    if any(edge.trial_id == trial_id for edge in archive.edges):
        raise ValueError(f"duplicate evolution trial id: {trial_id}")

    assessment = SelfEvolutionAssessor.assess(trial)
    if assessment.verdict is EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE:
        next_status = VariantStatus.ASSURED
    elif assessment.verdict in {EvolutionVerdict.META_OVERFIT, EvolutionVerdict.NO_IMPROVEMENT, EvolutionVerdict.BLOCKED}:
        next_status = VariantStatus.REJECTED
    else:
        next_status = VariantStatus.CHALLENGER

    updated_variants = tuple(
        replace(variant, status=next_status) if variant.variant_id == child_variant_id else variant
        for variant in archive.variants
    )
    edge = EvolutionEdge(
        trial_id=trial_id,
        parent_id=trial.parent_version,
        child_id=child_variant_id,
        verdict=assessment.verdict,
        reasons=assessment.reasons,
    )
    return EvolutionArchive(updated_variants, archive.edges + (edge,), archive.incumbent_id), assessment


def promote_incumbent(
    archive: EvolutionArchive,
    variant_id: str,
    *,
    governance_approved: bool,
) -> EvolutionArchive:
    """Promote an assured branch only after an explicit governance decision."""

    if not governance_approved:
        raise ValueError("explicit governance approval is required for incumbent promotion")
    by_id = {variant.variant_id: variant for variant in archive.variants}
    target = by_id.get(variant_id)
    if target is None:
        raise ValueError("variant does not exist")
    if target.status is not VariantStatus.ASSURED:
        raise ValueError("only an assured variant can become incumbent")
    updated: list[RAKLVariant] = []
    for variant in archive.variants:
        if variant.variant_id == variant_id:
            updated.append(replace(variant, status=VariantStatus.INCUMBENT))
        elif variant.variant_id == archive.incumbent_id and variant.status is VariantStatus.INCUMBENT:
            # Preserve the old branch as an assured rollback target rather than
            # deleting it or pretending it never existed.
            updated.append(replace(variant, status=VariantStatus.ASSURED))
        else:
            updated.append(variant)
    return EvolutionArchive(tuple(updated), archive.edges, variant_id)


def rank_variants_for_task(
    archive: EvolutionArchive,
    *,
    required_capability_tags: Tuple[str, ...] = (),
    allowed_statuses: Tuple[VariantStatus, ...] = (VariantStatus.INCUMBENT, VariantStatus.ASSURED),
) -> Tuple[VariantSelection, ...]:
    required = set(required_capability_tags)
    selections: list[VariantSelection] = []
    for variant in archive.variants:
        if variant.status not in allowed_statuses:
            continue
        matched = tuple(sorted(required & set(variant.capability_tags)))
        if required and set(matched) != required:
            continue
        cost = sum(value for _, value in variant.resource_profile)
        selections.append(VariantSelection(variant.variant_id, matched, cost, variant.status))
    selections.sort(
        key=lambda item: (
            item.status is not VariantStatus.INCUMBENT,
            item.resource_cost,
            item.variant_id,
        )
    )
    return tuple(selections)


def evolution_portrait(archive: EvolutionArchive) -> dict[str, object]:
    status_counts: dict[str, int] = {}
    for variant in archive.variants:
        status_counts[variant.status.value] = status_counts.get(variant.status.value, 0) + 1
    return {
        "variant_count": len(archive.variants),
        "edge_count": len(archive.edges),
        "incumbent_id": archive.incumbent_id,
        "status_counts": dict(sorted(status_counts.items())),
        "assured_rollback_targets": tuple(
            sorted(
                variant.variant_id
                for variant in archive.variants
                if variant.status is VariantStatus.ASSURED
            )
        ),
    }
