from __future__ import annotations

import json
from pathlib import Path

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
STATUS = ROUND / "ROUND_008_STATUS.json"
PACKET = ROUND / "packets/minimal_conflict_correction_analysis_v1.json"


def _status() -> dict:
    return json.loads(STATUS.read_text(encoding="utf-8"))


def test_alternate_vocabulary_repeat_preserves_surface_flatness_but_not_operator_flatness() -> None:
    doc = _status()
    assert doc["search_mode"] == "INDEPENDENT_ALTERNATE_VOCABULARY_REPEAT"
    assert doc["surface_saturation_verdict"] == "CANONICAL_METHOD_SURFACE_STILL_FLAT_ON_REGISTERED_AND_REPEAT_ROUTE_UNIVERSE"
    assert doc["operator_basis_saturation_verdict"] == "NOT_SATURATED"
    assert doc["literature_saturation_verdict"] == "NOT_CLAIMED"
    assert doc["new_top_level_method_surfaces"] == []
    assert doc["new_missing_operator_implementations"] == ["minimal_conflict_correction_analysis_v1"]


def test_minimal_conflict_correction_packet_is_valid_and_unassessed() -> None:
    packet = packet_from_dict(json.loads(PACKET.read_text(encoding="utf-8")))
    report = validate_mechanic_research_packet(packet)
    expected_hash = packet.with_content_hash().packet_content_sha256
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, (
        report.reasons,
        "observed_hash",
        packet.packet_content_sha256,
        "recomputed_hash",
        expected_hash,
    )
    assert packet.mechanism_gate_state.value == "UNASSESSED"
    assert packet.applicability_gate_state.value == "UNASSESSED"
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False


def test_conflict_correction_semantics_are_distinct_from_failure_minimization() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    joined = " ".join(doc["assumptions"] + doc["hard_gate_obligations"] + doc["minimal_counterexamples"])
    assert "inclusion-minimal is not minimum-cardinality unless proven" in joined
    assert "returned conflict is actually inconsistent" in joined
    assert "returned correction actually restores consistency" in joined
    parent_ids = {parent["parent_id"] for parent in doc["strongest_parents"]}
    assert "QuickXplain_minimal_conflict" in parent_ids
    assert "MARCO_MUS_MCS_enumeration" in parent_ids
    assert "failure_condition_minimization_parent" in parent_ids


def test_repeat_maps_atms_and_algorithm_configuration_without_new_surface() -> None:
    mappings = _status()["repeat_flat_mappings"]
    assert "provenance" in mappings["ATMS_truth_maintenance"]
    assert "selector" in mappings["ParamILS_SMAC_algorithm_configuration"]


def test_new_conflict_operator_expands_failure_and_controller_neighbors() -> None:
    expanded = _status()["basis_expanded_before_execution"]
    assert "QuickXplain_minimal_conflict" in expanded["failure_condition_minimization_v1"]["required_new_parents_or_neighbors"]
    assert expanded["verified_failure_constraint_pdr_v2"]["required_new_input_type"] == ["verified_MUS_or_conflict_explanation"]
    assert set(expanded["mechanic_controller_with_synthesis_queries_v5"]["required_new_actions"]) == {
        "compute_minimal_conflict",
        "compute_minimal_correction_set",
    }
