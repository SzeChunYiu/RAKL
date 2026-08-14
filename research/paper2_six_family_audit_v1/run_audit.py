#!/usr/bin/env python3
"""Auxiliary audit of the Paper II six-family robustness confirmatory packet.

STATUS: AUXILIARY_DIAGNOSTIC_ONLY. This script is NOT part of the frozen
robustness preregistration (`ROBUSTNESS_REGISTRATION_V1.md`) and NOT part of
the frozen confirmatory freeze (`ROBUSTNESS_CONFIRMATORY_FREEZE_V1.json`).

It modifies nothing frozen. It reads the same frozen generator
(`src/rakl/objective_transfer_robustness.py`) and adds falsifiers that the
frozen registration does NOT contain:

  A. full-arm constant-loss probe
       The frozen primary statistic is
           mean( brier(mechanism) - brier(full) )
       over decidable items, with `full = verify` = the gold function and
       `binary_probability(ACCEPT)=0.98`, `binary_probability(REJECT)=0.02`.
       Therefore brier(full) is a CONSTANT 0.0004 on every decidable item.
       The "paired" difference has zero variance in one arm; it is the
       mechanism arm's absolute Brier loss shifted by a constant.

  B. sign-test degeneracy probe
       Re-runs the frozen `summarize()` across many non-registered seeds and
       records `family_sign_test.positive_families`. If this is 6/6 for every
       seed, the registered `p = 0.03125` is guaranteed by generator design
       and carries no evidential weight about cross-family generalization.

  C. trivial-arm clean baseline
       `full` attains invalid_false_accept = 0.0. So does a trivial
       always-REJECT gate. Selectivity is not edge. The discriminating
       quantity is valid-transfer retention at equal false-accept.

  D. coordinate-shuffle equal-n null
       Each task is scored using a ComponentAssessment drawn from a DIFFERENT
       randomly chosen task in the SAME family (equal n, same marginal
       distribution of coordinate values). This separates "the merge rule is
       conservative" from "the coordinates carry task-specific information".

  E. per-coordinate leave-one-out
       Which single applicability coordinate carries the false-accept
       reduction.

  F. per-item-type dose-response
       Where the full-minus-mechanism advantage is concentrated. The frozen
       strata include item types constructed so the discriminating coordinate
       is NOT `effect`; `mechanism_only` IS `effect`. This quantifies how much
       of the headline advantage is structural necessity of those strata.

Nothing here promotes anything. Outputs are proposal-only diagnostics.
"""
from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import (
    FAMILIES,
    ITEM_TYPES,
    RobustTask,
    components,
    generate,
    mechanism_predict,
    merge_decisions,
    relational_predict,
    verify,
)
from scripts.paper2_robustness_confirmatory import (
    CONFIRMATORY_SEED,
    N_PER_CELL,
    summarize,
)
from scripts.paper2_robustness_development import binary_probability, brier

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

COORDINATES = ("qoi", "boundary", "direction", "relation", "precondition", "effect")


def _decidable(tasks: list[RobustTask]) -> list[RobustTask]:
    return [t for t in tasks if verify(t) is not Decision.CANNOT_CHECK]


def probe_a_full_arm_constant_loss(tasks: list[RobustTask]) -> dict:
    """The frozen primary statistic's full arm has zero variance."""
    losses = [brier(binary_probability(verify(t)), verify(t)) for t in _decidable(tasks)]
    mech = [brier(binary_probability(mechanism_predict(t)), verify(t)) for t in _decidable(tasks)]
    return {
        "full_arm_losses_distinct_values": sorted(set(round(x, 12) for x in losses)),
        "full_arm_loss_variance": statistics.pvariance(losses),
        "full_arm_loss_is_constant": len(set(round(x, 12) for x in losses)) == 1,
        "mechanism_arm_mean_loss": statistics.mean(mech),
        "registered_primary_gain_equals_mechanism_loss_minus_constant": True,
        "interpretation": (
            "brier(full) is constant because full==verify==gold and "
            "binary_probability maps the gold decision to 0.98/0.02. The registered "
            "'paired' Brier gain is therefore the mechanism arm's absolute loss minus "
            "a fixed 0.0004; it is not a paired comparison of two predictors."
        ),
    }


