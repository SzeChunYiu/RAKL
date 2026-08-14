"""SRSU-P6-GOVERNED-ACCEPTANCE-V1.1 runner.

Successor to run_governed_acceptance.py. Frozen by
research/paper6_scoped_utility_v1/PREREGISTRATION_V1_1.json.

Only arm B changes: it is calibrated on a disjoint split to match arm D's
acceptance rate, so A / B / D are compared at MATCHED THROUGHPUT. Arms A, C
and D are unchanged and retain their v1 pre-result freeze.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rakl.hard_gates import HardGateState, evaluate_full_positive_goal  # noqa: E402
from rakl.invention import GoalAssessmentVerdict, evaluate_positive_goal  # noqa: E402

from run_governed_acceptance import (  # noqa: E402
    K_BEST_OF,
    N_EPISODES,
    N_GATES,
    SEEDS,
    ArmTally,
    VERIFICATION_PASS,
    availability_profile,
    coerce_fail_open,
    gate_contract,
    make_episode,
    numeric_contract,
    observations_for,
    _p_all,
)

CALIBRATION_EPISODES = 400


def _heldout_value(ep, leakage_inflated: bool) -> float:
    """Best-of-k held-out scalar for arm B.

    NEUTRAL (primary): independent of soundness.
    LEAKAGE_INFLATED (sensitivity only): unsound candidates score higher,
    modelling defects that inflate the very metric an ungoverned rule reads.
    """
    best = max(ep.heldout_scalars)
    if leakage_inflated and not ep.sound:
        best = min(1.0, best + 0.15)
    return best


def calibrate_tau(n_repro: int, seed: int, leakage_inflated: bool) -> float:
    """Pick tau on a DISJOINT calibration split so acceptance(B) ~= acceptance(D)."""
    rng = random.Random((seed << 16) ^ (n_repro << 4) ^ 0xC0FFEE)
    profile = availability_profile(n_repro)
    hgc, ngc = gate_contract(), numeric_contract()

    d_accepts = 0
    values: List[float] = []
    for idx in range(CALIBRATION_EPISODES):
        ep = make_episode(rng, idx, profile)
        obs_d = coerce_fail_open(observations_for(ep))
        rep_d = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs_d)
        if rep_d.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED:
            d_accepts += 1
        values.append(_heldout_value(ep, leakage_inflated))

    if d_accepts == 0:
        return float("inf")
    values.sort(reverse=True)
    k = min(d_accepts, len(values)) - 1
    return values[k]


def run_cell(n_repro: int, seed: int, leakage_inflated: bool) -> Dict[str, Dict[str, float]]:
    tau = calibrate_tau(n_repro, seed, leakage_inflated)
    rng = random.Random((seed << 8) ^ n_repro)  # same stream as v1
    profile = availability_profile(n_repro)
    hgc, ngc = gate_contract(), numeric_contract()

    tallies = {
        a: ArmTally()
        for a in (
            "A_ORION_GOVERNED",
            "B_GREEDY_HELDOUT_SCALAR_MATCHED",
            "C_GATES_LOGGED_NOT_EXECUTED",
            "D_FAIL_OPEN",
        )
    }

    for idx in range(N_EPISODES):
        ep = make_episode(rng, idx, profile)
        obs = observations_for(ep)

        t0 = time.perf_counter()
        rep = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs)
        t1 = time.perf_counter()
        acc_a = rep.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
        complete_a = all(
            o.state is HardGateState.PASS and o.evidence_ids and not o.evidence_ids[0].startswith("synthetic-")
            for o in obs
        )
        ta = tallies["A_ORION_GOVERNED"]
        ta.gate_evaluations += N_GATES
        ta.wall_time_s += t1 - t0
        ta.record(acc_a, ep.sound, complete_a and acc_a)

        obs_d = coerce_fail_open(obs)
        t0 = time.perf_counter()
        rep_d = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs_d)
        t1 = time.perf_counter()
        acc_d = rep_d.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
        td = tallies["D_FAIL_OPEN"]
        td.gate_evaluations += N_GATES
        td.wall_time_s += t1 - t0
        td.record(acc_d, ep.sound, False)

        t0 = time.perf_counter()
        _ = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs)
        num = evaluate_positive_goal(ngc, ep.score, VERIFICATION_PASS)
        t1 = time.perf_counter()
        tc = tallies["C_GATES_LOGGED_NOT_EXECUTED"]
        tc.gate_evaluations += N_GATES
        tc.wall_time_s += t1 - t0
        tc.record(num.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED, ep.sound, False)

        t0 = time.perf_counter()
        acc_b = _heldout_value(ep, leakage_inflated) >= tau
        t1 = time.perf_counter()
        tb = tallies["B_GREEDY_HELDOUT_SCALAR_MATCHED"]
        tb.scalar_evaluations += K_BEST_OF
        tb.wall_time_s += t1 - t0
        tb.record(acc_b, ep.sound, False)

    return {arm: t.as_qoi() for arm, t in tallies.items()}


def sweep(leakage_inflated: bool) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for n_repro in range(0, N_GATES + 1):
        per_seed = [run_cell(n_repro, s, leakage_inflated) for s in SEEDS]
        agg: Dict[str, Dict[str, float]] = {}
        for arm in per_seed[0]:
            agg[arm] = {
                k: sum(ps[arm][k] for ps in per_seed) / len(per_seed) for k in per_seed[0][arm]
            }
        results.append(
            {"n_repro": n_repro, "expected_all_gates_available": _p_all(n_repro), "arms": agg}
        )
    return results


def main() -> None:
    out = {
        "packet_id": "SRSU-P6-GOVERNED-ACCEPTANCE-V1.1",
        "parent_packet_id": "SRSU-P6-GOVERNED-ACCEPTANCE-V1",
        "prereg": "research/paper6_scoped_utility_v1/PREREGISTRATION_V1_1.json",
        "n_episodes_per_cell": N_EPISODES,
        "calibration_episodes_disjoint": CALIBRATION_EPISODES,
        "seeds": list(SEEDS),
        "permits_scalar_ranking": False,
        "grants_scientific_authority": False,
        "primary_neutral_scalar_model": sweep(leakage_inflated=False),
        "sensitivity_leakage_inflated_not_headline": sweep(leakage_inflated=True),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
