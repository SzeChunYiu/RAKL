from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "research/p5_p6_saturation_v1/ROUND_009_STATUS.json"


def _doc() -> dict:
    return json.loads(STATUS.read_text(encoding="utf-8"))


def test_round009_supports_bounded_operator_family_flatness_only() -> None:
    doc = _doc()
    assert doc["surface_saturation_verdict"] == "CANONICAL_METHOD_SURFACE_FLAT_ON_BOUNDED_SEARCH_UNIVERSE"
    assert doc["operator_family_saturation_verdict"] == "OPERATOR_FAMILY_FLAT_ON_REGISTERED_ROUTE_AND_REPEAT_UNIVERSE"
    assert doc["implementation_basis_verdict"] == "NOT_CLOSED"
    assert doc["empirical_evidence_verdict"] == "NOT_CLOSED"
    assert doc["literature_saturation_verdict"] == "NOT_CLAIMED"
    assert doc["new_top_level_method_surfaces"] == []
    assert doc["new_operator_families"] == []
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_adversarial_neighborhoods_map_to_existing_operator_families() -> None:
    mappings = _doc()["new_stronger_parent_mappings"]
    assert "CEGIS_counterexample_refinement" in mappings["automated_program_repair"]
    assert "minimal_conflict_correction_analysis" in mappings["abductive_diagnosis"]
    assert "CEGAR_refinement" in mappings["abstract_interpretation"]
    assert "minimal_correction_or_diagnosis" in mappings["hitting_set_diagnosis"]


def test_flatness_licenses_pause_not_global_saturation() -> None:
    doc = _doc()
    assert "broad operator-family search may pause" in doc["licensed_boundary"]
    assert "Reopen" in doc["licensed_boundary"]
    assert doc["next_phase"] == "IMPLEMENT_ABSORB_BENCHMARK_EXISTING_FROZEN_OPERATOR_FAMILIES"
