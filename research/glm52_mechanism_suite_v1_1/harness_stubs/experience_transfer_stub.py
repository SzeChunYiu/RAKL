from __future__ import annotations

from typing import Any, Mapping

from experience_transfer import TransferTask, lesson_bank  # type: ignore[import-not-found]
from harness.experience_transfer_harness import (
    EXPERIENCE_ARMS,
    HOSTILE_FAMILIES,
    evaluate_dev_gate,
    materialize_for_arm,
    run_offline_panel,
)


def run_stub(task: Mapping[str, Any], state: Mapping[str, Any] | None = None, budget: int = 8) -> dict[str, Any]:
    transfer_task = TransferTask(
        task_id=str(task.get("task_id", "stub")),
        question=str(task.get("question", "q")),
        evidence=str(task.get("evidence", "")),
        verdict=str(task.get("verdict", "CANNOT_CHECK")),
        gold_lesson_id=str(task.get("gold_lesson_id", "L-SCOPE-ALIGNMENT")),
    )
    materialized = materialize_for_arm(transfer_task, lesson_bank(707), "CURRENT_RAKL_EXPERIENCE", budget=budget)
    panel = run_offline_panel(phase="dev", n_per_family=1)
    return {
        "experiment": "experience_transfer",
        "lane": 3,
        "arms": list(EXPERIENCE_ARMS),
        "hostile_families": list(HOSTILE_FAMILIES),
        "arm": "CURRENT_RAKL_EXPERIENCE",
        "outcome_access": "NO_NEW_GLM_OUTCOME",
        "materialized": materialized,
        "dev_gate": evaluate_dev_gate(panel["summary"]),
        "model_runs": 0,
    }
