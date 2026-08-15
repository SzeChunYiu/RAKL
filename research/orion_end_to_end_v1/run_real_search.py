"""A real search, second attempt: the researcher supplies *connected* evidence.

The first attempt matched all five atoms and still returned UNREACHABLE. That
was diagnosed, not guessed:

    _atom_is_supplied() is a COVERAGE predicate — "some licensed structure
    covers this role". The final verdict from solve_problem is a ROUTE predicate
    — "a connected chain reaches the goal". A role can be covered by a structure
    that is not connected to the path, so a fibre closes as MATCHED without its
    inbound edge ever being supplied.

    Concretely: the researcher for `gate_tests` never ran, because an earlier
    structure carried `gate_tests` as a role. Its inbound edge
    gate_module -> gate_tests was therefore never added, and the chain broke.

Fix on the research side: each finding supplies the edge *into* the atom AND the
atom's role, so coverage and connectivity are established together. The solver
semantics gap is recorded separately as a mechanic finding.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "src")

from rakl.recursive_solver import SolveEvent, solve_recursive  # noqa: E402
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace  # noqa: E402
from rakl.support_solver import Atom, SupportEdge, SupportStructure  # noqa: E402

OUT = Path("research/orion_end_to_end_v1/REAL_SEARCH_RESULT.json")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def reduced(sid, roles, edges=(), auth=5):
    atoms = tuple(Atom(atom_id=r) for r in sorted({*roles, *[e for edge in edges for e in edge[:2]]}))
    return ReducedStructure(
        structure=SupportStructure(structure_id=sid, atoms=atoms,
                                   edges=tuple(SupportEdge(a, b, c, l) for a, b, c, l in edges)),
        roles=frozenset(roles), established_at=auth,
    )


# Each atom: (predecessor, search command as argv, human-readable command)
SEARCHES = {
    "gate_module": ("start",
                    ["ls-tree", "--name-only", "origin/main", "src/rakl/construct_independence.py"],
                    "git ls-tree origin/main src/rakl/construct_independence.py"),
    "gate_tests": ("gate_module",
                   ["grep", "-l", "construct_independence", "origin/main", "--", "tests"],
                   "git grep -l construct_independence origin/main -- tests"),
    "cluster_research": ("gate_tests",
                         ["grep", "-il", "construct dependence", "origin/main", "--", "research"],
                         "git grep -il 'construct dependence' origin/main -- research"),
    "frontier_source": ("cluster_research",
                        ["grep", "-l", "negative_frontier_v1", "origin/main", "--",
                         "research/self_rakl_recursive_question_audit_v1"],
                        "git grep -l negative_frontier_v1 origin/main -- research/self_rakl_recursive_question_audit_v1"),
    "merged_by": ("frontier_source",
                  ["log", "--oneline", "origin/main", "-Sclass ConstructObligation", "--",
                   "src/rakl/construct_independence.py"],
                  "git log --oneline origin/main -S'class ConstructObligation' -- src/rakl/construct_independence.py"),
}

FINDINGS: list[dict] = []
TRACE: list[str] = []


def make_researcher(ref_override: str | None = None):
    def researcher(fiber):
        atom = fiber.atom
        if atom not in SEARCHES:
            return []
        pred, argv, shown = SEARCHES[atom]
        if ref_override:
            argv = [a.replace("origin/main", ref_override) for a in argv]
            shown = shown.replace("origin/main", ref_override)
        out = git(*argv)
        found = bool(out)
        FINDINGS.append({"atom": atom, "cmd": shown, "found": found, "output": out[:400]})
        line = f"   solver asks {atom:<18} [{'FOUND' if found else 'none '}] {shown}"
        print(line)
        TRACE.append(line)
        for l in out.splitlines()[:2]:
            print(f"                                     {l[:90]}")
        if not found:
            return []
        # Supply the edge INTO this atom from its predecessor, plus the atom's role.
        # This is what the first attempt got wrong: coverage without connectivity.
        return [reduced(f"ev-{atom}", {pred, atom}, edges=((pred, atom, 1.0, 9),))]
    return researcher


def observer(event: SolveEvent) -> None:
    if event.kind in {"FIBER_MATCHED", "RESEARCH_FLAT"}:
        print("   " + event.render().strip())


def no_decompose(atom):
    return None


def run(label: str, ref: str | None):
    print("=" * 78)
    print(f"{label}")
    print("=" * 78)
    FINDINGS.clear()
    TRACE.clear()
    space = StructureSpace(label)
    space.accumulate(reduced("seed", {"start"}))
    problem = ProblemStructure(
        problem_id="gate-provenance",
        qoi="evidenced route from the construct gate back to the frontier that motivated it",
        required_roles=frozenset({"start", *SEARCHES}),
    )
    result = solve_recursive(space, problem, start="start", goal="merged_by",
                             researcher=make_researcher(ref), decomposer=no_decompose,
                             observer=observer, max_rounds_per_fiber=3)
    print()
    print(f"outcome  : {result.report.outcome.name}")
    if result.report.route is not None:
        print(f"route    : {' -> '.join(result.report.route.atoms)}")
    for f in result.fibers:
        print(f"    {f.atom:<18} {f.state.name}")
    print(f"searches : {len(FINDINGS)}  found={sum(1 for f in FINDINGS if f['found'])}")
    return {
        "label": label,
        "ref": ref or "origin/main",
        "outcome": result.report.outcome.name,
        "route": list(result.report.route.atoms) if result.report.route else None,
        "fibers": {f.atom: f.state.name for f in result.fibers},
        "research_rounds": result.research_rounds_spent,
        "findings": list(FINDINGS),
    }


live = run("LIVE: search origin/main with git", None)
print()
control = run("CONTROL: same search against cf508565, before the gate existed", "cf508565")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "schema_version": "rakl-orion-real-search-v1",
    "status": "REAL_SEARCH__RESEARCHER_DID_NOT_KNOW_THE_ANSWERS",
    "grants_scientific_authority": False,
    "question": "can the solver, with a researcher that actually searches, establish an evidenced provenance route?",
    "corpus": "this repository, queried live with git ls-tree / git grep / git log -S",
    "live": live,
    "control": control,
    "mechanic_finding": {
        "id": "COVERAGE_IS_NOT_REACHABILITY",
        "where": "src/rakl/recursive_solver.py::_atom_is_supplied",
        "what": (
            "_atom_is_supplied checks whether some licensed structure covers the role. The final "
            "verdict from solve_problem requires a connected route. A role can be covered by a "
            "structure not connected to the path, so a fibre closes MATCHED without its inbound "
            "edge ever being researched. First attempt: all five fibres MATCHED, outcome "
            "UNREACHABLE_IN_PRINCIPLE, because gate_tests was 'already supplied' as a role and "
            "its researcher never ran."
        ),
        "consequence": (
            "the fibre loop can declare success on every atom while the composed structure has "
            "no route. This is not a bug in solve_problem, which is correct; it is a mismatch "
            "between the predicate the fibre loop closes on and the predicate the verdict needs."
        ),
        "worked_around_here": "the researcher supplies the inbound edge with every finding",
        "not_fixed_in_the_solver": "changing _atom_is_supplied changes frozen behaviour; recorded for a governed change",
    },
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"\nwrote {OUT}")
