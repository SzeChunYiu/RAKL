"""Contract tests for Paper III pre-label power design (#248)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paper3_power_simulation.py"


def _load():
    spec = importlib.util.spec_from_file_location("paper3_power_simulation", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_zero_labels_verified_on_frozen_packet():
    h = _load()
    zero = h.verify_zero_labels()
    assert zero["status"] == "ZERO_LABELS_VERIFIED"
    assert zero["packet_item_count"] == 16
    assert zero["contaminated_item_fields"] == []
    assert zero["suspicious_files"] == []
    assert zero["grants_scientific_authority"] is False
    assert zero["family_field_present_in_public_packet"] is True


def test_path_c_when_n16_underpowered():
    h = _load()
    zero = {
        "status": "ZERO_LABELS_VERIFIED",
        "git_subject_sha": "deadbeef",
    }
    results = {
        "primary_mde": 0.05,
        "n16_primary_power": {"power_ci_excludes_zero_positive": 0.22},
        "smallest_n_reaching_target_power_at_mde": 64,
        "annotation_burden": [
            {
                "n": 64,
                "feasible_under_ceiling": False,
                "total_person_hours": 40,
            }
        ],
    }
    decision = h.decide(zero, results, h.CONFIG)
    assert decision["path"] == "C"
    assert decision["decision"] == "CONFIRMATORY_PACKET_POWER_LIMITED"
    assert decision["grants_scientific_authority"] is False


def test_simulate_diffs_length_and_bounds():
    h = _load()
    import random

    diffs = h.simulate_paired_brier_diffs(
        n=16,
        mean_lift=0.05,
        balance=0.5,
        correlation=0.5,
        noise_sd=0.18,
        rng=random.Random(0),
    )
    assert len(diffs) == 16
    assert all(-1.0 <= d <= 1.0 for d in diffs)
