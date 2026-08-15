"""Non-compensatory engineering-closure and research-saturation semantics.

The engineering programme can become locally/reference saturated while production
assurance remains open.  This module makes that distinction machine-readable so
"more files" cannot be mistaken for production readiness.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple


ENGINEERING_FIBERS: Tuple[str, ...] = tuple(f"E{index}" for index in range(1, 21))


class EngineeringFiberLevel(str, Enum):
    OPEN = "OPEN"
    REFERENCE_IMPLEMENTED = "REFERENCE_IMPLEMENTED"
    PRODUCTION_IMPLEMENTED = "PRODUCTION_IMPLEMENTED"
    ASSURED = "ASSURED"
    ABSORBED_STRONGER_PARENT = "ABSORBED_STRONGER_PARENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class EngineeringFiberAssessment:
    fiber_id: str
    level: EngineeringFiberLevel
    evidence_ids: Tuple[str, ...]
    residuals: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.fiber_id not in ENGINEERING_FIBERS:
            raise ValueError(f"unknown engineering fiber:{self.fiber_id}")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence ids must be unique")
        if len(self.residuals) != len(set(self.residuals)):
            raise ValueError("residuals must be unique")
        if self.level in {
            EngineeringFiberLevel.REFERENCE_IMPLEMENTED,
            EngineeringFiberLevel.PRODUCTION_IMPLEMENTED,
            EngineeringFiberLevel.ASSURED,
            EngineeringFiberLevel.ABSORBED_STRONGER_PARENT,
        } and not self.evidence_ids:
            raise ValueError("implemented/assured fiber requires evidence")
        if self.level is EngineeringFiberLevel.ASSURED and self.residuals:
            raise ValueError("ASSURED fiber cannot retain in-scope residuals")


@dataclass(frozen=True)
class EngineeringClosureReport:
    required_fibers: Tuple[str, ...]
    assessments: Tuple[EngineeringFiberAssessment, ...]
    reference_saturated: bool
    production_ready_scoped: bool
    open_fibers: Tuple[str, ...]
    cannot_check_fibers: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_engineering_closure(
    assessments: Iterable[EngineeringFiberAssessment],
    *,
    required_fibers: Tuple[str, ...] = ENGINEERING_FIBERS,
) -> EngineeringClosureReport:
    if len(required_fibers) != len(set(required_fibers)) or any(
        fiber not in ENGINEERING_FIBERS for fiber in required_fibers
    ):
        raise ValueError("required engineering fibers must be unique registered IDs")
    items = tuple(assessments)
    by_id = {item.fiber_id: item for item in items}
    if len(by_id) != len(items):
        raise ValueError("one assessment per engineering fiber")

    open_fibers: list[str] = []
    cannot: list[str] = []
    reference_ok = {
        EngineeringFiberLevel.REFERENCE_IMPLEMENTED,
        EngineeringFiberLevel.PRODUCTION_IMPLEMENTED,
        EngineeringFiberLevel.ASSURED,
        EngineeringFiberLevel.ABSORBED_STRONGER_PARENT,
        EngineeringFiberLevel.NOT_APPLICABLE,
    }
    production_ok = {
        EngineeringFiberLevel.ASSURED,
        EngineeringFiberLevel.ABSORBED_STRONGER_PARENT,
        EngineeringFiberLevel.NOT_APPLICABLE,
    }
    reasons: list[str] = []
    reference_saturated = True
    production_ready = True
    for fiber in required_fibers:
        assessment = by_id.get(fiber)
        if assessment is None:
            open_fibers.append(fiber)
            reasons.append(f"{fiber}:unassessed")
            reference_saturated = False
            production_ready = False
            continue
        if assessment.level is EngineeringFiberLevel.CANNOT_CHECK:
            cannot.append(fiber)
        if assessment.level not in reference_ok or assessment.residuals:
            open_fibers.append(fiber)
            reference_saturated = False
        if assessment.level not in production_ok or assessment.residuals:
            production_ready = False
        for residual in assessment.residuals:
            reasons.append(f"{fiber}:residual:{residual}")
        if assessment.level is EngineeringFiberLevel.CANNOT_CHECK:
            reasons.append(f"{fiber}:cannot_check")
        elif assessment.level is EngineeringFiberLevel.OPEN:
            reasons.append(f"{fiber}:open")
    if reference_saturated:
        reasons.append("reference_engineering_fibers_closed_at_registered_cutoff")
    if production_ready:
        reasons.append("production_ready_scoped_requires_exact_assurance_evidence")
    return EngineeringClosureReport(
        required_fibers=required_fibers,
        assessments=items,
        reference_saturated=reference_saturated,
        production_ready_scoped=production_ready,
        open_fibers=tuple(dict.fromkeys(open_fibers)),
        cannot_check_fibers=tuple(cannot),
        reasons=tuple(reasons) or ("no_registered_reason",),
    )


@dataclass(frozen=True)
class EngineeringResearchRound:
    round_id: str
    route_family: str
    independent_route: bool
    retained_new_finding_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.round_id or not self.route_family:
            raise ValueError("research round requires identity and route family")
        if len(self.retained_new_finding_ids) != len(set(self.retained_new_finding_ids)):
            raise ValueError("finding ids must be unique")

    @property
    def flat(self) -> bool:
        return not self.retained_new_finding_ids


@dataclass(frozen=True)
class EngineeringResearchSaturationReport:
    bounded_saturated: bool
    recent_novelty_count: int
    independent_flat_route_families: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_absolute_completeness(self) -> bool:
        return False


def assess_engineering_research_saturation(
    rounds: Iterable[EngineeringResearchRound],
    *,
    required_route_families: Tuple[str, ...],
    min_independent_flat_routes: int = 3,
    window: int = 6,
) -> EngineeringResearchSaturationReport:
    items = tuple(rounds)
    if min_independent_flat_routes < 1 or window < 1:
        raise ValueError("positive saturation thresholds required")
    recent = items[-window:]
    novelty = sum(len(item.retained_new_finding_ids) for item in recent)
    flat_routes = tuple(
        dict.fromkeys(
            item.route_family
            for item in recent
            if item.independent_route and item.flat
        )
    )
    missing = tuple(sorted(set(required_route_families) - {item.route_family for item in recent}))
    reasons: list[str] = []
    if novelty:
        reasons.append("recent_retained_engineering_novelty")
    if len(flat_routes) < min_independent_flat_routes:
        reasons.append("insufficient_independent_flat_engineering_routes")
    if missing:
        reasons.append("required_engineering_routes_missing:" + ",".join(missing))
    return EngineeringResearchSaturationReport(
        bounded_saturated=not reasons,
        recent_novelty_count=novelty,
        independent_flat_route_families=flat_routes,
        reasons=tuple(reasons),
    )
