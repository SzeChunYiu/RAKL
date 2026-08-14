"""Tests for recursion, targeted saturation, and governed invention.

The two load-bearing tests:

* `test_invention_is_gated_behind_two_distinct_failures` — the LIFT discipline,
  checked structurally. An inventor must never be consulted while research or
  decomposition can still move.
* `test_invented_structure_cannot_serve_a_problem_demanding_authority` — proposal
  non-sovereignty, operational. Invention can change what the system explores; it
  cannot supply a licensed route.
"""

from __future__ import annotations

import pytest

from rakl.recursive_solver import (
    AtomFiber,
    FiberState,
    InventionCandidate,
    solve_recursive,
)
from rakl.structure_space import (
    ProblemStructure,
    ReducedStructure,
    StructureSpace,
)
from rakl.support_solver import Atom, Outcome, SupportEdge, SupportStructure


def _reduced(sid, roles, *, edges=(), auth=5):
    atoms = tuple(
        Atom(atom_id=r)
        for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]})
    )
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=sid,
            atoms=atoms,
            edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges),
        ),
        roles=frozenset(roles),
        established_at=auth,
    )


def _no_research(fiber):
    return []


def _no_decompose(atom):
    return None


# --- the no-alarm case -------------------------------------------------------------


def test_fully_matchable_problem_spends_nothing():
    """No fibers, no research, no invention when the space already suffices."""
    space = StructureSpace("s")
    space.accumulate(_reduced("done", {"a", "goal"}, edges=(("a", "goal", 1.0, 9),)))
    problem = ProblemStructure("P", "q", frozenset({"a", "goal"}))

    result = solve_recursive(
        space, problem, start="a", goal="goal",
        researcher=_no_research, decomposer=_no_decompose,
    )
    assert result.report.outcome is Outcome.REACHED
    assert result.fibers == ()
    assert result.inventions == ()
    assert result.research_rounds_spent == 0


# --- targeted research -------------------------------------------------------------


def test_targeted_research_closes_a_fiber():
    """One round of aimed accumulation supplies the missing role."""
    space = StructureSpace("s")
    space.accumulate(_reduced("half", {"a"}, edges=(("a", "bridge", 1.0, 9),)))

    def researcher(fiber):
        assert fiber.atom in {"bridge", "goal"}
        return [_reduced(f"found-{fiber.atom}", {"a", "bridge", "goal"},
                         edges=(("bridge", "goal", 1.0, 9),))]

    problem = ProblemStructure("P", "q", frozenset({"a", "bridge", "goal"}))
    result = solve_recursive(
        space, problem, start="a", goal="goal",
        researcher=researcher, decomposer=_no_decompose,
    )
    assert result.report.outcome is Outcome.REACHED
    assert all(f.state is FiberState.MATCHED for f in result.fibers)


def test_fiber_saturates_after_two_flat_rounds_not_at_the_round_bound():
    """A researcher that only restates known roles must stop early."""
    space = StructureSpace("s")
    space.accumulate(_reduced("known", {"a"}))

    calls = []

    def stale_researcher(fiber):
        calls.append(fiber.atom)
        return [_reduced(f"restate-{len(calls)}", {"a"})]  # nothing new, ever

    problem = ProblemStructure("P", "q", frozenset({"a", "missing"}))
    result = solve_recursive(
        space, problem, start="a", goal="missing",
        researcher=stale_researcher, decomposer=_no_decompose,
        max_rounds_per_fiber=8,
    )
    fiber = result.fibers[0]
    assert fiber.growth_rounds == [0, 0], "saturation is two flat rounds, not the bound"
    assert any("saturated after 2 rounds" in a for a in fiber.failed_attempts)


def test_round_bound_without_flatness_is_reported_as_bounded_open():
    """Hitting the bound while still growing is CANNOT_CHECK, not saturation."""
    space = StructureSpace("s")
    space.accumulate(_reduced("seed", {"a"}))
    n = [0]

    def novelty_treadmill(fiber):
        n[0] += 1
        return [_reduced(f"novel-{n[0]}", {f"irrelevant-{n[0]}"})]  # always new, never right

    problem = ProblemStructure("P", "q", frozenset({"a", "missing"}))
    result = solve_recursive(
        space, problem, start="a", goal="missing",
        researcher=novelty_treadmill, decomposer=_no_decompose,
        max_rounds_per_fiber=3,
    )
    fiber = result.fibers[0]
    assert len(fiber.growth_rounds) == 3
    assert any("without saturating" in a for a in fiber.failed_attempts)


# --- recursion ---------------------------------------------------------------------


def test_decomposition_recurses_and_a_bridging_structure_closes_the_parent():
    """The pattern: understanding the pieces surfaces a structure covering the whole."""
    space = StructureSpace("s")
    space.accumulate(_reduced("base", {"a"}, edges=(("a", "hard", 1.0, 9),)))

    def decomposer(atom):
        if atom == "hard":
            return ProblemStructure("sub", "q", frozenset({"part1", "part2"}))
        return None

    def researcher(fiber):
        if fiber.atom in {"part1", "part2"}:
            # researching the parts surfaces a structure that also covers the parent
            return [_reduced(f"via-{fiber.atom}", {fiber.atom, "hard", "goal"},
                             edges=(("hard", "goal", 1.0, 9),))]
        return []  # direct research on "hard" and "goal" finds nothing

    problem = ProblemStructure("P", "q", frozenset({"a", "hard", "goal"}))
    result = solve_recursive(
        space, problem, start="a", goal="goal",
        researcher=researcher, decomposer=decomposer,
    )
    hard = next(f for f in result.fibers if f.atom == "hard")
    assert hard.state is FiberState.MATCHED
    assert hard.failed_attempts, "the failed research round must remain on record"
    children = [f for f in result.fibers if f.parent == hard.fiber_id]
    assert {c.atom for c in children} == {"part1", "part2"}
    assert all(c.depth == hard.depth + 1 for c in children)
    assert result.report.outcome is Outcome.REACHED


