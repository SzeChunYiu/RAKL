"""Arm executor for BENEFIT-L5-SATURATION-V1. One process per arm (step 2 spawns
each separately) over the byte-identical gold-stripped corpus.

Arm A — budget-exhaustion stopping, PROTOCOL.json
arms.A_budget_exhaustion_stopping, implemented verbatim to the frozen
decision-equivalent rule in EVALUATOR.py (stop_round = T_MAX = 24 always).

Arm B — saturation stopping: after each round, builds the SaturationRound
records honestly from the rendered per-round world facts and calls the exact
pinned rakl.epistemic_saturation.audit_bounded_epistemic_saturation
(required_consecutive_flat_rounds=2) on the rounds so far under a per-world
frozen SaturationBasis (module pin verified before any declaration). Stops at
the first round where the report status is BOUNDED_SATURATED; else T_MAX.

Record -> framework-object encoding (bookkeeping constants documented; none
participates in a verdict branch beyond its registered semantics):
- EpistemicGrowthVector: len(new_fact_ids) enters
  independent_evidence_roots_added and other_substantive_updates enters
  unresolved_fiber_updates, so growth.total equals the frozen replica's
  growth_total (newly retained deduplicated facts + rendered non-fact
  substantive updates); the audit consumes only totals/flatness.
- OperatorOrderAudit: the rendered operator_order_stable gate fact becomes a
  flat (stable) or unit (unstable) substantive_difference vector; digests and
  evidence ids are constant renderings of the round identity.
- SaturationBasis: per-world frozen constant coordinates derived from the
  world id; every round carries its fingerprint (no mid-run basis drift).
- freshness_cutoff: constant "2026-08-14" (the audit's optional
  required_freshness_cutoff channel is unexercised, as frozen).
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

from rakl.epistemic_saturation import (  # noqa: E402
    EpistemicGrowthVector,
    OperatorOrderAudit,
    SaturationBasis,
    SaturationRound,
    SaturationStatus,
    audit_bounded_epistemic_saturation,
)

T_MAX = 24
REQUIRED_FLAT_ROUNDS = 2
FRESHNESS = "2026-08-14"


def arm_a_stop(row: dict[str, Any]) -> dict[str, Any]:
    return {"world_id": row["world_id"], "stop_round": T_MAX}


def _basis(world_id: str) -> SaturationBasis:
    return SaturationBasis(
        basis_id=f"basis:{world_id}",
        scope=f"world:{world_id}",
        identity_policy_id="canonical-fact-id-v1",
        route_family_version="rendered-stream-v1",
        novelty_policy_id="retained-new-after-dedup-v1",
        evidence_policy_id="rendered-round-facts-v1",
    )


def _round(world_id: str, r: int, rnd: dict[str, Any], fingerprint: str) -> SaturationRound:
    stable = bool(rnd["gates"]["operator_order_stable"])
    return SaturationRound(
        round_id=f"{world_id}:r{r}",
        basis_fingerprint=fingerprint,
        growth=EpistemicGrowthVector(
            independent_evidence_roots_added=len(rnd["new_fact_ids"]),
            unresolved_fiber_updates=int(rnd["other_substantive_updates"]),
        ),
        bounded_discovery_closed=bool(rnd["gates"]["bounded_discovery_closed"]),
        route_coverage_stable=bool(rnd["gates"]["route_coverage_stable"]),
        omission_audit_passed=bool(rnd["gates"]["omission_audit_passed"]),
        nearest_work_audit_passed=bool(rnd["gates"]["nearest_work_audit_passed"]),
        operator_order_audit=OperatorOrderAudit(
            audit_id=f"{world_id}:r{r}:ooa",
            expand_then_consolidate_digest=f"{world_id}:r{r}:ec",
            consolidate_then_expand_digest=f"{world_id}:r{r}:ce",
            substantive_difference=(
                EpistemicGrowthVector() if stable
                else EpistemicGrowthVector(mechanisms_added=1)),
            evidence_ids=(f"{world_id}:r{r}:ev0",),
        ),
        freshness_cutoff=FRESHNESS,
        blocking_fibers=tuple(rnd["blocking_fibers"]),
    )


def arm_b_stop(row: dict[str, Any]) -> dict[str, Any]:
    world_id = row["world_id"]
    basis = _basis(world_id)
    fingerprint = basis.fingerprint
    rounds: list[SaturationRound] = []
    statuses: list[str] = []
    for r, rnd in enumerate(row["rounds"], start=1):
        rounds.append(_round(world_id, r, rnd, fingerprint))
        report = audit_bounded_epistemic_saturation(
            rounds, basis=basis,
            required_consecutive_flat_rounds=REQUIRED_FLAT_ROUNDS)
        statuses.append(report.status.value)
        if report.status is SaturationStatus.BOUNDED_SATURATED:
            return {"world_id": world_id, "stop_round": r,
                    "certified": True,
                    "consecutive_flat_rounds": report.consecutive_flat_rounds}
    return {"world_id": world_id, "stop_round": T_MAX, "certified": False,
            "final_status": statuses[-1]}


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
        if "gold_basis" in row or "t_complete" in row or "class" in row:
            print("REFUSING: arm input contains gold/t_complete/class fields",
                  file=sys.stderr)
            return 2

    stop = arm_a_stop if args.arm == "A" else arm_b_stop
    t0 = time.monotonic()
    stops = [stop(row) for row in sorted(rows, key=lambda r: r["world_id"])]
    elapsed = time.monotonic() - t0
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    payload = {
        "protocol_id": "BENEFIT-L5-SATURATION-V1",
        "arm": args.arm,
        "stops": stops,
        "n_early_stops": sum(1 for s in stops if s["stop_round"] < T_MAX),
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
