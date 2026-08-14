from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/p5_p6_operator_absorption_v1/run_development.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("p5_p6_failure_analysis_development", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_development_harness_absorbs_parent_semantics_without_performance_claim() -> None:
    result = _load_module().run_development()
    assert result["terminal"] == "PARENT_SEMANTICS_ABSORBED", result
    assert result["hard_gates_pass"] is True
    assert result["blocking_failures"] == []
    assert result["grants_scientific_authority"] is False
    assert result["grants_promotion_authority"] is False
    assert result["performance_claim_against_quickxplain_or_marco"] is False
    assert {case["case_id"] for case in result["cases"]} == {
        "D1_FAIL_IRRELEVANT",
        "D2_MINIMALITY_TRAP",
        "D3_MULTIPLE_MUS",
        "D4_MULTIPLE_MCS",
        "D5_CANNOT_CHECK",
    }
    assert all(case["hard_gate_pass"] for case in result["cases"])


def test_development_harness_exposes_minimality_distinctions_and_cannot_check() -> None:
    result = _load_module().run_development()
    by_id = {case["case_id"]: case for case in result["cases"]}
    assert by_id["D1_FAIL_IRRELEVANT"]["minimality_gap"] == 0
    assert by_id["D2_MINIMALITY_TRAP"]["minimality_gap"] >= 0
    assert by_id["D3_MULTIPLE_MUS"]["cardinality_gap_to_smallest_mus"] >= 0
    assert len(by_id["D4_MULTIPLE_MCS"]["all_mcs"]) == 4
    assert by_id["D5_CANNOT_CHECK"]["failure_minimizer_verdict"] == "CANNOT_CHECK"
    assert by_id["D5_CANNOT_CHECK"]["conflict_analyzer_verdict"] == "CANNOT_CHECK"
