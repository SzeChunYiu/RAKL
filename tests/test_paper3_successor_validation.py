"""Tests for Paper III #326 successor-validation freeze."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.paper3_power_design import (
    verify_issue_217_zero_public_responses,
    verify_public_annotation_directory,
)
from rakl.paper3_successor_validation import (
    DECISION_RECEIPT_PATH,
    TERMINAL_RECEIPT_PATH,
    ZERO_LABELS_REPO_WIDE_PATH,
    build_successor_packet,
    decide_successor_terminal,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_annotation_dir_clean_with_demoted_sibling_present() -> None:
    scan = verify_public_annotation_directory(ROOT)
    assert scan["verdict"] == "ZERO_PUBLIC_ANNOTATION_PAYLOADS"
    assert scan["forbidden_payload_files"] == []
    assert (ROOT / "research/paper3/ai_operator_v2_1").is_dir()


def test_independent_external_labels_absent_while_demoted_present() -> None:
    scan = verify_issue_217_zero_public_responses(ROOT)
    assert scan["verdict"] == "ZERO_IMPORTED_EXTERNAL_PAYLOADS"
    assert scan["imported_external_payload_paths"] == []
    # Sibling demoted packet exists but is outside the public annotation scan.
    demoted = ROOT / "research/paper3/ai_operator_v2_1"
    assert demoted.is_dir()
    assert any(demoted.glob("SUBMISSION_AI_OPERATOR_*.json"))


def test_successor_terminal_is_power_limited_retain() -> None:
    packet = build_successor_packet(ROOT, created_at_utc="2026-08-11T23:50:00Z")
    assert packet["terminal_receipt"]["terminal_status"] == "POWER_LIMITED_RETAIN_V2_1"
    assert packet["terminal_receipt"]["grants_scientific_authority"] is False
    assert packet["decision_receipt"]["retains_packet"]["version"] == "v2.1"
    assert packet["machine_witness_protocol"]["human_labels_may_enter_extractor"] is False
    assert packet["anti_circularity_protocol"]["if_definitionally_coupled"] == (
        "NOT_INFORMATIVE_DEFINITIONAL_COUPLING"
    )


def test_frozen_326_artifacts_match_builder() -> None:
    live = build_successor_packet(ROOT, created_at_utc="2026-08-11T23:50:00Z")
    frozen_terminal = _load(ROOT / TERMINAL_RECEIPT_PATH)
    frozen_decision = _load(ROOT / DECISION_RECEIPT_PATH)
    frozen_zero = _load(ROOT / ZERO_LABELS_REPO_WIDE_PATH)
    assert frozen_terminal["terminal_status"] == live["terminal_receipt"]["terminal_status"]
    assert frozen_decision["terminal_status"] == "POWER_LIMITED_RETAIN_V2_1"
    assert frozen_zero["observation"] == "ZERO_LABELS_REPO_WIDE"
    assert frozen_zero["counts"]["external_annotations"] == 0


def test_window_closes_when_independent_labels_present() -> None:
    zero = {
        "state": "ZERO_LABELS_OBSERVED",
        "issue_217_scan": {"first_real_independent_label_present": True},
    }
    decision = decide_successor_terminal(
        zero_labels=zero,
        power_evaluation={"path": "C", "decision": "CONFIRMATORY_PACKET_POWER_LIMITED"},
    )
    assert decision["terminal_status"] == "WINDOW_CLOSED_USE_V2_1_POWER_LIMITED"
