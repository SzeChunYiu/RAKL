"""Fail-closed tests for #409 competitive causal-attribution terminal."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/competitive_advantage_causal_attribution_v1"


def _load(name: str) -> dict:
    return json.loads((PACKET / name).read_text(encoding="utf-8"))


def test_issue_409_terminal_cannot_check_without_epoch1() -> None:
    terminal = _load("ISSUE_409_TERMINAL_RECEIPT.json")
    assert terminal["issue"] == 409
    assert terminal["terminal_status"] == "CANNOT_CHECK"
    assert terminal["scientific_verdict"] == "BLOCKED_UPSTREAM_EPOCH1_INPUTS_ABSENT"
    assert terminal["grants_scientific_authority"] is False
    assert terminal["acceptance_assessment"]["advantage_cases_emitted"] is False
    assert terminal["acceptance_assessment"]["cargo_cult_copying_performed"] is False
    assert terminal["acceptance_assessment"]["challenger_handoffs_emitted"] is False


def test_blocked_upstream_inventory_empty() -> None:
    blocked = _load("BLOCKED_UPSTREAM_RECEIPT.json")
    assert blocked["status"] == "CANNOT_CHECK"
    assert blocked["advantage_cases"] == []
    assert blocked["supported_root_causes"] == []
    assert blocked["challenger_handoffs"] == []
    assert len(blocked["missing_inputs"]) >= 4
