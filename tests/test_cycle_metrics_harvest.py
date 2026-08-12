"""Tests for prospective cycle-metrics harvest instrumentation (#446)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rakl.cycle_metrics_harvest import (
    INSTRUMENTATION_SCHEMA,
    build_instrumentation_row,
    emit_cycle_metrics_record,
    instrumentation_coverage,
    metrology_denominators_known,
    payload_schema_class,
    slice_metrology_fields,
)
from rakl.rakl_cycle_metrics import SCHEMA_VERSION, is_cannot_measure, minimal_cycle_metrics_template

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "research" / "paper5_longitudinal_v1" / "longitudinal_event_universe.jsonl"


def _v1_payload(**overrides) -> dict:
    doc = minimal_cycle_metrics_template(
        cycle_id="PROSPECTIVE-CYCLE-001",
        reason="eligible memory universe not frozen before retrieval",
    )
    doc.update(overrides)
    return doc


def test_payload_schema_class_detects_v1_and_legacy() -> None:
    assert payload_schema_class(_v1_payload()) == SCHEMA_VERSION
    assert payload_schema_class({"schema_version": "rakl-cycle-metrics-v1-proposal-shadow"}) == (
        "legacy_declared"
    )
    assert payload_schema_class({"cycle_id": "X"}) == "legacy_undeclared"
    assert payload_schema_class(None) == "unparseable"


def test_slice_metrology_fail_closed_for_legacy_payload() -> None:
    metrology = slice_metrology_fields({"schema_version": "legacy-shadow", "cycle_id": "C1"})
    universe = metrology["opportunity_denominators"]["eligible_memory_universe_count"]
    cost = metrology["cost"]["model_input_tokens"]
    reuse = metrology["reuse_funnel"]["successful_fresh_reuse"]
    assert is_cannot_measure(universe)
    assert is_cannot_measure(cost)
    assert is_cannot_measure(reuse)


def test_slice_metrology_passes_through_v1_sections() -> None:
    payload = _v1_payload()
    payload["opportunity_denominators"]["eligible_memory_universe_count"] = 5
    payload["reuse_funnel"]["successful_fresh_reuse"] = 2
    payload["cost"]["model_calls"] = 3
    metrology = slice_metrology_fields(payload)
    assert metrology["opportunity_denominators"]["eligible_memory_universe_count"] == 5
    assert metrology["reuse_funnel"]["successful_fresh_reuse"] == 2
    assert metrology["cost"]["model_calls"] == 3
    assert metrology_denominators_known(metrology) is True


def test_slice_metrology_missing_section_is_cannot_measure() -> None:
    payload = _v1_payload()
    payload.pop("cost")
    metrology = slice_metrology_fields(payload)
    assert is_cannot_measure(metrology["cost"]["model_input_tokens"])


def test_emit_cycle_metrics_record_returns_v1_verbatim() -> None:
    payload = _v1_payload(cycle_id="KEEP-ME")
    emitted = emit_cycle_metrics_record(payload)
    assert emitted["cycle_id"] == "KEEP-ME"
    assert emitted["schema_version"] == SCHEMA_VERSION


def test_emit_cycle_metrics_record_fail_closed_for_legacy() -> None:
    emitted = emit_cycle_metrics_record(
        {"schema_version": "legacy", "cycle_id": "LEGACY-1"},
    )
    assert emitted["schema_version"] == SCHEMA_VERSION
    universe = emitted["opportunity_denominators"]["eligible_memory_universe_count"]
    assert is_cannot_measure(universe)
    assert emitted["cycle_id"] == "LEGACY-1"


def test_build_instrumentation_row_marks_legacy_without_coercion() -> None:
    envelope = {
        "event_id": "abc123",
        "declared_schema_version": "rakl-cycle-metrics-v1-proposal-shadow",
        "payload": {"schema_version": "rakl-cycle-metrics-v1-proposal-shadow", "cycle_id": "C-OLD"},
    }
    row = build_instrumentation_row(envelope, instrumented_at="2026-08-12T10:00:00Z")
    assert row["schema_version"] == INSTRUMENTATION_SCHEMA
    assert row["payload_schema_class"] == "legacy_declared"
    assert row["denominators_known"] is False
    assert row["audit_passed"] is False
    assert row["emitted_cycle_metrics"]["cycle_id"] == "C-OLD"
    assert row["grants_scientific_authority"] is False


def test_build_instrumentation_row_audits_v1_payload() -> None:
    payload = _v1_payload()
    envelope = {
        "event_id": "v1blob",
        "declared_schema_version": SCHEMA_VERSION,
        "payload": payload,
    }
    row = build_instrumentation_row(envelope, instrumented_at="2026-08-12T10:00:00Z")
    assert row["payload_schema_class"] == SCHEMA_VERSION
    assert row["audit_passed"] is True
    assert row["audit_errors"] == []


def test_instrumentation_coverage_refuses_cross_version_pooling() -> None:
    rows = [
        {"payload_schema_class": SCHEMA_VERSION, "denominators_known": False, "audit_passed": True},
        {"payload_schema_class": "legacy_declared", "denominators_known": False, "audit_passed": False},
    ]
    report = instrumentation_coverage(rows)
    assert report["row_count"] == 2
    assert report["legacy_coercion_performed"] is False
    assert report["comparable_across_declared_versions"] is False


def test_longitudinal_harvester_wires_cycle_metrics_instrumentation() -> None:
    harvest_script = ROOT / "experiments" / "paper5" / "harvest_raklmath_longitudinal.py"
    source = harvest_script.read_text(encoding="utf-8")
    assert "from rakl.cycle_metrics_harvest import" in source
    assert "build_instrumentation_row" in source
    assert "instrumentation_coverage" in source
    assert "prospective_cycle_metrics_instrumentation.jsonl" in source
    assert "cycle_metrics_instrumentation_report.json" in source


@pytest.mark.skipif(not UNIVERSE.exists(), reason="frozen universe not present")
def test_instrument_frozen_universe_without_rerunning_harvest() -> None:
    envelopes = []
    for line in UNIVERSE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            envelopes.append(json.loads(line))
    rows = [build_instrumentation_row(env, instrumented_at="2026-08-12T10:00:00Z") for env in envelopes]
    report = instrumentation_coverage(rows)
    assert report["row_count"] == len(envelopes)
    assert report["legacy_coercion_performed"] is False
    for row in rows:
        assert row["grants_scientific_authority"] is False
        emitted = row["emitted_cycle_metrics"]
        assert emitted["schema_version"] == SCHEMA_VERSION
        if row["payload_schema_class"] != SCHEMA_VERSION:
            universe = emitted["opportunity_denominators"]["eligible_memory_universe_count"]
            assert is_cannot_measure(universe)
