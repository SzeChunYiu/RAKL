"""Unit tests for the Paper5 RAKL_math longitudinal harvester (#253)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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
