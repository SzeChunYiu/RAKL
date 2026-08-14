from __future__ import annotations

import json
from pathlib import Path

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
STATUS = ROUND / "ROUND_007_STATUS.json"
PACKET = ROUND / "packets/failure_condition_minimization_v1.json"


def _status() -> dict:
    return json.loads(STATUS.read_text(encoding="utf-8"))


def test_registered_route_universe_is_complete_for_self_rakl_minimum_routes() -> None:
    doc = _status()
    routes = set(doc["registered_route_universe"])
    required = {
        "scientific_method_philosophy_metascience",
        "metacognition_self_regulated_learning_expert_learning",
        "expertise_deliberate_practice_adaptive_expertise",
        "cognitive_problem_solving_insight_representation_restructuring",
        "learning_science_productive_failure_contrastive_learning_self_explanation",
        "memory_retrieval_spacing_interleaving_chunking_scripts",
        "creativity_design_fixation_incubation_recombination",
        "organizational_learning_exploration_exploitation_brokerage",
        "active_learning_experiment_design_optimal_control",
        "formal_methods_truth_maintenance_belief_revision_provenance",
        "knowledge_representation_local_to_global_consistency",
        "causal_inference_identification_partial_identification_transportability",
        "information_retrieval_databases_memory_context_compression",
        "software_reliability_reproducibility_supply_chain_provenance",
        "self_improving_agents_program_evolution_skill_learning",
        "scientific_visualization_human_factors_communication",
    }
    assert required <= routes
    assert "domain_workflow_software_debugging" in routes
    assert "domain_workflow_model_based_engineering_diagnosis" in routes


def test_round007_claims_surface_flatness_not_operator_or_literature_saturation() -> None:
    doc = _status()
    assert doc["surface_saturation_verdict"] == "CANONICAL_METHOD_SURFACE_FLAT_ON_REGISTERED_ROUTE_UNIVERSE"
    assert doc["operator_basis_saturation_verdict"] == "NOT_SATURATED"
    assert doc["literature_saturation_verdict"] == "NOT_CLAIMED"
    assert doc["new_top_level_method_surfaces_this_round"] == []
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_failure_condition_minimization_packet_is_valid_and_unassessed() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    packet = packet_from_dict(doc)
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, report.reasons
    assert packet.mechanism_gate_state.value == "UNASSESSED"
    assert packet.applicability_gate_state.value == "UNASSESSED"
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False


def test_failure_minimization_does_not_confuse_minimal_context_with_cause() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    joined = " ".join(doc["assumptions"] + doc["hard_gate_obligations"] + doc["minimal_counterexamples"])
    assert "1-minimal is not globally minimum unless proven" in joined
    assert "minimized conditions do not by themselves identify causal mechanism" in joined
    assert "no causal authority from minimization" in joined
    parent_ids = {parent["parent_id"] for parent in doc["strongest_parents"]}
    assert "classic_delta_debugging_ddmin" in parent_ids
    assert "model_based_minimal_diagnosis" in parent_ids


def test_next_gate_requires_independent_repeat_before_operator_basis_flatness() -> None:
    assert "independent alternate-vocabulary repeat coverage pass" in _status()["next_gate"]
