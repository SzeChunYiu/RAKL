"""Label-blind Paper II ExperienceBenchmark power design (#247).

Verifies zero confirmatory outcomes for the root-cause successor packet,
runs no evaluated arm access, and freezes MDE / task-count requirements
before any ORACLE or diagnostic-arm execution.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .inference import paired_lift_verdict
from .v3_authority import canonical_sha256

POWER_DIR = Path("research/paper2/power_design")
SUCCESSOR_PACKET_DIR = Path("research/paper2_experience_benchmark_root_cause_v1")
CONFIG_PATH = POWER_DIR / "POWER_SIMULATION_CONFIG.json"
RESULTS_PATH = POWER_DIR / "POWER_RESULTS.json"
ZERO_OUTCOMES_PATH = POWER_DIR / "ZERO_OUTCOMES_AT_POWER_DESIGN.json"
DECISION_PATH = POWER_DIR / "DECISION_RECEIPT.json"
CAPABILITY_RECEIPT_PATH = Path("research/paper2/CAPABILITY_FLOOR_DECISION_RECEIPT.json")

_FORBIDDEN_OUTCOME_FRAGMENTS = (
    "native_job_",
    "harvest-",
    "result_receipt",
    "evaluated_outcome",
)
_ROOT_CAUSE_JOB_RE = re.compile(r"root_cause_v1.*job-\d+", re.IGNORECASE)


def git_head_sha(repo_root: Path) -> str:
    return (
        subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
        )
        .strip()
    )


def _norm_cdf(x: float) -> float:
    import math

    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def analytic_power_mean_ci_excludes_zero(
    *,
    n: int,
    true_mean: float,
    sigma: float,
    alpha: float = 0.05,
) -> float:
    import math

    if n <= 1 or sigma <= 0:
        return float("nan")
    z = 1.959963984540054
    se = sigma / math.sqrt(n)
    return 1.0 - _norm_cdf((z * se - true_mean) / se)


def verify_no_root_cause_confirmatory_outcomes(repo_root: Path) -> dict[str, Any]:
    """Ensure no successor-packet evaluated outcomes exist in the repository."""
    hits: list[str] = []
    successor = repo_root / SUCCESSOR_PACKET_DIR
    if successor.is_dir():
        for path in successor.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root).as_posix()
            lower = rel.lower()
            if any(fragment in lower for fragment in _FORBIDDEN_OUTCOME_FRAGMENTS):
                hits.append(rel)
            if _ROOT_CAUSE_JOB_RE.search(rel):
                hits.append(rel)
            if path.suffix == ".json":
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if payload.get("evaluated_outcome") is True:
                    hits.append(rel)
                if payload.get("success_rate") is not None and payload.get("arm"):
                    hits.append(rel)

    return {
        "successor_packet_dir": str(SUCCESSOR_PACKET_DIR),
        "imported_evaluated_outcome_paths": sorted(set(hits)),
        "verdict": "ZERO_CONFIRMATORY_OUTCOMES" if not hits else "EVALUATED_OUTCOME_PRESENT",
    }


def build_zero_outcomes_at_power_design(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    outcome_scan = verify_no_root_cause_confirmatory_outcomes(repo_root)
    if outcome_scan["verdict"] != "ZERO_CONFIRMATORY_OUTCOMES":
        raise ValueError("root-cause successor packet already contains evaluated outcomes")

    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "paper2-zero-outcomes-at-power-design-v1",
        "observation": "ZERO_OUTCOMES_AT_POWER_DESIGN",
        "created_at_utc": created,
        "git_subject_sha256": git_head_sha(repo_root),
        "state": "ZERO_CONFIRMATORY_OUTCOMES_OBSERVED",
        "first_confirmatory_outcome_at_utc": None,
        "evaluated_arm_outcome_accessed": False,
        "counts": {
            "oracle_runs": 0,
            "diagnostic_arm_runs": 0,
            "powered_confirmatory_runs": 0,
        },
        "authority_source": {
            "repository": "SzeChunYiu/RAKL",
            "issue_number": 247,
            "blocked_by_compute": "CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE",
        },
        "outcome_directory_scan": outcome_scan,
        "parent_negative_history": {
            "paper2_experience_benchmark_v1_2_job": 3476548,
            "protocol_subject_hash": "c4ae092b70859d145b7a4b8a7d6485b3d2a552867756fec6783c1e35f7d5f352",
            "immutable": True,
            "reusable_as_confirmatory": False,
        },
        "claim_boundary": (
            "Outcome-free zero-observation immediately before the pre-execution power "
            "decision. Not independent review, not ORACLE evidence, and not an "
            "experience-learning efficacy claim."
        ),
    }


def evaluate_power_decision(
    config: dict[str, Any],
    results: dict[str, Any],
) -> dict[str, Any]:
    primary_mde = float(
        config["registered_material_effects"]["primary_paired_success_rate_lift_mde"]
    )
    threshold = float(config["adequate_power_threshold"])
    sigmas = [float(s) for s in config["decision_sigma_set"]]
    alpha = float(config["alpha"])
    n_current = int(config["current_underpowered_transfer_count"])
    n_target = int(config["successor_packet_transfer_task_count"])

    analytic_at_current = {
        str(sigma): analytic_power_mean_ci_excludes_zero(
            n=n_current,
            true_mean=primary_mde,
            sigma=sigma,
            alpha=alpha,
        )
        for sigma in sigmas
    }
    analytic_at_target = {
        str(sigma): analytic_power_mean_ci_excludes_zero(
            n=n_target,
            true_mean=primary_mde,
            sigma=sigma,
            alpha=alpha,
        )
        for sigma in sigmas
    }

    mc_tolerance = float(config.get("monte_carlo_tolerance", 0.1))
    mc_cells = [
        row
        for row in results["monte_carlo_validation"]
        if int(row["n"]) == n_target
        and float(row["mde_success_rate_lift"]) == primary_mde
        and float(row["sigma"]) in sigmas
    ]
    mc_agrees = True
    for row in mc_cells:
        sigma = float(row["sigma"])
        analytic = analytic_at_target[str(sigma)]
        mc_power = float(row["power_ci_excludes_zero_positive"])
        if abs(analytic - mc_power) > mc_tolerance:
            mc_agrees = False

    path_a = all(power >= threshold for power in analytic_at_target.values())
    path_a = path_a and mc_agrees and bool(mc_cells)

    min_n_for_adequacy: int | None = None
    for n in sorted(int(n) for n in config["n_grid"]):
        powers = [
            analytic_power_mean_ci_excludes_zero(
                n=n,
                true_mean=primary_mde,
                sigma=sigma,
                alpha=alpha,
            )
            for sigma in sigmas
        ]
        if all(p >= threshold for p in powers):
            min_n_for_adequacy = n
            break

    successor_frozen = bool(config["expansion_feasibility"].get("successor_packet_frozen_in_repo", False))
    ceiling_tasks = int(config["expansion_feasibility"].get("max_transfer_tasks_without_new_freeze", n_target))
    expansion_feasible = (
        min_n_for_adequacy is not None
        and min_n_for_adequacy <= ceiling_tasks
        and successor_frozen
    )

    if path_a:
        path = "A"
        decision = "SUCCESSOR_PACKET_ADEQUATELY_POWERED"
    elif expansion_feasible:
        path = "B"
        decision = "EXPAND_TASK_PANEL_BEFORE_EXECUTION"
    else:
        path = "C"
        decision = "CONFIRMATORY_PACKET_POWER_LIMITED"

    return {
        "path": path,
        "decision": decision,
        "primary_mde_success_rate_lift": primary_mde,
        "adequate_power_threshold": threshold,
        "decision_sigma_set": sigmas,
        "analytic_power_at_n_current": analytic_at_current,
        "analytic_power_at_n_target": analytic_at_target,
        "monte_carlo_agrees_at_n_target": mc_agrees,
        "minimum_n_for_adequacy_all_sigmas": min_n_for_adequacy,
        "successor_packet_frozen_in_repo": successor_frozen,
        "expansion_feasible_within_ceiling": expansion_feasible,
        "confirmatory_transfer_task_count_decision": (
            n_target if path != "B" else min_n_for_adequacy
        ),
        "underpowered_interpretation_rules": [
            "v1.2 n=3 transfer tasks is UNDERPOWERED for all registered primary contrasts.",
            "If paired bootstrap CI for primary success-rate lift includes zero, verdict is "
            "MEASURED_BUT_INDISTINGUISHABLE — not negative evidence.",
            "UNDERPOWERED status blocks confirmatory refutation or promotional experience claims.",
            "Hostile-near-miss harm contrast requires separate pre-registered MDE; a mean lift "
            "that crosses null while hostile safety degrades must narrow the architecture claim.",
        ],
    }


def build_decision_receipt(
    repo_root: Path,
    *,
    config: dict[str, Any],
    results: dict[str, Any],
    zero_outcomes: dict[str, Any],
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    evaluation = evaluate_power_decision(config, results)
    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    panel_path = SUCCESSOR_PACKET_DIR / "TASK_PANEL_DESIGN.json"
    protocol_path = SUCCESSOR_PACKET_DIR / "PROTOCOL_FREEZE_PACKET.json"
    panel = json.loads((repo_root / panel_path).read_text(encoding="utf-8"))
    protocol = json.loads((repo_root / protocol_path).read_text(encoding="utf-8"))

    return {
        "schema_version": "paper2-power-decision-receipt-v1",
        "receipt_id": "paper2-power-design-decision-20260811",
        "created_at_utc": created,
        "git_subject_sha256": zero_outcomes["git_subject_sha256"],
        "issue_number": 247,
        "decision_path": evaluation["path"],
        "decision": evaluation["decision"],
        "confirmatory_packet_version": "root_cause_v1",
        "confirmatory_transfer_task_count": evaluation["confirmatory_transfer_task_count_decision"],
        "material_effects": config["registered_material_effects"],
        "primary_endpoint": config["primary_endpoint"],
        "headline_contrasts": config["headline_contrasts"],
        "power_evaluation": evaluation,
        "frozen_artifacts": {
            "zero_outcomes_receipt_sha256": canonical_sha256(zero_outcomes),
            "config_sha256": results["config_sha256"],
            "results_sha256": canonical_sha256(results),
            "task_panel_path": str(panel_path),
            "task_panel_sha256": hashlib.sha256((repo_root / panel_path).read_bytes()).hexdigest(),
            "task_panel_canonical_sha256": canonical_sha256(panel),
            "protocol_path": str(protocol_path),
            "protocol_canonical_sha256": canonical_sha256(protocol),
        },
        "execution_gate": {
            "oracle_required_before_diagnostic_arms": True,
            "local_model_assets_available": False,
            "lunarc_required_for_oracle": True,
            "blocked_status": "CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE",
        },
        "claim_boundary": (
            "Pre-execution power-design decision only. No ORACLE run, no diagnostic-arm "
            "outcome, no experience-learning efficacy claim, and no capability-floor clearance."
        ),
    }


def paired_lift_verdict_from_diffs(diffs: list[float], **kwargs: Any) -> dict[str, Any]:
    verdict = paired_lift_verdict(diffs, **kwargs)
    return {
        "point_estimate": verdict.point_estimate,
        "ci_lo": verdict.ci_lo,
        "ci_hi": verdict.ci_hi,
        "p_value": verdict.p_value,
        "excludes_null": verdict.excludes_null,
        "status": verdict.status.value,
        "n": verdict.n,
        "alpha": verdict.alpha,
    }
