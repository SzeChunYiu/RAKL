from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE = ROOT / "research" / "empirical_10_of_10_v1" / "PAPER3" / "OBJECTIVE"


def _load(name: str) -> dict:
    return json.loads((OBJECTIVE / name).read_text(encoding="utf-8"))


def test_confirmatory_receipts_are_consistent_with_frozen_design() -> None:
    freeze = _load("PRECONFIRMATORY_FREEZE_V1.json")
    final = _load("FINAL_OBJECTIVE_RECEIPT.json")
    pred = _load("PREDICTIVE_RESULTS.json")
    inference = _load("PAIRED_INFERENCE.json")
    family = _load("FAMILY_ROBUSTNESS.json")
    lane = json.loads(
        (OBJECTIVE.parent / "LANE_STATUS.json").read_text(encoding="utf-8")
    )

    assert freeze["confirmatory_seed"] == final["chronology"]["confirmatory_seed"] == pred["seed"] == 2026081202
    assert freeze["confirmatory_total_n"] == final["chronology"]["confirmatory_n"] == pred["n"] == 576
    assert inference["n_decidable"] == final["gold"]["decidable_n"] == 512
    assert inference["registered_required_decidable_n"] == final["gold"]["registered_required_decidable_n"] == 431
    assert final["chronology"]["preconfirmatory_freeze_merge_sha"] == "7d67a18a96499f5df7bf58bc6b1356d1ce1cafbf"
    assert final["primary_residual"]["delta"] == inference["paired_binary_brier"]["MECHANISM_MINUS_FULL_DELTA"] == 0.12
    assert final["headline_objective_result"]["full_invalid_false_accept"] == 0.0
    assert pred["arms"]["MECHANISM_DERIVED_EFFECT_ONLY"]["invalid_false_accept"] == 0.25
    assert family["all_four_full_vs_mechanism_residual_positive"] is True
    assert family["broad_generalization_supported"] is False
    assert lane["objective_broader_family_generalization_supported"] is False
    assert final["grants_scientific_authority"] is False


def test_confirmatory_packets_regenerate_byte_for_byte(tmp_path: Path) -> None:
    script = ROOT / "scripts" / "paper2_objective_track_a_confirmatory.py"
    spec = importlib.util.spec_from_file_location("paper2_confirmatory_runner", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    receipt = module.run(tmp_path)
    assert receipt["seed"] == 2026081202
    assert receipt["n"] == 576
    assert all(item["matches_expected"] for item in receipt["files"].values())


def test_external_validity_remains_explicitly_unresolved() -> None:
    final = _load("FINAL_OBJECTIVE_RECEIPT.json")
    assert final["remaining_coordinates"]["direct_llm_transfer_validity_control"].startswith("PENDING")
    assert final["remaining_coordinates"]["natural_domain_independent_human"] == "BLOCKED_HUMAN"
    assert final["terminal"] == "PAPER2_OBJECTIVE_PRIMARY_SUPPORTED__FLAGSHIP_CLAIM_NOT_YET_COMPLETE"
