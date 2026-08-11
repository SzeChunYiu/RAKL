"""Lock the V4 microtrial parse-rate-vs-reasoning facts against silent drift.

These read the committed ingest receipts directly.  They exist because the claim
"DIRECT_CORPUS has never produced a scorable output in any generation" was asserted
and is false: V4.2 job 3476540 scored both arms.  The distinction matters because in
that one generation both arms scored identically, which makes every other
generation's apparent RAKL advantage a parse-rate difference rather than a
demonstrated reasoning difference.

These tests assert measured receipt contents, not a research conclusion.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_V4_2 = _ROOT / "research/paper2_microtrial_v4_2/PAPER2_V4_2_NATIVE_JOB_3476540_INGEST_RECEIPT_20260811.json"
_V4_3 = _ROOT / "research/paper2_microtrial_v4_3/PAPER2_V4_3_NATIVE_JOB_3476566_INGEST_RECEIPT_20260811.json"


def _outcome(path: Path) -> dict:
    if not path.exists():  # CANNOT_CHECK rather than a silent pass
        pytest.skip(f"receipt absent: {path.relative_to(_ROOT)}")
    return json.loads(path.read_text())["task_seed_outcome"]


def _by_condition(outcome: dict) -> dict:
    return {r["condition"]: r for r in outcome["records"]}


def test_v4_2_scored_both_arms() -> None:
    """The baseline arm HAS been scored; 'never scorable in any generation' is false."""
    o = _outcome(_V4_2)
    assert o["parse_valid_arm_count"] == 2
    assert o["scorable_arm_count"] == 2


def test_v4_2_both_arms_scored_identically() -> None:
    """When both arms parsed, RAKL did not out-reason the baseline."""
    o = _outcome(_V4_2)
    unscored = [r["condition"] for r in o["records"] if not isinstance(r.get("score"), dict)]
    assert not unscored, f"expected both arms scored, unscorable: {unscored}"
    scores = [r["score"]["conceptual_correct"] for r in o["records"]]
    totals = {r["score"]["conceptual_total"] for r in o["records"]}
    assert totals == {5}
    assert scores == [3, 3]


def test_v4_3_direct_corpus_regressed_to_parse_invalid() -> None:
    """V4.3 lost a baseline that V4.2 had working - a regression with a findable cause."""
    arms = _by_condition(_outcome(_V4_3))
    assert arms["DIRECT_CORPUS"]["parse_valid"] is False
    assert arms["DIRECT_CORPUS"]["score"] is None
    assert arms["RAKL_CONTEXT"]["parse_valid"] is True


def test_v4_3_larger_model_did_not_produce_exact_passes() -> None:
    """0.5B -> 1.5B escalation has been run and did not clear the exact gate."""
    o = _outcome(_V4_3)
    assert o["exact_conceptual_pass_arm_count"] == 0
    arms = _by_condition(o)
    assert arms["RAKL_CONTEXT"]["score"]["exact_conceptual_pass"] is False


def test_no_generation_licenses_an_arm_comparison() -> None:
    """Power (n=1) is the first-order blocker: even the both-scorable run refused it."""
    for path in (_V4_2, _V4_3):
        o = _outcome(path)
        assert o["evaluated_task_seed_unit_count"] == 1
        assert o["score_comparison_permitted"] is False


def test_arm_prompts_differ_only_by_the_rakl_context_map() -> None:
    """The parse asymmetry is not caused by differing output instructions."""
    d = _ROOT / "research/paper2_microtrial_v4_2"
    direct, rakl = d / "DIRECT_CORPUS_PROMPT.txt", d / "RAKL_CONTEXT_PROMPT.txt"
    if not (direct.exists() and rakl.exists()):
        pytest.skip("v4.2 prompt artifacts absent")
    a, b = direct.read_text(), rakl.read_text()
    start, end = b.find("RAKL CONTEXT MAP"), b.find("REGISTERED QUESTIONS")
    assert start != -1 and end > start
    assert b[:start] + b[end:] == a
