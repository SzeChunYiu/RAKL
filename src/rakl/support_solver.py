"""The RAKL solving loop, executable.

    distil -> saturate -> navigate -> connect

The framework had every part of this and no composition of them. `L4-NAVIGATION`
is specified in ``FORMAL_SYSTEM_SPECIFICATION.md`` §8 and stated in Paper I §04g,
but nothing ran it: a grep for ``epistemic_cut`` or ``support_hypergraph`` across
``src/rakl`` returned nothing. This module is that composition.

Four commitments distinguish it from a graph search:

**Distillation is obstruction-preserving.** A structure carries explicit
obstruction objects, not only pairwise edges. Paper I proves that a distillation
recording only pairwise data cannot decide global realizability
(``RaklFormal.no_pairwise_predicate_decides_global_realizability``), so a solver
consuming one would assemble routes whose every step is licensed and which have
no global section. Here that is enforced rather than assumed.

**Authority is carried on every step.** A target demanding authority α is
reachable only through edges licensed at α or above. A cheap route through weakly
licensed evidence is not a route.

**Failure is informative.** When no admissible route exists the solver returns an
*epistemic cut*: the minimum-cost set of elements that, if established, would open
one. "Not reachable" is the least useful thing a research system can say.

**The universe is finite by construction.** A distilled structure supplies the
finite basis that makes bounded saturation certifiable rather than merely bounded.

Proposal-only: a route is a *support* claim. It grants no scientific authority and
promotes nothing.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
import heapq


class Outcome(str, Enum):
    REACHED = "REACHED"
    CUT = "CUT"
    UNREACHABLE_IN_PRINCIPLE = "UNREACHABLE_IN_PRINCIPLE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class Atom:
    """A retained semantic object: the 'core' a distillation keeps."""

    atom_id: str
    established_at: int = 0

    def __post_init__(self) -> None:
        if not self.atom_id.strip():
            raise ValueError("atom_id is required")
        if self.established_at < 0:
            raise ValueError("authority layers are non-negative")


@dataclass(frozen=True)
class SupportEdge:
    """A typed transition, usable only at or above its licensing layer."""

    source: str
    target: str
    cost: float
    licensed_at: int

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("edge cost must be non-negative")
        if self.licensed_at < 0:
            raise ValueError("authority layers are non-negative")


@dataclass(frozen=True)
class Obstruction:
    """A cover whose members are pairwise fine and jointly unrealizable.

    This is the datum a "keep the core of each piece" distillation drops, because
    it is an absence rather than a fact. Paper I's three-context parity
    construction is the canonical instance.
    """

    obstruction_id: str
    cover: frozenset[str]
    detail: str = ""

    def __post_init__(self) -> None:
        if len(self.cover) < 2:
            raise ValueError("an obstruction needs at least two atoms to obstruct")


@dataclass(frozen=True)
class SupportStructure:
    """A distilled, obstruction-preserving support hypergraph."""

    structure_id: str
    atoms: tuple[Atom, ...]
    edges: tuple[SupportEdge, ...]
    obstructions: tuple[Obstruction, ...] = ()

    def __post_init__(self) -> None:
        ids = {a.atom_id for a in self.atoms}
        if len(ids) != len(self.atoms):
            raise ValueError("duplicate atom_id in structure")
        for edge in self.edges:
            if edge.source not in ids or edge.target not in ids:
                raise ValueError(f"edge {edge.source}->{edge.target} references an unknown atom")
        for obstruction in self.obstructions:
            missing = obstruction.cover - ids
            if missing:
                raise ValueError(f"obstruction {obstruction.obstruction_id} covers unknown atoms {missing}")

    @property
    def universe(self) -> frozenset[str]:
        """The finite basis. This is what makes saturation certifiable."""
        return frozenset(a.atom_id for a in self.atoms)


@dataclass(frozen=True)
class Target:
    """A registered target contract tau = (q, alpha, gamma)."""

    target_id: str
    qoi: str
    goal_atom: str
    required_authority: int
    context: str = ""


@dataclass(frozen=True)
class SupportRoute:
    atoms: tuple[str, ...]
    edges: tuple[SupportEdge, ...]
    total_cost: float


@dataclass(frozen=True)
class EpistemicCut:
    """The bottleneck: a set every structural route must pass through.

    This is the object ``FORMAL_SYSTEM_SPECIFICATION.md`` §8 defines — *"every
    admissible support route to tau intersecting B"*. It answers **what cannot be
    avoided**, and is a lower bound on the work required.

    It is deliberately *not* the same object as `MinimalRepair`. Resolving a
    bottleneck is necessary, not sufficient: on a single chain the bottleneck is
    any one under-licensed edge, while opening the route requires all of them.
    Conflating the two overstates progress, so both are reported.

    ``exact`` is False when the search exceeded its bound and a greedy cover was
    returned. A cut is never silently approximated.
    """

    elements: tuple[str, ...]
    cost: float
    exact: bool
    rationale: str


@dataclass(frozen=True)
class MinimalRepair:
    """The cheapest set whose establishment actually opens a route.

    Answers **what would be enough** — an upper bound on the work required, and
    the actionable object for a research plan.
    """

    elements: tuple[str, ...]
    cost: float
    opens_route: tuple[str, ...]
    exact: bool


@dataclass(frozen=True)
class SolveReport:
    outcome: Outcome
    route: SupportRoute | None = None
    cut: EpistemicCut | None = None
    repair: MinimalRepair | None = None
    blocked_by_obstruction: tuple[str, ...] = ()
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def grants_scientific_authority(self) -> bool:
        """Always false. A support route is a support claim, not a verdict."""
        return False


def _usable(edge: SupportEdge, target: Target) -> bool:
    """An edge serves a target only if licensed at or above the demanded layer."""
    return edge.licensed_at >= target.required_authority


def _violates_obstruction(
    atoms: Iterable[str], structure: SupportStructure
) -> tuple[str, ...]:
    used = set(atoms)
    return tuple(
        o.obstruction_id for o in structure.obstructions if o.cover <= used
    )


def _cheapest_route(
    structure: SupportStructure,
    start: str,
    target: Target,
    *,
    edge_filter,
) -> SupportRoute | None:
    """Dijkstra over admitted edges, rejecting routes that realize an obstruction.

    Obstruction rejection is applied to the *assembled* atom set rather than
    edge-locally, because an obstruction is a property of a cover and no local
    check can see it — that is exactly the paper's identifiability result.
    """
    adjacency: dict[str, list[SupportEdge]] = {}
    for edge in structure.edges:
        if edge_filter(edge):
            adjacency.setdefault(edge.source, []).append(edge)

    # (cost, atoms so far, edges so far) — atoms carried so covers can be checked.
    queue: list[tuple[float, int, tuple[str, ...], tuple[SupportEdge, ...]]] = [
        (0.0, 0, (start,), ())
    ]
    best: dict[tuple[str, frozenset[str]], float] = {}
    counter = 1
    while queue:
        cost, _, atoms, edges = heapq.heappop(queue)
        node = atoms[-1]
        if node == target.goal_atom:
            return SupportRoute(atoms=atoms, edges=edges, total_cost=cost)
        key = (node, frozenset(atoms))
        if best.get(key, float("inf")) <= cost:
            continue
        best[key] = cost
        for edge in adjacency.get(node, ()):
            if edge.target in atoms:
                continue  # simple routes only
            extended = atoms + (edge.target,)
            if _violates_obstruction(extended, structure):
                continue
            heapq.heappush(
                queue, (cost + edge.cost, counter, extended, edges + (edge,))
            )
            counter += 1
    return None


def _all_simple_routes(
    structure: SupportStructure, start: str, goal: str, *, limit: int
) -> list[tuple[SupportEdge, ...]]:
    """Enumerate simple routes ignoring licensing, bounded by ``limit``."""
    adjacency: dict[str, list[SupportEdge]] = {}
    for edge in structure.edges:
        adjacency.setdefault(edge.source, []).append(edge)

    routes: list[tuple[SupportEdge, ...]] = []

    def walk(node: str, seen: frozenset[str], acc: tuple[SupportEdge, ...]) -> None:
        if len(routes) >= limit:
            return
        if node == goal:
            routes.append(acc)
            return
        for edge in adjacency.get(node, ()):
            if edge.target in seen:
                continue
            walk(edge.target, seen | {edge.target}, acc + (edge,))

    walk(start, frozenset({start}), ())
    return routes


def _edge_name(edge: SupportEdge) -> str:
    return f"{edge.source}->{edge.target}"


def _minimum_cut(
    routes: Sequence[tuple[SupportEdge, ...]],
    structure: SupportStructure,
    target: Target,
    *,
    max_exact: int = 12,
) -> EpistemicCut:
    """Cheapest set of blockers meeting every route.

    A blocker is an under-licensed edge, or an obstruction the route realizes.
    Exact by enumeration while the blocker universe is small; greedy beyond, and
    the result says which it was.
    """
    per_route: list[set[str]] = []
    weights: dict[str, float] = {}
    for route in routes:
        blockers: set[str] = set()
        for edge in route:
            if not _usable(edge, target):
                name = _edge_name(edge)
                blockers.add(name)
                # cost of establishing = the authority shortfall
                weights[name] = float(target.required_authority - edge.licensed_at)
        atoms = {route[0].source} | {e.target for e in route} if route else set()
        for obstruction_id in _violates_obstruction(atoms, structure):
            blockers.add(obstruction_id)
            weights[obstruction_id] = float(len(next(
                o for o in structure.obstructions if o.obstruction_id == obstruction_id
            ).cover))
        if not blockers:
            # a route with no blockers means the caller should not have asked for a cut
            return EpistemicCut((), 0.0, True, "an unblocked route exists")
        per_route.append(blockers)

    universe = sorted(weights)
    if len(universe) <= max_exact:
        best: tuple[float, tuple[str, ...]] | None = None
        for size in range(1, len(universe) + 1):
            for candidate in combinations(universe, size):
                chosen = set(candidate)
                if all(chosen & blockers for blockers in per_route):
                    cost = sum(weights[c] for c in candidate)
                    if best is None or cost < best[0]:
                        best = (cost, candidate)
            if best is not None:
                break
        assert best is not None
        return EpistemicCut(
            elements=best[1],
            cost=best[0],
            exact=True,
            rationale="minimum-cost set of blockers meeting every admissible route",
        )

    chosen: set[str] = set()
    remaining = [set(b) for b in per_route]
    while remaining:
        pick = min(
            (c for c in universe if c not in chosen),
            key=lambda c: weights[c] / max(1, sum(1 for r in remaining if c in r)),
        )
        chosen.add(pick)
        remaining = [r for r in remaining if pick not in r]
    return EpistemicCut(
        elements=tuple(sorted(chosen)),
        cost=sum(weights[c] for c in chosen),
        exact=False,
        rationale=(
            f"greedy cover; blocker universe {len(universe)} exceeded the exact bound "
            f"{max_exact}, so minimality is NOT established"
        ),
    )


def _minimal_repair(
    routes: Sequence[tuple[SupportEdge, ...]],
    structure: SupportStructure,
    target: Target,
) -> MinimalRepair | None:
    """Cheapest set of blockers whose establishment opens at least ONE route.

    Necessary work is the bottleneck; sufficient work is this. A route obstructed
    by a cover is skipped entirely — an obstruction is not repaired by licensing,
    it is repaired by finding a different route.
    """
    best: tuple[float, tuple[str, ...], tuple[str, ...]] | None = None
    for route in routes:
        atoms = {route[0].source} | {e.target for e in route} if route else set()
        if _violates_obstruction(atoms, structure):
            continue
        needed: list[str] = []
        cost = 0.0
        for edge in route:
            if not _usable(edge, target):
                needed.append(_edge_name(edge))
                cost += float(target.required_authority - edge.licensed_at)
        if best is None or cost < best[0]:
            path = (route[0].source,) + tuple(e.target for e in route) if route else ()
            best = (cost, tuple(needed), path)
    if best is None:
        return None
    return MinimalRepair(elements=best[1], cost=best[0], opens_route=best[2], exact=True)


def solve(
    structure: SupportStructure,
    target: Target,
    *,
    start: str,
    route_enumeration_limit: int = 256,
) -> SolveReport:
    """Navigate a distilled support structure toward a target contract.

    Returns a route, or the epistemic cut that would open one, or a statement
    that the structure cannot connect the two at all.
    """
    if start not in structure.universe:
        return SolveReport(Outcome.CANNOT_CHECK, reasons=(f"unknown start atom {start!r}",))
    if target.goal_atom not in structure.universe:
        return SolveReport(
            Outcome.CANNOT_CHECK, reasons=(f"unknown goal atom {target.goal_atom!r}",)
        )

    route = _cheapest_route(
        structure, start, target, edge_filter=lambda e: _usable(e, target)
    )
    if route is not None:
        return SolveReport(Outcome.REACHED, route=route)

    relaxed = _all_simple_routes(
        structure, start, target.goal_atom, limit=route_enumeration_limit
    )
    if not relaxed:
        return SolveReport(
            Outcome.UNREACHABLE_IN_PRINCIPLE,
            reasons=(
                "no route exists even ignoring authority licensing; the structure "
                "does not connect these atoms at all",
            ),
        )

    obstructed = sorted({
        oid
        for r in relaxed
        for oid in _violates_obstruction({r[0].source} | {e.target for e in r}, structure)
    })
    cut = _minimum_cut(relaxed, structure, target)
    repair = _minimal_repair(relaxed, structure, target)
    return SolveReport(
        Outcome.CUT,
        cut=cut,
        repair=repair,
        blocked_by_obstruction=tuple(obstructed),
        reasons=(
            f"{len(relaxed)} route(s) exist structurally; none is admissible at "
            f"authority {target.required_authority}",
        ),
    )
