from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
AMEND = ROUND / "ROUND_002_AMENDMENTS.json"
SUPER1 = ROUND / "ROUND_001_SUPERSESSION.json"

EXPECTED_AFFECTED = {
    "vtg_lean_geometry_v2",
    "field_cheapest_useful_selector_v2",
    "diagnosis_discriminating_intervention_v3",
    "navigation_quotient_validation_v1",
    "verified_solver_compilation_v1",
    "mechanic_value_of_computation_controller_v1",
}


def _amend() -> dict:
    return json.loads(AMEND.read_text(encoding="utf-8"))


def test_round002_is_not_saturated_and_grants_no_authority() -> None:
    doc = _amend()
    assert doc["saturation_verdict"] == "NOT_SATURATED"
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_round002_expands_exact_expected_candidate_basis_before_execution() -> None:
    doc = _amend()
    assert set(doc["basis_expanded_before_execution"]) == EXPECTED_AFFECTED
    next_packets = [row["next_packet_family"] for row in doc["basis_expanded_before_execution"].values()]
    assert len(next_packets) == len(set(next_packets))


def test_round002_does_not_rewrite_round001_supersession_history() -> None:
    first = json.loads(SUPER1.read_text(encoding="utf-8"))
    assert first["round"] == 1
    assert first["saturation_verdict"] == "NOT_SATURATED"
    assert first["superseded_before_execution"]["vtg_lean_geometry_v1"] == "vtg_lean_geometry_v2"
    # Round 002 appends a new basis-amendment layer instead of mutating round 001.
    assert _amend()["parent_round_head"] == "6c62396bd0ae90d9561e3dded360819d9a32a662"


def test_round002_records_adaptive_representation_and_execution_substrate_gaps() -> None:
    doc = _amend()["basis_expanded_before_execution"]
    assert "proof_state_snapshotting" in doc["vtg_lean_geometry_v2"]["required_new_parents"]
    assert "CEGAR_adaptive_abstraction_refinement" in doc["navigation_quotient_validation_v1"]["required_new_parents"]
    assert "ECED_correlated_noisy_tests" in doc["diagnosis_discriminating_intervention_v3"]["required_new_parents"]
    assert "real_time_cost_algebraic_search" in doc["field_cheapest_useful_selector_v2"]["required_new_parents"]


def test_hyperheuristic_generation_is_not_silently_collapsed_into_routing() -> None:
    row = _amend()["basis_expanded_before_execution"]["mechanic_value_of_computation_controller_v1"]
    assert "generation_hyperheuristic" in row["required_new_parent_or_child_surface"]
    assert "method-evolution" in row["governance_boundary"]
    assert "cannot self-promote" in row["governance_boundary"]


def test_unaffected_round001_packet_set_is_explicit_not_accidental() -> None:
    assert set(_amend()["unaffected_round001_packets"]) == {
        "path_equivalence_stateful_por_v3",
        "navigation_dynamic_parallel_portfolio_v3",
    }
