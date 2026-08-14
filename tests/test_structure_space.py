"""Tests for the end-to-end loop: reduce → accumulate → saturate → match → compose.

Two tests carry most of the weight:

* `test_matching_fails_closed_on_a_disjoint_structure` — the direct guard against
  the fail-open defect found in `assess_transfer_v2` on 2026-08-14, which returned
  LICENSED with zero reasons for structures sharing nothing.
* `test_composition_carries_obstructions_forward` — a composition can realize a
  cover no contributing structure realized alone. Dropping obstructions at the
  glue step would reintroduce exactly the unsoundness Paper I proves.
"""

from __future__ import annotations

import pytest

from rakl.structure_space import (
    MatchVerdict,
    ProblemStructure,
    ReducedStructure,
    SpaceSaturation,
    StructureSpace,
    compose,
    match,
    reduce_all,
    solve_problem,
    unmatched_roles,
)
from rakl.support_solver import (
    Atom,
    Obstruction,
    Outcome,
    SupportEdge,
    SupportStructure,
)


def _reduced(sid, roles, *, edges=(), obstructions=(), relations=frozenset(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=sid,
            atoms=atoms,
            edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges),
            obstructions=obstructions,
        ),
        roles=frozenset(roles),
        relations=relations,
        established_at=auth,
    )


# --- accumulation and saturation ---------------------------------------------------


def test_growth_counts_new_roles_not_structures():
    """Restating a known shape is representation growth, not epistemic growth."""
    space = StructureSpace("s")
    assert space.accumulate(_reduced("A", {"x", "y"})) == 2
    assert space.accumulate(_reduced("B", {"x", "y"})) == 0
    assert space.accumulate(_reduced("C", {"z"})) == 1
    assert space.growth_per_round == [2, 0, 1]


def test_space_saturates_only_after_consecutive_flat_rounds():
    """One flat round is not enough — the tail must be flat, not just the last entry."""
    space = StructureSpace("s")
    space.accumulate(_reduced("A", {"x"}))          # growth 1
    assert space.saturation() is SpaceSaturation.OPEN
    space.accumulate(_reduced("B", {"x"}))          # growth 0, but tail is [1, 0]
    assert space.saturation() is SpaceSaturation.OPEN
    space.accumulate(_reduced("C", {"x"}))          # tail now [0, 0]
    assert space.saturation() is SpaceSaturation.BOUNDED_SATURATED


def test_new_material_reopens_a_saturated_space():
    space = StructureSpace("s")
    for sid in ("A", "B", "C"):
        space.accumulate(_reduced(sid, {"x"}))
    assert space.saturation() is SpaceSaturation.BOUNDED_SATURATED
    space.accumulate(_reduced("D", {"brand-new"}))
    assert space.saturation() is SpaceSaturation.OPEN


def test_reduce_all_applies_the_operator_across_sources():
    space = StructureSpace("s")
    reduce_all(lambda src: _reduced(src, {src}), ["p", "q", "r"], space)
    assert space.universe == {"p", "q", "r"}


# --- matching fails closed ---------------------------------------------------------


def test_matching_fails_closed_on_a_disjoint_structure():
    """The guard against the assess_transfer_v2 fail-open defect.

    A structure sharing no role with the problem must be REJECTED with a reason,
    never licensed by the absence of an objection.
    """
    space = StructureSpace("s")
    space.accumulate(_reduced("unrelated", {"finance", "volatility"}))
    problem = ProblemStructure("P", "q", frozenset({"physics", "momentum"}))
    result = match(space, problem)[0]
    assert result.verdict is MatchVerdict.REJECTED
    assert "covers no required role" in result.reasons


def test_a_genuinely_applicable_structure_is_licensed():
    """No-alarm case: fail-closed must not mean refuse-everything."""
    space = StructureSpace("s")
    space.accumulate(_reduced("apt", {"physics", "momentum"}))
    problem = ProblemStructure("P", "q", frozenset({"physics", "momentum"}))
    result = match(space, problem)[0]
    assert result.verdict is MatchVerdict.LICENSED
    assert result.covered_roles == {"physics", "momentum"}


def test_underauthorized_structure_is_rejected():
    space = StructureSpace("s")
    space.accumulate(_reduced("weak", {"physics"}, auth=1))
    problem = ProblemStructure("P", "q", frozenset({"physics"}), required_authority=4)
    result = match(space, problem)[0]
    assert result.verdict is MatchVerdict.REJECTED
    assert any("requires 4" in r for r in result.reasons)


def test_relation_claimed_without_both_roles_is_a_defect():
    space = StructureSpace("s")
    space.accumulate(
        _reduced("dangling", {"a"}, relations=frozenset({("a", "b")}))
    )
    problem = ProblemStructure(
        "P", "q", frozenset({"a"}), required_relations=frozenset({("a", "b")})
    )
    result = match(space, problem)[0]
    assert result.verdict is MatchVerdict.REJECTED
    assert any("without both roles" in r for r in result.reasons)


def test_empty_problem_decomposition_is_rejected_at_construction():
    """A decomposition constraining nothing would license everything."""
    with pytest.raises(ValueError, match="license every candidate"):
        ProblemStructure("P", "q", frozenset())


def test_unmatched_roles_name_what_the_space_lacks():
    space = StructureSpace("s")
    space.accumulate(_reduced("partial", {"physics"}))
    problem = ProblemStructure("P", "q", frozenset({"physics", "chemistry"}))
    assert unmatched_roles(space, problem) == {"chemistry"}


def test_matches_are_ranked_by_coverage():
    space = StructureSpace("s")
    space.accumulate(_reduced("thin", {"a"}))
    space.accumulate(_reduced("thick", {"a", "b", "c"}))
    problem = ProblemStructure("P", "q", frozenset({"a", "b", "c"}))
    assert match(space, problem)[0].structure_id == "thick"


