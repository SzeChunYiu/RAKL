"""End-to-end validation of the Paper 5 attribution instrument.

The four-arm study had never been executed, so the pipeline had never been shown
to report the truth. These tests drive the real production path -- schedule
builder, executor contract builder, orchestrator, analyzer -- against a synthetic
adapter whose answers are known in advance, and check that the analyzer recovers
them.

Three modes, because one is not enough:

* ``NULL_CONSTANT`` and ``NULL_NOISE`` check that the harness does not invent an
  effect. On their own they are satisfied by a pipeline hard-wired to report
  nothing.
* ``PLANTED_LIFT`` checks the other direction: a known ``+0.20`` on
  ``RAKL_LEARNING`` must be recovered on the three contrasts that involve that
  arm, and must **not** appear on ``ARCHITECTURE``, which compares two arms that
  carry no offset. That is the specificity check -- it catches an analyzer that
  finds an effect but attributes it to the wrong arm.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "experiments/paper5/run_harness_selftest.py"
RUN_SCHEMA = ROOT / "schemas" / "paper5-attribution-run-v1.schema.json"

LEARNING_CONTRASTS = ("TOTAL", "EXPERIENCE", "CONTENT")
TASKS_PER_STRATUM = 4


def _load_module(relative: str, name: str) -> Any:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter() -> Any:
    return _load_module("experiments/paper5/selftest_adapter.py", "selftest_adapter")


def _analyzer() -> Any:
    return _load_module("experiments/paper5/analyze_attribution_results.py", "analyze_attribution_results")


def _execute(root: Path, mode: str, repetitions: int) -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable, str(DRIVER),
            "--mode", mode,
            "--out-root", str(root),
            "--tasks-per-stratum", str(TASKS_PER_STRATUM),
            "--repetitions", str(repetitions),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"{mode} r{repetitions} driver failed:\n{proc.stdout}\n{proc.stderr}"
    mode_dir = root / f"{mode}-r{repetitions}"
    return {
        "dir": mode_dir,
        "summary": json.loads((mode_dir / "analysis" / "summary.json").read_text(encoding="utf-8")),
        "receipt": json.loads((mode_dir / "selftest_receipt.json").read_text(encoding="utf-8")),
        "records": [
            json.loads(line)
            for line in (mode_dir / "results.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ],
    }


@pytest.fixture(scope="module")
def selftest_runs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """Execute all three modes once; the modes are deterministic."""
    root = tmp_path_factory.mktemp("paper5-selftest")
    out: dict[str, dict[str, Any]] = {}
    for mode in ("NULL_CONSTANT", "NULL_NOISE", "PLANTED_LIFT"):
        out[mode] = _execute(root, mode, 1)
    return out


@pytest.fixture(scope="module")
def planted_lift_three_reps(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """PLANTED_LIFT at the preregistered 3 repetitions.

    At one repetition the analyzer's ``success = successes > repetitions/2.0``
    collapses to ``successes > 0.5``, so the majority-vote aggregation the
    confirmatory packet actually depends on is never exercised, and neither is
    the within-task mean over generations. Validating the instrument only in a
    configuration the real study will not use would leave that rule untested.
    """
    root = tmp_path_factory.mktemp("paper5-selftest-r3")
    return _execute(root, "PLANTED_LIFT", 3)


def _contrasts(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["contrast"]: row for row in summary["contrasts"]}


def test_every_mode_produced_the_full_run_grid(selftest_runs: dict[str, dict[str, Any]]) -> None:
    expected = TASKS_PER_STRATUM * 3 * 4  # strata x arms, one repetition
    for mode, data in selftest_runs.items():
        assert len(data["records"]) == expected, mode


def test_all_records_validate_against_the_frozen_run_schema(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    validator = Draft202012Validator(json.loads(RUN_SCHEMA.read_text(encoding="utf-8")))
    for mode, data in selftest_runs.items():
        for record in data["records"]:
            errors = list(validator.iter_errors(record))
            assert not errors, f"{mode}/{record['run_id']}: {[err.message for err in errors]}"


def test_null_constant_yields_exactly_zero_on_every_contrast(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    """Score depends on task_id alone, so every paired difference must be exactly 0."""
    for name, row in _contrasts(selftest_runs["NULL_CONSTANT"]["summary"]).items():
        assert row["mean_score_delta"] == 0.0, name
        assert row["success_rate_delta"] == 0.0, name
        assert row["score_delta_ci_low"] == 0.0 and row["score_delta_ci_high"] == 0.0, name


def test_null_noise_produces_real_variation_but_no_detected_effect(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    contrasts = _contrasts(selftest_runs["NULL_NOISE"]["summary"])
    assert any(row["mean_score_delta"] != 0.0 for row in contrasts.values()), (
        "NULL_NOISE must realize non-zero deltas, otherwise it is not testing anything NULL_CONSTANT does not"
    )
    for name, row in contrasts.items():
        assert row["score_delta_ci_low"] <= 0.0 <= row["score_delta_ci_high"], f"{name} interval excludes 0"
        assert row["score_sign_flip_p"] >= 0.05, f"{name} false positive at p={row['score_sign_flip_p']}"


def test_planted_lift_is_recovered_on_the_learning_contrasts(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    """The positive control: the instrument must be able to find a real effect."""
    contrasts = _contrasts(selftest_runs["PLANTED_LIFT"]["summary"])
    for name in LEARNING_CONTRASTS:
        row = contrasts[name]
        assert row["mean_score_delta"] >= 0.10, f"{name} failed to recover the planted lift: {row}"
        assert row["score_delta_ci_low"] > 0.0, f"{name} interval covers 0 despite a planted effect"
        assert row["score_sign_flip_p"] < 0.05, f"{name} p={row['score_sign_flip_p']}"


def test_planted_lift_does_not_leak_onto_the_architecture_contrast(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    """RAKL_RESET vs MODEL_ONLY carries no offset, so the effect must not appear there."""
    row = _contrasts(selftest_runs["PLANTED_LIFT"]["summary"])["ARCHITECTURE"]
    assert abs(row["mean_score_delta"]) < 0.10, row
    assert row["score_sign_flip_p"] >= 0.05, row
    for name in LEARNING_CONTRASTS:
        learning = _contrasts(selftest_runs["PLANTED_LIFT"]["summary"])[name]
        assert learning["mean_score_delta"] > row["mean_score_delta"], name


def test_summaries_are_stamped_as_instrument_validation(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    for mode, data in selftest_runs.items():
        summary = data["summary"]
        assert summary["harness_self_test"] is not None, mode
        assert summary["harness_self_test"]["mode"] == mode
        assert summary["harness_self_test"]["model_invoked"] is False
        assert summary["grants_scientific_authority"] is False
        assert "HARNESS SELF-TEST" in summary["claim_boundary"]
        assert data["receipt"]["grants_scientific_authority"] is False
        assert data["receipt"]["model_invoked"] is False


def test_majority_vote_aggregation_recovers_the_planted_lift_at_three_repetitions(
    planted_lift_three_reps: dict[str, Any]
) -> None:
    """Exercises the aggregation rule the confirmatory packet depends on."""
    data = planted_lift_three_reps
    assert len(data["records"]) == TASKS_PER_STRATUM * 3 * 4 * 3, "12 tasks x 4 arms x 3 repetitions"
    assert data["summary"]["repetitions"] == 3
    contrasts = _contrasts(data["summary"])
    for name in LEARNING_CONTRASTS:
        row = contrasts[name]
        assert row["mean_score_delta"] >= 0.10, f"{name} lost the planted lift under 3-rep aggregation: {row}"
        # success_rate_delta comes from majority vote, not the mean score path.
        assert row["success_rate_delta"] > 0.0, f"{name} majority-vote success did not move: {row}"
    assert abs(contrasts["ARCHITECTURE"]["mean_score_delta"]) < 0.10


def test_analysis_parameters_are_pinned_not_inherited_from_defaults(
    selftest_runs: dict[str, dict[str, Any]]
) -> None:
    """The receipt quotes intervals and p-values, so their inputs must be recorded."""
    for mode, data in selftest_runs.items():
        params = data["receipt"]["analysis_parameters"]
        assert params["bootstrap_seed"] == 20260811, mode
        assert params["bootstrap_iterations"] == 20000, mode
        assert params["permutation_iterations"] == 100000, mode


def test_analyzer_refuses_to_mix_self_test_and_model_records() -> None:
    analyzer = _analyzer()
    tagged = {"run_id": "a", "harness_self_test": {"adapter_id": "x", "mode": "NULL_NOISE"}}
    untagged = {"run_id": "b"}
    assert analyzer.self_test_provenance([untagged]) is None
    assert analyzer.self_test_provenance([tagged])["mode"] == "NULL_NOISE"
    with pytest.raises(SystemExit):
        analyzer.self_test_provenance([tagged, untagged])


def test_analyzer_refuses_to_mix_two_self_test_modes() -> None:
    analyzer = _analyzer()
    rows = [
        {"run_id": "a", "harness_self_test": {"adapter_id": "x", "mode": "NULL_NOISE"}},
        {"run_id": "b", "harness_self_test": {"adapter_id": "x", "mode": "PLANTED_LIFT"}},
    ]
    with pytest.raises(SystemExit):
        analyzer.self_test_provenance(rows)


def test_null_constant_score_ignores_arm_and_repetition() -> None:
    adapter = _adapter()
    baseline = adapter.score_for("NULL_CONSTANT", "S001", 1, "MODEL_ONLY")
    for arm in ("MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING"):
        for repetition in (1, 2, 3):
            assert adapter.score_for("NULL_CONSTANT", "S001", repetition, arm) == baseline


def test_null_noise_uses_identical_bounds_for_every_arm() -> None:
    """Arm selects the draw, never the distribution."""
    adapter = _adapter()
    per_arm: dict[str, list[float]] = {}
    for arm in ("MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING"):
        per_arm[arm] = [
            adapter.score_for("NULL_NOISE", f"S{index:03d}", 1, arm) for index in range(400)
        ]
    for arm, scores in per_arm.items():
        assert min(scores) >= 0.2, arm
        assert max(scores) <= 0.8, arm
        assert abs(sum(scores) / len(scores) - 0.5) < 0.03, arm


def test_planted_lift_offset_applies_to_exactly_one_arm() -> None:
    adapter = _adapter()
    for index in range(50):
        task_id = f"S{index:03d}"
        without = adapter.score_for("PLANTED_LIFT", task_id, 1, "RAKL_RESET")
        assert 0.2 <= without <= 0.6
        with_offset = adapter.score_for("PLANTED_LIFT", task_id, 1, adapter.PLANTED_ARM)
        assert with_offset >= 0.2 + adapter.PLANTED_LIFT_DELTA
        assert with_offset <= 1.0


def test_adapter_refuses_a_packet_that_is_not_a_self_test_packet() -> None:
    """The synthetic adapter must not be usable against a real Paper 5 packet."""
    adapter = _adapter()
    with pytest.raises(SystemExit):
        adapter.mode_from_packet_id("paper5-confirmatory-v1")
    with pytest.raises(SystemExit):
        adapter.mode_from_packet_id("paper5-harness-selftest-NOT_A_MODE")
    assert adapter.mode_from_packet_id("paper5-harness-selftest-PLANTED_LIFT") == "PLANTED_LIFT"
