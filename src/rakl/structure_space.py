"""The framework, end to end.

    reduce -> accumulate -> saturate -> decompose -> match -> compose

A transform (a mathematical tool, or an LLM) reduces information to a structure.
Repeat, and structures accumulate in a space. The space saturates. A semantic
processor decomposes a problem into *its* structure. Solving is then search: find
the accumulated structures whose shape fits the problem, and compose them.

``support_solver`` navigates **one** structure. This module is the space, and the
matching that decides which structures are usable for a given problem.

**What is pluggable and what is not.** The reduction operator and the semantic
processor are interfaces — an LLM, a parser, a domain tool, anything. Everything
around them is the framework and is not pluggable: accumulation identity,
saturation over the space, obstruction preservation, the matching discipline, the
authority contract, and the epistemic cut on failure. That division is the point.
A prompt can reduce and decompose; it cannot tell you when the space is saturated
or refuse a match that is not licensed.

**Matching fails closed.** A candidate with no satisfied obligations is REJECTED,
never licensed. This is deliberate: ``assess_transfer_v2`` was found on
2026-08-14 to return LICENSED with zero reasons for two structures sharing no
roles, no relations and no invariants. An empty obligation set is an absence of
evidence, not evidence of applicability.

Proposal-only. Grants no scientific authority; a composition is a support claim.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum

from .support_solver import (
    Atom,
    Obstruction,
    SolveReport,
    SupportEdge,
    SupportStructure,
    Target,
    solve,
)


class MatchVerdict(str, Enum):
    LICENSED = "LICENSED"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class SpaceSaturation(str, Enum):
    OPEN = "OPEN"
    BOUNDED_SATURATED = "BOUNDED_SATURATED"


@dataclass(frozen=True)
class ProblemStructure:
    """A problem decomposed by a semantic processor into its shape.

    ``required_roles`` are the kinds of thing the problem needs; ``required_relations``
    the connections between them. Both are the processor's output, and the framework
    treats them as a proposal, never as ground truth.
    """

    problem_id: str
    qoi: str
    required_roles: frozenset[str]
    required_relations: frozenset[tuple[str, str]] = frozenset()
    required_authority: int = 0

    def __post_init__(self) -> None:
        if not self.required_roles:
            raise ValueError(
                "a decomposition with no required roles cannot constrain matching; "
                "an empty problem structure would license every candidate"
            )


@dataclass(frozen=True)
class ReducedStructure:
    """A structure produced by one application of the reduction operator."""

    structure: SupportStructure
    roles: frozenset[str]
    relations: frozenset[tuple[str, str]] = frozenset()
    provenance: str = ""
    established_at: int = 0


@dataclass(frozen=True)
class Match:
    structure_id: str
    verdict: MatchVerdict
    covered_roles: frozenset[str]
    covered_relations: frozenset[tuple[str, str]]
    reasons: tuple[str, ...]

    @property
    def coverage(self) -> int:
        return len(self.covered_roles) + len(self.covered_relations)


@dataclass
class StructureSpace:
    """An accumulating, saturating space of reduced structures."""

    space_id: str
    structures: list[ReducedStructure] = field(default_factory=list)
    #: Obstructions whose cover SPANS structures. These have no home in any single
    #: contributor -- a structure cannot declare a cover it does not fully contain --
    #: yet they are the dangerous case: an incompatibility that only materializes
    #: once two independently sound structures are composed.
    cross_structure_obstructions: list[Obstruction] = field(default_factory=list)
    #: Roles newly seen per accumulation round — the growth signal.
    growth_per_round: list[int] = field(default_factory=list)
    _seen_roles: set[str] = field(default_factory=set, repr=False)

    def accumulate(self, reduced: ReducedStructure) -> int:
        """Add a structure. Returns how many roles it newly contributed.

        Growth is measured in *newly seen roles*, not in structure count: adding
        the hundredth restatement of a known shape is representation growth, not
        epistemic growth. This mirrors the marginal-growth-vector discipline in
        ``epistemic_saturation``.
        """
        new = reduced.roles - self._seen_roles
        self._seen_roles |= reduced.roles
        self.structures.append(reduced)
        self.growth_per_round.append(len(new))
        return len(new)

    @property
    def universe(self) -> frozenset[str]:
        return frozenset(self._seen_roles)

    def saturation(self, *, required_flat_rounds: int = 2) -> SpaceSaturation:
        """Bounded saturation over the space.

        Never absolute: this is relative to the reduction operator and the sources
        fed to it, exactly as Paper I requires. A space can be saturated and still
        be missing a structure no source described.
        """
        if len(self.growth_per_round) < required_flat_rounds:
            return SpaceSaturation.OPEN
        tail = self.growth_per_round[-required_flat_rounds:]
        return (
            SpaceSaturation.BOUNDED_SATURATED
            if all(g == 0 for g in tail)
            else SpaceSaturation.OPEN
        )


def match(space: StructureSpace, problem: ProblemStructure) -> tuple[Match, ...]:
    """Which accumulated structures are licensed for this problem?

    Fails closed. A candidate is LICENSED only if it covers at least one required
    role *and* every relation it claims to cover holds between roles it actually
    has. Zero coverage is REJECTED, never licensed.
    """
    results: list[Match] = []
    for reduced in space.structures:
        covered_roles = reduced.roles & problem.required_roles
        covered_relations = frozenset(
            rel
            for rel in problem.required_relations
            if rel in reduced.relations and {rel[0], rel[1]} <= reduced.roles
        )
        reasons: list[str] = []
        if not covered_roles:
            reasons.append("covers no required role")
        if reduced.established_at < problem.required_authority:
            reasons.append(
                f"established at {reduced.established_at}, "
                f"problem requires {problem.required_authority}"
            )
        # A relation claimed but not backed by both roles is a defect, not a miss.
        dangling = frozenset(
            rel
            for rel in problem.required_relations
            if rel in reduced.relations and not {rel[0], rel[1]} <= reduced.roles
        )
        if dangling:
            reasons.append(f"claims relations without both roles: {sorted(dangling)}")

        verdict = MatchVerdict.REJECTED if reasons else MatchVerdict.LICENSED
        results.append(
            Match(
                structure_id=reduced.structure.structure_id,
                verdict=verdict,
                covered_roles=covered_roles,
                covered_relations=covered_relations,
                reasons=tuple(reasons),
            )
        )
    return tuple(sorted(results, key=lambda m: (-m.coverage, m.structure_id)))


def unmatched_roles(
    space: StructureSpace, problem: ProblemStructure
) -> frozenset[str]:
    """Required roles no licensed structure supplies.

    This is the space-level analogue of an epistemic cut: it names what the space
    would have to acquire before the problem becomes solvable at all.
    """
    covered: set[str] = set()
    for m in match(space, problem):
        if m.verdict is MatchVerdict.LICENSED:
            covered |= m.covered_roles
    return problem.required_roles - covered


def compose(
    space: StructureSpace,
    problem: ProblemStructure,
    *,
    start: str,
    goal: str,
) -> SupportStructure:
    """Glue the licensed matches into one structure to navigate.

    Obstructions are carried through from every contributing structure. Dropping
    them here would reintroduce exactly the unsoundness Paper I proves: a
    composition can realize a cover that no contributing structure realized alone.
    """
    atoms: dict[str, Atom] = {}
    edges: list[SupportEdge] = []
    obstructions: list[Obstruction] = []
    licensed = {m.structure_id for m in match(space, problem) if m.verdict is MatchVerdict.LICENSED}
    obstructions.extend(space.cross_structure_obstructions)

    for reduced in space.structures:
        if reduced.structure.structure_id not in licensed:
            continue
        for atom in reduced.structure.atoms:
            atoms.setdefault(atom.atom_id, atom)
        edges.extend(reduced.structure.edges)
        obstructions.extend(reduced.structure.obstructions)

    for required in (start, goal):
        atoms.setdefault(required, Atom(atom_id=required))

    seen: set[str] = set()
    unique_obstructions: list[Obstruction] = []
    for obstruction in obstructions:
        if obstruction.obstruction_id in seen:
            continue
        seen.add(obstruction.obstruction_id)
        if obstruction.cover <= set(atoms):
            unique_obstructions.append(obstruction)

    return SupportStructure(
        structure_id=f"composed::{problem.problem_id}",
        atoms=tuple(atoms.values()),
        edges=tuple(edges),
        obstructions=tuple(unique_obstructions),
    )


def solve_problem(
    space: StructureSpace,
    problem: ProblemStructure,
    *,
    start: str,
    goal: str,
) -> SolveReport:
    """The whole loop: match the space to the problem, compose, navigate."""
    composed = compose(space, problem, start=start, goal=goal)
    target = Target(
        target_id=problem.problem_id,
        qoi=problem.qoi,
        goal_atom=goal,
        required_authority=problem.required_authority,
    )
    return solve(composed, target, start=start)


# --- pluggable interfaces ----------------------------------------------------------

#: Reduce raw information to a structure. An LLM, a parser, or a domain tool.
ReductionOperator = Callable[[str], ReducedStructure]

#: Decompose a problem statement into its structure. Same freedom, same status:
#: its output is a proposal that the matching discipline then constrains.
SemanticProcessor = Callable[[str], ProblemStructure]


def reduce_all(
    operator: ReductionOperator, sources: Sequence[str], space: StructureSpace
) -> StructureSpace:
    """Apply the reduction operator across sources, accumulating into the space."""
    for source in sources:
        space.accumulate(operator(source))
    return space
