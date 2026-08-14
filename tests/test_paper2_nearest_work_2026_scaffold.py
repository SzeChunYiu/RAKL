"""#487 nearest-work audit directory contract.

The audit advanced from scaffold to filled on 2026-08-14. The lifecycle-state
assertion below tracks that transition; every safety invariant the scaffold
version asserted is retained, and the filled state adds stronger obligations
(non-empty deliverables, primary-source-anchored bibliography).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKT = ROOT / "research" / "paper2_nearest_work_2026"

DELIVERABLES = (
    "README.md",
    "CLAIM_MATRIX.md",
    "NOVELTY_THREAT_RANKING.md",
    "COMPARATOR_REQUIREMENTS.md",
    "MANUSCRIPT_DIFF_PLAN.md",
    "BIBLIOGRAPHY_PATCH.tex",
    "AUDIT_STATUS.json",
)


def test_nearest_work_audit_deliverables_exist() -> None:
    for name in DELIVERABLES:
        assert (PKT / name).is_file(), name


def test_nearest_work_audit_safety_invariants_hold() -> None:
    """These must hold in every lifecycle state, scaffold or filled."""
    status = json.loads((PKT / "AUDIT_STATUS.json").read_text(encoding="utf-8"))
    assert status["grants_scientific_authority"] is False
    assert status["grants_novelty_claim"] is False
    assert status["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"


def test_nearest_work_audit_terminal_state() -> None:
    status = json.loads((PKT / "AUDIT_STATUS.json").read_text(encoding="utf-8"))
    assert status["terminal"] == "AUDIT_FILLED__RED_THREAT_FOUND__MANUSCRIPT_ACTION_REQUIRED"
    assert all(state != "SCAFFOLD" for state in status["deliverables"].values())


def test_filled_audit_deliverables_are_substantive() -> None:
    """A filled audit must not regress to placeholder content."""
    for name in DELIVERABLES:
        text = (PKT / name).read_text(encoding="utf-8")
        assert "scaffold" not in text.lower(), f"{name} still reads as a scaffold"

    bibliography = (PKT / "BIBLIOGRAPHY_PATCH.tex").read_text(encoding="utf-8")
    assert bibliography.count(r"\bibitem") >= 20

    # The RED threat and its surviving residuals must stay recorded.
    ranking = (PKT / "NOVELTY_THREAT_RANKING.md").read_text(encoding="utf-8")
    assert "RED" in ranking
    assert "transportability" in ranking.lower()


def test_negative_results_are_preserved() -> None:
    """CANNOT_CHECK results carry the exact queries that produced them."""
    status = json.loads((PKT / "AUDIT_STATUS.json").read_text(encoding="utf-8"))
    assert status["cannot_check"], "negative results must not be dropped"
    for entry in status["cannot_check"]:
        assert entry["target"]
        assert entry["queries"], "a CANNOT_CHECK without its queries is not auditable"
