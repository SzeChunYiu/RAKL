"""Watch the solver work: every fibre, every round, every state change."""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from rakl.recursive_solver import SolveEvent, render_trace, solve_recursive  # noqa: E402
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace  # noqa: E402
from rakl.support_solver import Atom, SupportEdge, SupportStructure  # noqa: E402


def reduced(sid, roles, *, edges=(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=sid, atoms=atoms,
            edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges),
        ),
        roles=frozenset(roles), established_at=auth,
    )


EVENTS: list[SolveEvent] = []


def observer(event: SolveEvent) -> None:
    EVENTS.append(event)
    print(event.render())


# --- scenario A: information is available, the search closes ---------------
SUPPLY = {"bridge": ("a", "bridge"), "goal": ("bridge", "goal")}


def researcher(fiber):
    edge = SUPPLY.get(fiber.atom)
    if not edge:
        return []
    return [reduced(f"f-{fiber.atom}", {edge[0], edge[1]}, edges=((edge[0], edge[1], 1.0, 9),))]


def no_decompose(atom):
    return None


print("=" * 78)
print("SCENARIO A — information available")
print("=" * 78)
space = StructureSpace("A")
space.accumulate(reduced("seed", {"a"}))
problem = ProblemStructure(problem_id="A", qoi="a -> goal",
                           required_roles=frozenset({"a", "bridge", "goal"}))
res = solve_recursive(space, problem, start="a", goal="goal",
                      researcher=researcher, decomposer=no_decompose, observer=observer)
print(f"\noutcome {res.report.outcome.name}  rounds {res.research_rounds_spent}  events {len(EVENTS)}")

# --- scenario B: the researcher holds nothing -------------------------------
print()
print("=" * 78)
print("SCENARIO B — researcher holds nothing (watch it saturate)")
print("=" * 78)
EVENTS.clear()


def empty_researcher(fiber):
    return []


space_b = StructureSpace("B")
space_b.accumulate(reduced("seed", {"a"}))
res_b = solve_recursive(space_b, problem, start="a", goal="goal",
                        researcher=empty_researcher, decomposer=no_decompose,
                        observer=observer, max_rounds_per_fiber=4)
print(f"\noutcome {res_b.report.outcome.name}  rounds {res_b.research_rounds_spent}  events {len(EVENTS)}")
for f in res_b.fibers:
    print(f"   fiber {f.atom}: {f.state.name}  attempts={len(f.failed_attempts)}")
