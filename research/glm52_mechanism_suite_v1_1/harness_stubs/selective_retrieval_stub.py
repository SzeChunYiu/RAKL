from __future__ import annotations

from typing import Any, Mapping

from framework_adapter import CanonicalFrameworkAdapter


def run_stub(task: Mapping[str, Any], budget: int = 8) -> dict[str, Any]:
    adapter = CanonicalFrameworkAdapter()
    receipt = adapter.retrieve(task, budget)
    return {
        "experiment": "selective_retrieval",
        "arm": "CURRENT_RAKL_EPISTEMIC_SEARCH",
        "outcome_access": "NO_NEW_GLM_OUTCOME",
        "receipt": {
            "protocol_id": receipt.protocol_id,
            "selected_candidate_ids": list(receipt.selected_candidate_ids),
            "interaction_space_id": receipt.interaction_space_id,
            "task_manifest_hash": receipt.task_manifest_hash,
            "framework_sha": receipt.framework_sha,
        },
    }
