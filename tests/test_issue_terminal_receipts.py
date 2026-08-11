"""Sanity checks for honest issue terminal receipts (MODEL_CAPABILITY_FLOOR_0_5B)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TERMINAL_RECEIPTS = (
    ROOT / "research/paper2_experience_benchmark_v1_3/ISSUE_247_TERMINAL_RECEIPT.json",
    ROOT / "research/paper5_confirmatory_packet_v1/ISSUE_250_TERMINAL_RECEIPT.json",
    ROOT / "research/paper5_confirmatory_packet_v1/ISSUE_251_TERMINAL_RECEIPT.json",
    ROOT / "research/paper2_learning_governance_factorial_v1/ISSUE_155_TERMINAL_RECEIPT.json",
    ROOT / "research/paper2_closest_parent/ISSUE_156_TERMINAL_RECEIPT.json",
    ROOT / "research/paper2_experience_to_method_v1/ISSUE_157_TERMINAL_RECEIPT.json",
    ROOT / "research/paper2_novelty_campaign/ISSUE_158_TERMINAL_RECEIPT.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_terminal_receipts_refuse_scientific_authority() -> None:
    for path in TERMINAL_RECEIPTS:
        receipt = _load(path)
        assert receipt["grants_scientific_authority"] is False, path.name
        assert receipt["schema_version"] == "rakl-issue-terminal-receipt-v1", path.name


def test_247_oracle_floor_binding() -> None:
    receipt = _load(TERMINAL_RECEIPTS[0])
    assert receipt["scientific_verdict"] == "MODEL_CAPABILITY_FLOOR_0_5B"
    assert receipt["success_rate_primary"] == 0.0
    assert receipt["parse_valid_primary"] is True
    assert receipt["promotional_lift_claim_allowed"] is False


def test_250_251_dependency_chain() -> None:
    r250 = _load(TERMINAL_RECEIPTS[1])
    r251 = _load(TERMINAL_RECEIPTS[2])
    assert r250["terminal_status"] == "CANNOT_FREEZE_CONFIRMATORY_PACKET"
    assert r251["terminal_status"] == "CANNOT_EXECUTE_FROZEN_PACKET"
    assert r251["upstream_dependency"]["issue"] == 250


def test_paper2_empirical_issues_blocked_not_promoted() -> None:
    for path in TERMINAL_RECEIPTS[3:6]:
        receipt = _load(path)
        assert receipt["terminal_status"] == "CANNOT_IDENTIFY", path.name
        assert receipt["evaluated_results_accessed"] is False, path.name
