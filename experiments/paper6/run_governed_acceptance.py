"""SRSU-P6-GOVERNED-ACCEPTANCE-V1 runner.

Frozen by research/paper6_scoped_utility_v1/PREREGISTRATION_V1.json.

Deterministic, seeded, no LLM in the loop. Measures what fail-closed governed
acceptance costs and what it buys on a population of candidate-promotion
decisions under externally anchored evidence-availability rates
(arXiv:2608.05179, via external-agent registry v1).

Reporting is Pareto/componentwise. No weighted aggregate is computed anywhere
in this file, by design.
"""

from __future__ import annotations

import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rakl.formalism import VerificationReport, VerificationVerdict  # noqa: E402
from rakl.hard_gates import (  # noqa: E402
    HardGateContract,
    HardGateObservation,
    HardGateRequirement,
    HardGateState,
    evaluate_full_positive_goal,
)
from rakl.invention import (  # noqa: E402
    CandidateScore,
    GoalAssessmentVerdict,
    PositiveGoalContract,
    evaluate_positive_goal,
)

# --- frozen contract ---------------------------------------------------------

GATE_IDS: Tuple[str, ...] = (
    "TYPED_CANDIDATE_IDENTITY",
    "THRESHOLDS_FROZEN_PRE_RESULT",
    "EVIDENCE_LINEAGE",
    "NO_TARGET_LEAKAGE",
    "MULTIPLICITY_ACCOUNTED",
    "FALSIFIERS_EXECUTED",
    "MECHANISM_ANCESTRY",
    "EXACT_CANDIDATE_BINDING",
    "INDEPENDENT_REVIEW",
    "REPLAY_REPRODUCIBLE",
    "SEED_AND_TRACE_BOUND",
    "NOVELTY_BOUNDED",
)

# Externally anchored availability rates (arXiv:2608.05179, PRIMARY_ABSTRACT).
P_CODE_CLASS = 0.83
P_REPRO_CLASS = 0.38

N_GATES = len(GATE_IDS)
K_BEST_OF = 5  # arm B steelman
N_EPISODES = 400
SEEDS = (11, 12, 13, 14, 15)
SOUND_FRACTION = 0.5


def gate_contract() -> HardGateContract:
    return HardGateContract(
        "paper6-scoped-utility-promotion-gates-v1",
        tuple(
            HardGateRequirement(gid, f"promotion gate {gid}", evidence_required=True)
            for gid in GATE_IDS
        ),
        frozen_before_candidate_results=True,
    )


def numeric_contract() -> PositiveGoalContract:
    return PositiveGoalContract(
        "paper6-scoped-utility-numeric-v1",
        min_descriptive_coverage=0.60,
        min_residual_closure=0.60,
        min_predictive_value=0.60,
        min_identification=0.60,
        min_falsifiability=0.60,
        min_robustness=0.60,
        max_complexity=None,
        verification_required=True,
        thresholds_frozen_before_results=True,
    )


def availability_profile(n_repro: int) -> Tuple[float, ...]:
    """Last `n_repro` gates are reproducibility-class; the rest are code-class."""
    n_code = N_GATES - n_repro
    return tuple([P_CODE_CLASS] * n_code + [P_REPRO_CLASS] * n_repro)


# --- episode -----------------------------------------------------------------


@dataclass(frozen=True)
class Episode:
    candidate_id: str
    sound: bool
    defect_gate_index: int  # -1 when sound
    available: Tuple[bool, ...]
    score: CandidateScore
    heldout_scalars: Tuple[float, ...]


def make_episode(rng: random.Random, idx: int, profile: Tuple[float, ...]) -> Episode:
    sound = rng.random() < SOUND_FRACTION
    available = tuple(rng.random() < p for p in profile)
    defect_gate_index = -1 if sound else rng.randrange(N_GATES)

    # Both sound and unsound candidates clear the numeric thresholds. The whole
    # point of a governance layer is the candidate whose NUMBERS look fine and
    # whose INTEGRITY is broken; a candidate caught by the numeric contract
    # alone would make the gate layer irrelevant by construction.
    def q() -> float:
        return 0.70 + rng.random() * 0.29

    score = CandidateScore(
        candidate_id=f"cand-{idx:05d}",
        descriptive_coverage=q(),
        residual_closure=q(),
        predictive_value=q(),
        identification=q(),
        falsifiability=q(),
        robustness=q(),
        novelty=q(),
        complexity=rng.random() * 3.0,
    )
    heldout = tuple(rng.random() for _ in range(K_BEST_OF))
    return Episode(score.candidate_id, sound, defect_gate_index, available, score, heldout)


