from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

_COST_FIELDS = ("compute", "verification", "representation", "evidence", "risk", "trust", "new_assumptions")


@dataclass(frozen=True)
class PathCostVector:
    compute: float = 0.0
    verification: float = 0.0
    representation: float = 0.0
    evidence: float = 0.0
    risk: float = 0.0
    trust: float = 0.0
    new_assumptions: float = 0.0

    def __post_init__(self) -> None:
        if any(getattr(self, name) < 0 for name in _COST_FIELDS):
            raise ValueError("path cost coordinates must be nonnegative")

    def add(self, other: "PathCostVector") -> "PathCostVector":
        return PathCostVector(**{name: getattr(self, name) + getattr(other, name) for name in _COST_FIELDS})

    def as_tuple(self) -> Tuple[float, ...]:
        return tuple(getattr(self, name) for name in _COST_FIELDS)


@dataclass(frozen=True)
class PathAdmissibility:
    licensed_assumptions: bool | None
    trusted_verifier: bool | None
    specification_aligned: bool | None
    portal_valid: bool | None
    root_scope_preserved: bool | None

    @property
    def admissible(self) -> bool:
        return all(value is True for value in (self.licensed_assumptions, self.trusted_verifier, self.specification_aligned, self.portal_valid, self.root_scope_preserved))

    @property
    def reasons(self) -> Tuple[str, ...]:
        fields = (("licensed_assumptions", self.licensed_assumptions), ("trusted_verifier", self.trusted_verifier), ("specification_aligned", self.specification_aligned), ("portal_valid", self.portal_valid), ("root_scope_preserved", self.root_scope_preserved))
        out = []
        for name, value in fields:
            if value is False:
                out.append(f"hard_constraint_failed:{name}")
            elif value is None:
                out.append(f"hard_constraint_unknown:{name}")
        return tuple(out)


@dataclass(frozen=True)
class PathOption:
    path_id: str
    cost: PathCostVector
    admissibility: PathAdmissibility

    def __post_init__(self) -> None:
        if not self.path_id:
            raise ValueError("path_id is required")


def dominates(left: PathCostVector, right: PathCostVector) -> bool:
    l = left.as_tuple()
    r = right.as_tuple()
    return all(a <= b for a, b in zip(l, r)) and any(a < b for a, b in zip(l, r))


def admissible_pareto_frontier(options: Iterable[PathOption]) -> Tuple[PathOption, ...]:
    admissible = tuple(option for option in options if option.admissibility.admissible)
    frontier = []
    for candidate in admissible:
        if any(dominates(other.cost, candidate.cost) for other in admissible if other.path_id != candidate.path_id):
            continue
        frontier.append(candidate)
    return tuple(sorted(frontier, key=lambda item: item.path_id))


def explicit_lexicographic_select(options: Iterable[PathOption], *, coordinate_order: Tuple[str, ...]) -> PathOption | None:
    if not coordinate_order or len(set(coordinate_order)) != len(coordinate_order):
        raise ValueError("coordinate_order must be nonempty and unique")
    if any(name not in _COST_FIELDS for name in coordinate_order):
        raise ValueError("unregistered path cost coordinate")
    admissible = tuple(option for option in options if option.admissibility.admissible)
    if not admissible:
        return None
    return min(admissible, key=lambda item: tuple(getattr(item.cost, name) for name in coordinate_order) + (item.path_id,))
