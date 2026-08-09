from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class ContextCompileVerdict(str, Enum):
    COMPILED = "COMPILED"
    CANNOT_COMPILE = "CANNOT_COMPILE"


@dataclass(frozen=True)
class ContextItem:
    """A materializable view over canonical RAKL memory.

    The compiler operates on metadata and pointers. It never deletes or rewrites the
    canonical archive, and it never grants scientific authority.
    """

    record_id: str
    token_cost: int
    coverage_atoms: tuple[str, ...] = ()
    fiber_ids: tuple[str, ...] = ()
    mandatory: bool = False
    relevant: bool = True
    compact_view: bool = False
    lossy: bool = False
    source_record_ids: tuple[str, ...] = ()
    erasure_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id cannot be empty")
        if self.token_cost <= 0:
            raise ValueError("token_cost must be positive")
        if self.compact_view and not self.source_record_ids:
            raise ValueError("compact_view requires source_record_ids for rehydration")
        if self.lossy and not self.compact_view:
            raise ValueError("lossy items must be declared compact_view")
        if self.lossy and not self.erasure_tags:
            raise ValueError("lossy compact_view requires erasure_tags")


@dataclass(frozen=True)
class ContextCompileRequest:
    budget_tokens: int
    target_fibers: tuple[str, ...] = ()
    required_coverage_atoms: tuple[str, ...] = ()
    coverage_weights: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        if self.budget_tokens < 0:
            raise ValueError("budget_tokens cannot be negative")
        if len(dict(self.coverage_weights)) != len(self.coverage_weights):
            raise ValueError("coverage_weights cannot contain duplicate atoms")
        if any(weight < 0 for _, weight in self.coverage_weights):
            raise ValueError("coverage weights cannot be negative")


@dataclass(frozen=True)
class ContextCompileReport:
    verdict: ContextCompileVerdict
    selected_record_ids: tuple[str, ...]
    omitted_record_ids: tuple[str, ...]
    used_tokens: int
    budget_tokens: int
    covered_atoms: tuple[str, ...]
    missing_required_atoms: tuple[str, ...]
    rehydration_record_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def compression_ratio(self) -> float:
        if self.budget_tokens == 0:
            return 0.0
        return self.used_tokens / self.budget_tokens


def _weight_map(request: ContextCompileRequest) -> Mapping[str, float]:
    return dict(request.coverage_weights)


def _atom_weight(atom: str, weights: Mapping[str, float]) -> float:
    return weights.get(atom, 1.0)


def _fiber_relevant(item: ContextItem, target_fibers: frozenset[str]) -> bool:
    if item.mandatory:
        return True
    if not item.relevant:
        return False
    if not target_fibers:
        return True
    if not item.fiber_ids:
        return False
    return bool(target_fibers.intersection(item.fiber_ids))


def _marginal_value(
    item: ContextItem,
    covered: frozenset[str],
    weights: Mapping[str, float],
) -> float:
    return sum(
        _atom_weight(atom, weights)
        for atom in set(item.coverage_atoms)
        if atom not in covered
    )


def compile_epistemic_context(
    items: Iterable[ContextItem],
    request: ContextCompileRequest,
) -> ContextCompileReport:
    """Compile a deterministic bounded working set from an external canonical archive.

    Policy:
    1. Explicitly mandatory epistemic items are never dropped for budget reasons.
    2. If mandatory material does not fit, fail closed instead of truncating it.
    3. Remaining budget is spent on highest marginal weighted coverage per token.
    4. Redundant items with zero new coverage are not filler-selected.
    5. Target-fiber filtering is applied before optional selection.
    6. Compact/lossy views remain rehydratable pointers, not replacement evidence.

    This is support infrastructure only. The function does not retrieve raw payloads,
    summarize evidence, change memory, or mint authority.
    """

    pool = tuple(items)
    by_id = {item.record_id: item for item in pool}
    if len(by_id) != len(pool):
        raise ValueError("duplicate context record_id")

    target_fibers = frozenset(request.target_fibers)
    weights = _weight_map(request)

    mandatory = tuple(sorted((item for item in pool if item.mandatory), key=lambda x: x.record_id))
    mandatory_cost = sum(item.token_cost for item in mandatory)

    if mandatory_cost > request.budget_tokens:
        omitted = tuple(sorted(item.record_id for item in pool if item.record_id not in {m.record_id for m in mandatory}))
        mandatory_atoms = frozenset(atom for item in mandatory for atom in item.coverage_atoms)
        missing = tuple(sorted(set(request.required_coverage_atoms) - mandatory_atoms))
        return ContextCompileReport(
            verdict=ContextCompileVerdict.CANNOT_COMPILE,
            selected_record_ids=tuple(item.record_id for item in mandatory),
            omitted_record_ids=omitted,
            used_tokens=mandatory_cost,
            budget_tokens=request.budget_tokens,
            covered_atoms=tuple(sorted(mandatory_atoms)),
            missing_required_atoms=missing,
            rehydration_record_ids=tuple(sorted({source for item in mandatory for source in item.source_record_ids})),
            reasons=("mandatory_over_budget",),
        )

    selected: list[ContextItem] = list(mandatory)
    selected_ids = {item.record_id for item in selected}
    used = mandatory_cost
    covered = frozenset(atom for item in selected for atom in item.coverage_atoms)

    candidates = [
        item
        for item in pool
        if item.record_id not in selected_ids and _fiber_relevant(item, target_fibers)
    ]

    while True:
        fitting = [item for item in candidates if used + item.token_cost <= request.budget_tokens]
        scored: list[tuple[float, float, int, str, ContextItem]] = []
        for item in fitting:
            marginal = _marginal_value(item, covered, weights)
            if marginal <= 0:
                continue
            ratio = marginal / item.token_cost
            scored.append((-ratio, -marginal, item.token_cost, item.record_id, item))
        if not scored:
            break

        scored.sort(key=lambda row: row[:4])
        chosen = scored[0][4]
        selected.append(chosen)
        selected_ids.add(chosen.record_id)
        used += chosen.token_cost
        covered = frozenset(set(covered).union(chosen.coverage_atoms))
        candidates = [item for item in candidates if item.record_id != chosen.record_id]

    missing_required = tuple(sorted(set(request.required_coverage_atoms) - set(covered)))
    all_ids = set(by_id)
    omitted_ids = tuple(sorted(all_ids - selected_ids))
    rehydration = tuple(
        sorted({source for item in selected for source in item.source_record_ids})
    )

    reasons: tuple[str, ...] = ()
    verdict = ContextCompileVerdict.COMPILED
    if missing_required:
        verdict = ContextCompileVerdict.CANNOT_COMPILE
        reasons = ("required_coverage_not_materialized",)

    return ContextCompileReport(
        verdict=verdict,
        selected_record_ids=tuple(item.record_id for item in selected),
        omitted_record_ids=omitted_ids,
        used_tokens=used,
        budget_tokens=request.budget_tokens,
        covered_atoms=tuple(sorted(covered)),
        missing_required_atoms=missing_required,
        rehydration_record_ids=rehydration,
        reasons=reasons,
    )
