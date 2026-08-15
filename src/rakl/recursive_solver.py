"""Recursive decomposition, targeted saturation, and governed invention.

The full loop, as the operator states it:

    decompose the problem -> reduce -> for each unresolved atom:
    {accumulate related knowledge -> saturate the fiber}
    (keep breaking the problem into smaller pieces)
    -> match the problem's structure against the space -> compose the matches
    -> and when the space cannot supply a match: research it, and if research
       exhausts, INVENT a candidate the space has never seen.

``structure_space`` implements the flat loop. This module adds the two verbs it
lacks:

**Recursion.** An unresolved atom becomes a *fiber* — the spec's
``f = (o_f, q_f, gamma_f, r_f, parent(f))`` from
``FORMAL_SYSTEM_SPECIFICATION.md`` §8 — and is researched with *targeted*
accumulation. If its fiber saturates without a match, the atom is decomposed into
sub-roles and the loop recurses. The fiber tree, with residuals and parent
chain, is preserved whole: that record *is* the learning-from-failure substrate
(the fuller challenge-learning loop is L6 and out of scope here).

**Governed invention.** When research saturates AND decomposition is exhausted,
the solver may propose a structure the space never contained. Discipline mirrors
the LIFT rule already enforced in ``semantic_shortcut``: invention requires at
least two distinct failed attempts first (a saturated research fiber and a failed
or impossible decomposition), and an invented structure enters the space at
**authority floor 0** with non-empty verification obligations. Proposal
non-sovereignty — machine-checked for canonical state — is thereby operational
here too: an invented structure can participate in exploration (demanded
authority 0) but cannot support any route a problem demands real authority for,
until something *outside this module* raises its establishment.

Proposal-only. Nothing here grants scientific authority.
"""

from __future__ import annotations

from typing import Callable, Iterable

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum

from .structure_space import (
    MatchVerdict,
    ProblemStructure,
    ReducedStructure,
    StructureSpace,
    match,
    solve_problem,
    unmatched_roles,
)
from .support_solver import SolveReport


class FiberState(str, Enum):
    OPEN = "OPEN"
    MATCHED = "MATCHED"
    DECOMPOSED = "DECOMPOSED"
    RESEARCH_SATURATED = "RESEARCH_SATURATED"
    INVENTION_PROPOSED = "INVENTION_PROPOSED"
    EXHAUSTED = "EXHAUSTED"


@dataclass
class AtomFiber:
    """Spec §8: an unresolved transformation with its residual and parent."""

    fiber_id: str
    atom: str
    qoi: str
    context: str
    residual: str
    parent: str | None
    depth: int
    state: FiberState = FiberState.OPEN
    #: New-role growth per targeted research round. Never rewritten.
    growth_rounds: list[int] = field(default_factory=list)
    failed_attempts: list[str] = field(default_factory=list)

    @property
    def research_saturated(self) -> bool:
        """Two consecutive flat targeted rounds — bounded, never absolute."""
        return len(self.growth_rounds) >= 2 and all(
            g == 0 for g in self.growth_rounds[-2:]
        )


@dataclass(frozen=True)
class InventionCandidate:
    """A structure the space has never seen, proposed to close a fiber.

    Enters the space only at authority floor 0 and only with obligations. It is a
    proposal in the strict Paper I sense: it can change what the system explores
    next, not what any claim is licensed to assert.
    """

    candidate_id: str
    fiber_id: str
    closes_role: str
    structure: ReducedStructure
    verification_obligations: tuple[str, ...]
    grants_scientific_authority: bool = False

    def __post_init__(self) -> None:
        if not self.verification_obligations:
            raise ValueError(
                "an invention with no verification obligations is a self-licensed "
                "claim, not a proposal"
            )
        if self.structure.established_at != 0:
            raise ValueError(
                "an invented structure must enter at authority floor 0; "
                "establishment is raised only by verification outside this module"
            )


@dataclass(frozen=True)
class RecursiveSolveReport:
    report: SolveReport
    fibers: tuple[AtomFiber, ...]
    inventions: tuple[InventionCandidate, ...]
    research_rounds_spent: int

    @property
    def grants_scientific_authority(self) -> bool:
        return False


#: One targeted research round for a fiber: fetch and reduce sources aimed at the
#: fiber's atom. An LLM, retrieval, a domain tool — operator-side, like the
#: reduction operator itself.
TargetedResearcher = Callable[[AtomFiber], Sequence[ReducedStructure]]

#: Decompose an unresolved atom into a finer problem structure, or None when the
#: atom is not further decomposable. Its output is a proposal, not ground truth.
AtomDecomposer = Callable[[str], ProblemStructure | None]

#: Propose a bridging structure for an exhausted fiber, or None to decline.
InventionOperator = Callable[[AtomFiber], InventionCandidate | None]


def _atom_is_supplied(space: StructureSpace, problem: ProblemStructure, atom: str) -> bool:
    for m in match(space, problem):
        if m.verdict is MatchVerdict.LICENSED and atom in m.covered_roles:
            return True
    return False


@dataclass(frozen=True)
class SolveEvent:
    """One observable transition inside the search.

    Emitted per fibre open, per research round, and at every state change. The
    round-level `growth` is the load-bearing field: a fibre researching for
    eight rounds with zero growth is saturating, while one still growing when it
    hits the bound is bounded-open. Those are different findings and the trace
    has to show which is happening while it happens, not only afterwards.
    """

    kind: str
    fiber_id: str = ""
    atom: str = ""
    depth: int = 0
    round_index: int = 0
    growth: int = 0
    state: str = ""
    detail: str = ""

    def render(self) -> str:
        head = f"{self.kind:<18}"
        loc = f"{self.fiber_id or '-':>4} {self.atom or '-':<22}"
        body = ""
        if self.kind == "RESEARCH_ROUND":
            body = f"round {self.round_index} growth {self.growth:+d}"
        elif self.state:
            body = self.state
        if self.detail:
            body = f"{body}  {self.detail}" if body else self.detail
        return f"  {head} d{self.depth} {loc} {body}".rstrip()


