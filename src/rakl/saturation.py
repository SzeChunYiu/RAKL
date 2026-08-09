from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence


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
    evidence_lineage: frozenset[str] = frozenset()
    lineage_complete: bool = False

    def __post_init__(self) -> None:
        if self.lineage_complete and not self.evidence_lineage:
            raise ValueError("lineage_complete requires at least one canonical evidence-lineage id")

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
        evidence_lineage: Iterable[str] = (),
        lineage_complete: bool = False,
    ) -> "ResearchRound":
        return cls(
            round_id=round_id,
            route=route,
            context_id=context_id,
            semantic_objects=frozenset(semantic_objects),
            independent=independent,
            cost=cost,
            source_ids=tuple(source_ids),
            evidence_lineage=frozenset(evidence_lineage),
            lineage_complete=lineage_complete,
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

    # Exact set-packing is intentionally bounded. Above this size RAKL returns a
    # deterministic conservative lower bound rather than pretending an expensive
    # heuristic is exact evidence of independence.
    lineage_exact_limit: int = 20

    def __post_init__(self) -> None:
        if self.same_context_flat_required < 1:
            raise ValueError("same_context_flat_required must be >= 1")
        if self.independent_flat_required < 1:
            raise ValueError("independent_flat_required must be >= 1")
        if self.lineage_exact_limit < 1:
            raise ValueError("lineage_exact_limit must be >= 1")

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

    def _independent_flat_tail(self) -> list[RecordedRound]:
        last_nonflat = self._last_nonflat_index()
        return [
            r
            for r in self.rounds[last_nonflat + 1 :]
            if r.flat and r.research_round.independent
        ]

    @staticmethod
    def _round_key(recorded: RecordedRound) -> tuple[str, tuple[str, ...]]:
        rr = recorded.research_round
        return (rr.round_id, tuple(sorted(rr.evidence_lineage)))

    def _maximum_disjoint_lineage_subset(
        self,
        rounds: Sequence[RecordedRound],
    ) -> tuple[tuple[RecordedRound, ...], str]:
        """Return a conservative set of fully lineage-disjoint flat rounds.

        For small collections this solves the set-packing problem exactly. For larger
        collections it uses a deterministic greedy lower bound. A lower bound can delay
        saturation but can never create false independent evidence.
        """

        ordered = tuple(sorted(rounds, key=self._round_key))
        if not ordered:
            return (), "exact"

        if len(ordered) > self.lineage_exact_limit:
            selected: list[RecordedRound] = []
            used: set[str] = set()
            for recorded in sorted(
                ordered,
                key=lambda r: (
                    len(r.research_round.evidence_lineage),
                    self._round_key(r),
                ),
            ):
                lineage = set(recorded.research_round.evidence_lineage)
                if used.isdisjoint(lineage):
                    selected.append(recorded)
                    used.update(lineage)
            return tuple(sorted(selected, key=self._round_key)), "greedy_lower_bound"

        best: tuple[RecordedRound, ...] = ()

        def choose(
            index: int,
            used: frozenset[str],
            selected: tuple[RecordedRound, ...],
        ) -> None:
            nonlocal best
            if len(selected) + (len(ordered) - index) < len(best):
                return
            if index >= len(ordered):
                if len(selected) > len(best):
                    best = selected
                elif len(selected) == len(best):
                    current_ids = tuple(r.research_round.round_id for r in selected)
                    best_ids = tuple(r.research_round.round_id for r in best)
                    if current_ids < best_ids:
                        best = selected
                return

            current = ordered[index]
            lineage = current.research_round.evidence_lineage
            if used.isdisjoint(lineage):
                choose(index + 1, used | lineage, selected + (current,))
            choose(index + 1, used, selected)

        choose(0, frozenset(), ())
        return best, "exact"

    def independence_diagnostic(self) -> dict:
        """Describe process independence separately from evidence-lineage independence.

        ``independent=True`` only asserts process/context independence. Full saturation
        credit additionally requires a complete canonical evidence-lineage declaration.
        Shared ancestry is treated as dependence. Missing ancestry is partial
        identification, not evidence of independence.
        """

        tail = self._independent_flat_tail()
        complete = [
            r
            for r in tail
            if r.research_round.lineage_complete and r.research_round.evidence_lineage
        ]
        unknown = [
            r.research_round.round_id
            for r in tail
            if not r.research_round.lineage_complete
            or not r.research_round.evidence_lineage
        ]

        overlap_pairs: list[dict] = []
        for i, left in enumerate(complete):
            for right in complete[i + 1 :]:
                shared = left.research_round.evidence_lineage & right.research_round.evidence_lineage
                if shared:
                    overlap_pairs.append(
                        {
                            "left": left.research_round.round_id,
                            "right": right.research_round.round_id,
                            "shared_lineage": sorted(shared),
                        }
                    )

        selected, method = self._maximum_disjoint_lineage_subset(complete)
        selected_ids = [r.research_round.round_id for r in selected]

        if unknown:
            status = "PARTIALLY_IDENTIFIED_LINEAGE"
        elif overlap_pairs:
            status = "DEPENDENCE_IDENTIFIED"
        else:
            status = "FULL_LINEAGE_DISJOINT"

        return {
            "status": status,
            "declared_process_independent_flat_rounds": len(tail),
            "lineage_complete_flat_rounds": len(complete),
            "unknown_or_incomplete_lineage_rounds": sorted(unknown),
            "overlap_pairs": overlap_pairs,
            "conservative_full_independent_rounds": len(selected),
            "credited_round_ids": selected_ids,
            "count_method": method,
            "exact_count": method == "exact",
        }

    def independent_flat_count(self) -> int:
        return int(self.independence_diagnostic()["conservative_full_independent_rounds"])

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

        # Threshold must be checked before descriptive intermediate labels. This is
        # load-bearing for projects that deliberately require only 1 or 2 independent
        # flat rounds in a scoped/cheap benchmark.
        if independent >= self.independent_flat_required:
            return SaturationState.SATURATED_SCOPED
        if independent == 1:
            return SaturationState.INDEPENDENT_FLAT_1
        if independent == 2:
            return SaturationState.INDEPENDENT_FLAT_2
        return SaturationState.INDEPENDENT_FLAT_3

    def novelty_history(self) -> list[dict]:
        return [
            {
                "round_id": r.research_round.round_id,
                "route": r.research_round.route,
                "context_id": r.research_round.context_id,
                "independent": r.research_round.independent,
                "evidence_lineage": sorted(r.research_round.evidence_lineage),
                "lineage_complete": r.research_round.lineage_complete,
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
