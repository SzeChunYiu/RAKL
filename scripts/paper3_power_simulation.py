#!/usr/bin/env python3
"""Label-blind power / MDE study for Paper III confirmatory packet (#248).

Uses only protocol-level assumptions and the stdlib paired-inference helpers in
``rakl.inference``. No external labels are read. Outputs are written under
``research/paper3_power/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rakl.inference import paired_lift_verdict

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "paper3_power"
ANNOTATION_DIR = ROOT / "research" / "paper3" / "annotation"
PACKET_PATH = ANNOTATION_DIR / "EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json"
SOURCE_PATH = ANNOTATION_DIR / "SOURCE_ITEM_SET_V2_1_20260810.json"

# Frozen design choices — change only by issuing a new config version.
CONFIG: dict[str, Any] = {
    "schema_version": "paper3-power-simulation-config-v1",
    "issue": 248,
    "primary_quantity": "paired_item_brier_reduction",
    "primary_definition": (
        "For each item i, brier_control_i - brier_structural_i with "
        "brier=(p-label)^2. Positive means structural witness reduces Brier "
        "relative to the strongest admissible non-structural control."
    ),
    "secondary_quantities": [
        "roc_auc_gain",
        "average_precision_gain",
        "q2_true_accept_rate",
        "q3_false_accept_rate",
    ],
    "material_effect_targets": {
        "primary_mde_brier_reduction": 0.05,
        "secondary_mde_brier_reduction_grid": [0.03, 0.05, 0.08, 0.10],
        "q2_floor_improvement": 0.15,
        "q3_ceiling_reduction": 0.15,
        "rationale": (
            "0.05 mean paired Brier reduction is the smallest effect that would "
            "justify Paper III's additional structural-witness layer as more than "
            "noise under the registered paired bootstrap/sign-flip gate "
            "(alpha=0.05). Smaller effects remain scientifically interesting but "
            "are treated as exploratory under a power-limited packet."
        ),
    },
    "n_grid": [16, 24, 32, 48, 64],
    "n_families_current": 4,
    "items_per_family_current": 4,
    "class_balances": [0.40, 0.50, 0.60],
    "control_structural_correlations": [0.20, 0.50, 0.80],
    "score_noise_sd": 0.18,
    "monte_carlo_trials": 120,
    "inference": {
        "alpha": 0.05,
        "n_boot": 600,
        "n_perm": 600,
        "seed": 24801,
    },
    "target_power": 0.80,
    "annotation_burden_model": {
        "annotators": 2,
        "adjudicator": 1,
        "minutes_per_item_per_annotator": 12,
        "minutes_per_item_adjudication": 6,
        "feasible_person_hours_ceiling": 24,
    },
    "grants_scientific_authority": False,
}


def _git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_zero_labels() -> dict[str, Any]:
    """Fail closed if any external judgement payload is present."""
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    judgement_fields = list(packet["instructions"]["judgement_fields"])
    contaminated: list[str] = []
    for item in packet["items"]:
        for field in judgement_fields:
            if field in item:
                contaminated.append(f"{item.get('item_id')}:{field}")

    suspicious_files: list[str] = []
    deny_tokens = (
        "submission",
        "annotator_a",
        "annotator_b",
        "adjudicat",
        "judgement_result",
        "judgment_result",
        "label_import",
    )
    for path in ANNOTATION_DIR.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if any(tok in name for tok in deny_tokens):
            suspicious_files.append(str(path.relative_to(ROOT)))

    status = "ZERO_LABELS_VERIFIED"
    if contaminated or suspicious_files:
        status = "LABEL_WINDOW_CLOSED"

    return {
        "schema_version": "paper3-zero-labels-at-power-design-v1",
        "status": status,
        "observed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_subject_sha": _git_sha(),
        "packet_path": str(PACKET_PATH.relative_to(ROOT)),
        "packet_sha256": _sha256_file(PACKET_PATH),
        "source_set_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_set_sha256": _sha256_file(SOURCE_PATH),
        "packet_item_count": len(packet["items"]),
        "judgement_fields_checked": judgement_fields,
        "contaminated_item_fields": contaminated,
        "suspicious_files": suspicious_files,
        "family_field_present_in_public_packet": all(
            "family" in item for item in packet["items"]
        ),
        "family_leak_note": (
            "Public packet item_ids are opaque (p3item-*), unlike the private "
            "source_item_id p3src-* series. No expected-outcome / near_miss / Q2 / "
            "Q3 tokens appear in public identifiers. Residual: the public packet "
            "still exposes a `family` string per item, which enables clustering "
            "and is weaker than case_id-answer leakage but is not fully "
            "label-blind metadata. Strip or hash family in any annotator-facing "
            "export before #217 starts; do not retune items after labels."
        ),
        "grants_scientific_authority": False,
    }


def _clip01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def simulate_paired_brier_diffs(
    *,
    n: int,
    mean_lift: float,
    balance: float,
    correlation: float,
    noise_sd: float,
    rng: random.Random,
) -> list[float]:
    """Simulate per-item Brier reductions under a registered alternative.

    Labels ~ Bern(balance). Control and structural latent scores share a common
    factor (correlation) plus independent noise. Structural gets a mean edge
    calibrated so E[brier_control - brier_structural] approximates ``mean_lift``
    under the clip-to-[0,1] score map. Exact calibration is not required; the
    Monte Carlo estimates power under this protocol-level generative model.
    """
    diffs: list[float] = []
    # Convert desired Brier lift into a rough score edge. For labels near 0.5 and
    # scores near 0.5, a score improvement of d yields ~d Brier change order.
    score_edge = mean_lift
    shared_sd = math.sqrt(max(correlation, 0.0)) * noise_sd
    indep_sd = math.sqrt(max(1.0 - correlation, 0.0)) * noise_sd
    for _ in range(n):
        label = 1 if rng.random() < balance else 0
        shared = rng.gauss(0.0, shared_sd)
        control = _clip01(0.5 + shared + rng.gauss(0.0, indep_sd))
        structural = _clip01(
            0.5 + shared + score_edge * (1 if label == 1 else -1) + rng.gauss(0.0, indep_sd)
        )
        brier_c = (control - label) ** 2
        brier_s = (structural - label) ** 2
        diffs.append(brier_c - brier_s)
    return diffs


def power_at(
    *,
    n: int,
    mean_lift: float,
    balance: float,
    correlation: float,
    trials: int,
    base_seed: int,
    inference: dict[str, Any],
    noise_sd: float,
) -> dict[str, Any]:
    exclusions = 0
    point_estimates: list[float] = []
    for t in range(trials):
        rng = random.Random(base_seed + 1009 * t + 17 * n)
        diffs = simulate_paired_brier_diffs(
            n=n,
            mean_lift=mean_lift,
            balance=balance,
            correlation=correlation,
            noise_sd=noise_sd,
            rng=rng,
        )
        verdict = paired_lift_verdict(
            diffs,
            alpha=inference["alpha"],
            n_boot=inference["n_boot"],
            n_perm=inference["n_perm"],
            seed=inference["seed"] + t,
        )
        point_estimates.append(verdict.point_estimate)
        if verdict.excludes_null and verdict.point_estimate > 0:
            exclusions += 1
    return {
        "n": n,
        "mean_lift": mean_lift,
        "balance": balance,
        "correlation": correlation,
        "trials": trials,
        "power_ci_excludes_zero_positive": exclusions / trials,
        "mean_point_estimate": sum(point_estimates) / len(point_estimates),
    }


def q_binomial_resolution(n: int, rate: float, alpha: float = 0.05) -> dict[str, Any]:
    """Wald half-width for a binomial rate — resolution scale, not a claim."""
    se = math.sqrt(rate * (1.0 - rate) / n) if n else float("inf")
    z = 1.959963984540054  # Phi^{-1}(0.975)
    half = z * se
    return {
        "n": n,
        "assumed_rate": rate,
        "approx_95_half_width": half,
        "alpha": alpha,
        "note": "Normal approximation; used only to size Q2/Q3 resolution.",
    }


def annotation_burden(n: int, model: dict[str, Any]) -> dict[str, Any]:
    ann_hours = (
        n * model["annotators"] * model["minutes_per_item_per_annotator"]
    ) / 60.0
    adj_hours = (n * model["minutes_per_item_adjudication"]) / 60.0
    total = ann_hours + adj_hours
    return {
        "n": n,
        "annotator_person_hours": ann_hours,
        "adjudication_person_hours": adj_hours,
        "total_person_hours": total,
        "feasible_under_ceiling": total <= model["feasible_person_hours_ceiling"],
        "ceiling_person_hours": model["feasible_person_hours_ceiling"],
    }


def family_lofo_effective_n(n_items: int, n_families: int) -> dict[str, Any]:
    if n_families <= 0:
        return {"error": "n_families must be positive"}
    per = n_items // n_families
    train = n_items - per
    return {
        "n_items": n_items,
        "n_families": n_families,
        "items_per_family": per,
        "lofo_train_n": train,
        "note": (
            "Leave-one-family-out confirmatory folds train on n - items_per_family. "
            "Power figures that ignore clustering overstate usable n."
        ),
    }


def run_study(config: dict[str, Any]) -> dict[str, Any]:
    inference = config["inference"]
    mde = config["material_effect_targets"]["primary_mde_brier_reduction"]
    rows: list[dict[str, Any]] = []
    # Primary surface: balance=0.5, correlation=0.5 across n grid and MDE grid.
    for n in config["n_grid"]:
        for lift in config["material_effect_targets"]["secondary_mde_brier_reduction_grid"]:
            rows.append(
                power_at(
                    n=n,
                    mean_lift=lift,
                    balance=0.5,
                    correlation=0.5,
                    trials=config["monte_carlo_trials"],
                    base_seed=config["inference"]["seed"],
                    inference=inference,
                    noise_sd=config["score_noise_sd"],
                )
            )
    # Sensitivity at primary MDE / n=16 and n=32.
    sensitivity: list[dict[str, Any]] = []
    for n in (16, 32):
        for balance in config["class_balances"]:
            for corr in config["control_structural_correlations"]:
                sensitivity.append(
                    power_at(
                        n=n,
                        mean_lift=mde,
                        balance=balance,
                        correlation=corr,
                        trials=config["monte_carlo_trials"],
                        base_seed=config["inference"]["seed"] + 777,
                        inference=inference,
                        noise_sd=config["score_noise_sd"],
                    )
                )

    n16 = [r for r in rows if r["n"] == 16 and r["mean_lift"] == mde][0]
    n_needed = None
    for n in config["n_grid"]:
        cell = [r for r in rows if r["n"] == n and r["mean_lift"] == mde][0]
        if cell["power_ci_excludes_zero_positive"] >= config["target_power"]:
            n_needed = n
            break

    burdens = [annotation_burden(n, config["annotation_burden_model"]) for n in config["n_grid"]]
    lofo = family_lofo_effective_n(
        16, config["n_families_current"]
    )

    return {
        "schema_version": "paper3-power-results-v1",
        "config_schema_version": config["schema_version"],
        "primary_mde": mde,
        "target_power": config["target_power"],
        "n16_primary_power": n16,
        "smallest_n_reaching_target_power_at_mde": n_needed,
        "power_grid": rows,
        "sensitivity_at_mde": sensitivity,
        "q2_q3_resolution": {
            "n16": q_binomial_resolution(16, 0.5),
            "n32": q_binomial_resolution(32, 0.5),
            "n64": q_binomial_resolution(64, 0.5),
        },
        "family_lofo_current_packet": lofo,
        "annotation_burden": burdens,
        "grants_scientific_authority": False,
    }


def decide(zero: dict[str, Any], results: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if zero["status"] != "ZERO_LABELS_VERIFIED":
        return {
            "schema_version": "paper3-power-decision-v1",
            "decision": "WINDOW_CLOSED_RETAIN_V2_1",
            "path": "CLOSED",
            "rationale": (
                "External labels or suspicious judgement artifacts were detected. "
                "Power redesign is forbidden; retain frozen v2.1 packet."
            ),
            "grants_scientific_authority": False,
        }

    mde = results["primary_mde"]
    n16_power = results["n16_primary_power"]["power_ci_excludes_zero_positive"]
    n_needed = results["smallest_n_reaching_target_power_at_mde"]
    burden_by_n = {b["n"]: b for b in results["annotation_burden"]}

    if n16_power >= config["target_power"]:
        decision = {
            "decision": "RETAIN_V2_1_ADEQUATELY_POWERED",
            "path": "A",
            "rationale": (
                f"At registered MDE={mde}, n=16 Monte Carlo power is {n16_power:.3f} "
                f">= target {config['target_power']}."
            ),
        }
    elif (
        n_needed is not None
        and burden_by_n[n_needed]["feasible_under_ceiling"]
    ):
        decision = {
            "decision": "EXPAND_BEFORE_LABELS",
            "path": "B",
            "recommended_n": n_needed,
            "rationale": (
                f"n=16 power {n16_power:.3f} < {config['target_power']} at MDE={mde}; "
                f"n={n_needed} reaches target under the burden ceiling."
            ),
        }
    else:
        decision = {
            "decision": "CONFIRMATORY_PACKET_POWER_LIMITED",
            "path": "C",
            "retain_packet": "EXTERNAL_ANNOTATION_PACKET_V2_1_20260810",
            "rationale": (
                f"n=16 Monte Carlo power at MDE={mde} is {n16_power:.3f}, below "
                f"target {config['target_power']}. "
                + (
                    f"Adequate n={n_needed} exceeds the frozen annotation-burden ceiling "
                    f"of {config['annotation_burden_model']['feasible_person_hours_ceiling']} "
                    "person-hours."
                    if n_needed is not None
                    else "No n in the registered grid reached target power under the "
                    "simulation model."
                )
                + " Retain v2.1 as an exploratory / limited-sample human validation. "
                "Wide nulls and INDISTINGUISHABLE / UNDERPOWERED outcomes are "
                "inconclusive, not refutation. Do not expand after any label arrives."
            ),
        }

    return {
        "schema_version": "paper3-power-decision-v1",
        "issue": 248,
        "observed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_subject_sha": zero["git_subject_sha"],
        "zero_labels_status": zero["status"],
        "primary_quantity": config["primary_quantity"],
        "primary_mde_brier_reduction": mde,
        "n16_power_at_mde": n16_power,
        "smallest_n_reaching_target_power_at_mde": n_needed,
        "manuscript_wording_required": (
            "power-limited exploratory/limited-sample human validation"
            if decision["path"] == "C"
            else (
                "adequately powered confirmatory design frozen before labels"
                if decision["path"] == "A"
                else "expanded label-blind confirmatory packet frozen before labels"
            )
        ),
        "interpretation_rules": {
            "UNDERPOWERED_or_INDISTINGUISHABLE": (
                "Treat as inconclusive for confirmatory claims; do not market as "
                "refutation of structural-witness value."
            ),
            "decoupling_rate_zero": (
                "If post-adjudication decoupling_rate==0 for transfer_valid vs "
                "AND(invariant,boundary,qoi,directional), report witnessed_structure "
                "as NOT_INFORMATIVE regardless of AUC."
            ),
        },
        "family_metadata_action": (
            "Before #217 annotator work, export an annotator-facing packet that "
            "omits or hashes `family` while preserving opaque item_id. Do not "
            "change source texts after labels."
        ),
        **decision,
        "grants_scientific_authority": False,
    }


def write_markdown(decision: dict[str, Any], results: dict[str, Any], config: dict[str, Any]) -> str:
    lines = [
        "# Paper III confirmatory power design (#248)",
        "",
        f"Status: `{decision['decision']}` (path {decision['path']})",
        "",
        "## Hard chronology",
        "",
        f"- Zero-label status at decision: `{decision['zero_labels_status']}`",
        f"- Git subject: `{decision['git_subject_sha']}`",
        "",
        "## Registered primary quantity",
        "",
        f"- `{config['primary_quantity']}`",
        f"- Material MDE: **{config['material_effect_targets']['primary_mde_brier_reduction']}** "
        "mean paired Brier reduction",
        f"- Target power: {config['target_power']} at alpha="
        f"{config['inference']['alpha']}",
        "",
        "## Headline simulation result",
        "",
        f"- n=16 power at MDE: **{decision['n16_power_at_mde']:.3f}**",
        f"- Smallest n in grid reaching target: "
        f"`{decision['smallest_n_reaching_target_power_at_mde']}`",
        f"- LOFO train n on current packet: "
        f"{results['family_lofo_current_packet']['lofo_train_n']}",
        "",
        "## Decision",
        "",
        decision["rationale"],
        "",
        "## Manuscript wording",
        "",
        decision["manuscript_wording_required"],
        "",
        "## Interpretation rules",
        "",
        f"- UNDERPOWERED/INDISTINGUISHABLE: {decision['interpretation_rules']['UNDERPOWERED_or_INDISTINGUISHABLE']}",
        f"- Decoupling rate: {decision['interpretation_rules']['decoupling_rate_zero']}",
        "",
        "## Family metadata",
        "",
        decision["family_metadata_action"],
        "",
        "## Authority",
        "",
        "Proposal-only design freeze. Grants no scientific authority and does not "
        "authorize training.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    zero = verify_zero_labels()
    if zero["status"] != "ZERO_LABELS_VERIFIED":
        (out / "ZERO_LABELS_AT_POWER_DESIGN.json").write_text(
            json.dumps(zero, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        decision = decide(zero, {"primary_mde": None, "n16_primary_power": {"power_ci_excludes_zero_positive": None}, "smallest_n_reaching_target_power_at_mde": None, "annotation_burden": []}, CONFIG)
        (out / "DECISION_RECEIPT.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise SystemExit("LABEL_WINDOW_CLOSED: refusing power redesign")

    config = dict(CONFIG)
    config_path = out / "POWER_SIMULATION_CONFIG.json"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    config["config_sha256"] = hashlib.sha256(config_path.read_bytes()).hexdigest()

    results = run_study(config)
    results["config_sha256"] = config["config_sha256"]
    results["generated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results["git_subject_sha"] = zero["git_subject_sha"]

    decision = decide(zero, results, config)

    (out / "ZERO_LABELS_AT_POWER_DESIGN.json").write_text(
        json.dumps(zero, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "POWER_RESULTS.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "DECISION_RECEIPT.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "PAPER3_POWER_DESIGN.md").write_text(
        write_markdown(decision, results, config), encoding="utf-8"
    )

    # Rewrite config with hash field for audit binding.
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(decision["decision"], f"n16_power={decision['n16_power_at_mde']:.3f}")
    print(out)


if __name__ == "__main__":
    main()
