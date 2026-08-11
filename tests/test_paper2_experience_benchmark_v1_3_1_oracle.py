"""Freeze locks for ExperienceBenchmark v1.3_1 Phase-1 1.5B ORACLE (#247)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.paper2_experience_benchmark_runner import (
    PACKET_REL_V1_3,
    PACKET_REL_V1_3_1,
    PROTOCOL_SUBJECT_HASH_V1_3,
    PROTOCOL_SUBJECT_HASH_V1_3_1,
)
from rakl.paper2_experience_root_cause import ORACLE_PASS_MIN_SUCCESS_RATE

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "research" / "paper2_experience_benchmark_v1_3_1"
PARENT_DIR = ROOT / "research" / "paper2_experience_benchmark_v1_3"


def test_v1_3_1_protocol_subject_hash_frozen() -> None:
    packet = json.loads((PACKET_DIR / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))
    assert packet["benchmark_id"] == "paper2-experience-benchmark-v1_3_1"
    assert packet["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_3_1
    assert packet["protocol_subject_hash"] != PROTOCOL_SUBJECT_HASH_V1_3
    assert PACKET_REL_V1_3_1 != PACKET_REL_V1_3
    assert packet["issue"] == 247
    assert packet["section"] == "PHASE1_ORACLE_1_5B"
    assert packet["learning_loop_mode"] == "root_cause_v1"
    assert packet["arms"][0] == "ORACLE_PROCEDURE_UPPER_BOUND"
    assert packet["primary_execution"]["model_scale"] == "Qwen2.5-1.5B-Instruct"
    assert packet["primary_execution"]["forbid_1_5B_until_oracle_gate"] is False
    assert packet["model"]["model_id"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert packet["model"]["model_revision"] == "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
    assert "paper2-model-qwen25-1_5b-v4-3" in packet["model"]["snapshot_path"]
    assert packet["parent_negative_history"]["parent_scientific_verdict"] == "MODEL_CAPABILITY_FLOOR_0_5B"
    assert packet["parent_negative_history"]["parent_job_id"] == "3476730"
    assert packet["parent_negative_history"]["not_scale_only_escape_from_v1_2"] is True
    assert packet["parent_negative_history"]["reopen_issue_138"] is False
    assert packet["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
    assert packet["runs"] == []


def test_difference_witness_scale_from_floored_0_5b_not_v1_2_escape() -> None:
    witness = json.loads((PACKET_DIR / "DIFFERENCE_WITNESS_V1_3_1.json").read_text(encoding="utf-8"))
    assert witness["scale_change_from_floored_0_5B_oracle"] is True
    assert witness["explicitly_not_scale_only_escape_from_v1_2"] is True
    assert witness["parent_scientific_verdict"] == "MODEL_CAPABILITY_FLOOR_0_5B"
    assert witness["parent_job_id"] == "3476730"
    assert witness["learning_staircase_authorized"] is False
    assert witness["promotional_lift_claim_allowed"] is False
    assert witness["reopen_issue_138"] is False
    changed = " ".join(witness["what_changed"]).lower()
    assert "1.5b" in changed and "0.5b" in changed
    unchanged = " ".join(witness["what_did_not_change"]).lower()
    assert "root_cause_v1" in unchanged
    assert "oracle_procedure_upper_bound" in unchanged or "diagnostic_arm" in unchanged


def test_parent_v1_3_oracle_floor_receipt_intact() -> None:
    decision = json.loads((PARENT_DIR / "ORACLE_DECISION_RECEIPT_V1_3.json").read_text(encoding="utf-8"))
    assert decision["scientific_verdict"] == "MODEL_CAPABILITY_FLOOR_0_5B"
    assert decision["oracle_gate_passed"] is False
    assert decision["experience_benchmark_1_5B_authorized"] is False
    assert ORACLE_PASS_MIN_SUCCESS_RATE == pytest.approx(2.0 / 3.0)


def test_batch_contract_bindings_match() -> None:
    contract = json.loads((PACKET_DIR / "BATCH_CONTRACT_V1_3_1_ORACLE.json").read_text(encoding="utf-8"))
    assert contract["protocol_subject_hash"] == PROTOCOL_SUBJECT_HASH_V1_3_1
    assert contract["model_scale"] == "Qwen2.5-1.5B-Instruct"
    assert contract["learning_staircase_authorized"] is False
    assert contract["scale_change_from_floored_0_5B_oracle"] is True
    import hashlib

    for binding in contract["bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == binding["sha256"], binding["role"]
