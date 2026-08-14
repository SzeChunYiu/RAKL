"""Tests for the executable RAKL solving loop.

The load-bearing test is `test_obstructed_cover_is_refused_though_every_step_is_licensed`:
it is Paper I's machine-checked obstruction proposition made operational. A solver
that passed every other test here and failed that one would be exactly the unsound
navigator the paper describes.
"""

from __future__ import annotations

import pytest

from rakl.support_solver import (
    Atom,
    EpistemicCut,
    Obstruction,
    Outcome,
    SupportEdge,
    SupportStructure,
    Target,
    solve,
)


def _atoms(*names: str) -> tuple[Atom, ...]:
    return tuple(Atom(atom_id=n) for n in names)


def _linear_structure(licensed_at: int = 3) -> SupportStructure:
    return SupportStructure(
        structure_id="linear",
        atoms=_atoms("evidence", "middle", "goal"),
        edges=(
            SupportEdge("evidence", "middle", 1.0, licensed_at),
            SupportEdge("middle", "goal", 1.0, licensed_at),
        ),
    )


TAU = Target(target_id="T", qoi="q", goal_atom="goal", required_authority=3)


def test_reaches_the_goal_when_a_licensed_route_exists():
    report = solve(_linear_structure(), TAU, start="evidence")
    assert report.outcome is Outcome.REACHED
    assert report.route is not None
    assert report.route.atoms == ("evidence", "middle", "goal")
    assert report.route.total_cost == 2.0


def test_a_route_grants_no_scientific_authority():
    report = solve(_linear_structure(), TAU, start="evidence")
    assert report.grants_scientific_authority is False


def test_cheapest_route_is_selected():
    structure = SupportStructure(
        structure_id="two-routes",
        atoms=_atoms("a", "cheap", "dear", "goal"),
        edges=(
            SupportEdge("a", "cheap", 1.0, 3),
            SupportEdge("cheap", "goal", 1.0, 3),
            SupportEdge("a", "dear", 5.0, 3),
            SupportEdge("dear", "goal", 5.0, 3),
        ),
    )
    report = solve(structure, TAU, start="a")
    assert report.route is not None
    assert report.route.total_cost == 2.0
    assert "cheap" in report.route.atoms


# --- authority ---------------------------------------------------------------------


def test_underlicensed_edge_blocks_the_route_and_yields_a_cut():
    """A cheap route through weakly licensed evidence is not a route."""
    structure = _linear_structure(licensed_at=1)
    report = solve(structure, TAU, start="evidence")
    assert report.outcome is Outcome.CUT
    assert report.cut is not None
    assert report.cut.exact
    # BOTTLENECK: on a single chain, either edge alone is a set every route hits.
    assert len(report.cut.elements) == 1
    assert set(report.cut.elements) <= {"evidence->middle", "middle->goal"}


def test_bottleneck_and_repair_are_different_objects():
    """Necessary is not sufficient, and the report must not conflate them.

    On a single chain the bottleneck is any ONE under-licensed edge (every route
    passes through it), but opening the route requires BOTH. Reporting only the
    bottleneck would overstate how close the target is.
    """
    structure = _linear_structure(licensed_at=1)
    report = solve(structure, TAU, start="evidence")
    assert report.cut is not None and report.repair is not None
    assert len(report.cut.elements) == 1
    assert set(report.repair.elements) == {"evidence->middle", "middle->goal"}
    assert report.repair.cost > report.cut.cost


def test_repair_names_the_route_it_opens():
    structure = _linear_structure(licensed_at=1)
    report = solve(structure, TAU, start="evidence")
    assert report.repair.opens_route == ("evidence", "middle", "goal")


def test_repair_skips_obstructed_routes():
    """An obstruction is not repaired by licensing; it needs a different route."""
    structure = SupportStructure(
        structure_id="obstructed-only",
        atoms=_atoms("x", "y", "z", "goal"),
        edges=(
            SupportEdge("x", "y", 1.0, 0),
            SupportEdge("y", "z", 1.0, 0),
            SupportEdge("z", "goal", 1.0, 0),
        ),
        obstructions=(Obstruction("OBS", frozenset({"x", "y", "z"})),),
    )
    report = solve(structure, TAU, start="x")
    assert report.outcome is Outcome.CUT
    assert report.repair is None, "licensing must not be offered as a repair for an obstruction"


def test_a_higher_authority_target_can_fail_where_a_lower_one_succeeds():
    structure = _linear_structure(licensed_at=2)
    low = Target(target_id="lo", qoi="q", goal_atom="goal", required_authority=2)
    high = Target(target_id="hi", qoi="q", goal_atom="goal", required_authority=5)
    assert solve(structure, low, start="evidence").outcome is Outcome.REACHED
    assert solve(structure, high, start="evidence").outcome is Outcome.CUT


def test_cut_cost_reflects_the_authority_shortfall():
    structure = _linear_structure(licensed_at=1)
    report = solve(structure, TAU, start="evidence")
    assert report.repair is not None
    assert report.repair.cost == 4.0  # two edges, shortfall 2 each


# --- obstruction: the load-bearing case --------------------------------------------


