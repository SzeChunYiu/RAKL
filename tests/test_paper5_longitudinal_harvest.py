"""Unit tests for the Paper5 RAKL_math longitudinal harvester (#253)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from rakl.cycle_metrics_harvest import INSTRUMENTATION_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "paper5" / "harvest_raklmath_longitudinal.py"


def _load():
    spec = importlib.util.spec_from_file_location("harvest_raklmath_longitudinal", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_is_telemetry_markers():
    h = _load()
    assert h.is_telemetry("research/foo/C001_RAKL_CYCLE_METRICS_v1.json")
    assert h.is_telemetry("x/PROPOSAL_TELEMETRY_bar.json")
    assert not h.is_telemetry("research/foo/README.md")
    assert not h.is_telemetry("CYCLE_METRICS_no_prefix.json")


def test_count_unmeasured_preserves_markers_without_invention():
    h = _load()
    raw = b'{"a":"CANNOT_MEASURE","b":"CANNOT_CHECK","c":"ok"}'
    counts = h.count_unmeasured(raw)
    assert counts == {"CANNOT_MEASURE": 1, "CANNOT_CHECK": 1}
    assert "NOT_MEASURED" not in counts


def test_coverage_report_refuses_cross_version_pooling():
    h = _load()
    envelopes = [
        {
            "declared_schema_version_present": True,
            "declared_schema_version": "v1",
            "payload_top_level_keys": ["cycle_id", "outcome"],
            "parse_error": None,
            "reachable_from_main_history": True,
            "source_refs": ["refs/remotes/origin/main"],
            "unmeasured_markers": {"CANNOT_MEASURE": 1},
        },
        {
            "declared_schema_version_present": False,
            "declared_schema_version": None,
            "payload_top_level_keys": ["cycle_id"],
            "parse_error": None,
            "reachable_from_main_history": False,
            "source_refs": ["refs/remotes/origin/research/x"],
            "unmeasured_markers": {},
        },
    ]
    report = h.coverage_report(envelopes)
    assert report["event_count"] == 2
    assert report["at_risk_branch_only"] == 1
    assert report["comparable_across_declared_versions"] is False
    assert report["grants_scientific_authority"] is False


def test_harvest_module_exports_instrumentation_version():
    h = _load()
    assert h.INSTRUMENTATION_VERSION == INSTRUMENTATION_SCHEMA


@pytest.mark.skipif(
    not (ROOT / "research" / "paper5_longitudinal_v1" / "longitudinal_event_universe.jsonl").exists(),
    reason="frozen universe not present",
)
def test_instrument_cycle_metrics_harvest_cli(tmp_path: Path):
    universe = ROOT / "research" / "paper5_longitudinal_v1" / "longitudinal_event_universe.jsonl"
    script = ROOT / "experiments" / "paper5" / "instrument_cycle_metrics_harvest.py"
    spec = importlib.util.spec_from_file_location("instrument_cycle_metrics_harvest", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # simulate CLI
    import sys
    from io import StringIO

    old_argv = sys.argv
    old_stdout = sys.stdout
    try:
        sys.argv = [
            "instrument_cycle_metrics_harvest.py",
            "--universe",
            str(universe),
            "--out-dir",
            str(tmp_path),
        ]
        sys.stdout = StringIO()
        mod.main()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout

    out_path = tmp_path / "prospective_cycle_metrics_instrumentation.jsonl"
    report_path = tmp_path / "cycle_metrics_instrumentation_report.json"
    assert out_path.exists()
    assert report_path.exists()
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(rows) == report["row_count"]
    assert report["legacy_coercion_performed"] is False
