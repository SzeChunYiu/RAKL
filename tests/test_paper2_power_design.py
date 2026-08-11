from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.paper2_power_design import (
    CONFIG_PATH,
    DECISION_PATH,
    RESULTS_PATH,
    ZERO_OUTCOMES_PATH,
    build_zero_outcomes_at_power_design,
    evaluate_power_decision,
    verify_no_root_cause_confirmatory_outcomes,
)
from rakl.v3_authority import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
POWER_DIR = ROOT / "research" / "paper2" / "power_design"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_no_confirmatory_outcomes_in_successor_packet() -> None:
    scan = verify_no_root_cause_confirmatory_outcomes(ROOT)
    assert scan["verdict"] == "ZERO_CONFIRMATORY_OUTCOMES"


def test_power_results_and_receipts_exist_and_bind_config() -> None:
    config = _load(ROOT / CONFIG_PATH)
    results = _load(ROOT / RESULTS_PATH)
    zero_outcomes = _load(ROOT / ZERO_OUTCOMES_PATH)
    decision = _load(ROOT / DECISION_PATH)

    assert results["config_sha256"] == canonical_sha256(config)
    assert zero_outcomes["observation"] == "ZERO_OUTCOMES_AT_POWER_DESIGN"
    assert zero_outcomes["counts"]["oracle_runs"] == 0
    assert zero_outcomes["authority_source"]["blocked_by_compute"] == (
        "CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE"
    )
    assert decision["frozen_artifacts"]["zero_outcomes_receipt_sha256"] == canonical_sha256(
        zero_outcomes
    )
    assert decision["frozen_artifacts"]["results_sha256"] == canonical_sha256(results)
    assert decision["confirmatory_packet_version"] == "root_cause_v1"
    assert decision["confirmatory_transfer_task_count"] == 18
    assert decision["execution_gate"]["blocked_status"] == "CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE"


def test_zero_outcomes_receipt_matches_live_verification() -> None:
    live = build_zero_outcomes_at_power_design(ROOT, created_at_utc="2026-08-11T22:00:00Z")
    frozen = _load(ROOT / ZERO_OUTCOMES_PATH)
    assert live["observation"] == frozen["observation"]
    assert live["outcome_directory_scan"] == frozen["outcome_directory_scan"]


def test_registered_decision_is_path_c_power_limited() -> None:
    config = _load(ROOT / CONFIG_PATH)
    results = _load(ROOT / RESULTS_PATH)
    evaluation = evaluate_power_decision(config, results)
    decision = _load(ROOT / DECISION_PATH)

    assert evaluation["path"] == "C"
    assert evaluation["decision"] == "CONFIRMATORY_PACKET_POWER_LIMITED"
    assert decision["decision_path"] == "C"
    assert evaluation["minimum_n_for_adequacy_all_sigmas"] is None
    assert decision["power_evaluation"]["underpowered_interpretation_rules"]


def test_v1_2_n3_is_underpowered_for_primary_mde() -> None:
    config = _load(ROOT / CONFIG_PATH)
    results = _load(ROOT / RESULTS_PATH)
    evaluation = evaluate_power_decision(config, results)
    threshold = float(config["adequate_power_threshold"])
    for power in evaluation["analytic_power_at_n_current"].values():
        assert float(power) < threshold


def test_successor_task_panel_has_required_strata() -> None:
    panel = _load(ROOT / "research/paper2_experience_benchmark_root_cause_v1/TASK_PANEL_DESIGN.json")
    assert panel["transfer_task_count"] == 18
    for stratum in panel["required_strata"]:
        assert panel["stratum_counts"][stratum] >= 3
