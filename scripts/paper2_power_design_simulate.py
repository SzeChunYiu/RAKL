#!/usr/bin/env python3
"""Outcome-blind power / MDE study for Paper II ExperienceBenchmark (#247).

Deterministic stdlib-only simulation. Does not access ORACLE/diagnostic-arm
outcomes or evaluated confirmatory results. Writes:

  research/paper2/power_design/POWER_RESULTS.json

Run from repository root:

  python3 scripts/paper2_power_design_simulate.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.inference import paired_lift_verdict  # noqa: E402
from rakl.paper2_power_design import analytic_power_mean_ci_excludes_zero  # noqa: E402
from rakl.v3_authority import canonical_sha256  # noqa: E402

OUT_DIR = ROOT / "research" / "paper2" / "power_design"
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


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    alpha = float(config["alpha"])
    threshold = float(config["adequate_power_threshold"])
    primary_mde = float(config["registered_material_effects"]["primary_paired_success_rate_lift_mde"])
    sigmas = [float(s) for s in config["decision_sigma_set"]]
    mc = config["monte_carlo_validation"]

    analytic_power_grid: list[dict] = []
    for n in config["n_grid"]:
        for mde in config["primary_mde_success_rate_lift_grid"]:
            for sigma in config["paired_success_diff_sigma_grid"]:
                power = analytic_power_mean_ci_excludes_zero(
                    n=int(n),
                    true_mean=float(mde),
                    sigma=float(sigma),
                    alpha=alpha,
                )
                analytic_power_grid.append(
                    {
                        "n": int(n),
                        "mde_success_rate_lift": float(mde),
                        "sigma": float(sigma),
                        "analytic_power": power,
                        "adequate": power >= threshold,
                    }
                )

    monte_carlo_validation: list[dict] = []
    for cell in mc["cells"]:
        row = monte_carlo_power(
            n=int(cell["n"]),
            true_mean=float(cell["mde_success_rate_lift"]),
            sigma=float(cell["sigma"]),
            n_sim=int(mc["n_sim"]),
            n_boot=int(mc["n_boot"]),
            n_perm=int(mc["n_perm"]),
            alpha=alpha,
            seed=int(config["seed"]) + int(cell["n"]) * 1000 + int(cell["sigma"] * 1000),
        )
        monte_carlo_validation.append(
            {
                "n": int(cell["n"]),
                "mde_success_rate_lift": float(cell["mde_success_rate_lift"]),
                "sigma": float(cell["sigma"]),
                **row,
            }
        )

    payload = {
        "schema_version": "paper2-power-results-v1",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_path": str(CONFIG_PATH.relative_to(ROOT)),
        "config_sha256": canonical_sha256(config),
        "analytic_power_grid": analytic_power_grid,
        "monte_carlo_validation": monte_carlo_validation,
        "claim_boundary": (
            "Simulation-only power study. No ORACLE outcome, no diagnostic-arm result, "
            "and no experience-learning claim is implied."
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "POWER_RESULTS.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
