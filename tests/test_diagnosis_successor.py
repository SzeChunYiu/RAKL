"""Tests for Issue #539 active sequential diagnosis successor (REVIVAL PASS)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT_FILE = ROOT / "research/unified_problem_solving_v1/results/diagnosis_active_successor.json"


def test_result_file_exists():
    """Test that result file was generated."""
    assert RESULT_FILE.exists(), f"Result file not found: {RESULT_FILE}"


def test_leakage_free_design():
    """Test that successor uses leakage-free design (symptoms from telemetry ONLY)."""
    with open(RESULT_FILE) as f:
        result = json.load(f)
    
    assert result["design"]["leakage_free"] is True, "Must be leakage-free"
    assert result["design"]["abstention_supported"] is True, "Must support abstention"
    assert result["design"]["matched_budget_sweep"] == [1, 2, 3, 5, 8], "Must sweep matched budgets"


def test_net_advantage_computed():
    """Test that net_advantage over strongest parent is computed (DEFECT 1 fix)."""
    with open(RESULT_FILE) as f:
        result = json.load(f)
    
    assert "net_advantage" in result, "Must compute net_advantage over strongest parent"
    net = result["net_advantage"]
    assert "mean" in net and "lo" in net and "hi" in net, "Net advantage must have CI"
    # Net advantage should be negative (successor loses to parents)
    assert net["mean"] < 0, f"Net advantage should be negative, got {net[mean]}"


def test_sequential_mechanic_exercised():
    """Test that sequential mechanic is exercised (DEFECT 2 fix - variance in probe cost)."""
    with open(RESULT_FILE) as f:
        result = json.load(f)
    
    cost = result["mean_probe_cost"]
    # Mean probe cost should be > 1.0 (not capped at single probe)
    assert cost["mean"] > 1.0, f"Probe cost should show variance > 1.0, got {cost[mean]}"
    # CI should have non-zero width (variance across samples)
    ci_width = cost["hi"] - cost["lo"]
    assert ci_width > 0, f"Probe cost CI should show variance, got width {ci_width}"


def test_honest_negative_reported():
    """Test that honest NEGATIVE status is reported (never tuned positive)."""
    with open(RESULT_FILE) as f:
        result = json.load(f)
    
    status = result["status"]
    assert status in ["NEGATIVE", "PARTIAL"], f"Status should be NEGATIVE or PARTIAL, got {status}"
    
    # Successor should lose to at least one parent
    parent_comp = result["parent_comparison"]
    assert parent_comp["successor_vs_random"] is False or \
           parent_comp["successor_vs_fixed_battery"] is False, \
           "Successor should lose to at least one parent for honest NEGATIVE"


def test_historical_negative_preserved():
    """Test that historical NEGATIVE (diagnosis_accuracy.json) is preserved unchanged."""
    historical_file = ROOT / "research/unified_problem_solving_v1/results/diagnosis_accuracy.json"
    assert historical_file.exists(), "Historical NEGATIVE file must be preserved"
    
    with open(historical_file) as f:
        historical = json.load(f)
    
    # Historical negative must have forced_wrong_rate=0.0 (signal leakage marker)
    assert historical["forced_wrong_rate"]["mean"] == 0.0, \
        "Historical forced_wrong_rate must be 0.0 (signal leakage marker)"
    assert historical["status"] == "NEGATIVE", \
        "Historical status must be NEGATIVE"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
