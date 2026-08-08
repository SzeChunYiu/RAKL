from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class SaturationState(str, Enum):
    UNSEARCHED = "UNSEARCHED"
    ACTIVE_NON_FLAT = "ACTIVE_NON_FLAT"
    ROUTE_LOCAL_FLAT = "ROUTE_LOCAL_FLAT"
    SAME_CONTEXT_PLATEAU = "SAME_CONTEXT_PLATEAU"
    INDEPENDENT_FLAT_1 = "INDEPENDENT_FLAT_1"
    INDEPENDENT_FLAT_2 = "INDEPENDENT_FLAT_2"
    INDEPENDENT_FLAT_3 = "INDEPENDENT_FLAT_3"
    SATURATED_SCOPED = "SATURATED_SCOPED"
    REOPENED_BY_RESIDUAL = "REOPENED_BY_RESIDUAL"


@dataclass(frozen=True)
class ResearchRound:
    round_id: str
    route: str
    context_id: str
    semantic_objects: frozenset[str]
    independent: bool = False
    cost: float = 0.0
    source_ids: tuple[str, ...] = ()

    @classmethod
    def from_objects(
        cls,
        round_id: str,
        route: str,
        context_id: str,
        semantic_objects: Iterable[str],
        *,
        independent: bool = False,
        cost: float = 0.0,
        source_ids: Iterable[str] = (),
    ) -> "ResearchRound":
        return cls(
            round_id=round_id,
            route=route,
            context_id=context_id,
            semantic_objects=frozenset(semantic_objects),
            independent=independent,
            cost=cost,
            source_ids=tuple(source_ids),
        )


@dataclass
class RecordedRound:
    research_round: ResearchRound
    new_semantic_objects: frozenset[str]

    @property
    def flat(self) -> bool:
        return not self.new_semantic_objects


@dataclass
class SaturationTracker:
    required_routes: frozenset[str]
    same_context_flat_required: int = 3
    independent_flat_required: int = 3
    rounds: list[RecordedRound] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)
    _reopened_reason: str | None = None

    def record(self, research_round: ResearchRound) -> RecordedRound:
        if any(
            existing.research_round.round_id == research_round.round_id
            for existing in self.rounds
        ):
            raise ValueError(f"duplicate round_id: {research_round.round_id}")

        new_objects = frozenset(research_round.semantic_objects - self._seen)
        recorded = RecordedRound(research_round, new_objects)
        self.rounds.append(recorded)
        self._seen.update(research_round.semantic_objects)
        self._reopened_reason = None
        return recorded

    def reopen(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("reopen reason cannot be empty")
        self._reopened_reason = reason.strip()

    @property
    def seen_semantic_objects(self) -> frozenset[str]:
        return frozenset(self._seen)

    @property
    def covered_routes(self) -> frozenset[str]:
        return frozenset(r.research_round.route for r in self.rounds)

    @property
    def missing_routes(self) -> frozenset[str]:
        return self.required_routes - self.covered_routes

    def _last_nonflat_index(self) -> int:
        last = -1
        for index, recorded in enumerate(self.rounds):
            if not recorded.flat:
                last = index
        return last

    def same_context_flat_count(self) -> int:
        if not self.rounds:
            return 0
        last_nonflat = self._last_nonflat_index()
        tail = self.rounds[last_nonflat + 1 :]
        if not tail:
            return 0

        non_independent_contexts = [
            r.research_round.context_id
            for r in tail
            if not r.research_round.independent
        ]
        if not non_independent_contexts:
            return 0

        active_context = non_independent_contexts[-1]
        return sum(
            1
            for r in tail
            if r.flat
            and not r.research_round.independent
            and r.research_round.context_id == active_context
        )

    def independent_flat_count(self) -> int:
        last_nonflat = self._last_nonflat_index()
        return sum(
            1
            for r in self.rounds[last_nonflat + 1 :]
            if r.flat and r.research_round.independent
        )

    @property
    def state(self) -> SaturationState:
        if self._reopened_reason is not None:
            return SaturationState.REOPENED_BY_RESIDUAL
        if not self.rounds:
            return SaturationState.UNSEARCHED
        if not self.rounds[-1].flat:
            return SaturationState.ACTIVE_NON_FLAT
        if self.missing_routes:
            return SaturationState.ROUTE_LOCAL_FLAT
        if self.same_context_flat_count() < self.same_context_flat_required:
            return SaturationState.ROUTE_LOCAL_FLAT

        independent = self.independent_flat_count()
        if independent <= 0:
            return SaturationState.SAME_CONTEXT_PLATEAU
        if independent == 1:
            return SaturationState.INDEPENDENT_FLAT_1
        if independent == 2:
            return SaturationState.INDEPENDENT_FLAT_2
        if independent == 3 and self.independent_flat_required > 3:
            return SaturationState.INDEPENDENT_FLAT_3
        if independent >= self.independent_flat_required:
            return SaturationState.SATURATED_SCOPED
        return SaturationState.INDEPENDENT_FLAT_3

    def novelty_history(self) -> list[dict]:
        return [
            {
                "round_id": r.research_round.round_id,
                "route": r.research_round.route,
                "context_id": r.research_round.context_id,
                "independent": r.research_round.independent,
                "new_count": len(r.new_semantic_objects),
                "new_semantic_objects": sorted(r.new_semantic_objects),
                "flat": r.flat,
            }
            for r in self.rounds
        ]

    def unseen_mass_diagnostic(self) -> dict:
        """Exploratory unseen-semantic diagnostic.

        This intentionally does NOT certify saturation. RAKL rounds are adaptive and
        heterogeneous, so classical iid species-estimation assumptions generally fail.
        """
        frequencies: Counter[str] = Counter()
        total_sightings = 0
        for recorded in self.rounds:
            for item in recorded.research_round.semantic_objects:
                frequencies[item] += 1
                total_sightings += 1

        observed = len(frequencies)
        f1 = sum(1 for count in frequencies.values() if count == 1)
        f2 = sum(1 for count in frequencies.values() if count == 2)

        if f2 > 0:
            chao_lower = observed + (f1 * f1) / (2.0 * f2)
        else:
            chao_lower = observed + (f1 * max(f1 - 1, 0)) / 2.0

        good_turing_unseen = f1 / total_sightings if total_sightings else 1.0

        return {
            "diagnostic_only": True,
            "adaptive_non_iid_warning": True,
            "observed_semantic_objects": observed,
            "singletons_f1": f1,
            "doubletons_f2": f2,
            "total_round_object_sightings": total_sightings,
            "chao_style_lower_support": chao_lower,
            "chao_style_unseen_lower": max(0.0, chao_lower - observed),
            "good_turing_style_unseen_mass": good_turing_unseen,
        }
