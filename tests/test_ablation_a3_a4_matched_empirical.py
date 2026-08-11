"""Matched A3 vs A4 empirical ablation packet freeze (#156)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.ablation_a3_a4_conformance import AblationArm
from rakl.ablation_a3_a4_matched_empirical import (
    PACKET_PATH,
    load_packet,
    run_dry_status,
    score_matched_arm_responses,
    validate_packet,
)
from rakl.authority_leakage_benchmark import TransitionDecision, TransitionResponse
from rakl.authority_leakage_panel_v2 import frozen_case_panel_v2

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


SCHEMA_PATH = Path("schemas/paper2-a3-a4-matched-empirical-packet-v1.schema.json")


def test_packet_frozen_empirics_unrun_and_no_authority() -> None:
    packet = validate_packet()
    assert packet["status"] == "PACKET_FROZEN_EMPIRICS_UNRUN"
    assert packet["grants_scientific_authority"] is False
    assert packet["execution_coordinates"]["results_invented"] is False
    assert packet["issue"] == 156
    arm_ids = {row["arm_id"] for row in packet["arms"]}
    assert arm_ids == {
        AblationArm.A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED.value,
        AblationArm.A4_SCIENTIFIC_AUTHORITY_TYPING.value,
    }
    for label in packet["naming_rule"]["forbidden_labels"]:
        assert label not in arm_ids
    assert "alr" in packet["frozen_metrics"]
    assert "valid_upgrade_recall" in packet["frozen_metrics"]
    assert packet["matched_resource_contract"]["report_benefit_and_cost"] is True


def test_packet_matches_schema() -> None:
    if jsonschema is None:
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    packet = load_packet()
    jsonschema.validate(packet, schema)


def test_dry_status_does_not_invent_scores() -> None:
    report = run_dry_status()
    assert report.status == "EMPIRICS_UNRUN"
    assert report.a3_score is None
    assert report.a4_score is None
    assert report.grants_scientific_authority is False
    status = json.loads(
        Path("research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_STATUS.json").read_text(
            encoding="utf-8"
        )
    )
    assert status["status"] == "EMPIRICS_UNRUN"
    assert status["a3_score"] is None
    assert status["a4_score"] is None


def test_score_refuses_incomplete_responses() -> None:
    panel = frozen_case_panel_v2()
    one = TransitionResponse(
        case_id=panel[0].case_id,
        transition_decision=TransitionDecision.BLOCKED,
        authority_delta={},
    )
    report = score_matched_arm_responses([one], [one])
    assert report.status == "EMPIRICS_BLOCKED"
    assert report.failures
    assert report.grants_scientific_authority is False


def test_packet_file_present() -> None:
    assert PACKET_PATH.is_file()


def test_empirics_authorize_and_plan_ready() -> None:
    from rakl.ablation_a3_a4_matched_empirical import (
        plan_matched_empirics_submission,
        validate_empirics_authorize,
    )

    auth = validate_empirics_authorize()
    assert auth["authorize_matched_a3_a4_model_empirics"] is True
    assert auth["grants_scientific_authority"] is False
    assert auth["autosci_cannot_check_disposition"] == "UNADJUDICATED_EXPLICIT"
    plan = plan_matched_empirics_submission()
    assert plan["status"] == "READY_TO_SUBMIT"
    assert plan["grants_scientific_authority"] is False


def test_governance_prompts_differ_and_bind_visible_case() -> None:
    from rakl.ablation_a3_a4_matched_empirical import (
        build_a3_governance_prompt,
        build_a4_governance_prompt,
    )

    panel = frozen_case_panel_v2()
    a3 = build_a3_governance_prompt(panel[0].visible)
    a4 = build_a4_governance_prompt(panel[0].visible)
    assert "transactional governance" in a3
    assert "scientific authority typing" in a4
    assert a3 != a4
    assert panel[0].visible.case_id in a3
    assert panel[0].visible.case_id in a4


def test_matched_model_arms_refuse_without_authorize() -> None:
    from rakl.ablation_a3_a4_matched_empirical import run_matched_model_arms

    with pytest.raises(PermissionError):
        run_matched_model_arms(Path("/tmp/no-model"), authorize=False)
