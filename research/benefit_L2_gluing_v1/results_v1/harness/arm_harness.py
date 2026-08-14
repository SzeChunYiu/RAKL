"""Arm executor for BENEFIT-L2-GLUING-V1. One process per arm (step 2 spawns
each separately) over the byte-identical gold-stripped corpus.

Arm A — pairwise-only compatibility, PROTOCOL.json arms.A_pairwise_only_compatibility,
implemented verbatim to the frozen decision-equivalent rule in EVALUATOR.py
(GLUE iff every overlap transition passes its pairwise checks with a complete
pairwise record; cycle witnesses, topology and constraint tables are present in
the input record and deliberately ignored — the PairwiseRealizable record of the
Lean construction).

Arm B — obstruction-retaining gluing: encodes each atlas as a
rakl.atlas_gluing.AtlasGluingTrial and calls evaluate_atlas_gluing — the exact
function pinned in PROTOCOL.json (repaired declared-topology semantics; module
pin verified before any declaration). GLUE iff the verdict is
GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY or GLOBAL_EXISTS_UNIQUENESS_UNPROVEN; every
other verdict maps to REFUSE (fail-closed) with the sub-verdict retained for the
per-class read.

Arm B computes its own inputs from the rendered record, never from gold:
- cover topology (connectivity, cycle count) recomputed from the transition set
  with the same multigraph semantics the repaired module uses; declared
  truthfully to the trial (a dishonest declaration would be refuted by the
  module's own recomputation as declared_topology_mismatch);
- cycle-witness composition_consistent = the arm's own holonomy computation:
  exact joint satisfiability of the cycle-path charts' rendered constraint
  tables (composing the overlap identifications around the loop closes iff the
  cycle charts admit a joint assignment);
- global_exists = exhaustive assignment search over ALL rendered constraint
  tables (<= 6 binary variables, <= 64 assignments); uniqueness is recorded as
  unchecked (the gold label concerns existence; PROTOCOL spec_binding).

Encoding notes (record -> AtlasGluingTrial), chosen so each frozen check maps
1:1 onto a module check: transition_map_passed carries the record's
pairwise_pass; a transition with fields_complete_pairwise != True gets empty
evidence_ids so the module fails closed on exactly that transition; witness
evidence_ids come from the record (the G6-sensitive field); all other trial
bookkeeping (layers, contexts, regimes, chronology flags) is constant
frozen-generator declaration.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import resource
import sys
import time
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from rakl.atlas_gluing import (  # noqa: E402
    AtlasChart,
    AtlasGluingTrial,
    AtlasGluingVerdict,
    CycleConsistencyWitness,
    GluingLayer,
    OverlapTransition,
    evaluate_atlas_gluing,
)
from rakl.generator_transport import AbstractionLevel  # noqa: E402

GLUE_VERDICTS = (
    AtlasGluingVerdict.GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY,
    AtlasGluingVerdict.GLOBAL_EXISTS_UNIQUENESS_UNPROVEN,
)


def arm_a_declare(row: dict[str, Any]) -> dict[str, Any]:
    """Verbatim frozen rule: pairwise transition record only."""
    for t in row["transitions"]:
        if t.get("fields_complete_pairwise") is not True:
            return {"atlas_id": row["atlas_id"], "declaration": "REFUSE",
                    "sub_verdict": "PAIRWISE_RECORD_INCOMPLETE"}
        if t.get("pairwise_pass") is not True:
            return {"atlas_id": row["atlas_id"], "declaration": "REFUSE",
                    "sub_verdict": "PAIRWISE_FAIL"}
    return {"atlas_id": row["atlas_id"], "declaration": "GLUE"}


def _topology(charts: list[str], transitions: list[dict[str, Any]]) -> dict[str, Any]:
    """Multigraph cover topology; same semantics as the repaired module (one
    edge per distinct unordered chart pair + overlap_id)."""
    edges = sorted({
        (*sorted((t["left_chart"], t["right_chart"])), t["overlap_id"])
        for t in transitions
    })
    pair_counts: dict[tuple[str, str], int] = {}
    for a, b, _ in edges:
        pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    parent = {c: c for c in charts}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, _ in edges:
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    components = len({find(c) for c in charts})
    return {
        "connected": components == 1,
        "cycles": len(edges) - len(charts) + components,
        "has_parallel": any(v > 1 for v in pair_counts.values()),
    }


def _satisfiable(variables: list[str], constraint_tables: dict[str, Any]) -> bool:
    """Exact exhaustive global-section search over binary variables."""
    tables = []
    for chart_id in sorted(constraint_tables):
        entry = constraint_tables[chart_id]
        tables.append((entry["variables"], {tuple(a) for a in entry["allowed"]}))
    for assignment in itertools.product([0, 1], repeat=len(variables)):
        values = dict(zip(variables, assignment))
        if all(tuple(values[v] for v in chart_vars) in allowed
               for chart_vars, allowed in tables):
            return True
    return False


def _cycle_consistent(row: dict[str, Any], chart_path: list[str]) -> bool | None:
    """Own holonomy computation: joint satisfiability of the cycle charts'
    rendered tables. None when the path references unknown charts (the module
    then fails closed on the path check anyway)."""
    cycle_charts = sorted(set(chart_path))
    tables = row["constraint_tables"]
    if any(c not in tables for c in cycle_charts):
        return None
    sub = {c: tables[c] for c in cycle_charts}
    sub_vars = sorted({v for c in cycle_charts for v in tables[c]["variables"]})
    return _satisfiable(sub_vars, sub)


def arm_b_declare(row: dict[str, Any]) -> dict[str, Any]:
    atlas_id = row["atlas_id"]
    qoi = f"glue:{atlas_id}"
    level = AbstractionLevel.L2
    layer = GluingLayer.OBSERVATIONAL

    charts = tuple(
        AtlasChart(
            chart_id=c,
            atlas_object_id=atlas_id,
            question_or_qoi=qoi,
            abstraction_level=level,
            context_id=f"ctx:{atlas_id}",
            assumptions=(),
            regime=("r0",),
            evidence_ids=(f"record:{atlas_id}",),
        )
        for c in row["charts"]
    )
    transitions = tuple(
        OverlapTransition(
            transition_id=f"t:{atlas_id}:{t['overlap_id']}:{i}",
            source_chart_id=t["left_chart"],
            target_chart_id=t["right_chart"],
            overlap_id=t["overlap_id"],
            mapping_pairs=((t["overlap_id"], t["overlap_id"]),),
            preserved=(f"overlap_restriction:{t['overlap_id']}",),
            not_preserved=(),
            certified_layers=(layer,),
            context_alignment_passed=True,
            assumption_compatibility_passed=True,
            regime_overlap=("r0",),
            transition_map_passed=(
                True if t.get("pairwise_pass") is True
                else (False if t.get("pairwise_pass") is False else None)
            ),
            evidence_ids=(
                (f"record:{atlas_id}:overlap:{t['overlap_id']}",)
                if t.get("fields_complete_pairwise") is True else ()
            ),
            declared_before_outcomes=True,
        )
        for i, t in enumerate(row["transitions"])
    )
    topo = _topology(row["charts"], row["transitions"])
    witnesses = tuple(
        CycleConsistencyWitness(
            cycle_id=w.get("cycle_id", ""),
            chart_path=tuple(w.get("chart_path", ())),
            composition_consistent=_cycle_consistent(row, w.get("chart_path", [])),
            evidence_ids=tuple(w.get("evidence_ids", ())),
        )
        for w in row["cycle_witnesses"]
    )
    global_exists = _satisfiable(row["variables"], row["constraint_tables"])
    trial = AtlasGluingTrial(
        trial_id=f"trial:{atlas_id}",
        atlas_object_id=atlas_id,
        question_or_qoi=qoi,
        abstraction_level=level,
        requested_layer=layer,
        charts=charts,
        transitions=transitions,
        cover_connected=topo["connected"],
        cover_has_cycles=topo["cycles"] > 0,
        cycle_basis_complete=True,
        cycle_witnesses=witnesses,
        global_existence_checked=True,
        global_exists=global_exists,
        uniqueness_checked=False,
        unique_global=None,
        hidden_labels_exposed=False,
        transition_family_frozen_before_outcomes=True,
    )
    report = evaluate_atlas_gluing(trial)
    if report.verdict in GLUE_VERDICTS:
        return {"atlas_id": atlas_id, "declaration": "GLUE",
                "sub_verdict": report.verdict.value}
    return {"atlas_id": atlas_id, "declaration": "REFUSE",
            "sub_verdict": report.verdict.value,
            "reasons": list(report.reasons)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("A", "B"))
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.corpus, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["atlases"]
    for row in rows:
        if "gold_label" in row or "class" in row or "twin_id" in row:
            print("REFUSING: arm input contains gold/class/twin fields", file=sys.stderr)
            return 2

    declare = arm_a_declare if args.arm == "A" else arm_b_declare
    t0 = time.monotonic()
    declarations = [declare(row) for row in sorted(rows, key=lambda r: r["atlas_id"])]
    elapsed = time.monotonic() - t0
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    payload = {
        "protocol_id": "BENEFIT-L2-GLUING-V1",
        "arm": args.arm,
        "declarations": declarations,
        "n_declared_glue": sum(1 for d in declarations if d["declaration"] == "GLUE"),
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
