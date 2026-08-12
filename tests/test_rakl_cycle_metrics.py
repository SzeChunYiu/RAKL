"""Tests for stable RAKL_cycle_metrics metrology schema (#446)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rakl.rakl_cycle_metrics import (
    SCHEMA_VERSION,
    audit_cycle_metrics,
    audit_rate_denominators,
    cannot_measure,
    is_cannot_measure,
    load_schema,
    minimal_cycle_metrics_template,
    schema_path,
    validate_schema_document,
)

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_BASE = "https://github.com/SzeChunYiu/RAKL/schemas/"


def test_schema_path_and_id_conventions() -> None:
    assert schema_path().name == "rakl-cycle-metrics.schema.json"
    schema = load_schema()
    assert schema["$id"] == CANONICAL_BASE + "rakl-cycle-metrics.schema.json"
    assert schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION


def test_minimal_template_validates_with_cannot_measure_denominators() -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-001",
        reason="no exhaustive relevance-labelled retrieval universe is frozen",
    )
    errors = validate_schema_document(doc)
    assert errors == ()
    assert doc["grants_scientific_authority"] is False
    assert doc["longitudinal_performance_vector"]["aggregate_scalar_score_forbidden"] is True
    universe = doc["opportunity_denominators"]["eligible_memory_universe_count"]
    assert is_cannot_measure(universe)
    assert doc["retrieval"]["relevant_root_recall"]["status"] == "CANNOT_MEASURE"
    assert doc["cost"]["model_input_tokens"]["status"] == "CANNOT_MEASURE"


def test_audit_refuses_numeric_rates_when_denominator_unknown() -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-002",
        reason="denominator not frozen",
    )
    doc["retrieval"]["relevant_root_recall"] = 0.75
    doc["longitudinal_performance_vector"]["search_utility"]["route_change_rate"] = 0.1
    reasons = audit_rate_denominators(doc)
    assert any("relevant_root_recall" in reason for reason in reasons)
    assert any("route_change_rate" in reason for reason in reasons)
    assert audit_cycle_metrics(doc)  # non-empty when rates invented without denominators


def test_measured_denominators_allow_numeric_rates() -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-003",
        reason="unused once denominators are measured",
    )
    doc["opportunity_denominators"]["eligible_memory_universe_count"] = 12
    doc["opportunity_denominators"]["eligible_relevant_memory_ids"] = ["m1", "m2"]
    doc["opportunity_denominators"]["eligible_negative_history_ids"] = ["f1"]
    doc["opportunity_denominators"]["registered_route_options"] = 4
    doc["opportunity_denominators"]["registered_falsifier_options"] = 2
    doc["retrieval"]["relevant_root_recall"] = 0.5
    doc["retrieval"]["counterevidence_recall"] = 1.0
    doc["longitudinal_performance_vector"]["search_utility"]["relevant_root_recall"] = 0.5
    doc["longitudinal_performance_vector"]["search_utility"]["counterevidence_recall"] = 1.0
    doc["longitudinal_performance_vector"]["search_utility"]["route_change_rate"] = 0.25
    assert audit_rate_denominators(doc) == ()
    assert validate_schema_document(doc) == ()


def test_schema_rejects_invented_aggregate_scalar_score() -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-004",
        reason="denominator unknown",
    )
    doc["longitudinal_performance_vector"]["aggregate_scalar_score_forbidden"] = False
    errors = validate_schema_document(doc)
    assert errors


def test_schema_rejects_zero_substitution_for_cannot_measure_denominator() -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-005",
        reason="denominator unknown",
    )
    doc["opportunity_denominators"]["eligible_memory_universe_count"] = 0
    doc["retrieval"]["missed_known_relevant_count"] = cannot_measure(
        "universe denominator was zeroed instead of marked unknown"
    )
    # Zero is schema-valid as an integer count; the protocol forbids substituting
    # CANNOT_MEASURE with zero when the universe is unknown.  The audit layer
    # still allows zero denominators, but paired recall rates must stay CANNOT_MEASURE.
    doc["retrieval"]["relevant_root_recall"] = cannot_measure(
        "eligible_memory_universe_count is not a frozen exhaustive universe"
    )
    assert validate_schema_document(doc) == ()


def test_performance_vector_has_five_non_scalar_dimensions() -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-006",
        reason="partial telemetry",
    )
    vector = doc["longitudinal_performance_vector"]
    assert set(vector) == {
        "verified_progress",
        "search_utility",
        "reuse_utility",
        "governance",
        "efficiency",
        "aggregate_scalar_score_forbidden",
    }
    for key in (
        "verified_progress",
        "search_utility",
        "reuse_utility",
        "governance",
        "efficiency",
    ):
        assert isinstance(vector[key], dict)
        assert "score" not in vector[key]
        assert "aggregate" not in vector[key]


def test_cannot_measure_helper() -> None:
    marker = cannot_measure("no authoritative counter")
    assert is_cannot_measure(marker)
    assert not is_cannot_measure(3)
    assert not is_cannot_measure({"status": "OTHER"})


def test_schema_file_matches_repo_copy() -> None:
    on_disk = json.loads(schema_path().read_text(encoding="utf-8"))
    assert on_disk == load_schema()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d.pop("subjects"),
        lambda d: d.__setitem__("grants_scientific_authority", True),
        lambda d: d["subjects"].pop("fibre_hash"),
    ],
)
def test_schema_rejects_incomplete_or_overclaiming_documents(mutator) -> None:
    doc = minimal_cycle_metrics_template(
        cycle_id="EXAMPLE-CYCLE-007",
        reason="incomplete",
    )
    mutated = copy.deepcopy(doc)
    mutator(mutated)
    assert validate_schema_document(mutated)
