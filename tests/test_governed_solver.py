"""E9 — the solver refuses to run on an unlicensed knowledge state.

The fibre's falsifier, verbatim:

    solver runs on an unlicensed/stale knowledge state, or search continues
    after valid bounded saturation without reason

Each test below is one half of that sentence. The load-bearing property is that
every refusal happens *before* `solve_recursive` is called — a search that runs
and is then discarded has already spent the effort whose attribution is in doubt.
"""

from __future__ import annotations

import pytest

from rakl.governed_solver import (
    GovernedSolveReport,
    SolveLicence,
    governed_solve,
    render_governed_solve,
)
from rakl.hard_gates import HardGateContract, HardGateObservation, HardGateRequirement, HardGateState
from rakl.research_machine_workflow import KnowledgeSaturationPolicy
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace
from rakl.support_solver import Atom, SupportEdge, SupportStructure


def reduced(sid, roles, *, edges=(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=sid,
            atoms=atoms,
            edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges),
        ),
        roles=frozenset(roles),
        established_at=auth,
    )


CALLED: list[str] = []


def spy_researcher(fiber):
    CALLED.append(fiber.atom)
    return []


def no_decompose(atom):
    return None


@pytest.fixture(autouse=True)
def _reset():
    CALLED.clear()


@pytest.fixture()
def world():
    space = StructureSpace("s")
    space.accumulate(reduced("seed", {"a"}))
    problem = ProblemStructure(
        problem_id="P", qoi="q", required_roles=frozenset({"a", "goal"})
    )
    return space, problem


def run(world, **kw) -> GovernedSolveReport:
    space, problem = world
    return governed_solve(
        space,
        problem,
        start="a",
        goal="goal",
        researcher=spy_researcher,
        decomposer=no_decompose,
        **kw,
    )


def _contract() -> HardGateContract:
    return HardGateContract(
        contract_id="c1",
        requirements=(
            HardGateRequirement(
                gate_id="g1", description="must hold", evidence_required=("ev-1",)
            ),
        ),
        frozen_before_candidate_results=True,
    )


def _observation(state: HardGateState, detail: str) -> HardGateObservation:
    return HardGateObservation(
        gate_id="g1",
        candidate_id="cand-1",
        state=state,
        evidence_ids=("ev-1",),
        detail=detail,
    )


POLICY = KnowledgeSaturationPolicy(
    required_route_families=("f1",), min_independent_flat_routes=2, window=4
)


# --- half one: never run on an unlicensed or stale state --------------------


def test_stale_knowledge_refuses_before_the_search_runs(world) -> None:
    report = run(world, policy=POLICY, freshness_stale=True)
    assert report.licence is SolveLicence.REFUSED_STALE_KNOWLEDGE
    assert report.ran is False
    assert CALLED == [], "the searcher was consulted despite a stale knowledge state"
    assert "stale" in " ".join(report.reasons)


def test_an_active_residual_refuses_before_the_search_runs(world) -> None:
    report = run(world, policy=POLICY, active_knowledge_residual_ids=("r1",))
    assert report.licence is SolveLicence.REFUSED_ACTIVE_RESIDUAL
    assert report.ran is False
    assert CALLED == []


def test_a_failed_hard_gate_refuses_before_the_search_runs(world) -> None:
    contract = _contract()
    observation = _observation(HardGateState.FAIL, "did not hold")
    report = run(
        world,
        hard_gate_contract=contract,
        hard_gate_observations=(observation,),
        candidate_id="cand-1",
    )
    assert report.licence is SolveLicence.REFUSED_HARD_GATE
    assert report.ran is False
    assert CALLED == []


def test_an_uncheckable_hard_gate_is_not_a_pass(world) -> None:
    contract = _contract()
    observation = _observation(HardGateState.CANNOT_CHECK, "no evidence")
    report = run(
        world,
        hard_gate_contract=contract,
        hard_gate_observations=(observation,),
        candidate_id="cand-1",
    )
    assert report.licence is SolveLicence.REFUSED_HARD_GATE
    assert "unrun gate is not a pass" in " ".join(report.reasons)


def test_staleness_is_checked_before_the_gates(world) -> None:
    """Ordering matters: a stale state is refused even if every gate passes."""

    contract = _contract()
    observation = _observation(HardGateState.PASS, "held")
    report = run(
        world,
        policy=POLICY,
        freshness_stale=True,
        hard_gate_contract=contract,
        hard_gate_observations=(observation,),
        candidate_id="cand-1",
    )
    assert report.licence is SolveLicence.REFUSED_STALE_KNOWLEDGE


# --- the licensed path ------------------------------------------------------


def test_a_licensed_state_runs_the_search(world) -> None:
    report = run(world)
    assert report.licence is SolveLicence.LICENSED
    assert report.ran is True
    assert report.solve is not None
    assert CALLED, "the searcher was never consulted on a licensed state"


def test_the_licence_travels_with_the_result(world) -> None:
    report = run(world, snapshot_id="snap-7")
    assert report.snapshot_id == "snap-7"
    assert "licenses the search" in " ".join(report.reasons)


def test_nothing_here_grants_authority(world) -> None:
    report = run(world)
    assert report.grants_scientific_authority is False
    assert report.grants_method_promotion_authority is False


# --- operator surface -------------------------------------------------------


def test_a_refusal_renders_its_reason(world) -> None:
    text = render_governed_solve(run(world, policy=POLICY, freshness_stale=True))
    assert "REFUSED_STALE_KNOWLEDGE" in text
    assert "stale" in text
    assert "search did not run" in text


def test_a_licensed_run_renders_its_outcome(world) -> None:
    text = render_governed_solve(run(world))
    assert "LICENSED" in text
    assert "outcome" in text
