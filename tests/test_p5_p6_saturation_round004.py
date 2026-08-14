from __future__ import annotations

import json
from pathlib import Path

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
AMEND = ROUND / "ROUND_004_AMENDMENTS.json"
PACKET = ROUND / "packets/verified_failure_constraint_compilation_v1.json"


def _amend() -> dict:
    return json.loads(AMEND.read_text(encoding="utf-8"))


def test_round004_not_saturated_and_non_authoritative() -> None:
    doc = _amend()
    assert doc["saturation_verdict"] == "NOT_SATURATED"
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_incremental_recomputation_parent_is_generalized_beyond_handcoded_lazy_repair() -> None:
    row = _amend()["basis_expanded_before_execution"]["navigation_dynamic_parallel_portfolio_v3"]
    assert "self_adjusting_computation_dynamic_dependence_graph" in row["required_new_parents"]
    assert "Adapton_demand_driven_incremental_computation" in row["required_new_parents"]
    assert "change_propagation_work" in row["required_new_cost_coordinates"]


def test_verified_failure_constraint_packet_is_valid_and_unassessed() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    packet = packet_from_dict(doc)
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, report.reasons
    assert packet.mechanism_gate_state.value == "UNASSESSED"
    assert packet.applicability_gate_state.value == "UNASSESSED"
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False


def test_failure_memory_cannot_become_pruning_authority_without_refutation() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    joined = " ".join(doc["assumptions"] + doc["hard_gate_obligations"] + doc["minimal_counterexamples"])
    assert "failed attempt is not refutation" in joined
    assert "CANNOT_CHECK" in joined
    assert "zero false pruning" in joined
    assert "refutation/conflict witness required" in joined


def test_round004_adds_constraint_compilation_as_separate_controller_action() -> None:
    row = _amend()["basis_expanded_before_execution"]["mechanic_predictive_hierarchical_controller_v3"]
    assert row["required_new_action_type"] == ["compile_verified_failure_to_scoped_constraint"]
    assert _amend()["new_candidate_packets"] == ["verified_failure_constraint_compilation_v1"]
