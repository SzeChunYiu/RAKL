from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "research/p5_p6_saturation_v1/ROUND_006_STATUS.json"


def _doc() -> dict:
    return json.loads(STATUS.read_text(encoding="utf-8"))


def test_round006_is_low_surface_gain_not_saturation() -> None:
    doc = _doc()
    assert doc["saturation_verdict"] == "NOT_SATURATED"
    assert doc["semantic_gain"] == "LOW_NEW_SURFACE_GAIN"
    assert doc["new_top_level_method_surfaces"] == []
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_human_learning_routes_map_to_existing_surfaces_with_new_activation_details() -> None:
    doc = _doc()
    assert "representation_or_fixation_failure_and_lift" in doc["mapped_existing_surfaces"]
    assert "explanation_reconstruction_and_mechanism_ancestry" in doc["mapped_existing_surfaces"]
    assert "failure_lattice_residual_consolidation" in doc["mapped_existing_surfaces"]
    assert "competence_frontier_deliberate_practice_scheduler" in doc["mapped_existing_surfaces"]
    assert "memory_retrieval_rehearsal_transfer" in doc["mapped_existing_surfaces"]
    assert "representation_challenge_on_inherited_constraint_mismatch" in doc["retained_activation_details"]


def test_round006_keeps_unsearched_route_families_explicitly_open() -> None:
    remaining = set(_doc()["remaining_route_families_before_bounded_surface_saturation"])
    assert "creativity_design_fixation_incubation_recombination" in remaining
    assert "organizational_learning_exploration_exploitation_brokerage" in remaining
    assert "causal_inference_identification_partial_identification" in remaining
    assert "scientific_method_philosophy_metascience" in remaining
    assert "scientific_visualization_human_factors_communication" in remaining
    assert "at_least_two_domain_specific_non_LLM_research_workflows" in remaining