def probe_b_sign_degeneracy(seeds: list[int]) -> dict:
    """Does the six-family sign test ever fail on any seed?"""
    rows = []
    for s in seeds:
        out = summarize(seed=s, n_per_cell=N_PER_CELL, bootstrap_reps=200, bootstrap_seed=s + 1)
        rows.append(
            {
                "seed": s,
                "positive_families": out["family_sign_test"]["positive_families"],
                "exact_two_sided_p": out["family_sign_test"]["exact_two_sided_p"],
                "supported": out["broad_known_world_robustness_supported"],
            }
        )
    always = all(r["positive_families"] == len(FAMILIES) for r in rows)
    return {
        "seeds_tested": len(rows),
        "rows": rows,
        "all_seeds_six_of_six_positive": always,
        "sign_test_is_structurally_guaranteed": always,
        "interpretation": (
            "If every seed yields 6/6 positive family signs, the registered "
            "p=0.03125 is a property of the generator's item strata, not evidence "
            "of cross-family generalization. The frozen gate cannot fail."
        ),
    }


def _arm_stats(tasks: list[RobustTask], predict) -> dict:
    valid = [t for t in tasks if verify(t) is Decision.ACCEPT]
    invalid = [t for t in tasks if verify(t) is Decision.REJECT]
    unknown = [t for t in tasks if verify(t) is Decision.CANNOT_CHECK]
    return {
        "exact3": sum(predict(t) is verify(t) for t in tasks) / len(tasks),
        "valid_accept": sum(predict(t) is Decision.ACCEPT for t in valid) / len(valid),
        "invalid_false_accept": sum(predict(t) is Decision.ACCEPT for t in invalid) / len(invalid),
        "unknown_abstain": sum(predict(t) is Decision.CANNOT_CHECK for t in unknown) / len(unknown),
    }


def probe_c_trivial_arms(tasks: list[RobustTask]) -> dict:
    """Clean baselines: a trivial gate also attains zero false-accept."""
    arms = {
        "always_reject": lambda t: Decision.REJECT,
        "always_accept": lambda t: Decision.ACCEPT,
        "always_cannot_check": lambda t: Decision.CANNOT_CHECK,
        "mechanism": mechanism_predict,
        "relational": relational_predict,
        "full": verify,
    }
    stats = {name: _arm_stats(tasks, fn) for name, fn in arms.items()}
    return {
        "arms": stats,
        "zero_false_accept_is_not_unique_to_full": stats["always_reject"]["invalid_false_accept"] == 0.0,
        "discriminating_quantity": "valid_accept at equal invalid_false_accept",
        "interpretation": (
            "always_reject attains invalid_false_accept=0.0 with valid_accept=0.0. "
            "full attains invalid_false_accept=0.0 with valid_accept=1.0. The "
            "defensible claim is joint retention+rejection, never the false-accept "
            "rate alone."
        ),
    }


def probe_d_coordinate_shuffle_null(tasks: list[RobustTask], seed: int, reps: int) -> dict:
    """Equal-n null: score each task with another same-family task's coordinates."""
    rng = random.Random(seed)
    by_family: dict[str, list[RobustTask]] = defaultdict(list)
    for t in tasks:
        by_family[t.family].append(t)

    exact3_draws, fa_draws, va_draws = [], [], []
    for _ in range(reps):
        pred: dict[str, Decision] = {}
        for fam, fam_tasks in by_family.items():
            donors = fam_tasks[:]
            rng.shuffle(donors)
            for t, donor in zip(fam_tasks, donors):
                pred[t.item_id] = components(donor).full
        valid = [t for t in tasks if verify(t) is Decision.ACCEPT]
        invalid = [t for t in tasks if verify(t) is Decision.REJECT]
        exact3_draws.append(sum(pred[t.item_id] is verify(t) for t in tasks) / len(tasks))
        fa_draws.append(sum(pred[t.item_id] is Decision.ACCEPT for t in invalid) / len(invalid))
        va_draws.append(sum(pred[t.item_id] is Decision.ACCEPT for t in valid) / len(valid))

    def _ci(xs):
        xs = sorted(xs)
        return [xs[int(0.025 * len(xs))], statistics.mean(xs), xs[min(len(xs) - 1, int(0.975 * len(xs)))]]

    return {
        "reps": reps,
        "null_exact3_lo_mean_hi": _ci(exact3_draws),
        "null_invalid_false_accept_lo_mean_hi": _ci(fa_draws),
        "null_valid_accept_lo_mean_hi": _ci(va_draws),
        "observed_full_exact3": 1.0,
        "observed_full_invalid_false_accept": 0.0,
        "observed_full_valid_accept": 1.0,
        "interpretation": (
            "Under the equal-n coordinate shuffle the merge rule and the marginal "
            "coordinate distribution are unchanged; only the task<->coordinate binding "
            "is destroyed. Collapse of valid_accept/exact3 under the null is the "
            "evidence that coordinates carry task-specific information rather than the "
            "gate being merely conservative."
        ),
    }


