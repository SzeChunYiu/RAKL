"""Lock issue #283: live arms leak; leak-free draft is CLEAN; gold alias works."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.degeneracy_probe import ArmPair, DegeneracyStatus, probe_arm_answer_leak

ROOT = Path(__file__).resolve().parents[1]


def _gold() -> dict[str, frozenset[str]]:
    return {
        "misaligned_source_ids": frozenset({"S4", "S5"}),
        "required_refuted_source_ids": frozenset({"S6"}),
    }


@pytest.mark.parametrize(
    "directory",
    [
        "research/paper2_microtrial_v4_2",
        "research/paper2_microtrial_v4_3_1",
    ],
)
def test_live_v4_arms_are_type_b_degenerate(directory: str) -> None:
    base = ROOT / directory
    report = probe_arm_answer_leak(
        ArmPair(
            directory,
            (base / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
            (base / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
            _gold(),
        )
    )
    assert report.status is DegeneracyStatus.DEGENERATE
    fields = {finding.detail for finding in report.findings}
    joined = "\n".join(fields)
    assert "misaligned_source_ids" in joined
    assert "required_refuted_source_ids" in joined


def test_leakfree_draft_is_clean_and_not_executable() -> None:
    base = ROOT / "research/paper2_microtrial_v4_4_leakfree_draft"
    report = probe_arm_answer_leak(
        ArmPair(
            "v4_4_leakfree_draft",
            (base / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
            (base / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
            _gold(),
        )
    )
    assert report.status is DegeneracyStatus.CLEAN
    readme = (base / "README.md").read_text(encoding="utf-8")
    assert "NOT EXECUTABLE" in readme
    assert "no" in readme.lower() and "claim authority" in readme.lower()
    status = json.loads(
        (base / "HISTORICAL_ARM_COMPARISON_NOT_INFORMATIVE.json").read_text(
            encoding="utf-8"
        )
    )
    assert status["verdict"] == "NOT_INFORMATIVE"
    assert 283 == status["issue"]


def test_sweep_gold_alias_assesses_misaligned_on_v4_2() -> None:
    """ROUND044 uses a longer key name; without the alias, misaligned is UNASSESSED."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sweep_degeneracy", ROOT / "scripts/sweep_degeneracy.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    gold, provenance = mod._find_gold(ROOT / "research/paper2_microtrial_v4_2")
    assert "misaligned_source_ids" in gold
    assert gold["misaligned_source_ids"] == frozenset({"S4", "S5"})
    assert "required_refuted_source_ids" in gold
    assert "ROUND044" in provenance or provenance.endswith(".json")