def observations_for(ep: Episode) -> Tuple[HardGateObservation, ...]:
    """Gate observations as ORION would actually receive them.

    Available evidence -> a decidable observation (PASS, or FAIL on the defect
    gate). Unavailable evidence -> CANNOT_CHECK with no evidence ids. The
    defect is NOT visible when its evidence is missing; that asymmetry is the
    whole reason a fail-closed rule exists.
    """
    out: List[HardGateObservation] = []
    for i, gid in enumerate(GATE_IDS):
        if not ep.available[i]:
            out.append(
                HardGateObservation(gid, ep.candidate_id, HardGateState.CANNOT_CHECK, (), "evidence_unavailable")
            )
        elif i == ep.defect_gate_index:
            out.append(
                HardGateObservation(
                    gid, ep.candidate_id, HardGateState.FAIL, (f"ev-{ep.candidate_id}-{gid}",), "planted_defect"
                )
            )
        else:
            out.append(
                HardGateObservation(gid, ep.candidate_id, HardGateState.PASS, (f"ev-{ep.candidate_id}-{gid}",), "")
            )
    return tuple(out)


def coerce_fail_open(obs: Tuple[HardGateObservation, ...]) -> Tuple[HardGateObservation, ...]:
    """Arm D: identical gates, CANNOT_CHECK coerced to PASS with synthetic evidence."""
    return tuple(
        HardGateObservation(o.gate_id, o.candidate_id, HardGateState.PASS, (f"synthetic-{o.gate_id}",), "coerced")
        if o.state is HardGateState.CANNOT_CHECK
        else o
        for o in obs
    )


VERIFICATION_PASS = VerificationReport(VerificationVerdict.PASS, ("oracles_passed",))


# --- arms --------------------------------------------------------------------


@dataclass
class ArmTally:
    accepted_sound: int = 0
    accepted_unsound: int = 0
    rejected_sound: int = 0
    rejected_unsound: int = 0
    gate_evaluations: int = 0
    scalar_evaluations: int = 0
    accepted_with_complete_receipt: int = 0
    wall_time_s: float = 0.0

    def record(self, accepted: bool, sound: bool, complete_receipt: bool) -> None:
        if accepted:
            if sound:
                self.accepted_sound += 1
            else:
                self.accepted_unsound += 1
            if complete_receipt:
                self.accepted_with_complete_receipt += 1
        else:
            if sound:
                self.rejected_sound += 1
            else:
                self.rejected_unsound += 1

    def as_qoi(self) -> Dict[str, float]:
        n = self.accepted_sound + self.accepted_unsound + self.rejected_sound + self.rejected_unsound
        n_sound = self.accepted_sound + self.rejected_sound
        n_unsound = self.accepted_unsound + self.rejected_unsound
        n_acc = self.accepted_sound + self.accepted_unsound
        return {
            # false promotion, out of ALL decisions
            "false_promotion_rate": self.accepted_unsound / n if n else 0.0,
            # of the unsound population, how many got through
            "unsound_admission_rate": self.accepted_unsound / n_unsound if n_unsound else 0.0,
            "true_promotion_rate": self.accepted_sound / n if n else 0.0,
            "fail_closed_tax": self.rejected_sound / n_sound if n_sound else 0.0,
            "gate_evaluations_per_decision": self.gate_evaluations / n if n else 0.0,
            "scalar_evaluations_per_decision": self.scalar_evaluations / n if n else 0.0,
            "wall_time_per_decision_s": self.wall_time_s / n if n else 0.0,
            "receipt_completeness_of_accepted": (
                self.accepted_with_complete_receipt / n_acc if n_acc else float("nan")
            ),
        }


