"""Build the capability-floor decision receipt from existing sealed jobs (#247).

Uses only committed ingest receipts already in the repository. Does not invent
model outputs or ORACLE scores.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paper2_experience_root_cause import ORACLE_PASS_MIN_SUCCESS_RATE
from .v3_authority import canonical_sha256

CAPABILITY_RECEIPT_PATH = Path("research/paper2/CAPABILITY_FLOOR_DECISION_RECEIPT.json")

_EVIDENCE_RECEIPTS: tuple[tuple[str, str], ...] = (
    ("experience_benchmark_v1_2", "research/paper2_experience_benchmark_v1_2/native_job_3476548"),
    ("microtrial_v4_2", "research/paper2_microtrial_v4_2/PAPER2_V4_2_NATIVE_JOB_3476540_INGEST_RECEIPT_20260811.json"),
    ("microtrial_v4_3", "research/paper2_microtrial_v4_3/PAPER2_V4_3_NATIVE_JOB_3476566_INGEST_RECEIPT_20260811.json"),
    ("microtrial_v4_3_1", "research/paper2_microtrial_v4_3_1/PAPER2_V4_3_1_NATIVE_JOB_3476576_INGEST_RECEIPT_20260811.json"),
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _first(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _extract_microtrial_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    native = receipt.get("native_execution", {})
    metrics = receipt.get("metrics", {})
    outcome = receipt.get("task_seed_outcome", {})
    return {
        "job_id": native.get("slurm_job_id"),
        "model_id": receipt.get("model", {}).get("model_id") or metrics.get("model_id"),
        "parse_valid_arm_count": _first(
            outcome.get("parse_valid_arm_count"), metrics.get("parse_valid_arm_count")
        ),
        "scorable_arm_count": _first(
            outcome.get("scorable_arm_count"), metrics.get("scorable_arm_count")
        ),
        "exact_conceptual_pass_arm_count": _first(
            outcome.get("exact_conceptual_pass_arm_count"),
            metrics.get("exact_conceptual_pass_arm_count"),
        ),
        "evaluated_task_seed_unit_count": _first(
            outcome.get("evaluated_task_seed_unit_count"),
            metrics.get("evaluated_task_seed_unit_count"),
        ),
        "score_comparison_permitted": _first(
            outcome.get("arm_comparison_estimable")
            if "arm_comparison_estimable" in outcome
            else None,
            metrics.get("score_comparison_permitted"),
        ),
        "verdict": receipt.get("verdict") or native.get("governed_harvest_verdict"),
    }


def _extract_v12_summary(repo_root: Path) -> dict[str, Any]:
    validation = repo_root / (
        "research/paper2_experience_benchmark_v1_2/native_job_3476548/VALIDATION_RECEIPT.json"
    )
    if not validation.is_file():
        return {"job_id": 3476548, "available": False}
    payload = _load_json(validation)
    transfer = [
        row
        for row in payload.get("metrics", [])
        if row.get("phase") == "FRESH_TRANSFER"
    ]
    reset = next((row for row in transfer if row.get("arm") == "RESET_BASELINE"), {})
    learning = next((row for row in transfer if row.get("arm") == "LEARNING_ENABLED"), {})
    return {
        "job_id": 3476548,
        "available": True,
        "reset_success_rate": reset.get("success_rate"),
        "learning_success_rate": learning.get("success_rate"),
        "transfer_success_delta": payload.get("deltas", {}).get("transfer_success_delta"),
        "total_retrieval_calls": learning.get("total_retrieval_calls"),
        "protocol_subject_hash": payload.get("protocol_subject_hash"),
        "harvest_validation_verdict": payload.get("harvest_validation_verdict"),
    }


def build_capability_floor_decision_receipt(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    microtrial: dict[str, Any] = {}
    for label, rel in _EVIDENCE_RECEIPTS[1:]:
        path = repo_root / rel
        if not path.is_file():
            microtrial[label] = {"available": False, "path": rel}
            continue
        if path.suffix == ".json":
            microtrial[label] = _extract_microtrial_summary(_load_json(path))
        else:
            microtrial[label] = {"available": True, "path": rel, "format": "markdown_ingest"}

    v12 = _extract_v12_summary(repo_root)

    # Adjacent microtrial evidence: zero exact conceptual passes at 0.5B and 1.5B.
    zero_exact_pass_jobs = [
        label
        for label, row in microtrial.items()
        if isinstance(row, dict) and row.get("exact_conceptual_pass_arm_count") == 0
    ]

    receipt = {
        "schema_version": "paper2-capability-floor-decision-receipt-v1",
        "receipt_id": "paper2-capability-floor-decision-20260811",
        "created_at_utc": created,
        "git_subject_sha256": git_head_sha(repo_root),
        "issue_number": 247,
        "oracle_execution_status": "NOT_EXECUTED",
        "oracle_blocked_status": "CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE",
        "oracle_blocked_reason": (
            "No local Qwen2.5-0.5B/1.5B model assets in repository; LUNARC snapshot paths "
            "are attested in frozen packets but not runnable in this environment."
        ),
        "oracle_pass_criterion_frozen": {
            "min_success_rate": ORACLE_PASS_MIN_SUCCESS_RATE,
            "phase": "FRESH_TRANSFER",
            "source": "research/PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md",
        },
        "experience_benchmark_v1_2": v12,
        "adjacent_microtrial_capability_evidence": microtrial,
        "observed_facts": {
            "v1_2_both_arms_zero_successes": v12.get("reset_success_rate") == 0.0
            and v12.get("learning_success_rate") == 0.0,
            "microtrial_zero_exact_pass_generations": zero_exact_pass_jobs,
            "v1_2_whole_state_dump_not_selective_rakl": v12.get("total_retrieval_calls") == 0.0,
        },
        "provisional_classification": "SUSPECTED_CAPABILITY_FLOOR_PENDING_ORACLE",
        "classification_rules": {
            "MODEL_CAPABILITY_FLOOR": (
                "Requires ORACLE_PROCEDURE_UPPER_BOUND at 0.5B with parse-valid outputs and "
                f"success_rate < {ORACLE_PASS_MIN_SUCCESS_RATE} on fresh-transfer tasks."
            ),
            "INSTRUMENT_DEFECT": "ORACLE parse-invalid outputs — repair harness, do not escalate model.",
            "cannot_close_from_microtrial_alone": (
                "Adjacent pendulum microtrial receipts measure a different task/gate and do not "
                "substitute for ExperienceBenchmark ORACLE on the frozen transfer panel."
            ),
        },
        "decision": {
            "primary_model_for_oracle_gate": "Qwen/Qwen2.5-0.5B-Instruct",
            "capability_staircase_after_oracle": [
                "Qwen/Qwen2.5-0.5B-Instruct (ORACLE gate)",
                "Qwen/Qwen2.5-1.5B-Instruct (adjacent microtrial: exact_conceptual_pass_arm_count=0)",
            ],
            "blocks_confirmatory_without_oracle": True,
            "kill_narrowing_available": False,
            "kill_narrowing_reason": (
                "ORACLE arm not executed; microtrial-only evidence is adjacent and task-mismatched. "
                "Honest close requires ORACLE on the ExperienceBenchmark transfer panel or explicit "
                "INSTRUMENT_DEFECT repair path."
            ),
        },
        "claim_boundary": (
            "Receipt from existing sealed jobs only. No invented ORACLE scores, no promotional "
            "capability claim, and no BENCHMARK_CANNOT_DISCRIMINATE kill without ORACLE."
        ),
    }
    receipt["artifact_sha256"] = canonical_sha256(receipt)
    return receipt


def write_capability_floor_decision_receipt(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> Path:
    payload = build_capability_floor_decision_receipt(repo_root, created_at_utc=created_at_utc)
    out = repo_root / CAPABILITY_RECEIPT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