def test_obstructed_cover_is_refused_though_every_step_is_licensed():
    """Paper I's proposition, operational.

    Every edge is licensed and every pairwise step is fine, but the assembled
    atom set realizes a cover with no global section. A pairwise-only navigator
    would return this route; this one must refuse it.
    """
    structure = SupportStructure(
        structure_id="parity",
        atoms=_atoms("x", "y", "z", "goal"),
        edges=(
            SupportEdge("x", "y", 1.0, 5),
            SupportEdge("y", "z", 1.0, 5),
            SupportEdge("z", "goal", 1.0, 5),
        ),
        obstructions=(
            Obstruction(
                obstruction_id="OBS-parity",
                cover=frozenset({"x", "y", "z"}),
                detail="pairwise compatible, no global section",
            ),
        ),
    )
    report = solve(structure, TAU, start="x")
    assert report.outcome is not Outcome.REACHED, "an obstructed cover was traversed"
    assert "OBS-parity" in report.blocked_by_obstruction


def test_the_same_structure_without_the_obstruction_object_is_traversed():
    """The control that makes the previous test meaningful.

    Identical structure, obstruction object removed — exactly what an
    obstruction-blind distillation would hand the navigator. It now succeeds,
    which is the unsoundness the paper proves and this solver prevents.
    """
    structure = SupportStructure(
        structure_id="parity-blind",
        atoms=_atoms("x", "y", "z", "goal"),
        edges=(
            SupportEdge("x", "y", 1.0, 5),
            SupportEdge("y", "z", 1.0, 5),
            SupportEdge("z", "goal", 1.0, 5),
        ),
        obstructions=(),
    )
    assert solve(structure, TAU, start="x").outcome is Outcome.REACHED


def test_a_route_avoiding_the_obstructed_cover_is_still_found():
    """Obstruction rejection must not degenerate into refusing everything."""
    structure = SupportStructure(
        structure_id="detour",
        atoms=_atoms("x", "y", "z", "bypass", "goal"),
        edges=(
            SupportEdge("x", "y", 1.0, 5),
            SupportEdge("y", "z", 1.0, 5),
            SupportEdge("z", "goal", 1.0, 5),
            SupportEdge("x", "bypass", 2.0, 5),
            SupportEdge("bypass", "goal", 2.0, 5),
        ),
        obstructions=(
            Obstruction(obstruction_id="OBS", cover=frozenset({"x", "y", "z"})),
        ),
    )
    report = solve(structure, TAU, start="x")
    assert report.outcome is Outcome.REACHED
    assert "bypass" in report.route.atoms
    assert "z" not in report.route.atoms


# --- failure is informative --------------------------------------------------------


def test_structurally_disconnected_goal_is_distinguished_from_a_cut():
    """'No route at any authority' is a different finding from 'not licensed'."""
    structure = SupportStructure(
        structure_id="disconnected",
        atoms=_atoms("a", "goal"),
        edges=(),
    )
    report = solve(structure, TAU, start="a")
    assert report.outcome is Outcome.UNREACHABLE_IN_PRINCIPLE
    assert report.cut is None


def test_cut_meets_every_structural_route():
    """The cut must actually be a cut — verified, not asserted."""
    structure = SupportStructure(
        structure_id="two-blocked-routes",
        atoms=_atoms("a", "p", "q", "goal"),
        edges=(
            SupportEdge("a", "p", 1.0, 0),
            SupportEdge("p", "goal", 1.0, 9),
            SupportEdge("a", "q", 1.0, 0),
            SupportEdge("q", "goal", 1.0, 9),
        ),
        obstructions=(),
    )
    report = solve(structure, TAU, start="a")
    assert report.outcome is Outcome.CUT
    chosen = set(report.cut.elements)
    for route in (("a->p", "p->goal"), ("a->q", "q->goal")):
        assert chosen & set(route), f"route {route} is not met by the cut"
    # a->p and a->q are the under-licensed pair; p->goal and q->goal are fine
    assert chosen == {"a->p", "a->q"}


def test_cut_marks_itself_inexact_when_the_search_is_bounded():
    """A cut is never silently approximated."""
    n = 16
    atoms = _atoms("a", "goal", *[f"m{i}" for i in range(n)])
    edges = []
    for i in range(n):
        edges.append(SupportEdge("a", f"m{i}", 1.0, 0))
        edges.append(SupportEdge(f"m{i}", "goal", 1.0, 9))
    structure = SupportStructure("wide", atoms, tuple(edges))
    report = solve(structure, TAU, start="a")
    assert report.outcome is Outcome.CUT
    assert report.cut.exact is False
    assert "minimality is NOT established" in report.cut.rationale


# --- finite basis ------------------------------------------------------------------


def test_structure_universe_is_finite_and_exact():
    """The finite basis is what makes bounded saturation certifiable."""
    structure = _linear_structure()
    assert structure.universe == {"evidence", "middle", "goal"}
    assert len(structure.universe) == len(structure.atoms)


# --- integrity ---------------------------------------------------------------------


def test_unknown_atoms_are_cannot_check_not_failure():
    structure = _linear_structure()
    bad = Target(target_id="T", qoi="q", goal_atom="nowhere", required_authority=3)
    assert solve(structure, bad, start="evidence").outcome is Outcome.CANNOT_CHECK
    assert solve(structure, TAU, start="nowhere").outcome is Outcome.CANNOT_CHECK


def test_structure_rejects_edges_referencing_unknown_atoms():
    with pytest.raises(ValueError, match="unknown atom"):
        SupportStructure("bad", _atoms("a"), (SupportEdge("a", "ghost", 1.0, 1),))


def test_obstruction_over_unknown_atoms_is_rejected():
    with pytest.raises(ValueError, match="covers unknown atoms"):
        SupportStructure(
            "bad", _atoms("a", "b"), (), (Obstruction("O", frozenset({"a", "ghost"})),)
        )


def test_a_single_atom_cannot_obstruct():
    with pytest.raises(ValueError, match="at least two atoms"):
        Obstruction("O", frozenset({"a"}))
