from __future__ import annotations

from typing import Any, Mapping

from framework_adapter import CanonicalFrameworkAdapter


def run_stub(proposal: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    adapter = CanonicalFrameworkAdapter()
    step = adapter.govern_trajectory(proposal, case)
    return {
        "experiment": "trajectory_governance",
        "arm": "CURRENT_RAKL_TRAJECTORY",
        "outcome_access": "NO_NEW_GLM_OUTCOME",
        "observed_step": {
            "step_id": step.step_id,
            "action": step.action,
            "evidence_ids": list(step.evidence_ids),
            "authority_before": step.authority_before,
            "authority_after": step.authority_after,
        },
    }
