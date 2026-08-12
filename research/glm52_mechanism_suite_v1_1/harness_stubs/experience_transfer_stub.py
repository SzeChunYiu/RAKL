from __future__ import annotations

from typing import Any, Mapping

from framework_adapter import CanonicalFrameworkAdapter


def run_stub(
    task: Mapping[str, Any],
    state: Mapping[str, Any] | None = None,
    budget: int = 8,
) -> dict[str, Any]:
    adapter = CanonicalFrameworkAdapter()
    receipt = adapter.materialize_experience(task, state or {}, budget)
    return {
        "experiment": "experience_transfer",
        "arm": "CURRENT_RAKL_EXPERIENCE",
        "outcome_access": "NO_NEW_GLM_OUTCOME",
        "receipt": {
            "protocol_id": receipt.protocol_id,
            "fibre_snapshot_hash": receipt.fibre_snapshot_hash,
            "episode_ids": list(receipt.episode_ids),
            "task_manifest_hash": receipt.task_manifest_hash,
            "framework_sha": receipt.framework_sha,
        },
    }
