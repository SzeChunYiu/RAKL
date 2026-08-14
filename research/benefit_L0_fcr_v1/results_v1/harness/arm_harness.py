"""Arm execution harness for BENEFIT-L0-FCR-V1. One process per arm so
wall-clock and peak RSS are charged per arm (PROTOCOL.json arms.cost_matching).

Both arms receive the byte-identical gold-stripped corpus; token budget is 0
for both (no retrieval, no network, no LLM calls).

Arm A (frozen verbatim, PROTOCOL.json arms.A_naive_text_comparison):
  "For each comparable pair, compare the canonical value strings for the shared
   facet only. Declare CONTRADICTION iff facet_left == facet_right and
   value_left != value_right. All context fields are present in the input
   record and deliberately ignored; no context extraction, alignment, or unit
   normalization is performed."

Arm B (frozen verbatim, PROTOCOL.json arms.B_context_aligned_projection):
  "Represent each claim as rakl.core.Projection with a rakl.core.Context. For
   each comparable pair: (1) require facet overlap; (2) compute
   rakl.core.compare_contexts(left_ctx, right_ctx) over the frozen field list
   [population, scale, horizon, observation_model, units, assumptions,
   intervention] (the default comparable_key fields of rakl.core.Context);
   (3) if differences are non-empty, the pair is not aligned: declare
   NO_CONTRADICTION (classified internally as CONTEXT_DEPENDENT_DIFFERENCE
   candidate per Relationship.CONTEXT_DEPENDENT_DIFFERENCE); (4) if aligned and
   values differ, declare CONTRADICTION; (5) if aligned and values equal,
   declare NO_CONTRADICTION."

Arm B drives the exact bound machinery: Context / Context.comparable_key /
compare_contexts / Projection / KnowledgeFiber.add_projection /
unresolved_pairs / add_relation / contradictions.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, utc_now_iso  # noqa: E402  (also wires src/ path)

from rakl.core import (  # noqa: E402
    Context, KnowledgeFiber, Projection, Relation, Relationship, compare_contexts,
)


def arm_a(record: dict) -> str:
    if record["facet_left"] == record["facet_right"] and \
            record["value_left"] != record["value_right"]:
        return "CONTRADICTION"
    return "NO_CONTRADICTION"


def _context(payload: dict) -> Context:
    return Context(
        population=payload["population"],
        scale=payload["scale"],
        horizon=payload["horizon"],
        observation_model=payload["observation_model"],
        units=payload["units"],
        assumptions=tuple(payload["assumptions"]),
        intervention=payload["intervention"],
    )


def arm_b(record: dict) -> str:
    pid = record["pair_id"]
    ctx_l = _context(record["context_left"])
    ctx_r = _context(record["context_right"])
    fiber = KnowledgeFiber(fiber_id=pid, object_id=f"obj:{pid}",
                           atomic_step="l0-contradiction-screen")
    left = Projection(projection_id=f"{pid}:L", object_id=f"obj:{pid}",
                      facets=(record["facet_left"],),
                      claim=record["surface_text_left"], source="left",
                      context=ctx_l)
    right = Projection(projection_id=f"{pid}:R", object_id=f"obj:{pid}",
                       facets=(record["facet_right"],),
                       claim=record["surface_text_right"], source="right",
                       context=ctx_r)
    fiber.add_projection(left)
    fiber.add_projection(right)

    # (1) facet overlap required: unresolved_pairs is empty iff no shared facet.
    if not fiber.unresolved_pairs():
        return "NO_CONTRADICTION"
    # comparable_key over the frozen default field list is the alignment tuple;
    # compare_contexts reports the coordinate-wise differences.
    assert ctx_l.comparable_key() == ctx_l.comparable_key(
        ("population", "scale", "horizon", "observation_model",
         "units", "assumptions", "intervention"))
    differences = compare_contexts(ctx_l, ctx_r)
    if differences:  # (3) not aligned
        fiber.add_relation(Relation(left.projection_id, right.projection_id,
                                    Relationship.CONTEXT_DEPENDENT_DIFFERENCE,
                                    scope="candidate:any-context-difference"))
    elif record["value_left"] != record["value_right"]:  # (4)
        fiber.add_relation(Relation(left.projection_id, right.projection_id,
                                    Relationship.CONTRADICTION,
                                    scope="aligned-values-differ"))
    else:  # (5)
        fiber.add_relation(Relation(left.projection_id, right.projection_id,
                                    Relationship.OBSERVATIONAL_EQUIVALENCE,
                                    scope="aligned-values-equal"))
    return "CONTRADICTION" if fiber.contradictions() else "NO_CONTRADICTION"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["A", "B"], required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.corpus, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload["pairs"]
    for row in records:
        for forbidden in ("gold_label", "class"):
            if forbidden in row:
                print(f"REFUSING: arm input contains {forbidden}", file=sys.stderr)
                return 2

    started = utc_now_iso()
    t0 = time.monotonic()
    decide = arm_a if args.arm == "A" else arm_b
    declarations = [
        {"pair_id": row["pair_id"], "declaration": decide(row)}
        for row in records
    ]
    elapsed = time.monotonic() - t0
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump({
            "arm": args.arm,
            "started_at": started,
            "wall_clock_seconds": elapsed,
            "peak_rss_bytes": peak_rss,
            "token_budget_used": 0,
            "n_declared_contradiction": sum(
                1 for d in declarations if d["declaration"] == "CONTRADICTION"),
            "declarations": declarations,
        }, handle, indent=2)
        handle.write("\n")
    print(f"arm {args.arm}: {len(declarations)} declarations, "
          f"{elapsed:.3f}s, peak_rss={peak_rss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