def probe_e_leave_one_coordinate_out(tasks: list[RobustTask]) -> dict:
    """Which single applicability coordinate carries the reduction."""
    out = {}
    for drop in COORDINATES:
        def pred(t, drop=drop):
            a = components(t)
            kept = [getattr(a, c) for c in COORDINATES if c != drop]
            return merge_decisions(tuple(kept))

        out[f"drop_{drop}"] = _arm_stats(tasks, pred)

    singles = {}
    for keep in COORDINATES:
        def pred(t, keep=keep):
            return getattr(components(t), keep)

        singles[f"only_{keep}"] = _arm_stats(tasks, pred)

    return {
        "leave_one_out": out,
        "single_coordinate": singles,
        "interpretation": (
            "drop_X false-accept above zero identifies coordinate X as load-bearing "
            "for fail-closed rejection on this benchmark."
        ),
    }


def probe_f_item_type_dose_response(tasks: list[RobustTask]) -> dict:
    """Where the full-minus-mechanism advantage is concentrated."""
    rows = {}
    for it in ITEM_TYPES:
        sub = [t for t in tasks if t.item_type == it]
        if not sub:
            continue
        dec = _decidable(sub)
        gain = (
            statistics.mean(
                brier(binary_probability(mechanism_predict(t)), verify(t))
                - brier(binary_probability(verify(t)), verify(t))
                for t in dec
            )
            if dec
            else None
        )
        rows[it] = {
            "n": len(sub),
            "decidable_n": len(dec),
            "mechanism_exact3": sum(mechanism_predict(t) is verify(t) for t in sub) / len(sub),
            "full_minus_mechanism_brier_gain": gain,
        }
    total = sum(r["decidable_n"] * (r["full_minus_mechanism_brier_gain"] or 0.0) for r in rows.values())
    share = {
        k: (v["decidable_n"] * (v["full_minus_mechanism_brier_gain"] or 0.0) / total if total else 0.0)
        for k, v in rows.items()
    }
    return {
        "per_item_type": rows,
        "share_of_total_gain": share,
        "interpretation": (
            "mechanism_only IS the `effect` coordinate. Item strata whose "
            "discriminating coordinate is not `effect` must therefore fail the "
            "mechanism arm by construction. Their share of the total gain measures "
            "how much of the headline result is generator design rather than "
            "empirical cross-family robustness."
        ),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    tasks = generate(CONFIRMATORY_SEED, N_PER_CELL)

    report = {
        "schema": "paper2-six-family-audit-v1",
        "status": "AUXILIARY_DIAGNOSTIC_ONLY__NOT_PART_OF_FROZEN_REGISTRATION",
        "grants_scientific_authority": False,
        "confirmatory_seed_audited": CONFIRMATORY_SEED,
        "n": len(tasks),
        "A_full_arm_constant_loss": probe_a_full_arm_constant_loss(tasks),
        "B_sign_test_degeneracy": probe_b_sign_degeneracy(
            [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010, 1111, 1212]
        ),
        "C_trivial_arm_baseline": probe_c_trivial_arms(tasks),
        "D_coordinate_shuffle_equal_n_null": probe_d_coordinate_shuffle_null(tasks, seed=4242, reps=200),
        "E_leave_one_coordinate_out": probe_e_leave_one_coordinate_out(tasks),
        "F_item_type_dose_response": probe_f_item_type_dose_response(tasks),
        "claim_boundary": (
            "Diagnostic only. Does not promote, demote or replace any frozen verdict. "
            "Does not establish natural-language extraction, natural-domain transfer, "
            "independent-human validation or downstream action utility."
        ),
    }

    path = RESULTS / "SIX_FAMILY_AUDIT.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
