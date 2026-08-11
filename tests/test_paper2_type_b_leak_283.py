"""Lock issue #283: sealed Type B leak disposition + leak-free successor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rakl.degeneracy_probe import ArmPair, DegeneracyStatus, probe_arm_answer_leak

ROOT = Path(__file__).resolve().parents[1]

SEALED_PROMPTS = {
    "research/paper2_microtrial_v1": (
        "e2f3b59071894791e3199e8991887a246c97bde9147f1550547752fce1dde89f"
    ),
    "research/paper2_microtrial_v4_2": (
        "8a2ccc9b2623b21234dd1f9645501c96f68bb87f2ab50b2146e16edbe9ac12ea"
    ),
    "research/paper2_microtrial_v4_3_1": (
        "367edbc1ad3ee4f230bd9568cbda9b1b80d7e546215dda69e771a6805087c1f5"
    ),
}

SEALED_INGEST = {
    "research/paper2_microtrial_v4_2/PAPER2_V4_2_NATIVE_JOB_3476540_INGEST_RECEIPT_20260811.json": (
        "a0038a2a5d476fafbf5f749c6c78557ff81187ad540d10317c2bdf72f640cb37"
    ),
    "research/paper2_microtrial_v4_3_1/PAPER2_V4_3_1_NATIVE_JOB_3476576_INGEST_RECEIPT_20260811.json": (
        "6c7360827d518ea374dd3b226e14b61dff504b6058448bda4513e80e96bd6208"
    ),
}


def _gold() -> dict[str, frozenset[str]]:
    return {
        "misaligned_source_ids": frozenset({"S4", "S5"}),
        "required_refuted_source_ids": frozenset({"S6"}),
    }


def _load_sweep():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sweep_degeneracy", ROOT / "scripts/sweep_degeneracy.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("directory, expected_sha", sorted(SEALED_PROMPTS.items()))
def test_sealed_historical_prompts_are_not_rewritten(
    directory: str, expected_sha: str
) -> None:
    path = ROOT / directory / "RAKL_CONTEXT_PROMPT.txt"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha
    disposition = json.loads(
        (ROOT / directory / "TYPE_B_LEAK_DISPOSITION_283.json").read_text(encoding="utf-8")
    )
    assert disposition["verdict"] == "NOT_INFORMATIVE"
    assert disposition["status"] == "SEALED_KNOWN_TYPE_B_DEGENERATE"
    assert disposition["sealed_rakl_context_prompt_sha256"] == expected_sha
    assert disposition["issue"] == 283


@pytest.mark.parametrize("rel, expected_sha", sorted(SEALED_INGEST.items()))
def test_sealed_ingest_score_receipts_are_not_rewritten(
    rel: str, expected_sha: str
) -> None:
    path = ROOT / rel
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha


@pytest.mark.parametrize("directory", sorted(SEALED_PROMPTS))
def test_sealed_v_arms_remain_type_b_degenerate(directory: str) -> None:
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
    joined = "\n".join(finding.detail for finding in report.findings)
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
    assert "claim authority" in readme.lower()
    status = json.loads(
        (base / "HISTORICAL_ARM_COMPARISON_NOT_INFORMATIVE.json").read_text(
            encoding="utf-8"
        )
    )
    assert status["verdict"] == "NOT_INFORMATIVE"
    assert status["issue"] == 283


def test_sweep_gold_alias_assesses_misaligned_on_v4_2() -> None:
    """ROUND044 uses a longer key name; without the alias, misaligned is UNASSESSED."""

    mod = _load_sweep()
    gold, provenance = mod._find_gold(ROOT / "research/paper2_microtrial_v4_2")
    assert "misaligned_source_ids" in gold
    assert gold["misaligned_source_ids"] == frozenset({"S4", "S5"})
    assert "required_refuted_source_ids" in gold
    assert "ROUND044" in provenance or provenance.endswith(".json")


def test_sweep_exit_ignores_sealed_known_but_keeps_inventory() -> None:
    mod = _load_sweep()
    reports = mod.sweep_arm_pairs(ROOT)
    sealed = [
        report
        for report in reports
        if report.status is DegeneracyStatus.DEGENERATE and mod._is_sealed_known(report)
    ]
    assert len(sealed) >= 3
    draft = next(
        report for report in reports if "v4_4_leakfree_draft" in report.surface
    )
    assert draft.status is DegeneracyStatus.CLEAN
    assert mod.actionable_status(reports) is not DegeneracyStatus.DEGENERATE
