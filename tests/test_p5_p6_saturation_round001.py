from __future__ import annotations

import json
from pathlib import Path

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
PACKETS = ROUND / "packets"
SUPERSESSION = ROUND / "ROUND_001_SUPERSESSION.json"

EXPECTED_NEW = {
    "vtg_lean_geometry_v2",
    "field_cheapest_useful_selector_v2",
    "diagnosis_discriminating_intervention_v3",
    "navigation_dynamic_parallel_portfolio_v3",
    "path_equivalence_stateful_por_v3",
    "mechanic_value_of_computation_controller_v1",
}

EXPECTED_SUPERSESSIONS = {
    "vtg_lean_geometry_v1": "vtg_lean_geometry_v2",
    "field_cheapest_useful_selector_v1": "field_cheapest_useful_selector_v2",
    "diagnosis_discriminating_intervention_v2": "diagnosis_discriminating_intervention_v3",
    "navigation_lazy_parallel_repair_v2": "navigation_dynamic_parallel_portfolio_v3",
    "path_equivalence_local_certification_v2": "path_equivalence_stateful_por_v3",
}


def _all_packet_docs() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(PACKETS.glob("*.json"))]


def _round001_packet_docs() -> list[dict]:
    by_variant = {doc["variant_id"]: doc for doc in _all_packet_docs()}
    return [by_variant[variant_id] for variant_id in sorted(EXPECTED_NEW)]


def test_round001_is_explicitly_not_saturated() -> None:
    supersession = json.loads(SUPERSESSION.read_text(encoding="utf-8"))
    assert supersession["saturation_verdict"] == "NOT_SATURATED"
    assert supersession["grants_scientific_authority"] is False
    assert supersession["grants_promotion_authority"] is False


def test_every_round001_successor_packet_is_content_valid_and_unassessed() -> None:
    docs = _round001_packet_docs()
    assert {doc["variant_id"] for doc in docs} == EXPECTED_NEW
    for doc in docs:
        packet = packet_from_dict(doc)
        report = validate_mechanic_research_packet(packet)
        assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, (
            doc["variant_id"], report.reasons
        )
        assert packet.mechanism_gate_state.value == "UNASSESSED"
        assert packet.applicability_gate_state.value == "UNASSESSED"
        assert packet.grants_scientific_authority is False
        assert packet.grants_promotion_authority is False


def test_shared_packet_directory_is_append_only_and_has_unique_variant_ids() -> None:
    variants = [doc["variant_id"] for doc in _all_packet_docs()]
    assert len(variants) == len(set(variants))
    assert EXPECTED_NEW <= set(variants)


def test_supersession_map_is_exact_and_replacements_are_present() -> None:
    supersession = json.loads(SUPERSESSION.read_text(encoding="utf-8"))
    assert supersession["superseded_before_execution"] == EXPECTED_SUPERSESSIONS
    replacements = set(supersession["superseded_before_execution"].values())
    packet_variants = {doc["variant_id"] for doc in _all_packet_docs()}
    assert replacements <= packet_variants
    assert set(supersession["new_variants"]) == {"mechanic_value_of_computation_controller_v1"}


def test_round001_packets_do_not_claim_outcomes() -> None:
    for doc in _round001_packet_docs():
        assert doc["frozen_before_implementation"] is True
        assert doc["frozen_before_outcome_access"] is True
        assert doc["mechanism_gate_state"] == "UNASSESSED"
        assert doc["applicability_gate_state"] == "UNASSESSED"
        assert "result" not in doc
        assert "promotion_verdict" not in doc


def test_value_of_computation_controller_keeps_do_nothing_and_authority_boundaries() -> None:
    controller = next(
        doc for doc in _round001_packet_docs()
        if doc["variant_id"] == "mechanic_value_of_computation_controller_v1"
    )
    joined = " ".join(controller["assumptions"] + controller["hard_gate_obligations"] + controller["minimal_counterexamples"])
    assert "do-nothing" in joined
    assert "authority" in joined
    assert controller["mechanic_id"] == "routing"


def test_path_por_packet_records_lower_bound_not_as_positive_authority() -> None:
    pathq = next(
        doc for doc in _round001_packet_docs()
        if doc["variant_id"] == "path_equivalence_stateful_por_v3"
    )
    assert "P=NP" in pathq["oracle_or_lower_bound"]
    assert "near-optimal" in pathq["oracle_or_lower_bound"]
    assert pathq["grants_scientific_authority"] is False
