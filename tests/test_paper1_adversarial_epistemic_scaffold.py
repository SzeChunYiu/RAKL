"""#489 adversarial epistemic benchmark design scaffold."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKT = ROOT / "research" / "paper1_adversarial_epistemic_benchmark_v1"


def test_adversarial_epistemic_design_scaffold() -> None:
    for name in (
        "README.md",
        "DESIGN_FREEZE.json",
        "COMPARATOR_MODELS.md",
        "EPISODE_FAMILIES.md",
        "METRICS.md",
        "PROTOCOL.md",
    ):
        assert (PKT / name).is_file(), name
    freeze = json.loads((PKT / "DESIGN_FREEZE.json").read_text(encoding="utf-8"))
    assert freeze["terminal"] == "BENCHMARK_DESIGN_SCAFFOLD_ONLY__NO_EPISODES_EXECUTED"
    assert freeze["episodes_generated"] == 0
    assert freeze["outcomes_accessed"] is False
    assert freeze["grants_scientific_authority"] is False
    assert freeze["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
    assert freeze["independent_human_review"] == "NOT_CLAIMED"