def run_cell(n_repro: int, seed: int) -> Dict[str, Dict[str, float]]:
    rng = random.Random((seed << 8) ^ n_repro)
    profile = availability_profile(n_repro)
    hgc = gate_contract()
    ngc = numeric_contract()

    tallies = {a: ArmTally() for a in ("A_ORION_GOVERNED", "B_GREEDY_HELDOUT_SCALAR", "C_GATES_LOGGED_NOT_EXECUTED", "D_FAIL_OPEN")}
    incumbent = 0.0

    for idx in range(N_EPISODES):
        ep = make_episode(rng, idx, profile)
        obs = observations_for(ep)

        # --- arm A: ORION governed acceptance, fail-closed
        t0 = time.perf_counter()
        rep = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs)
        t1 = time.perf_counter()
        acc_a = rep.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
        # a complete receipt = every gate PASS with real (non-synthetic) evidence
        complete_a = all(o.state is HardGateState.PASS and o.evidence_ids and not o.evidence_ids[0].startswith("synthetic-") for o in obs)
        ta = tallies["A_ORION_GOVERNED"]
        ta.gate_evaluations += N_GATES
        ta.wall_time_s += t1 - t0
        ta.record(acc_a, ep.sound, complete_a and acc_a)

        # --- arm D: identical gates, CANNOT_CHECK coerced to PASS
        obs_d = coerce_fail_open(obs)
        t0 = time.perf_counter()
        rep_d = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs_d)
        t1 = time.perf_counter()
        acc_d = rep_d.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
        complete_d = all(o.evidence_ids and not o.evidence_ids[0].startswith("synthetic-") for o in obs_d)
        td = tallies["D_FAIL_OPEN"]
        td.gate_evaluations += N_GATES
        td.wall_time_s += t1 - t0
        td.record(acc_d, ep.sound, complete_d and acc_d)

        # --- arm C: gates evaluated (cost charged) but decision on numbers only
        t0 = time.perf_counter()
        _ = evaluate_full_positive_goal(ngc, hgc, ep.score, VERIFICATION_PASS, obs)  # logged
        num = evaluate_positive_goal(ngc, ep.score, VERIFICATION_PASS)
        t1 = time.perf_counter()
        acc_c = num.verdict is GoalAssessmentVerdict.GOAL_ACHIEVED
        tc = tallies["C_GATES_LOGGED_NOT_EXECUTED"]
        tc.gate_evaluations += N_GATES
        tc.wall_time_s += t1 - t0
        # acceptance is not bound to the gate report, so no acceptance is receipt-backed
        tc.record(acc_c, ep.sound, False)

        # --- arm B: greedy accept on held-out scalar, best-of-k, no gates
        t0 = time.perf_counter()
        best = max(ep.heldout_scalars)
        acc_b = best > incumbent
        if acc_b:
            incumbent = best
        t1 = time.perf_counter()
        tb = tallies["B_GREEDY_HELDOUT_SCALAR"]
        tb.scalar_evaluations += K_BEST_OF
        tb.wall_time_s += t1 - t0
        tb.record(acc_b, ep.sound, False)

    return {arm: t.as_qoi() for arm, t in tallies.items()}


def main() -> None:
    results: List[Dict[str, object]] = []
    for n_repro in range(0, N_GATES + 1):
        per_seed = [run_cell(n_repro, s) for s in SEEDS]
        arms = per_seed[0].keys()
        agg: Dict[str, Dict[str, float]] = {}
        for arm in arms:
            keys = per_seed[0][arm].keys()
            agg[arm] = {
                k: sum(ps[arm][k] for ps in per_seed) / len(per_seed) for k in keys
            }
        results.append({"n_repro": n_repro, "expected_all_gates_available": _p_all(n_repro), "arms": agg})

    out = {
        "packet_id": "SRSU-P6-GOVERNED-ACCEPTANCE-V1",
        "prereg": "research/paper6_scoped_utility_v1/PREREGISTRATION_V1.json",
        "n_episodes_per_cell": N_EPISODES,
        "seeds": list(SEEDS),
        "availability_anchor": {
            "source": "arXiv:2608.05179",
            "code_class_rate": P_CODE_CLASS,
            "repro_class_rate": P_REPRO_CLASS,
        },
        "permits_scalar_ranking": False,
        "grants_scientific_authority": False,
        "results": results,
    }
    print(json.dumps(out, indent=2))


def _p_all(n_repro: int) -> float:
    p = 1.0
    for v in availability_profile(n_repro):
        p *= v
    return p


if __name__ == "__main__":
    main()
