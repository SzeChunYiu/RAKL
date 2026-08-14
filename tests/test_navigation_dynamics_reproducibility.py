"""Test navigation_dynamics_experiment reproducibility.

This test validates that the experiment script produces deterministic, byte-identical
output across multiple runs with the same parameters. The test uses a minimal
parameter set (graphs_per_cell=1) to keep runtime short.

Root cause of issue #31: The committed artifact was manually annotated with
heuristic_contract_audit (PR #541), which the script does not generate.
See NAVIGATION_DYNAMICS_REPRODUCIBILITY_RECEIPT.json for full documentation.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
EXP_SCRIPT = REPO / "research" / "unified_problem_solving_v1" / "navigation_dynamics_experiment.py"
ARTIFACT_PATH = REPO / "research" / "unified_problem_solving_v1" / "results" / "navigation_dynamics.json"


@pytest.fixture(autouse=True)
def restore_committed_artifact():
    """Restore the committed artifact after each test that overwrites it."""
    # Read original content before test
    original_content = ARTIFACT_PATH.read_bytes()
    yield
    # Restore after test
    ARTIFACT_PATH.write_bytes(original_content)


def _run_experiment(seed: int, graphs_per_cell: int) -> bytes:
    """Run the experiment script once and return the output JSON bytes.

    WARNING: This overwrites the committed artifact. The restore_committed_artifact
    fixture will restore it after the test completes.
    """
    result = subprocess.run(
        [
            sys.executable,
            str(EXP_SCRIPT),
            "--seed", str(seed),
            "--graphs-per-cell", str(graphs_per_cell),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    if result.returncode != 0:
        pytest.fail(f"Experiment script failed: {result.stderr}")

    # Read the generated output
    return ARTIFACT_PATH.read_bytes()


def test_experiment_determinism_small():
    """Test that experiment produces identical output on two consecutive runs with small parameters.

    Uses graphs_per_cell=1 to keep runtime minimal while still testing the full code path.
    This validates RNG seeding, iteration order, and any other potential nondeterminism sources.
    """
    seed = 42  # Use a different seed than production to avoid conflicts
    graphs_per_cell = 1

    output1 = _run_experiment(seed, graphs_per_cell)
    output2 = _run_experiment(seed, graphs_per_cell)

    # Byte-for-byte identical
    assert output1 == output2, "Experiment output not deterministic: bytes differ between runs"

    # Verify it's valid JSON
    data = json.loads(output1)
    assert data["seed"] == seed
    assert data["graphs_per_cell"] == graphs_per_cell


def test_experiment_determinism_medium():
    """Test with slightly larger parameters to catch edge cases.

    Uses graphs_per_cell=2 to catch any issues that only appear with multiple graphs per cell.
    This is closer to the actual committed artifact parameters.
    """
    seed = 123
    graphs_per_cell = 2

    output1 = _run_experiment(seed, graphs_per_cell)
    output2 = _run_experiment(seed, graphs_per_cell)

    assert output1 == output2, "Experiment output not deterministic with graphs_per_cell=2"

    data = json.loads(output1)
    assert data["seed"] == seed
    assert data["graphs_per_cell"] == graphs_per_cell


def test_committed_artifact_semantically_correct():
    """Verify that running the script with committed parameters produces semantically equivalent output.

    The committed artifact has manual annotations (heuristic_contract_audit) that the script
    doesn't generate. This test verifies that the core data is identical even though the
    manual annotation is missing from the fresh output.

    Root cause (issue #31): The committed artifact was manually edited in PR #541 to add
    heuristic_contract_audit. The script cannot regenerate this byte-for-byte.
    """
    # Parameters from committed artifact
    seed = 461
    graphs_per_cell = 2

    output = _run_experiment(seed, graphs_per_cell)
    data = json.loads(output)

    # Read committed artifact (restored by fixture)
    committed_data = json.loads(ARTIFACT_PATH.read_bytes())

    # Core data should be identical
    assert data["schema_version"] == committed_data["schema_version"]
    assert data["seed"] == committed_data["seed"]
    assert data["graphs_per_cell"] == committed_data["graphs_per_cell"]
    assert data["graphs_made"] == committed_data["graphs_made"]
    assert data["status"] == committed_data["status"]  # Should both be NEGATIVE

    # The committed artifact has heuristic_contract_audit that we don't generate
    assert "heuristic_contract_audit" in committed_data
    assert "heuristic_contract_audit" not in data

    # Verify regime cells are semantically the same
    assert set(data["regime_cells"].keys()) == set(committed_data["regime_cells"].keys())
    for cell_key in data["regime_cells"]:
        assert data["regime_cells"][cell_key] == committed_data["regime_cells"][cell_key]


def test_reproducibility_receipt_exists():
    """Verify that the reproducibility receipt documenting issue #31 exists."""
    receipt_path = REPO / "research" / "unified_problem_solving_v1" / "NAVIGATION_DYNAMICS_REPRODUCIBILITY_RECEIPT.json"
    assert receipt_path.exists(), "Reproducibility receipt not found"

    receipt_data = json.loads(receipt_path.read_bytes())
    assert receipt_data["schema_version"] == "reproducibility-receipt-v1"
    assert "root_cause" in receipt_data
    assert "determinism_test" in receipt_data
