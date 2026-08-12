"""Pre-confirmatory Paper II objective-lane directory contract (#444)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE = ROOT / "research" / "empirical_10_of_10_v1" / "PAPER3" / "OBJECTIVE"
PAPER3 = OBJECTIVE.parent


def test_objective_lane_artifacts_exist_without_confirmatory_outcomes() -> None:
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
        "DEVELOPMENT_RESULT_V1.json",
        "PRECONFIRMATORY_FREEZE_V1.json",
        "NO_OUTCOME_ACCESS_AT_FREEZE.json",
    ]
    for name in required:
        assert (OBJECTIVE / name).is_file(), name

    generator = json.loads((OBJECTIVE / "GENERATOR_MANIFEST.json").read_text(encoding="utf-8"))
    assert generator["status"] == "DEVELOPMENT_COMPLETE__CONFIRMATORY_FROZEN_NOT_RUN"
    assert generator["development"]["outcomes_accessed"] is True
    assert generator["confirmatory"]["items_generated"] == 0
    assert generator["confirmatory"]["outcomes_accessed"] is False
    assert generator["confirmatory"]["total_n"] == 576
    assert generator["grants_scientific_authority"] is False

    freeze = json.loads((OBJECTIVE / "PRECONFIRMATORY_FREEZE_V1.json").read_text(encoding="utf-8"))
    assert freeze["status"] == "FROZEN_BEFORE_CONFIRMATORY_GENERATION"
    assert freeze["confirmatory_items_generated"] == 0
    assert freeze["confirmatory_outcomes_accessed"] is False

    # Confirmatory placeholders stay empty until the separately frozen epoch runs.
    assert (OBJECTIVE / "OBJECTIVE_TASKS.jsonl").read_text(encoding="utf-8") == ""
    assert (OBJECTIVE / "MACHINE_WITNESS_OUTPUTS.jsonl").read_text(encoding="utf-8") == ""
    assert (OBJECTIVE / "SEMANTIC_CONTROL_SCORES.jsonl").read_text(encoding="utf-8") == ""

    # Confirmatory result files must not exist before outcome access.
    for forbidden in ("PREDICTIVE_RESULTS.json", "PAIRED_INFERENCE.json", "FAMILY_ROBUSTNESS.json"):
        assert not (OBJECTIVE / forbidden).exists(), forbidden

    lane = json.loads((PAPER3 / "LANE_STATUS.json").read_text(encoding="utf-8"))
    assert lane["objective"] == "DEVELOPMENT_COMPLETE__CONFIRMATORY_FROZEN_NOT_RUN"
    assert lane["natural_domain_human"] == "BLOCKED_HUMAN"
    assert lane["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
    assert lane["grants_scientific_authority"] is False
