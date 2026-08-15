"""Orion end to end: licence -> search -> audit -> operator report.

Four stages, each a real module, no fixtures:

    1. governed_solve      is the knowledge state licensed for a search?
    2. solve_recursive     the search itself, with this session as researcher
    3. research_session    what pursuit action the result licenses next
    4. render_*            the whole thing, legible

Run three times against the same problem under different knowledge states, so
the difference between "refused", "stopped" and "ran" is visible rather than
asserted.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from rakl.governed_solver import SolveLicence, governed_solve, render_governed_solve  # noqa: E402
from rakl.hard_gates import (  # noqa: E402
    HardGateContract,
    HardGateObservation,
    HardGateRequirement,
    HardGateState,
)
from rakl.recursive_framework_audit import AuditCoordinate, AuditNode, AuditResidual  # noqa: E402
from rakl.research_machine_workflow import KnowledgeSaturationPolicy  # noqa: E402
from rakl.research_session import SupportDeclaration, next_step, render_step  # noqa: E402
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace  # noqa: E402
from rakl.support_solver import Atom, SupportEdge, SupportStructure  # noqa: E402


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


KNOWN = {
    "bridge": ("a", "bridge"),
    "goal": ("bridge", "goal"),
}


def researcher(fiber):
    """This session supplying structure when the solver asks for an atom."""

    edge = KNOWN.get(fiber.atom)
    print(f"      solver needs {fiber.atom!r} -> " + ("supplied" if edge else "nothing held"))
    if not edge:
        return []
    src, dst = edge
    return [reduced(f"found-{fiber.atom}", {src, dst}, edges=((src, dst, 1.0, 9),))]


def decomposer(atom):
    return None


def fresh_problem():
    space = StructureSpace("e2e")
    space.accumulate(reduced("seed", {"a"}))
    problem = ProblemStructure(
        problem_id="e2e", qoi="can a route from a to goal be licensed?",
        required_roles=frozenset({"a", "bridge", "goal"}),
    )
    return space, problem


POLICY = KnowledgeSaturationPolicy(
    required_route_families=("literature",), min_independent_flat_routes=2, window=4
)

CONTRACT = HardGateContract(
    contract_id="e2e-gates",
    requirements=(
        HardGateRequirement(
            gate_id="no_self_licensing", description="a candidate may not license itself",
            evidence_required=("ev-1",),
        ),
    ),
    frozen_before_candidate_results=True,
)


def observation(state: HardGateState) -> HardGateObservation:
    return HardGateObservation(
        gate_id="no_self_licensing", candidate_id="cand-1", state=state,
        evidence_ids=("ev-1",), detail=state.name,
    )


def run(label, **kw):
    print("=" * 78)
    print(f"RUN: {label}")
    space, problem = fresh_problem()
    report = governed_solve(
        space, problem, start="a", goal="goal",
        researcher=researcher, decomposer=decomposer,
        snapshot_id="snap-e2e", **kw,
    )
    print(render_governed_solve(report))

    # Stage 3: what does the result license us to do next?
    if report.ran and report.solve is not None:
        outcome = report.solve.report.outcome.name
        residual = (
            AuditResidual()
            if outcome == "REACHED"
            else AuditResidual(plausible_causes=(AuditCoordinate.EVIDENCE,))
        )
        support = SupportDeclaration(
            population="e2e structure space",
            predicate_in_domain=True,
            conditioning_variables=("route_family",),
            reachable_ceiling=1.0,
            ceiling_basis="a route either composes to the goal or it does not",
        )
        step = next_step(
            target_id="e2e",
            node=AuditNode(closure_coordinates_pass=(outcome == "REACHED"),
                           material_open_residual=(outcome != "REACHED")),
            residual=residual,
            support=support,
        )
        print(render_step(step))
    print()


run("stale knowledge", policy=POLICY, freshness_stale=True)
run("hard gate fails", hard_gate_contract=CONTRACT,
    hard_gate_observations=(observation(HardGateState.FAIL),), candidate_id="cand-1")
run("licensed", hard_gate_contract=CONTRACT,
    hard_gate_observations=(observation(HardGateState.PASS),), candidate_id="cand-1")
