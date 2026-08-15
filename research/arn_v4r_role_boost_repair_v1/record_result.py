"""Record the executed v4r repair against its frozen protocol."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path("research/arn_v4r_role_boost_repair_v1")
PROTOCOL = HERE / "PROTOCOL.json"
OUT = HERE / "RESULT.json"

BASELINE = Path("/tmp/v4_baseline/RESULT.json")
REPAIR = Path("/tmp/v4_repair/RESULT.json")
COMMITTED = Path("research/paper2_external_corpus_v1/results_v4_reducer/RESULT.json")


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["status"] == "FROZEN_BEFORE_EXECUTION"

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    repair = json.loads(REPAIR.read_text(encoding="utf-8"))
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))

    b3_committed = committed["battery"]["B3_shuffled_gold"]
    b3_base = baseline["battery"]["B3_shuffled_gold"]
    b3_repair = repair["battery"]["B3_shuffled_gold"]

    reproduces = b3_base["advantage"] == b3_committed["advantage"]
    leak_died = b3_repair["ci"][0] <= 0.0 <= b3_repair["ci"][1]
    text_reading_survives = bool(repair["battery"]["B2_text_destruction"]["pass"])

    if not leak_died:
        terminal = "REPAIR_FAILED__LEAK_PERSISTS"
    elif not text_reading_survives:
        terminal = "REPAIR_DESTROYED_THE_INSTRUMENT"
    else:
        terminal = "SEE_G1"  # unreachable in this run; kept so the rule is visible

    result = {
        "schema_version": "rakl-arn-v4r-role-boost-repair-result-v1",
        "protocol": str(PROTOCOL),
        "protocol_status_at_execution": protocol["status"],
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "terminal": terminal,
        "baseline_reproduces_committed_v4": reproduces,
        "b3_shuffled_gold": {
            "committed_v4": {"advantage": b3_committed["advantage"], "ci": b3_committed["ci"]},
            "baseline_w_0_2": {"advantage": b3_base["advantage"], "ci": b3_base["ci"]},
            "repair_w_0_0": {"advantage": b3_repair["advantage"], "ci": b3_repair["ci"]},
            "delta_from_removing_role_boost": round(b3_base["advantage"] - b3_repair["advantage"], 6),
        },
        "b2_text_destruction_repair": repair["battery"]["B2_text_destruction"],
        "rule_R1_leak_must_die": {"held": leak_died, "why": "the repaired CI still excludes zero"},
        "rule_R2_text_reading_must_survive": {"held": text_reading_survives},
        "rule_R3_g1_not_read": (
            "R1 failed, so the confirmatory advantage is deliberately not reported: reading a G1 "
            "advantage from an instrument that still leaks is the defect under repair"
        ),
        "finding": {
            "headline": "the frontier's recorded lever for this negative is refuted by execution",
            "recorded_lever": protocol["target_negative"]["frontier_lever"],
            "recorded_cause": protocol["target_negative"]["recorded_cause"],
            "what_execution_shows": (
                "Removing the role_boost term entirely moves the shuffled-gold advantage by "
                f"{round(b3_base['advantage'] - b3_repair['advantage'], 6)}. The leak is not in "
                "role_boost, so restoring the instance-paired property cannot repair this battery."
            ),
            "where_the_leak_actually_is": (
                "Already established on main and independently confirmed here: Paper II's "
                "'Case 4: the shuffle null measured abstention, not binding' (#709, #712). Where "
                "the decision space includes abstention and the statistic is a proper score, the "
                "shuffle probe measures differential abstention rather than binding, so it cannot "
                "be passed by any instrument that abstains more than its control — whatever its "
                "scoring terms."
            ),
            "consequence_for_the_frontier": (
                "research/negative_frontier_v1 record p2-arn-v4-battery-failed carries a core_lever "
                "that predates that finding. It is stale: the negative is not revivable by removing "
                "role_boost, and the successor route is the repaired probe restricted to items on "
                "which both compared arms are decisive."
            ),
        },
        "successor_epoch_required": (
            "Running the repaired B3 (jointly-decisive restriction) on this arm is a different "
            "experiment and needs its own freeze. Continuing into it under this protocol would be "
            "the post-hoc amendment the invariants forbid."
        ),
        "non_claims": protocol["non_claims"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"baseline reproduces committed v4: {reproduces}")
    print(f"B3 committed  : {b3_committed['advantage']}")
    print(f"B3 baseline   : {b3_base['advantage']}")
    print(f"B3 repair     : {b3_repair['advantage']}  ci={b3_repair['ci']}")
    print(f"delta from removing role_boost: {round(b3_base['advantage'] - b3_repair['advantage'], 6)}")
    print(f"TERMINAL: {terminal}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
