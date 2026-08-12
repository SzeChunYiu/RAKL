from __future__ import annotations

from typing import Any, Mapping

from harness.trajectory_governance_harness import (
    GOVERNANCE_ARMS,
    evaluate_noninferiority_stub,
    govern_for_arm,
    run_offline_panel,
)
from trajectory_governance import make_world  # type: ignore[import-not-found]


def run_stub(proposal: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    world = make_world(1, "same_root_echo")
    step = world.steps[0]
    observed = govern_for_arm(step, world, "CURRENT_RAKL_TRAJECTORY")
    panel = run_offline_panel(phase="dev", n_per_kind=1)
    return {
        "experiment": "trajectory_governance",
        "lane": 4,
        "arms": list(GOVERNANCE_ARMS),
        "arm": "CURRENT_RAKL_TRAJECTORY",
        "outcome_access": "NO_NEW_GLM_OUTCOME",
        "proposal_action": proposal.get("action"),
        "observed_step": {
            "step_id": observed.step_id,
            "action": observed.action,
            "evidence_ids": list(observed.evidence_ids),
            "authority_before": observed.authority_before,
            "authority_after": observed.authority_after,
        },
        "noninferiority": evaluate_noninferiority_stub(panel["summary"]),
        "model_runs": 0,
    }