# --- composition -------------------------------------------------------------------


def test_composition_carries_obstructions_forward():
    """A composition can realize a cover no contributor realized alone.

    Structure A supplies x,y; structure B supplies z. NEITHER CAN DECLARE the
    obstructed cover {x,y,z}, because a structure may not name a cover it does not
    contain — so it lives at the space level. Composed, the cover materializes.

    This is the dangerous case: an incompatibility that appears only when two
    independently sound structures are put together. Dropping it at the glue step
    is precisely the unsoundness Paper I proves.
    """
    space = StructureSpace("s")
    # A supplies x,y; B supplies z and the goal. Neither contains the cover {x,y,z},
    # so neither COULD declare the obstruction -- it lives at the space level.
    space.accumulate(_reduced("A", {"x", "y"}, edges=(("x", "y", 1.0, 9),)))
    space.accumulate(
        _reduced("B", {"z", "goal"}, edges=(("y", "z", 1.0, 9), ("z", "goal", 1.0, 9)))
    )
    space.cross_structure_obstructions.append(
        Obstruction("OBS", frozenset({"x", "y", "z"}),
                    detail="materializes only once A and B are composed")
    )
    problem = ProblemStructure("P", "q", frozenset({"x", "y", "z", "goal"}))
    composed = compose(space, problem, start="x", goal="goal")
    assert any(o.obstruction_id == "OBS" for o in composed.obstructions)

    report = solve_problem(space, problem, start="x", goal="goal")
    assert report.outcome is not Outcome.REACHED
    assert "OBS" in report.blocked_by_obstruction


def test_rejected_structures_do_not_contribute_to_the_composition():
    """A rejected match must not smuggle its edges into the composed structure."""
    space = StructureSpace("s")
    space.accumulate(_reduced("apt", {"a", "goal"}, edges=(("a", "goal", 1.0, 9),)))
    space.accumulate(_reduced("alien", {"zzz"}, edges=(("zzz", "goal", 0.1, 9),)))
    problem = ProblemStructure("P", "q", frozenset({"a", "goal"}))
    composed = compose(space, problem, start="a", goal="goal")
    assert all("zzz" not in (e.source, e.target) for e in composed.edges)


def test_end_to_end_solve_reaches_the_goal():
    """reduce → accumulate → match → compose → navigate, all the way through."""
    space = StructureSpace("s")
    space.accumulate(_reduced("first", {"evidence", "middle"},
                              edges=(("evidence", "middle", 1.0, 9),)))
    space.accumulate(_reduced("second", {"middle", "goal"},
                              edges=(("middle", "goal", 1.0, 9),)))
    problem = ProblemStructure("P", "q", frozenset({"evidence", "middle", "goal"}))
    report = solve_problem(space, problem, start="evidence", goal="goal")
    assert report.outcome is Outcome.REACHED
    assert report.route.atoms == ("evidence", "middle", "goal")


def test_end_to_end_failure_returns_a_cut_not_just_no():
    """When the composed space cannot reach the goal, say what would open it.

    The structure is established highly enough to be LICENSED for matching, but
    its edge is licensed below what the problem demands — so the route exists
    structurally and is inadmissible. That must yield a cut and a repair, not a
    bare refusal.
    """
    space = StructureSpace("s")
    space.accumulate(
        _reduced("weak-edge", {"evidence", "goal"},
                 edges=(("evidence", "goal", 1.0, 1),), auth=9)
    )
    problem = ProblemStructure(
        "P", "q", frozenset({"evidence", "goal"}), required_authority=4
    )
    report = solve_problem(space, problem, start="evidence", goal="goal")
    assert report.outcome is Outcome.CUT
    assert report.cut is not None and report.cut.elements == ("evidence->goal",)
    assert report.repair is not None
    assert report.repair.cost == 3.0  # shortfall 4 - 1
    assert report.repair.opens_route == ("evidence", "goal")


def test_composition_grants_no_authority():
    space = StructureSpace("s")
    space.accumulate(_reduced("a", {"x", "goal"}, edges=(("x", "goal", 1.0, 9),)))
    problem = ProblemStructure("P", "q", frozenset({"x", "goal"}))
    report = solve_problem(space, problem, start="x", goal="goal")
    assert report.grants_scientific_authority is False


def test_cross_structure_obstruction_has_a_home_at_the_space_level():
    """A cover spanning contributors cannot be declared by any of them."""
    with pytest.raises(ValueError, match="covers unknown atoms"):
        SupportStructure(
            "partial", (Atom(atom_id="x"), Atom(atom_id="y")), (),
            (Obstruction("OBS", frozenset({"x", "y", "z"})),),
        )
    space = StructureSpace("s")
    space.cross_structure_obstructions.append(
        Obstruction("OBS", frozenset({"x", "y", "z"}))
    )
    assert space.cross_structure_obstructions[0].obstruction_id == "OBS"


def test_cross_structure_obstruction_is_dropped_when_the_cover_is_not_realized():
    """It must only bind when the composition actually realizes the cover."""
    space = StructureSpace("s")
    space.accumulate(_reduced("A", {"x", "goal"}, edges=(("x", "goal", 1.0, 9),)))
    space.cross_structure_obstructions.append(
        Obstruction("OBS-elsewhere", frozenset({"p", "q"}))
    )
    problem = ProblemStructure("P", "q", frozenset({"x", "goal"}))
    composed = compose(space, problem, start="x", goal="goal")
    assert composed.obstructions == ()
    assert solve_problem(space, problem, start="x", goal="goal").outcome is Outcome.REACHED
