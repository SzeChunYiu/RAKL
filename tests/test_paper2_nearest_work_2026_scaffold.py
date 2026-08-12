"""#487 nearest-work audit directory contract (scaffold only)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKT = ROOT / "research" / "paper2_nearest_work_2026"


def test_nearest_work_audit_scaffold_exists() -> None:
    for name in (
        "README.md",
        "CLAIM_MATRIX.md",
        "NOVELTY_THREAT_RANKING.md",
        "COMPARATOR_REQUIREMENTS.md",
        "MANUSCRIPT_DIFF_PLAN.md",
        "BIBLIOGRAPHY_PATCH.tex",
        "AUDIT_STATUS.json",
    ):
        assert (PKT / name).is_file(), name
    status = json.loads((PKT / "AUDIT_STATUS.json").read_text(encoding="utf-8"))
    assert status["terminal"] == "AUDIT_SCAFFOLD_ONLY__ROWS_NOT_FILLED"
    assert status["grants_scientific_authority"] is False
    assert status["grants_novelty_claim"] is False
    assert status["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
