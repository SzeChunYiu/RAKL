"""COVERAGE_IS_NOT_REACHABILITY — the solver's second phase.

Found by a real search: the researcher located every atom by live git query,
every fibre closed MATCHED, and the outcome was UNREACHABLE_IN_PRINCIPLE.

    _atom_is_supplied()  asks whether some licensed structure COVERS the role
    solve_problem()      asks whether a connected ROUTE reaches the goal

A role can be covered by a structure that sits on no path. Worse: a fibre whose
role is already covered never has its researcher called, so the edge into it is
never researched, and nothing on the research side can reach it. The fix opens
route fibres for covered-but-disconnected atoms after coverage closes.
"""

from __future__ import annotations

from rakl.recursive_solver import SolveEvent, solve_recursive
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace
from rakl.support_solver import Atom, SupportEdge, SupportStructure


def reduced(sid, roles, *, edges=(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(structure_id=sid, atoms=atoms,
                                   edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges)),
        roles=frozenset(roles), established_at=auth,
    )


def no_decompose(atom):
    return None


def test_a_covered_but_disconnected_atom_gets_its_researcher_called() -> None:
    """The exact shape of the real-search failure, in miniature.

    Space already carries `mid` as a role (via a structure that does not connect
    it to anything on the path). The coverage loop therefore never asks the
    researcher for `mid`, so the edge start->mid is never supplied — unless the
    reachability phase asks for it.
    """

    space = StructureSpace("s")
    space.accumulate(reduced("seed", {"start"}))
    # `mid` is COVERED (it appears as a role) but nothing reaches it.
    space.accumulate(reduced("orphan", {"mid", "goal"}, edges=(("mid", "goal", 1.0, 9),)))

    problem = ProblemStructure(
        problem_id="P", qoi="start -> goal", required_roles=frozenset({"start", "mid", "goal"})
    )

    asked: list[str] = []
    events: list[SolveEvent] = []

    def researcher(fiber):
        asked.append(fiber.atom)
        if fiber.atom == "mid":
            return [reduced("connect-mid", {"start", "mid"}, edges=(("start", "mid", 1.0, 9),))]
        return []

    result = solve_recursive(
        space, problem, start="start", goal="goal",
        researcher=researcher, decomposer=no_decompose, observer=events.append,
    )

    # Before the fix: coverage saw every role supplied, asked for nothing, and
    # returned UNREACHABLE. After: the reachability phase asks for `mid`.
    assert "mid" in asked, "the researcher was never asked for the disconnected atom"
    assert result.report.outcome.name == "REACHED"
    assert result.report.route is not None
    assert list(result.report.route.atoms) == ["start", "mid", "goal"]

    route_events = [e for e in events if e.kind == "ROUTE_FIBER"]
    assert route_events and route_events[0].atom == "mid"


def test_reachability_phase_does_not_run_when_coverage_already_reaches() -> None:
    """No route fibres are opened when the coverage phase already connected the goal."""

    space = StructureSpace("s")
    space.accumulate(reduced("seed", {"start"}))
    events: list[SolveEvent] = []

    def researcher(fiber):
        if fiber.atom == "goal":
            return [reduced("g", {"start", "goal"}, edges=(("start", "goal", 1.0, 9),))]
        return []

    problem = ProblemStructure(problem_id="P", qoi="q", required_roles=frozenset({"start", "goal"}))
    result = solve_recursive(
        space, problem, start="start", goal="goal",
        researcher=researcher, decomposer=no_decompose, observer=events.append,
    )
    assert result.report.outcome.name == "REACHED"
    assert not [e for e in events if e.kind == "ROUTE_FIBER"]


def test_a_route_fibre_that_finds_nothing_exhausts_honestly() -> None:
    """When connectivity cannot be researched, the route fibre says so."""

    space = StructureSpace("s")
    space.accumulate(reduced("seed", {"start"}))
    space.accumulate(reduced("orphan", {"mid", "goal"}, edges=(("mid", "goal", 1.0, 9),)))
    problem = ProblemStructure(
        problem_id="P", qoi="q", required_roles=frozenset({"start", "mid", "goal"})
    )

    def empty(fiber):
        return []

    result = solve_recursive(
        space, problem, start="start", goal="goal",
        researcher=empty, decomposer=no_decompose, max_rounds_per_fiber=3,
    )
    assert result.report.outcome.name != "REACHED"
    route_fibres = [f for f in result.fibers if f.context == "reachability"]
    assert route_fibres
    assert all(f.state.name == "EXHAUSTED" for f in route_fibres)
    assert any("no licensed edge into this atom" in a for f in route_fibres for a in f.failed_attempts)
