"""Tests for Wave-1 Lane B confirmatory ALR / A3↔A4 prep packet."""

from __future__ import annotations

from pathlib import Path

import pytest

from rakl.paper2_alr_a3a4_confirmatory_prep_wave1 import (
    PREP_PACKET_PATH,
    load_prep_packet,
    refuse_confirmatory_model_job,
    validate_prep_packet,
)

ROOT = Path(__file__).resolve().parents[1]


def test_wave1_prep_packet_fail_closed() -> None:
    report = validate_prep_packet(ROOT)
    assert report["ok"] is True
    assert report["CAPABLE_MODEL_AVAILABLE"] is False
    assert report["model_job_submission_allowed"] is False
    assert report["grants_scientific_authority"] is False
    assert report["status"] == "PREP_FROZEN_EXECUTION_FORBIDDEN"


def test_wave1_prep_binds_successor_issues_and_parent_history() -> None:
    prep = load_prep_packet(ROOT)
    successors = prep["successor_issues"]
    assert successors["alr_confirmatory"] == 350
    assert successors["a3_a4_matched_confirmatory"] == 352
    assert 324 in successors["parents_closed_science_unmet"]
    assert 156 in successors["parents_closed_science_unmet"]
    assert (ROOT / "research/paper2_alr_confirmatory_v1/ISSUE_324_TERMINAL_RECEIPT.json").is_file()
    assert (
        ROOT / "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json"
    ).is_file()
    assert (ROOT / PREP_PACKET_PATH).is_file()


def test_wave1_prep_refuses_model_job_submission() -> None:
    with pytest.raises(PermissionError, match="CAPABLE_MODEL_AVAILABLE=false"):
        refuse_confirmatory_model_job(ROOT)
