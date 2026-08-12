"""Validate capability-gated closeout terminals (no confirmatory authority)."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_ISSUES = (350, 352, 398, 399, 367)
ALLOWED_PRIMARY = {
    "BLOCKED_CAPABLE_MODEL",
    "CANNOT_IDENTIFY",
    "NOT_YET",
    "NONCONFIRMATORY",
}


def load_closeout(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    packet = root / "research" / "capability_gated_closeout_20260812"
    batch = json.loads((root / "research" / "CAPABILITY_GATED_CLOSEOUT_350_352_398_399_367.json").read_text())
    receipts = {}
    for issue in REQUIRED_ISSUES:
        receipts[issue] = json.loads((packet / f"ISSUE_{issue}_TERMINAL_RECEIPT.json").read_text())
    return {"batch": batch, "receipts": receipts, "packet": packet}


def validate_closeout(repo_root: Path | None = None) -> list[str]:
    data = load_closeout(repo_root)
    errors: list[str] = []
    batch = data["batch"]
    if batch.get("CAPABLE_MODEL_AVAILABLE") is not False:
        errors.append("batch CAPABLE_MODEL_AVAILABLE must be false")
    if batch.get("capable_model_score") != "NO_REFUTED":
        errors.append("batch capable_model_score must be NO_REFUTED")
    if batch.get("confirmatory_lunarc_jobs_submitted") is not False:
        errors.append("confirmatory jobs must not be submitted")
    if batch.get("grants_scientific_authority") is not False:
        errors.append("batch must not grant scientific authority")
    for issue, receipt in data["receipts"].items():
        term = receipt.get("terminal_status", "")
        if term not in ALLOWED_PRIMARY and not any(term.startswith(p) for p in ALLOWED_PRIMARY):
            # allow compound forms that contain allowed vocabulary
            if not any(p in term for p in ALLOWED_PRIMARY):
                errors.append(f"#{issue} unexpected terminal_status={term!r}")
        if receipt.get("CAPABLE_MODEL_AVAILABLE") not in (False, "NO_REFUTED"):
            errors.append(f"#{issue} CAPABLE_MODEL_AVAILABLE must be NO_REFUTED/false")
        if receipt.get("grants_scientific_authority") is not False:
            errors.append(f"#{issue} must not grant scientific authority")
        if receipt.get("confirmatory_model_jobs_submitted") or receipt.get("confirmatory_jobs_submitted"):
            errors.append(f"#{issue} must not submit confirmatory jobs")
    v2 = json.loads(
        (Path(repo_root) if repo_root else Path(__file__).resolve().parents[2])
        .joinpath("research/paper2_oracle_capability_gate_v2_exec/ORACLE_DECISION_RECEIPT_V2_EXEC.json")
        .read_text()
    )
    if v2.get("scientific_verdict") != "MODEL_CAPABILITY_FLOOR_7B_V2_EXEC":
        errors.append("V2_EXEC verdict drift")
    if float(v2.get("success_rate_primary", 1.0)) >= 2.0 / 3.0:
        errors.append("V2_EXEC success_rate unexpectedly cleared gate")
    return errors
