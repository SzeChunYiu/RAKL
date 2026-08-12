"""Fail-closed tests for #399 continual-learning BLOCKED_CAPABILITY terminal."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/paper2_continual_learning_causal_ladder_v1"


def _load(name: str) -> dict:
    return json.loads((PACKET / name).read_text(encoding="utf-8"))


def test_issue_399_terminal_is_blocked_capability() -> None:
    terminal = _load("ISSUE_399_TERMINAL_RECEIPT.json")
    assert terminal["issue"] == 399
    assert terminal["terminal_status"] == "BLOCKED_CAPABILITY"
    assert terminal["scientific_verdict"] == "CANNOT_IDENTIFY_RAKL_LEARNING"
    assert terminal["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
    assert terminal["grants_scientific_authority"] is False
    assert terminal["promotional_lift_claim_allowed"] is False
    assert terminal["acceptance_assessment"]["treatment_arms_executed"] is False
    assert terminal["acceptance_assessment"]["capable_model_authorize_receipt_present"] is False


def test_blocked_capability_receipt_forbids_arms() -> None:
    blocked = _load("BLOCKED_CAPABILITY_RECEIPT.json")
    assert blocked["status"] == "BLOCKED_CAPABILITY"
    assert blocked["arms_authorized"] is False
    assert blocked["capable_model_available"] is False
    assert all(v == "NOT_RUN" for v in blocked["arms"].values())
    assert "CAPABLE_MODEL_AVAILABLE_NO_REFUTED" in blocked["blockers"]


def test_upstream_v2_exec_license_still_no_refuted() -> None:
    license_path = (
        ROOT
        / "research/paper2_oracle_capability_gate_v2_exec/LEARNING_CLAIMS_LICENSE_STATUS.json"
    )
    assert license_path.is_file()
    license_doc = json.loads(license_path.read_text(encoding="utf-8"))
    assert license_doc["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
    assert license_doc["learning_staircase_authorized"] is False
