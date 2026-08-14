from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
AMEND = ROUND / "ROUND_003_AMENDMENTS.json"


def _doc() -> dict:
    return json.loads(AMEND.read_text(encoding="utf-8"))


def test_round003_is_not_saturated_and_non_authoritative() -> None:
    doc = _doc()
    assert doc["saturation_verdict"] == "NOT_SATURATED"
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_predictive_field_is_distinct_from_goal_specific_field() -> None:
    row = _doc()["basis_expanded_before_execution"]["field_online_learning_portfolio_v3"]
    assert "successor_representation" in row["required_new_parents"]
    assert "successor_features_generalized_policy_improvement" in row["required_new_parents"]
    assert "same_dynamics_changed_goal_or_QoI" in row["required_new_scope_coordinates"]
    assert _doc()["new_candidate_family"]["predictive_dynamics_field_v1"]


def test_diagnosis_requires_active_diagnosability_gate_before_policy_optimization() -> None:
    row = _doc()["basis_expanded_before_execution"]["diagnosis_structured_acquisition_v4"]
    assert "active_diagnosability_planning_DES" in row["required_new_parents"]
    assert row["required_new_hard_gate"] == "ACTIVE_DIAGNOSABILITY_OR_IDENTIFIED_REPAIR_PARTITION"


def test_geometry_must_challenge_behavioral_metric_and_operator_basis() -> None:
    row = _doc()["basis_expanded_before_execution"]["vtg_lean_geometry_v3"]
    assert "behavioral_or_bisimulation_metric_on_transition_known_subfamilies" in row["required_new_parent_or_ablation"]
    assert "operator_basis_hierarchy_tactics_lemmas_macros" in row["required_new_parent_or_ablation"]


def test_controller_basis_includes_policy_recombination_and_temporal_hierarchy() -> None:
    row = _doc()["basis_expanded_before_execution"]["mechanic_hyperheuristic_voc_controller_v2"]
    assert "policy_cache_generalized_policy_improvement" in row["required_new_parent_or_action_type"]
    assert "hierarchical_temporally_extended_operator_selection" in row["required_new_parent_or_action_type"]