def test_depth_bound_is_respected_and_recorded():
    space = StructureSpace("s")
    space.accumulate(_reduced("seed", {"a"}))

    def endless_decomposer(atom):
        return ProblemStructure(f"sub-{atom}", "q", frozenset({f"{atom}.deeper"}))

    problem = ProblemStructure("P", "q", frozenset({"a", "abyss"}))
    result = solve_recursive(
        space, problem, start="a", goal="abyss",
        researcher=_no_research, decomposer=endless_decomposer, max_depth=2,
    )
    deepest = max(result.fibers, key=lambda f: f.depth)
    assert deepest.depth == 2
    assert any("depth bound 2 reached" in a for a in deepest.failed_attempts)


# --- governed invention ------------------------------------------------------------


def _invention_for(fiber: AtomFiber) -> InventionCandidate:
    return InventionCandidate(
        candidate_id=f"INV-{fiber.fiber_id}",
        fiber_id=fiber.fiber_id,
        closes_role=fiber.atom,
        structure=_reduced(f"invented-{fiber.atom}", {fiber.atom}, auth=0),
        verification_obligations=("reproduce on a fresh case", "independent check"),
    )


def test_invention_is_gated_behind_two_distinct_failures():
    """The LIFT discipline, structurally: no invention while anything can move."""
    seen_fibers = []

    def inventor(fiber):
        seen_fibers.append(fiber)
        return _invention_for(fiber)

    space = StructureSpace("s")
    space.accumulate(_reduced("seed", {"a"}))
    problem = ProblemStructure("P", "q", frozenset({"a", "missing"}))
    result = solve_recursive(
        space, problem, start="a", goal="missing",
        researcher=_no_research, decomposer=_no_decompose, inventor=inventor,
    )
    assert len(seen_fibers) >= 1
    for fiber in seen_fibers:
        assert len(fiber.failed_attempts) >= 2, (
            "inventor consulted before two distinct failures were on record"
        )
    assert result.inventions


def test_inventor_is_never_consulted_when_research_can_still_close():
    def forbidden_inventor(fiber):  # pragma: no cover - must not run
        raise AssertionError("inventor consulted while research could still move")

    space = StructureSpace("s")
    space.accumulate(_reduced("half", {"a"}, edges=(("a", "goal", 1.0, 9),)))

    def researcher(fiber):
        return [_reduced("supply", {"a", "goal"})]

    problem = ProblemStructure("P", "q", frozenset({"a", "goal"}))
    result = solve_recursive(
        space, problem, start="a", goal="goal",
        researcher=researcher, decomposer=_no_decompose, inventor=forbidden_inventor,
    )
    assert result.inventions == ()


def test_invention_candidate_requires_obligations():
    fiber = AtomFiber("F1", "x", "q", "c", "r", None, 0)
    with pytest.raises(ValueError, match="self-licensed"):
        InventionCandidate(
            candidate_id="INV", fiber_id="F1", closes_role="x",
            structure=_reduced("inv", {"x"}, auth=0),
            verification_obligations=(),
        )


def test_invention_candidate_must_enter_at_authority_floor():
    with pytest.raises(ValueError, match="authority floor 0"):
        InventionCandidate(
            candidate_id="INV", fiber_id="F1", closes_role="x",
            structure=_reduced("inv", {"x"}, auth=3),
            verification_obligations=("check",),
        )


def test_invented_structure_cannot_serve_a_problem_demanding_authority():
    """Proposal non-sovereignty, operational.

    The invented structure closes the role for an exploration problem (authority
    0) but is REJECTED for the same problem at demanded authority 1. Raising its
    establishment is verification's job, outside this module.
    """
    space = StructureSpace("s")
    space.accumulate(_reduced("seed", {"a"}, edges=(("a", "novel", 1.0, 9),)))

    problem_exploring = ProblemStructure(
        "P0", "q", frozenset({"a", "novel"}), required_authority=0
    )
    result = solve_recursive(
        space, problem_exploring, start="a", goal="novel",
        researcher=_no_research, decomposer=_no_decompose,
        inventor=_invention_for,
    )
    assert result.inventions, "exploration path should have produced an invention"

    from rakl.structure_space import MatchVerdict, match

    demanding = ProblemStructure(
        "P1", "q", frozenset({"a", "novel"}), required_authority=1
    )
    invented_matches = [
        m for m in match(space, demanding)
        if m.structure_id.startswith("invented-") and m.verdict is MatchVerdict.LICENSED
    ]
    assert invented_matches == [], (
        "an unverified invention was licensed for a problem demanding authority"
    )


def test_report_grants_no_authority():
    space = StructureSpace("s")
    space.accumulate(_reduced("d", {"a", "goal"}, edges=(("a", "goal", 1.0, 9),)))
    problem = ProblemStructure("P", "q", frozenset({"a", "goal"}))
    result = solve_recursive(
        space, problem, start="a", goal="goal",
        researcher=_no_research, decomposer=_no_decompose,
    )
    assert result.grants_scientific_authority is False
