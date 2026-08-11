"""Tests for Paper II #324 confirmatory ALR freeze."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.authority_leakage_panel_v2 import PANEL_V2_ID
from rakl.paper2_alr_confirmatory import (
    TERMINAL_RECEIPT_PATH,
    assess_confirmatory_readiness,
    build_confirmatory_packet,
    refuse_confirmatory_claim,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_confirmatory_packet_binds_clean_v2_and_co_primary_metrics() -> None:
    packet = build_confirmatory_packet(ROOT, created_at_utc="2026-08-11T23:50:00Z")
    assert packet["panel_manifest"]["panel_id"] == PANEL_V2_ID
    assert packet["panel_manifest"]["n_cases"] == 16
    assert packet["degeneracy_binding"]["clean"] is True
    assert packet["inference_plan"]["co_primary_outcomes"] == [
        "authority_leakage_rate",
        "valid_upgrade_recall",
    ]
    assert packet["terminal_receipt"]["grants_scientific_authority"] is False
    assert packet["terminal_receipt"]["promotional_lift_claim_allowed"] is False


def test_confirmatory_execution_blocked_by_capability_floor() -> None:
    readiness = assess_confirmatory_readiness(ROOT)
    assert readiness["ready"] is False
    assert "CAPABILITY_FLOOR_BLOCKS_CONFIRMATORY_MODEL" in readiness["blockers"]
    assert readiness["terminal_status"] == "CANNOT_EXECUTE_CONFIRMATORY_MODEL_COMPARISON"
    with pytest.raises(PermissionError, match="confirmatory ALR claim refused"):
        refuse_confirmatory_claim(ROOT)


def test_frozen_324_terminal_receipt() -> None:
    frozen = _load(ROOT / TERMINAL_RECEIPT_PATH)
    live = build_confirmatory_packet(ROOT, created_at_utc="2026-08-11T23:50:00Z")[
        "terminal_receipt"
    ]
    assert frozen["issue"] == 324
    assert frozen["terminal_status"] == live["terminal_status"]
    assert frozen["acceptance_assessment"]["rakl_typed_authority_arm_executed"] is False
    assert frozen["evaluated_results_accessed"] is False
