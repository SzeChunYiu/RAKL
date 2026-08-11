"""Label-blind Paper III confirmatory power design (#248).

Verifies zero external labels, runs no label access, and evaluates whether the
frozen v2.1 packet is adequately powered for preregistered material effects.
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
from .paper3_annotation import canonical_sha256

ANNOTATION_DIR = Path("research/paper3/annotation")
POWER_DIR = Path("research/paper3/power_design")
CONFIG_PATH = POWER_DIR / "POWER_SIMULATION_CONFIG.json"
RESULTS_PATH = POWER_DIR / "POWER_RESULTS.json"
ZERO_LABELS_PATH = POWER_DIR / "ZERO_LABELS_AT_POWER_DESIGN.json"
DECISION_PATH = POWER_DIR / "DECISION_RECEIPT.json"

_ALLOWED_ANNOTATION_SUFFIXES = {
    ".json",
    ".md",
}
_FORBIDDEN_ANNOTATION_NAME_FRAGMENTS = (
    "submission",
    "adjudication",
    "provenance_audit",
    "annotator_response",
    "evaluated_result",
)
_FROZEN_PUBLIC_PREFIXES = (
    "EXTERNAL_ANNOTATION_PACKET_",
    "SOURCE_ITEM_SET_",
    "RUBRIC_",
    "README_",
)


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


def verify_public_annotation_directory(repo_root: Path) -> dict[str, Any]:
    """Ensure the public annotation dir holds frozen inputs only.

    Demoted AI_OPERATOR trees (explicit independent_external_human=false) may
    live under a carved-out subdirectory; they are not public external-human
    payloads and do not satisfy Constitution-grade #217 review.
    """
    annotation_dir = repo_root / ANNOTATION_DIR
    if not annotation_dir.is_dir():
        raise ValueError(f"missing annotation directory: {annotation_dir}")

    files: list[str] = []
    forbidden: list[str] = []
    unexpected: list[str] = []
    demoted_ai_operator_dirs: list[str] = []

    for path in sorted(annotation_dir.iterdir()):
        if path.name.startswith("."):
            continue
        if path.is_dir():
            if path.name == "ai_operator_v2_1":
                demoted_ai_operator_dirs.append(
                    path.relative_to(repo_root).as_posix()
                )
                continue
            forbidden.append(str(path.relative_to(repo_root)))
            continue
        if not path.is_file():
            forbidden.append(str(path.relative_to(repo_root)))
            continue
        files.append(path.name)
        lower = path.name.lower()
        if any(fragment in lower for fragment in _FORBIDDEN_ANNOTATION_NAME_FRAGMENTS):
            forbidden.append(path.name)
            continue
        if path.suffix not in _ALLOWED_ANNOTATION_SUFFIXES:
            unexpected.append(path.name)
            continue
        if path.suffix == ".json" and not any(
            path.name.startswith(prefix) for prefix in _FROZEN_PUBLIC_PREFIXES
        ):
            unexpected.append(path.name)

    ok = not forbidden and not unexpected
    return {
        "annotation_dir": str(ANNOTATION_DIR),
        "files_observed": files,
        "demoted_ai_operator_dirs": demoted_ai_operator_dirs,
        "forbidden_payload_files": forbidden,
        "unexpected_files": unexpected,
        "verdict": "ZERO_PUBLIC_ANNOTATION_PAYLOADS" if ok else "FORBIDDEN_PAYLOAD_PRESENT",
    }


def verify_issue_217_zero_public_responses(repo_root: Path) -> dict[str, Any]:
    """Scan repository for imported external annotation payloads."""
    patterns = (
        re.compile(r"paper3-external-annotation-submission"),
        re.compile(r"paper3-adjudication"),
        re.compile(r"paper3-provenance-audit"),
    )
    hits: list[str] = []
    for path in repo_root.rglob("*.json"):
        rel = path.relative_to(repo_root).as_posix()
        if "/paper3/annotation/" not in rel:
            continue
        # Demoted AI_OPERATOR payloads are operator-override compute enablers,
        # not imported independent external-human responses for #217.
        if "/ai_operator_v2_1/" in rel:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        schema_version = payload.get("schema_version", "")
        if any(pattern.search(schema_version) for pattern in patterns):
            hits.append(rel)
        elif payload.get("annotator_id") and payload.get("items"):
            hits.append(rel)

    return {
        "issue_number": 217,
        "repository": "SzeChunYiu/RAKL",
        "imported_external_payload_paths": hits,
        "verdict": "ZERO_IMPORTED_EXTERNAL_PAYLOADS" if not hits else "IMPORTED_PAYLOAD_PRESENT",
    }


def build_zero_labels_at_power_design(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    git_subject = git_head_sha(repo_root)
    annotation_scan = verify_public_annotation_directory(repo_root)
    issue_scan = verify_issue_217_zero_public_responses(repo_root)

    if annotation_scan["verdict"] != "ZERO_PUBLIC_ANNOTATION_PAYLOADS":
        raise ValueError("public annotation directory contains forbidden payloads")
    if issue_scan["verdict"] != "ZERO_IMPORTED_EXTERNAL_PAYLOADS":
        raise ValueError("imported external annotation payloads detected")

    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "paper3-zero-labels-at-power-design-v1",
        "observation": "ZERO_LABELS_AT_POWER_DESIGN",
        "created_at_utc": created,
        "git_subject_sha256": git_subject,
        "state": "ZERO_LABELS_OBSERVED",
        "first_external_label_at_utc": None,
        "label_payload_accessed": False,
        "counts": {
            "external_annotations": 0,
            "adjudications": 0,
            "evaluated_results": 0,
        },
        "authority_source": {
            "repository": "SzeChunYiu/RAKL",
            "issue_number": 248,
            "blocked_annotation_issue": 217,
        },
        "annotation_directory_scan": annotation_scan,
        "issue_217_scan": issue_scan,
        "descriptor_status": {
            "v2_1_descriptors_exist": True,
            "deferred_reason": (
                "Strong semantic descriptors for all sixteen v2.1 items were harvested "
                "label-blind before this power decision (jobs 3476527-3476529); no new "
                "descriptor run is required for Path C retain."
            ),
        },
        "claim_boundary": (
            "Payload-free zero-label observation immediately before the pre-label power "
            "decision. Not independent review, not annotation evidence, and not training "
            "authorization."
        ),
    }


def evaluate_power_decision(
    config: dict[str, Any],
    results: dict[str, Any],
) -> dict[str, Any]:
    primary_mde = config["registered_material_effects"]["primary_paired_brier_reduction_mde"]
    threshold = float(config["adequate_power_threshold"])
    sigmas = list(config["decision_sigma_set"])
    alpha = float(config["alpha"])
    n_current = 16

    analytic_at_n16 = {
        str(sigma): analytic_power_mean_ci_excludes_zero(
            n=n_current,
            true_mean=primary_mde,
            sigma=float(sigma),
            alpha=alpha,
        )
        for sigma in sigmas
    }
    path_a = all(power >= threshold for power in analytic_at_n16.values())

    mc_tolerance = float(config.get("monte_carlo_tolerance", 0.1))
    mc_cells_n16 = [
        row
        for row in results["monte_carlo_validation"]
        if int(row["n"]) == n_current
        and float(row["mde_brier_reduction"]) == primary_mde
        and float(row["sigma"]) in sigmas
    ]
    mc_agrees = True
    for row in mc_cells_n16:
        sigma = float(row["sigma"])
        analytic = analytic_at_n16[str(sigma)]
        mc_power = float(row["power_ci_excludes_zero_positive"])
        if abs(analytic - mc_power) > mc_tolerance:
            mc_agrees = False
    path_a = path_a and mc_agrees and bool(mc_cells_n16)

    min_n_for_adequacy: int | None = None
    for n in sorted(int(n) for n in config["n_grid"]):
        powers = [
            analytic_power_mean_ci_excludes_zero(
                n=n,
                true_mean=primary_mde,
                sigma=float(sigma),
                alpha=alpha,
            )
            for sigma in sigmas
        ]
        if all(p >= threshold for p in powers):
            min_n_for_adequacy = n
            break

    ceiling_items = int(
        config["expansion_feasibility"].get(
            "max_confirmatory_items_without_new_freeze", 16
        )
    )
    expansion_packet_frozen = bool(
        config["expansion_feasibility"].get("expansion_packet_frozen_in_repo", False)
    )
    expansion_feasible = (
        min_n_for_adequacy is not None
        and min_n_for_adequacy <= ceiling_items
        and expansion_packet_frozen
    )

    if path_a:
        path = "A"
        decision = "RETAIN_V2_1_ADEQUATELY_POWERED"
    elif expansion_feasible:
        path = "B"
        decision = "EXPAND_BEFORE_LABELS"
    else:
        path = "C"
        decision = "CONFIRMATORY_PACKET_POWER_LIMITED"

    return {
        "path": path,
        "decision": decision,
        "primary_mde_brier_reduction": primary_mde,
        "adequate_power_threshold": threshold,
        "decision_sigma_set": sigmas,
        "analytic_power_at_n16": analytic_at_n16,
        "monte_carlo_agrees_at_n16": mc_agrees,
        "minimum_n_for_adequacy_all_sigmas": min_n_for_adequacy,
        "expansion_packet_frozen_in_repo": expansion_packet_frozen,
        "expansion_feasible_within_ceiling": expansion_feasible,
        "confirmatory_item_count_decision": n_current if path != "B" else min_n_for_adequacy,
        "underpowered_interpretation_rules": (
            [
                "If paired bootstrap CI for primary Brier reduction includes zero, verdict is "
                "MEASURED_BUT_INDISTINGUISHABLE — not negative evidence.",
                "UNDERPOWERED status blocks confirmatory refutation claims.",
                "Q2/Q3 binomial estimates remain descriptive only at n=16.",
            ]
            if path == "C"
            else []
        ),
    }


def build_decision_receipt(
    repo_root: Path,
    *,
    config: dict[str, Any],
    results: dict[str, Any],
    zero_labels: dict[str, Any],
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    evaluation = evaluate_power_decision(config, results)
    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    source_set_path = ANNOTATION_DIR / "SOURCE_ITEM_SET_V2_1_20260810.json"
    packet_path = ANNOTATION_DIR / "EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json"
    source_set = json.loads((repo_root / source_set_path).read_text(encoding="utf-8"))
    packet = json.loads((repo_root / packet_path).read_text(encoding="utf-8"))

    return {
        "schema_version": "paper3-power-decision-receipt-v1",
        "receipt_id": "paper3-power-design-decision-20260811",
        "created_at_utc": created,
        "git_subject_sha256": zero_labels["git_subject_sha256"],
        "issue_number": 248,
        "decision_path": evaluation["path"],
        "decision": evaluation["decision"],
        "confirmatory_packet_version": "v2.1",
        "confirmatory_item_count": 16 if evaluation["path"] != "B" else evaluation["confirmatory_item_count_decision"],
        "material_effects": config["registered_material_effects"],
        "primary_endpoint": config["primary_endpoint"],
        "power_evaluation": evaluation,
        "frozen_artifacts": {
            "zero_labels_receipt_sha256": canonical_sha256(zero_labels),
            "config_sha256": results["config_sha256"],
            "results_sha256": canonical_sha256(results),
            "source_set_path": str(source_set_path),
            "source_set_sha256": hashlib.sha256(
                (repo_root / source_set_path).read_bytes()
            ).hexdigest(),
            "source_set_canonical_sha256": canonical_sha256(source_set),
            "packet_path": str(packet_path),
            "packet_canonical_sha256": canonical_sha256(packet),
        },
        "annotation_packet_for_issue_217": {
            "packet_version": packet.get("packet_id"),
            "item_count": len(packet.get("items", [])),
            "instruction_readme": "research/paper3/annotation/README_V2_1.md",
            "supersedes_issue_43_reference": True,
            "blocked_until_power_decision_resolved": False,
        },
        "claim_boundary": (
            "Pre-label power-design decision only. No external annotation, gate pass, "
            "training authorization, or confirmatory result is claimed."
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
