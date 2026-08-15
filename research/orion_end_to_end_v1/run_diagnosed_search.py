"""The real search, with stage diagnostics on every run.

Three runs, one problem:
  1. live corpus, current solver           -> should pass every stage
  2. live corpus, coverage-only (pre-fix)   -> should FAIL exactly at reachability
  3. control ref before anything existed   -> should FAIL at coverage / fibres

If the diagnostic is any good, run 2 pinpoints the stage the bug lived in.
"""

from __future__ import annotations

import subprocess
import sys

sys.path.insert(0, "src")

from rakl.diagnostics import diagnose_run  # noqa: E402
from rakl.recursive_solver import SolveEvent, solve_recursive  # noqa: E402
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace  # noqa: E402
from rakl.support_solver import Atom, SupportEdge, SupportStructure  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def reduced(sid, roles, edges=(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(structure_id=sid, atoms=atoms,
                                   edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges)),
        roles=frozenset(roles), established_at=auth,
    )


SEARCHES = {
    "gate_module": ("start", ["ls-tree", "--name-only", "REF", "src/rakl/construct_independence.py"]),
    "gate_tests": ("gate_module", ["grep", "-l", "construct_independence", "REF", "--", "tests"]),
    "cluster_research": ("gate_tests", ["grep", "-il", "construct dependence", "REF", "--", "research"]),
    "frontier_source": ("cluster_research", ["grep", "-l", "negative_frontier_v1", "REF", "--",
                                             "research/self_rakl_recursive_question_audit_v1"]),
    "merged_by": ("frontier_source", ["log", "--oneline", "REF", "-Sclass ConstructObligation", "--",
                                      "src/rakl/construct_independence.py"]),
}


def make_researcher(ref, *, connect: bool):
    def r(fiber):
        if fiber.atom not in SEARCHES:
            return []
        pred, argv = SEARCHES[fiber.atom]
        out = git(*[a.replace("REF", ref) for a in argv])
        if not out:
            return []
        if connect:
            return [reduced(f"ev-{fiber.atom}", {pred, fiber.atom}, edges=((pred, fiber.atom, 1.0, 9),))]
        # pre-fix shape: role only, no inbound edge -- coverage without connectivity
        return [reduced(f"ev-{fiber.atom}", {fiber.atom})]
    return r


def no_decompose(atom):
    return None


def run(label, ref, *, connect):
    print("=" * 78)
    print(label)
    space = StructureSpace(label)
    space.accumulate(reduced("seed", {"start"}))
    problem = ProblemStructure(problem_id="prov", qoi="gate provenance",
                               required_roles=frozenset({"start", *SEARCHES}))
    events: list[SolveEvent] = []
    result = solve_recursive(space, problem, start="start", goal="merged_by",
                             researcher=make_researcher(ref, connect=connect),
                             decomposer=no_decompose, observer=events.append,
                             max_rounds_per_fiber=3)
    diag = diagnose_run(space, problem, start="start", goal="merged_by",
                        result=result, events=tuple(events), licence="LICENSED",
                        licence_reasons=("knowledge state licenses the search",))
    print(diag.render())
    print()
    return diag


d1 = run("RUN 1  live corpus, connected evidence, current solver", "origin/main", connect=True)
d2 = run("RUN 2  live corpus, coverage-only evidence (the pre-fix failure shape)", "origin/main", connect=False)
d3 = run("RUN 3  control: cf508565, before any of it existed", "cf508565", connect=True)

print("=" * 78)
print("first failing stage per run:")
print(f"  run 1: {d1.first_failing_stage}")
print(f"  run 2: {d2.first_failing_stage}")
print(f"  run 3: {d3.first_failing_stage}")
