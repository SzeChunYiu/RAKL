"""Fail-closed tests for #154 model ALR baseline prereg + runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from rakl.alr_model_baselines import (
    ARM_IDS,
    BASELINE_PACKET_ID,
    PREREG_PATH,
    authorize_model_execution,
    build_direct_prompt,
    default_preregistration,
    load_preregistration,
    parse_model_json_response,
    plan_lunarc_submission,
    run_baseline_arm,
    run_deterministic_controls,
    validate_preregistration,
)
from rakl.authority_leakage_benchmark import (
    TransitionDecision,
    TransitionResponse,
    always_blocked_responder,
)
from rakl.authority_leakage_panel_v2 import PANEL_V2_ID, frozen_case_panel_v2


def test_prereg_on_disk_validates_and_binds_v2() -> None:
    data = validate_preregistration(load_preregistration())
    assert data["packet_id"] == BASELINE_PACKET_ID
    assert data["panel_id"] == PANEL_V2_ID
    assert data["grants_scientific_authority"] is False
    assert data["novelty_licensed"] is False
    assert Path(PREREG_PATH).is_file()
    assert set(ARM_IDS) <= {arm["arm_id"] for arm in data["arms"]}
    assert data["power_design"]["mde_alr_absolute"] == 0.25


def test_default_prereg_matches_disk_hash_payload() -> None:
    disk = dict(load_preregistration())
    default = dict(default_preregistration())
    disk_body = {k: v for k, v in disk.items() if k != "artifact_hash"}
    assert disk_body == default


def test_deterministic_controls_score_without_granting_authority() -> None:
    receipts = run_deterministic_controls()
    by_id = {r.arm_id: r for r in receipts}
    assert by_id["CTRL_ALWAYS_BLOCKED"].evaluation["score"]["alr"] == 0.0
    assert by_id["CTRL_ALWAYS_ESCALATE"].evaluation["score"]["alr"] == 1.0
    assert by_id["CTRL_ALWAYS_BLOCKED"].grants_authority is False


def test_model_arm_blocked_without_authorization() -> None:
    receipt = run_baseline_arm("BASE_DIRECT_STRONG_PROMPT")
    assert receipt.status == "BLOCKED"
    assert receipt.grants_authority is False


def test_model_arm_blocked_without_backend() -> None:
    with pytest.raises(PermissionError, match="backend"):
        authorize_model_execution(authorize=True, backend=None)


def test_authorized_model_arm_scores_non_confirmatory() -> None:
    receipt = run_baseline_arm(
        "BASE_DIRECT_STRONG_PROMPT",
        authorize_model_run=True,
        model_backend=always_blocked_responder,
    )
    assert receipt.status == "MODEL_SCORED_NON_CONFIRMATORY"
    assert receipt.grants_authority is False


def test_direct_prompt_is_label_blind() -> None:
    case = frozen_case_panel_v2()[0]
    prompt = build_direct_prompt(case.visible)
    assert "allowed_authority_effects" not in prompt
    assert "falsifier_note" not in prompt


def test_parse_fail_closed() -> None:
    resp = parse_model_json_response("x", "not json")
    assert resp.transition_decision is TransitionDecision.CANNOT_CHECK
    assert resp.authority_delta == {}


def test_lunarc_plan_ready_with_authorize_receipt() -> None:
    plan = plan_lunarc_submission()
    assert plan["status"] == "READY_TO_SUBMIT"
    assert plan["grants_authority"] is False
    assert plan["sbatch_planned"] is True


def test_custom_backend_path() -> None:
    def oracle(visible):  # type: ignore[no-untyped-def]
        return TransitionResponse(
            case_id=visible.case_id,
            transition_decision=TransitionDecision.CANNOT_CHECK,
            authority_delta={},
        )

    receipt = run_baseline_arm(
        "RAKL_AUTHORITY_GATES",
        authorize_model_run=True,
        model_backend=oracle,
    )
    assert receipt.status == "MODEL_SCORED_NON_CONFIRMATORY"
