"""Tests for Paper5 durable registry + honest longitudinal analysis (#253)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "paper5" / "analyze_longitudinal_universe.py"
UNIVERSE = ROOT / "research" / "paper5_longitudinal_v1" / "longitudinal_event_universe.jsonl"


def _load():
    spec = importlib.util.spec_from_file_location("analyze_longitudinal_universe", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_refuses_cross_version_pooled_trajectory(tmp_path: Path):
    h = _load()
    assert UNIVERSE.is_file()
    out = tmp_path / "out"
    # Invoke core builders on the frozen universe without requiring matplotlib.
    universe = h.load_universe(UNIVERSE)
    analysis_id = "test-analysis"
    growth = []
    for env in universe:
        growth.extend(h.build_retained_growth_events(env, analysis_id))
    summary = h.cohort_axis_summary(growth)
    assert summary["pooled_trajectory_across_schema_versions"] == "CANNOT_MEASURE"
    assert summary["cohorts"]
    # Every cohort must refuse pooling with other versions.
    assert all(cohort["pooled_with_other_versions"] is False for cohort in summary["cohorts"])


def test_missing_stages_are_not_zeroed():
    h = _load()
    envelope = {
        "event_id": "blob1",
        "git_blob_sha1": "blob1",
        "payload_sha256": "abc",
        "declared_schema_version_present": True,
        "declared_schema_version": "rakl-cycle-metrics-v1",
        "payload": {
            "cycle_id": "C1",
            "new_ids": {"episode_ids": ["e1"], "lesson_ids": ["l1"]},
        },
        "source_paths": [],
        "source_refs": [],
        "reachable_from_main_history": False,
        "parse_error": None,
        "unmeasured_markers": {},
    }
    row = h.build_experience_conversion_row(envelope, "test")
    assert row["stages"]["task_episode_ids_declared"] == 1
    assert row["stages"]["lesson_ids_declared"] == 1
    assert row["stages"]["successful_reuse_ids_declared"] is None
    assert "successful_reuse_ids_declared" in row["absent_stages"]
    assert row["retrieval_is_not_reuse"] is True
    assert row["grants_scientific_authority"] is False


def test_registry_marks_branch_only_as_framework_archive():
    h = _load()
    envelope = {
        "event_id": "blob2",
        "git_blob_sha1": "blob2",
        "payload_sha256": "def",
        "declared_schema_version_present": False,
        "declared_schema_version": None,
        "payload": {"cycle_id": "C2"},
        "source_paths": ["x.json"],
        "source_refs": ["refs/remotes/origin/research/x"],
        "reachable_from_main_history": False,
        "parse_error": None,
        "unmeasured_markers": {"CANNOT_MEASURE": 1},
    }
    row = h.build_registry_row(envelope, "test")
    assert row["durability_class"] == "DURABLE_FRAMEWORK_ARCHIVE_ONLY_BRANCH_SOURCE"
    assert row["completeness_class"] in {
        "RETROSPECTIVE_INCOMPLETE",
        "RETROSPECTIVE_RECONSTRUCTABLE",
        "CANNOT_MEASURE",
        "PROSPECTIVE_PARTIAL",
    }
    assert row["grants_scientific_authority"] is False


def test_cli_writes_manifest_and_refuses_authority(tmp_path: Path):
    h = _load()
    out = tmp_path / "out"
    # Run main via module functions to keep the test hermetic.
    import sys
    from unittest import mock

    with mock.patch.object(
        sys,
        "argv",
        [
            "analyze_longitudinal_universe.py",
            "--universe",
            str(UNIVERSE),
            "--out-dir",
            str(out),
            "--analysis-id",
            "test-cli",
            "--skip-plots",
        ],
    ):
        h.main()

    receipt = json.loads((out / "ANALYSIS_RECEIPT.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "DATASET_MANIFEST.json").read_text(encoding="utf-8"))
    fig = json.loads((out / "figure_sources.json").read_text(encoding="utf-8"))
    assert receipt["grants_scientific_authority"] is False
    assert receipt["pooling_authorized"] is False
    assert receipt["status"] == "ANALYSIS_ADVANCED_RESIDUAL_OPEN"
    assert manifest["cross_version_pooling_authorized"] is False
    assert fig["fig2"]["pooled_trajectory"] == "CANNOT_MEASURE"
    assert fig["fig7"]["status"] == "CANNOT_MEASURE_AS_PROCESS_TELEMETRY_DASHBOARD"
    assert (out / "CYCLE_REGISTRY.jsonl").is_file()
    assert (out / "retained_growth_events.jsonl").is_file()
    registry_lines = (out / "CYCLE_REGISTRY.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(registry_lines) == 56
