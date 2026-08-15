"""Solver telemetry — one event per state transition.

A search you cannot watch is a search you cannot debug: "it ran and found
nothing" and "it never asked for the right atom" were indistinguishable from
outside. The load-bearing assertion is that the trace distinguishes a fibre
that saturated from one that hit its round bound while still growing, because
those are different findings.
"""

from __future__ import annotations

import pytest

from rakl.recursive_solver import SolveEvent, render_trace, solve_recursive
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace
from rakl.support_solver import Atom, SupportEdge, SupportStructure


def reduced(sid, roles, *, edges=(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=sid, atoms=atoms,
            edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges),
        ),
        roles=frozenset(roles), established_at=auth,
    )


@pytest.fixture()
def problem():
    return ProblemStructure(
        problem_id="P", qoi="a -> goal", required_roles=frozenset({"a", "bridge", "goal"})
    )


@pytest.fixture()
def space():
    s = StructureSpace("s")
    s.accumulate(reduced("seed", {"a"}))
    return s


SUPPLY = {"bridge": ("a", "bridge"), "goal": ("bridge", "goal")}


def supplying(fiber):
    edge = SUPPLY.get(fiber.atom)
    if not edge:
        return []
    return [reduced(f"f-{fiber.atom}", set(edge), edges=((edge[0], edge[1], 1.0, 9),))]


def empty(fiber):
    return []


def no_decompose(atom):
    return None


def collect(space, problem, researcher, **kw):
    events: list[SolveEvent] = []
    result = solve_recursive(
        space, problem, start="a", goal="goal",
        researcher=researcher, decomposer=no_decompose,
        observer=events.append, **kw,
    )
    return result, events


# --- the observer is optional and inert by default --------------------------


def test_no_observer_changes_nothing(space, problem) -> None:
    result = solve_recursive(
        space, problem, start="a", goal="goal", researcher=supplying, decomposer=no_decompose
    )
    assert result.report.outcome.name == "REACHED"


# --- a productive search ----------------------------------------------------


def test_a_productive_search_reports_growth_per_round(space, problem) -> None:
    result, events = collect(space, problem, supplying)
    assert result.report.outcome.name == "REACHED"

    kinds = [e.kind for e in events]
    assert kinds.count("FIBER_OPENED") == 2
    assert "RESEARCH_ROUND" in kinds
    assert kinds.count("FIBER_MATCHED") == 2

    rounds = [e for e in events if e.kind == "RESEARCH_ROUND"]
    assert all(e.growth > 0 for e in rounds), "a productive round reported no growth"
    assert all(e.round_index >= 1 for e in rounds)
    assert all(e.fiber_id and e.atom for e in rounds)


# --- the load-bearing distinction -------------------------------------------


def test_a_flat_search_is_visibly_flat_before_it_terminates(space, problem) -> None:
    """Zero growth per round, and a RESEARCH_FLAT event naming why it stopped."""

    result, events = collect(space, problem, empty, max_rounds_per_fiber=4)
    assert result.report.outcome.name == "UNREACHABLE_IN_PRINCIPLE"

    rounds = [e for e in events if e.kind == "RESEARCH_ROUND"]
    assert rounds, "no research rounds were reported"
    assert all(e.growth == 0 for e in rounds), "a fruitless round reported growth"

    flat = [e for e in events if e.kind == "RESEARCH_FLAT"]
    assert flat, "saturation was never announced"
    assert "no growth" in flat[0].detail


def test_the_trace_orders_open_before_round_before_close(space, problem) -> None:
    _, events = collect(space, problem, supplying)
    first = next(i for i, e in enumerate(events) if e.kind == "FIBER_OPENED")
    round_i = next(i for i, e in enumerate(events) if e.kind == "RESEARCH_ROUND")
    matched = next(i for i, e in enumerate(events) if e.kind == "FIBER_MATCHED")
    assert first < round_i < matched


# --- rendering --------------------------------------------------------------


def test_events_render_as_an_operator_log(space, problem) -> None:
    _, events = collect(space, problem, supplying)
    text = render_trace(events)
    assert "FIBER_OPENED" in text
    assert "RESEARCH_ROUND" in text
    assert "growth" in text
    assert len(text.splitlines()) == len(events)


def test_an_event_renders_its_own_identity(space, problem) -> None:
    _, events = collect(space, problem, supplying)
    opened = next(e for e in events if e.kind == "FIBER_OPENED")
    line = opened.render()
    assert opened.atom in line
    assert opened.fiber_id in line
    assert "parent=" in line
