#!/usr/bin/env python3
"""Label-blind power / MDE study for Paper III confirmatory packet (#248).

Deterministic stdlib-only simulation. Does not access annotations, descriptor
scores as labels, or evaluated confirmatory outcomes. Writes:

  research/paper3/power_design/POWER_RESULTS.json

Run from repository root:

  python3 scripts/paper3_power_design_simulate.py
"""

from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.inference import paired_lift_verdict  # noqa: E402
from rakl.paper3_annotation import canonical_sha256  # noqa: E402
from rakl.paper3_power_design import (  # noqa: E402
    analytic_power_mean_ci_excludes_zero,
)

OUT_DIR = ROOT / "research" / "paper3" / "power_design"
CONFIG_PATH = OUT_DIR / "POWER_SIMULATION_CONFIG.json"


def monte_carlo_power(
    *,
    n: int,
    true_mean: float,
    sigma: float,
    n_sim: int,
    n_boot: int,
    n_perm: int,
    alpha: float,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    hits = 0
    distinguishable = 0
    for _ in range(n_sim):
        diffs = [rng.gauss(true_mean, sigma) for _ in range(n)]
        verdict = paired_lift_verdict(
            diffs,
            alpha=alpha,
            n_boot=n_boot,
            n_perm=n_perm,
            seed=rng.randint(0, 2**31 - 1),
        )
        if verdict.excludes_null and verdict.point_estimate > 0:
            hits += 1
        if verdict.status.value == "MEASURED_AND_DISTINGUISHABLE":
            distinguishable += 1
    return {
        "power_ci_excludes_zero_positive": hits / n_sim,
        "fraction_distinguishable_status": distinguishable / n_sim,
        "n_sim": n_sim,
        "n_boot": n_boot,
        "n_perm": n_perm,
    }


def binomial_half_width(n: int, p: float = 0.5, z: float = 1.959963984540054) -> float:
    return z * math.sqrt(p * (1.0 - p) / n) if n > 0 else float("inf")


def hanley_mcneil_se(n_pos: int, n_neg: int, auc: float = 0.75) -> float:
    if n_pos <= 0 or n_neg <= 0:
        return float("nan")
    q1 = auc / (2.0 - auc)
    q2 = 2.0 * auc * auc / (1.0 + auc)
    return math.sqrt(
        (
            auc * (1.0 - auc)
            + (n_pos - 1) * (q1 - auc * auc)
            + (n_neg - 1) * (q2 - auc * auc)
        )
        / (n_pos * n_neg)
    )


def annotation_burden(n_items: int, n_annotators: int = 2) -> dict:
    coordinates_per_item = 9
    return {
        "items": n_items,
        "annotators": n_annotators,
        "item_judgement_units": n_items * n_annotators,
        "coordinate_judgement_units": n_items * n_annotators * coordinates_per_item,
        "adjudication_items": n_items,
        "note": (
            "Two full independent annotations plus distinct adjudication and "
            "provenance audit; units count rubric coordinates, not wall hours."
        ),
    }


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    seed = int(config["seed"])
    alpha = float(config["alpha"])
    n_grid = list(config["n_grid"])
    mde_grid = list(config["primary_mde_brier_reduction_grid"])
    sigma_grid = list(config["paired_brier_diff_sigma_grid"])
    mc = config["monte_carlo_validation"]

    analytic_rows = []
    for sigma in sigma_grid:
        for mde in mde_grid:
            for n in n_grid:
                analytic_rows.append(
                    {
                        "n": n,
                        "mde_brier_reduction": mde,
                        "sigma": sigma,
                        "analytic_power": analytic_power_mean_ci_excludes_zero(
                            n=n, true_mean=mde, sigma=sigma, alpha=alpha
                        ),
                        "cohen_d": mde / sigma if sigma else None,
                    }
                )

    mc_rows = []
    for cell in mc["cells"]:
        mc_rows.append(
            {
                **cell,
                **monte_carlo_power(
                    n=int(cell["n"]),
                    true_mean=float(cell["mde_brier_reduction"]),
                    sigma=float(cell["sigma"]),
                    n_sim=int(mc["n_sim"]),
                    n_boot=int(mc["n_boot"]),
                    n_perm=int(mc["n_perm"]),
                    alpha=alpha,
                    seed=seed + int(cell["n"]) * 1009 + int(round(cell["sigma"] * 1000)),
                ),
            }
        )

    secondary = []
    for n in n_grid:
        n_pos = n // 2
        n_neg = n - n_pos
        q_n = max(n // 2, 1)
        secondary.append(
            {
                "n": n,
                "assumed_pos_neg": [n_pos, n_neg],
                "hanley_mcneil_se_auc_at_0_75": hanley_mcneil_se(n_pos, n_neg, 0.75),
                "hanley_mcneil_se_auc_at_0_70": hanley_mcneil_se(n_pos, n_neg, 0.70),
                "auc_gain_0_05_in_se_units_at_auc_0_75": (
                    0.05 / hanley_mcneil_se(n_pos, n_neg, 0.75)
                ),
                "q2_q3_binomial_half_width_p0_5": binomial_half_width(q_n, 0.5),
                "q2_threshold_0_8_distance_in_halfwidths": (
                    abs(0.8 - 0.5) / binomial_half_width(q_n, 0.5)
                ),
                "one_item_flip_delta_on_half_set": 1.0 / q_n,
                "annotation_burden": annotation_burden(n),
                "lofo_train_items_if_4_equal_families": n - (n // 4),
            }
        )

    family_sensitivity = []
    for n in n_grid:
        for n_families in (4, 6, 8):
            if n % n_families != 0:
                continue
            per = n // n_families
            for rho in (0.0, 0.3, 0.5, 0.7):
                deff = 1.0 + (per - 1) * rho
                n_eff = n / deff
                family_sensitivity.append(
                    {
                        "n": n,
                        "n_families": n_families,
                        "items_per_family": per,
                        "intra_family_rho": rho,
                        "design_effect": deff,
                        "n_effective": n_eff,
                    }
                )

    results = {
        "schema_version": "paper3-power-results-v1",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_path": "research/paper3/power_design/POWER_SIMULATION_CONFIG.json",
        "config_sha256": canonical_sha256(config),
        "simulation_script_sha256": canonical_sha256(
            Path(__file__).read_text(encoding="utf-8")
        ),
        "claim_boundary": (
            "Label-blind design study only. No annotation, adjudication, "
            "descriptor-as-label, confirmatory gate pass, or training "
            "authorization is claimed."
        ),
        "primary_endpoint": config["primary_endpoint"],
        "registered_material_effects": config["registered_material_effects"],
        "analytic_power_grid": analytic_rows,
        "monte_carlo_validation": mc_rows,
        "secondary_resolution": secondary,
        "family_cluster_sensitivity": family_sensitivity,
        "summary_rules": {
            "adequate_power_threshold": config["adequate_power_threshold"],
            "path_a_requires": (
                "For every registered material sigma in the decision set, "
                "analytic_power at n=16 for the primary MDE must be "
                ">= adequate_power_threshold, and Monte Carlo cells at n=16 "
                "must agree within tolerance."
            ),
        },
    }
    out = OUT_DIR / "POWER_RESULTS.json"
    out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    print("config_sha256", results["config_sha256"])
    primary_mde = config["registered_material_effects"]["primary_paired_brier_reduction_mde"]
    print(f"primary_mde={primary_mde}")
    for sigma in config["decision_sigma_set"]:
        for n in n_grid:
            p = analytic_power_mean_ci_excludes_zero(
                n=n, true_mean=primary_mde, sigma=sigma, alpha=alpha
            )
            print(f"  sigma={sigma} n={n} analytic_power={p:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
