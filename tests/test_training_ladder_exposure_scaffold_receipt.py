"""Committed #461 exposure scaffold receipt must stay pre-outcome."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "research"
    / "training_time_rakl_phase0_1"
    / "EXPOSURE_CURVE_HARNESS_SCAFFOLD.json"
)


def test_committed_exposure_scaffold_is_pre_outcome() -> None:
    assert RECEIPT.is_file()
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "training-ladder-exposure-scaffold-v1"
    assert payload["frozen_before_outcomes"] is True
    assert payload["learner_outcomes_accessed"] is False
    assert payload["grants_efficacy_claim"] is False
    assert payload["grants_scientific_authority"] is False
    assert payload["schedule_entry_count"] > 0
    assert payload["scientific_claim_status"] == "NO_EMPIRICAL_RESULT"