def render_trace(events: "Iterable[SolveEvent]") -> str:
    """Render a trace as an operator log, newest last."""

    return "\n".join(e.render() for e in events)


def solve_recursive(
    space: StructureSpace,
    problem: ProblemStructure,
    *,
    start: str,
    goal: str,
    researcher: TargetedResearcher,
    decomposer: AtomDecomposer,
    inventor: InventionOperator | None = None,
    max_depth: int = 4,
    max_rounds_per_fiber: int = 8,
    observer: "Callable[[SolveEvent], None] | None" = None,
) -> RecursiveSolveReport:
    """Run the loop to a terminal: solved, or a fiber tree naming exactly why not.

    Every unresolved atom gets a fiber. A fiber is researched until matched or
    saturated; a saturated fiber is decomposed and recursed; an exhausted fiber
    may receive an invention — in that order, never skipping ahead. The order is
    the discipline: invention before exhaustion would be a shortcut around
    evidence, and the LIFT precondition (>=2 distinct failed attempts) is checked
    structurally, not on trust.
    """
    fibers: list[AtomFiber] = []
    inventions: list[InventionCandidate] = []
    rounds_spent = 0
    counter = 0

    def emit(kind: str, **kw: object) -> None:
        if observer is not None:
            observer(SolveEvent(kind=kind, **kw))  # type: ignore[arg-type]

    def close_atom(atom: str, prob: ProblemStructure, parent: str | None, depth: int) -> None:
        nonlocal rounds_spent, counter
        counter += 1
        fiber = AtomFiber(
            fiber_id=f"F{counter}",
            atom=atom,
            qoi=prob.qoi,
            context=f"depth={depth}",
            residual="no licensed structure covers this role",
            parent=parent,
            depth=depth,
        )
        fibers.append(fiber)
        emit("FIBER_OPENED", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
             detail=f"parent={parent or 'root'}")

        # 1. Targeted research until matched or the fiber saturates.
        while len(fiber.growth_rounds) < max_rounds_per_fiber:
            if _atom_is_supplied(space, prob, atom):
                fiber.state = FiberState.MATCHED
                emit("FIBER_MATCHED", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
                     state="MATCHED", detail="already supplied")
                return
            if fiber.research_saturated:
                emit("RESEARCH_FLAT", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
                     round_index=len(fiber.growth_rounds),
                     detail="no growth across the saturation window")
                break
            batch = researcher(fiber)
            rounds_spent += 1
            growth = sum(space.accumulate(r) for r in batch)
            fiber.growth_rounds.append(growth)
            emit("RESEARCH_ROUND", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
                 round_index=len(fiber.growth_rounds), growth=growth,
                 detail=f"{len(batch)} structure(s) returned")
        if _atom_is_supplied(space, prob, atom):
            fiber.state = FiberState.MATCHED
            emit("FIBER_MATCHED", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
                 state="MATCHED", detail=f"after {len(fiber.growth_rounds)} round(s)")
            return
        fiber.state = FiberState.RESEARCH_SATURATED
        # "Saturated" and "hit the round bound while still growing" are different
        # findings — conflating them would report CANNOT_CHECK as checked-and-flat.
        if fiber.research_saturated:
            fiber.failed_attempts.append(
                f"targeted research saturated after {len(fiber.growth_rounds)} rounds"
            )
        else:
            fiber.failed_attempts.append(
                f"targeted research hit the {max_rounds_per_fiber}-round bound "
                "without saturating; the fiber is bounded-open, not exhausted"
            )

        # 2. Decompose and recurse.
        if depth < max_depth:
            sub = decomposer(atom)
            if sub is not None:
                fiber.state = FiberState.DECOMPOSED
                emit("DECOMPOSED", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
                     state="DECOMPOSED",
                     detail=f"into {len(sub.required_roles)} sub-atom(s)")
                for sub_atom in sorted(sub.required_roles):
                    if not _atom_is_supplied(space, sub, sub_atom):
                        close_atom(sub_atom, sub, fiber.fiber_id, depth + 1)
                if _atom_is_supplied(space, prob, atom):
                    fiber.state = FiberState.MATCHED
                    return
                fiber.failed_attempts.append("decomposition did not yield a match")
            else:
                fiber.failed_attempts.append("atom is not further decomposable")
        else:
            fiber.failed_attempts.append(f"depth bound {max_depth} reached")

        # 3. Invention — only now, and only with the LIFT precondition satisfied.
        if inventor is not None and len(fiber.failed_attempts) >= 2:
            emit("INVENTION_ELIGIBLE", fiber_id=fiber.fiber_id, atom=atom, depth=depth,
                 detail=f"{len(fiber.failed_attempts)} distinct failed attempts")
            candidate = inventor(fiber)
            if candidate is not None:
                space.accumulate(candidate.structure)
                inventions.append(candidate)
                fiber.state = FiberState.INVENTION_PROPOSED
                return
        fiber.state = FiberState.EXHAUSTED

    for atom in sorted(unmatched_roles(space, problem)):
        close_atom(atom, problem, None, 0)

    report = solve_problem(space, problem, start=start, goal=goal)
    return RecursiveSolveReport(
        report=report,
        fibers=tuple(fibers),
        inventions=tuple(inventions),
        research_rounds_spent=rounds_spent,
    )
