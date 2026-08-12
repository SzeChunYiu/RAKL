"""Pre-outcome Paper III objective-lane directory contract (#444)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE = ROOT / "research" / "empirical_10_of_10_v1" / "PAPER3" / "OBJECTIVE"
PAPER3 = OBJECTIVE.parent


def test_objective_lane_scaffold_artifacts_exist_without_outcomes() -> None:
    required = [
        "PROTOCOL.md",
        "GENERATOR_MANIFEST.json",
        "HIDDEN_GOLD_MANIFEST.json",
        "OBJECTIVE_TASKS.jsonl",
        "VERIFIER_BINDING.json",
        "DEGENERACY_AUDIT.json",
        "POWER_RECEIPT.json",
        "MACHINE_WITNESS_PROTOCOL.json",
        "MACHINE_WITNESS_OUTPUTS.jsonl",
        "SEMANTIC_CONTROL_MANIFEST.json",
        "SEMANTIC_CONTROL_SCORES.jsonl",
    ]
    for name in required:
        assert (OBJECTIVE / name).is_file(), name

    generator = json.loads((OBJECTIVE / "GENERATOR_MANIFEST.json").read_text(encoding="utf-8"))
    assert generator["status"] == "SCAFFOLD_ONLY__NO_ITEMS_GENERATED"
    assert generator["items_generated"] == 0
    assert generator["outcomes_accessed"] is False
    assert generator["grants_scientific_authority"] is False

    # Empty placeholders must stay empty until generation/execution.
    assert (OBJECTIVE / "OBJECTIVE_TASKS.jsonl").read_text(encoding="utf-8") == ""
    assert (OBJECTIVE / "MACHINE_WITNESS_OUTPUTS.jsonl").read_text(encoding="utf-8") == ""
    assert (OBJECTIVE / "SEMANTIC_CONTROL_SCORES.jsonl").read_text(encoding="utf-8") == ""

    # Outcome-bearing result files must not be fabricated at scaffold time.
    for forbidden in ("PREDICTIVE_RESULTS.json", "PAIRED_INFERENCE.json", "FAMILY_ROBUSTNESS.json"):
        assert not (OBJECTIVE / forbidden).exists(), forbidden

    lane = json.loads((PAPER3 / "LANE_STATUS.json").read_text(encoding="utf-8"))
    assert lane["terminal"] == "OBJECTIVE_LANE_SCAFFOLD_ONLY__HUMAN_LANE_ABSENT"
    assert lane["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
