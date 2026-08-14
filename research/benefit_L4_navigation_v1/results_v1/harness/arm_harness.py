"""Arm executor for BENEFIT-L4-NAVIGATION-V1. One process per arm (step 2 spawns
each separately) over the byte-identical gold-stripped corpus.

Arm A — budgeted raw reading, PROTOCOL.json arms.A_budgeted_raw_reading,
implemented verbatim to the frozen decision-equivalent policy in EVALUATOR.py
(read in descending lexical overlap with the target token set at COST_READ=1.0;
after each read, admissible-route check over all facts read so far — the same
connect rule as arm B).

Arm B — distil-and-navigate: distils each chosen source at COST_DISTIL=2.0 into
a growing typed rakl.support_solver.SupportStructure (Atoms, licensed
SupportEdges, explicit Obstructions) and calls the exact pinned
rakl.support_solver.solve on the partial structure against the Target contract
(module pin verified before any declaration). Outcome mapping:

  REACHED                  -> declare SOLVED with the module's route
  CUT with a MinimalRepair -> guidance = endpoints of the repair elements + goal
  CUT with repair None     -> guidance = forward frontier from start + backward
  UNREACHABLE_IN_PRINCIPLE    frontier into goal + {start, goal}

The repair-None case (every structurally existing route realizes a known
obstruction) is mapped to the frontier construction: that is the frozen
EXECUTABLE semantics (EVALUATOR.py need_atoms, enforced by the protocol's
declaration drift check); PROTOCOL.json's prose alternative ("the EpistemicCut")
would name obstruction ids, which have no endpoints and match no index tokens.
The prose/executable divergence is recorded in RUN_RECEIPT.md; the executable
rule is authoritative per the frozen drift-check clause.

Next source = max overlap between index tokens and the guidance set (ties by
target-token overlap, then source_id); the first acquisition bootstraps by
target-token overlap exactly like arm A. ALL distillation cost is charged to
arm B. NOT_SOLVED at budget exhaustion.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import verify_module_pins  # noqa: E402

from rakl.support_solver import (  # noqa: E402
    Atom,
    Obstruction,
    Outcome,
    SupportEdge,
    SupportStructure,
    Target,
    solve,
)

COST_READ = 1.0
COST_DISTIL = 2.0


def _target_tokens(row: dict[str, Any]) -> set[str]:
    target = row["target"]
    return set(target.get("description_tokens") or ()) | {
        target["start_atom"], target["goal_atom"]}


def arm_a_declare(row: dict[str, Any]) -> dict[str, Any]:
    target = row["target"]
    tokens = _target_tokens(row)
    order = sorted(
        row["sources"],
        key=lambda s: (-len(tokens & set(s["index_tokens"])), s["source_id"]),
    )
    edges: list[dict[str, Any]] = []
    obstructions: list[dict[str, Any]] = []
    spent = 0.0
    for source in order:
        if spent + COST_READ > row["budget_units"]:
            break
        spent += COST_READ
        edges.extend(source["edges"])
        obstructions.extend(source.get("obstructions") or ())
        route = _connect(edges, obstructions, target)
        if route is not None:
            return {"world_id": row["world_id"], "declaration": "SOLVED",
                    "route": route, "budget_spent": spent}
    return {"world_id": row["world_id"], "declaration": "NOT_SOLVED",
            "route": None, "budget_spent": spent}


def _structure(edges: list[dict[str, Any]], obstructions: list[dict[str, Any]],
               target: dict[str, Any]) -> SupportStructure:
    atom_ids = {target["start_atom"], target["goal_atom"]}
    for e in edges:
        atom_ids.add(e["source"])
        atom_ids.add(e["target"])
    for o in obstructions:
        atom_ids.update(o["cover"])
    # canonical edge order (source, target, cost): keeps the module's route
    # enumeration aligned with the frozen replica's sorted-adjacency order
    dedup = sorted(
        {(e["source"], e["target"], e["cost"], e["licensed_at"]) for e in edges})
    return SupportStructure(
        structure_id="partial",
        atoms=tuple(Atom(a) for a in sorted(atom_ids)),
        edges=tuple(SupportEdge(s, t, c, lic) for s, t, c, lic in dedup),
        obstructions=tuple(
            Obstruction(o["obstruction_id"], frozenset(o["cover"]),
                        o.get("detail", ""))
            for o in obstructions),
    )


def _connect(edges: list[dict[str, Any]], obstructions: list[dict[str, Any]],
             target: dict[str, Any]) -> list[str] | None:
    """Shared connect rule, realized through the pinned module for both arms:
    admissible-route check = support_solver.solve REACHED on the assembled facts."""
    structure = _structure(edges, obstructions, target)
    report = solve(
        structure,
        Target(target_id="tau", qoi="route", goal_atom=target["goal_atom"],
               required_authority=target["required_authority"]),
        start=target["start_atom"],
    )
    if report.outcome is Outcome.REACHED and report.route is not None:
        return list(report.route.atoms)
    return None


def _frontier(edges: list[dict[str, Any]], start: str, goal: str) -> set[str]:
    forward: set[str] = {start}
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge["source"] in forward and edge["target"] not in forward:
                forward.add(edge["target"])
                changed = True
    backward: set[str] = {goal}
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge["target"] in backward and edge["source"] not in backward:
                backward.add(edge["source"])
                changed = True
    return forward | backward | {start, goal}


def arm_b_declare(row: dict[str, Any]) -> dict[str, Any]:
    target = row["target"]
    tokens = _target_tokens(row)
    edges: list[dict[str, Any]] = []
    obstructions: list[dict[str, Any]] = []
    spent = 0.0
    remaining = sorted(row["sources"], key=lambda s: s["source_id"])
    guidance: set[str] | None = None
    outcomes: list[str] = []
    while remaining and spent + COST_DISTIL <= row["budget_units"]:
        if guidance is None:  # first acquisition: lexical bootstrap, like arm A
            choice = min(remaining,
                         key=lambda s: (-len(tokens & set(s["index_tokens"])),
                                        s["source_id"]))
        else:
            need = guidance
            choice = min(
                remaining,
                key=lambda s: (-len(need & set(s["index_tokens"])),
                               -len(tokens & set(s["index_tokens"])),
                               s["source_id"]),
            )
        remaining.remove(choice)
        spent += COST_DISTIL
        edges.extend(choice["edges"])
        obstructions.extend(choice.get("obstructions") or ())

        structure = _structure(edges, obstructions, target)
        report = solve(
            structure,
            Target(target_id="tau", qoi="route", goal_atom=target["goal_atom"],
                   required_authority=target["required_authority"]),
            start=target["start_atom"],
        )
        outcomes.append(report.outcome.value)
        if report.outcome is Outcome.REACHED and report.route is not None:
            return {"world_id": row["world_id"], "declaration": "SOLVED",
                    "route": list(report.route.atoms), "budget_spent": spent,
                    "solver_outcomes": outcomes}
        if report.outcome is Outcome.CUT and report.repair is not None:
            endpoints: set[str] = set()
            for element in report.repair.elements:
                src, _, dst = element.partition("->")
                endpoints.update((src, dst))
            guidance = set(sorted(endpoints | {target["goal_atom"]}))
        else:
            guidance = _frontier(edges, target["start_atom"], target["goal_atom"])
    return {"world_id": row["world_id"], "declaration": "NOT_SOLVED",
            "route": None, "budget_spent": spent, "solver_outcomes": outcomes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("A", "B"))
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    verify_module_pins()
    with open(args.corpus, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["worlds"]
    for row in rows:
        if "gold_label" in row or "minimal_source_count" in row or "class" in row:
            print("REFUSING: arm input contains gold/S*/class fields", file=sys.stderr)
            return 2

    declare = arm_a_declare if args.arm == "A" else arm_b_declare
    t0 = time.monotonic()
    declarations = [declare(row) for row in sorted(rows, key=lambda r: r["world_id"])]
    elapsed = time.monotonic() - t0
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    payload = {
        "protocol_id": "BENEFIT-L4-NAVIGATION-V1",
        "arm": args.arm,
        "declarations": declarations,
        "n_declared_solved": sum(1 for d in declarations if d["declaration"] == "SOLVED"),
        "wall_clock_seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "token_budget_used": 0,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
