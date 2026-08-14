"""Research-machine control primitives for quantified knowledge acquisition.

This module is deliberately narrow. It does not create a second RAKL metrology or
promotion system. Instead it turns literature/knowledge acquisition into an
explicit state transition that reuses ``saturation_vector`` for stopping and
reopening decisions.

The object being controlled is not "number of papers read". It is retained
semantic structure: new facets, mechanisms, contexts, contradictions, falsifiers,
blind spots, or other content-addressed semantic objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple

from .saturation_vector import NoveltyRound, SaturationAxis, SaturationVectorReport, assess_saturation_vector


class KnowledgeSearchMode(str, Enum):
    INITIAL_BROAD = "INITIAL_BROAD"
    RESIDUAL_TARGETED = "RESIDUAL_TARGETED"
    FRESHNESS_REFRESH = "FRESHNESS_REFRESH"
    APPLE_JUMP = "APPLE_JUMP"


class KnowledgeDecision(str, Enum):
    CONTINUE_SEARCH = "CONTINUE_SEARCH"
    PROCEED_OBJECT_WORK = "PROCEED_OBJECT_WORK"
    TARGETED_REFRESH_REQUIRED = "TARGETED_REFRESH_REQUIRED"
    FRESHNESS_REFRESH_REQUIRED = "FRESHNESS_REFRESH_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class KnowledgeAcquisitionRound:
    """One bounded search/read/normalize round.

    ``retained_semantic_ids`` contains content-addressed semantic objects after
    normalization/deduplication. Raw paper/source counts are inventory only.
    """

    round_id: str
    route_family: str
    mode: KnowledgeSearchMode
    independent_route: bool
    query_ids: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    relevant_source_ids: Tuple[str, ...]
    retained_semantic_ids: Tuple[str, ...]
    new_facet_ids: Tuple[str, ...] = ()
    new_mechanism_ids: Tuple[str, ...] = ()
    new_context_ids: Tuple[str, ...] = ()
    new_contradiction_ids: Tuple[str, ...] = ()
    new_falsifier_ids: Tuple[str, ...] = ()
    new_blind_spot_ids: Tuple[str, ...] = ()
    cost_policy_id: str = ""
    cost: float = 0.0
    evidence_pointers: Tuple[str, ...] = ()
    residual_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.round_id or not self.route_family:
            raise ValueError("knowledge round requires round_id and route_family")
        if not self.query_ids:
            raise ValueError("knowledge round requires at least one query id")
        if not self.cost_policy_id:
            raise ValueError("knowledge round requires cost_policy_id")
        if self.cost < 0:
            raise ValueError("knowledge round cost cannot be negative")
        for name in (
            "query_ids",
            "source_ids",
            "relevant_source_ids",
            "retained_semantic_ids",
            "new_facet_ids",
            "new_mechanism_ids",
            "new_context_ids",
            "new_contradiction_ids",
            "new_falsifier_ids",
            "new_blind_spot_ids",
            "evidence_pointers",
            "residual_ids",
        ):
            values = getattr(self, name)
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique within a knowledge round")
        if set(self.relevant_source_ids) - set(self.source_ids):
            raise ValueError("relevant sources must be a subset of processed sources")
        categorized = (
            set(self.new_facet_ids)
            | set(self.new_mechanism_ids)
            | set(self.new_context_ids)
            | set(self.new_contradiction_ids)
            | set(self.new_falsifier_ids)
            | set(self.new_blind_spot_ids)
        )
        if categorized - set(self.retained_semantic_ids):
            raise ValueError("categorized semantic objects must be included in retained_semantic_ids")

    @property
    def semantic_novelty_count(self) -> int:
        return len(self.retained_semantic_ids)

    @property
    def source_count(self) -> int:
        return len(self.source_ids)

    @property
    def relevance_precision(self) -> float | None:
        if not self.source_ids:
            return None
        return len(self.relevant_source_ids) / len(self.source_ids)

    @property
    def semantic_yield_per_source(self) -> float | None:
        if not self.source_ids:
            return None
        return self.semantic_novelty_count / len(self.source_ids)

    @property
    def cost_per_semantic_object(self) -> float | None:
        if self.semantic_novelty_count == 0:
            return None
        return self.cost / self.semantic_novelty_count

    def as_novelty_round(self) -> NoveltyRound:
        residual_axes = (SaturationAxis.KNOWLEDGE,) if self.residual_ids else ()
        return NoveltyRound(
            round_id=self.round_id,
            route_family=self.route_family,
            independent_route=self.independent_route,
            retained_novelty=((SaturationAxis.KNOWLEDGE, self.semantic_novelty_count),),
            residual_axes=residual_axes,
            residual_signature=self.residual_ids,
        )


@dataclass(frozen=True)
class KnowledgeSaturationPolicy:
    """Frozen stopping policy for one knowledge fiber."""

    required_route_families: Tuple[str, ...]
    min_independent_flat_routes: int = 3
    window: int = 6

    def __post_init__(self) -> None:
        if not self.required_route_families:
            raise ValueError("knowledge saturation policy requires route families")
        if len(self.required_route_families) != len(set(self.required_route_families)):
            raise ValueError("required route families must be unique")
        if self.min_independent_flat_routes < 2:
            raise ValueError("at least two independent flat routes are required")
        if self.window < self.min_independent_flat_routes:
            raise ValueError("window cannot be smaller than independent-flat-route requirement")


@dataclass(frozen=True)
class KnowledgeSaturationAssessment:
    decision: KnowledgeDecision
    reasons: Tuple[str, ...]
    saturation_report: SaturationVectorReport | None
    covered_route_families: Tuple[str, ...]
    missing_route_families: Tuple[str, ...]
    source_count: int
    relevant_source_count: int
    retained_semantic_count: int
    total_cost: float

    @property
    def bounded_saturated(self) -> bool:
        return self.decision is KnowledgeDecision.PROCEED_OBJECT_WORK


def assess_knowledge_saturation(
    rounds: Iterable[KnowledgeAcquisitionRound],
    *,
    policy: KnowledgeSaturationPolicy,
    active_knowledge_residual_ids: Tuple[str, ...] = (),
    freshness_stale: bool = False,
) -> KnowledgeSaturationAssessment:
    """Decide whether knowledge acquisition should continue or reopen.

    Precedence is fail-closed:
      1. an active native knowledge residual forces targeted refresh;
      2. stale freshness forces incremental refresh;
      3. otherwise bounded saturation requires semantic flatness *and* registered
         route-family coverage.

    A previously saturated fiber is therefore persistent across ordinary local
    iterations, but native residuals and freshness events can invalidate it.
    """

    items = tuple(rounds)
    source_count = sum(item.source_count for item in items)
    relevant_source_count = sum(len(item.relevant_source_ids) for item in items)
    retained_semantic_count = sum(item.semantic_novelty_count for item in items)
    total_cost = sum(item.cost for item in items)

    if active_knowledge_residual_ids:
        return KnowledgeSaturationAssessment(
            decision=KnowledgeDecision.TARGETED_REFRESH_REQUIRED,
            reasons=("native_knowledge_residual_reopens_fiber",),
            saturation_report=None,
            covered_route_families=tuple(sorted({item.route_family for item in items})),
            missing_route_families=(),
            source_count=source_count,
            relevant_source_count=relevant_source_count,
            retained_semantic_count=retained_semantic_count,
            total_cost=total_cost,
        )

    if freshness_stale:
        return KnowledgeSaturationAssessment(
            decision=KnowledgeDecision.FRESHNESS_REFRESH_REQUIRED,
            reasons=("knowledge_freshness_epoch_expired_or_new_source_event",),
            saturation_report=None,
            covered_route_families=tuple(sorted({item.route_family for item in items})),
            missing_route_families=(),
            source_count=source_count,
            relevant_source_count=relevant_source_count,
            retained_semantic_count=retained_semantic_count,
            total_cost=total_cost,
        )

    if not items:
        return KnowledgeSaturationAssessment(
            decision=KnowledgeDecision.CONTINUE_SEARCH,
            reasons=("no_knowledge_acquisition_rounds",),
            saturation_report=None,
            covered_route_families=(),
            missing_route_families=policy.required_route_families,
            source_count=0,
            relevant_source_count=0,
            retained_semantic_count=0,
            total_cost=0.0,
        )

    recent = items[-policy.window :]
    covered = tuple(sorted({item.route_family for item in recent if item.independent_route}))
    missing = tuple(sorted(set(policy.required_route_families) - set(covered)))
    report = assess_saturation_vector(
        (item.as_novelty_round() for item in items),
        required_axes=(SaturationAxis.KNOWLEDGE,),
        min_independent_flat_routes=policy.min_independent_flat_routes,
        window=policy.window,
    )

    reasons = list(report.reasons)
    if missing:
        reasons.append("required_search_route_family_coverage_incomplete:" + ",".join(missing))

    if report.bounded_saturated and not missing:
        decision = KnowledgeDecision.PROCEED_OBJECT_WORK
        reasons.append("bounded_knowledge_saturation_established")
    else:
        decision = KnowledgeDecision.CONTINUE_SEARCH

    return KnowledgeSaturationAssessment(
        decision=decision,
        reasons=tuple(reasons),
        saturation_report=report,
        covered_route_families=covered,
        missing_route_families=missing,
        source_count=source_count,
        relevant_source_count=relevant_source_count,
        retained_semantic_count=retained_semantic_count,
        total_cost=total_cost,
    )


def knowledge_round_metrics(round_: KnowledgeAcquisitionRound) -> dict[str, float | int | None]:
    """Return descriptive/controller-candidate metrics without granting authority."""

    return {
        "sources_processed": round_.source_count,
        "relevant_sources": len(round_.relevant_source_ids),
        "semantic_novelty": round_.semantic_novelty_count,
        "new_facets": len(round_.new_facet_ids),
        "new_mechanisms": len(round_.new_mechanism_ids),
        "new_context_coordinates": len(round_.new_context_ids),
        "new_contradictions": len(round_.new_contradiction_ids),
        "new_falsifiers": len(round_.new_falsifier_ids),
        "new_blind_spots": len(round_.new_blind_spot_ids),
        "relevance_precision": round_.relevance_precision,
        "semantic_yield_per_source": round_.semantic_yield_per_source,
        "cost": round_.cost,
        "cost_per_semantic_object": round_.cost_per_semantic_object,
    }
