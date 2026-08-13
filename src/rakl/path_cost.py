from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable, Tuple

_COST_FIELDS = ("compute", "verification", "representation", "evidence", "risk", "trust", "new_assumptions")


class CostCompositionKind(str, Enum):
    SUM = "SUM"
    MAX = "MAX"
    SET_UNION = "SET_UNION"
    WORST_CASE = "WORST_CASE"
    CUSTOM_VERIFIED = "CUSTOM_VERIFIED"


class CostComparisonKind(str, Enum):
    MINIMIZE = "MINIMIZE"
    SET_INCLUSION = "SET_INCLUSION"
    REGISTERED_PARTIAL_ORDER = "REGISTERED_PARTIAL_ORDER"
    CUSTOM_VERIFIED = "CUSTOM_VERIFIED"


@dataclass(frozen=True)
class PathCostCoordinateRule:
    coordinate: str
    composition: CostCompositionKind
    comparison: CostComparisonKind
    semantics_id: str

    def __post_init__(self) -> None:
        if not self.coordinate or not self.semantics_id:
            raise ValueError("path-cost coordinate rule requires coordinate and semantics identity")


@dataclass(frozen=True)
class PathCostAlgebra:
    """Registered composition/comparison semantics for theorem-level path cost.

    This object is deliberately metadata-first. ``PathCostVector`` below remains
    a numeric development projection used by current stress plots. A coordinate
    such as assumptions or evidence may be declared SET_UNION/partial-order here
    without being falsely coerced into numeric addition.
    """

    algebra_id: str
    coordinate_rules: Tuple[PathCostCoordinateRule, ...]
    hard_admissibility_profile_id: str

    def __post_init__(self) -> None:
        if not self.algebra_id or not self.hard_admissibility_profile_id:
            raise ValueError("path-cost algebra requires identity and admissibility profile")
        if not self.coordinate_rules:
            raise ValueError("path-cost algebra requires coordinate rules")
        names = [rule.coordinate for rule in self.coordinate_rules]
        if len(names) != len(set(names)):
            raise ValueError("path-cost algebra coordinate rules must be unique")

    def rule_for(self, coordinate: str) -> PathCostCoordinateRule:
        for rule in self.coordinate_rules:
            if rule.coordinate == coordinate:
                return rule
        raise KeyError(coordinate)

    @property
    def is_uniformly_additive_numeric(self) -> bool:
        return all(
            rule.composition is CostCompositionKind.SUM
            and rule.comparison is CostComparisonKind.MINIMIZE
            for rule in self.coordinate_rules
        )


@dataclass(frozen=True)
class PathCostVector:
    """Numeric development projection; not the universal VTG path algebra."""

    compute: float = 0.0
    verification: float = 0.0
    representation: float = 0.0
    evidence: float = 0.0
    risk: float = 0.0
    trust: float = 0.0
    new_assumptions: float = 0.0

    def __post_init__(self) -> None:
        # Finiteness axiom (audit I1): the carrier is [0, inf)^7 with the
        # standard total order per coordinate. NaN is incomparable with
        # everything (dominance stops being a strict order; lexicographic
        # min becomes input-order-dependent), so it must never construct.
        for name in _COST_FIELDS:
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError("path cost coordinates must be finite and nonnegative")

    def add(self, other: "PathCostVector") -> "PathCostVector":
        """All-additive development projection, not theorem-level composition."""
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


def _require_unique_path_ids(options: Tuple[PathOption, ...]) -> None:
    # Identity axiom (audit I2): both algorithms treat path_id as a key into
    # the option set (dominance self-exemption; lexicographic tie-break).
    # Duplicate ids disable pruning between distinct options and break the
    # total tie-break order, so they fail closed.
    ids = [option.path_id for option in options]
    if len(ids) != len(set(ids)):
        raise ValueError("path_id must be unique across options")


def admissible_pareto_frontier(options: Iterable[PathOption]) -> Tuple[PathOption, ...]:
    options = tuple(options)
    _require_unique_path_ids(options)
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
    options = tuple(options)
    _require_unique_path_ids(options)
    admissible = tuple(option for option in options if option.admissibility.admissible)
    if not admissible:
        return None
    for option in admissible:
        if any(not isfinite(getattr(option.cost, name)) for name in coordinate_order):
            raise ValueError("lexicographic selection requires finite cost coordinates")
    return min(admissible, key=lambda item: tuple(getattr(item.cost, name) for name in coordinate_order) + (item.path_id,))
