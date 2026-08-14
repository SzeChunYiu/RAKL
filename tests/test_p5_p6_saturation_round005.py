from __future__ import annotations

import json
from pathlib import Path

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "research/p5_p6_saturation_v1"
AMEND = ROUND / "ROUND_005_AMENDMENTS.json"
PACKET = ROUND / "packets/counterexample_guided_mechanism_synthesis_v1.json"


def _amend() -> dict:
    return json.loads(AMEND.read_text(encoding="utf-8"))


def test_round005_is_not_saturated_and_non_authoritative() -> None:
    doc = _amend()
    assert doc["saturation_verdict"] == "NOT_SATURATED"
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_cegis_synthesis_packet_is_valid_and_unassessed() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    packet = packet_from_dict(doc)
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, report.reasons
    assert packet.mechanism_gate_state.value == "UNASSESSED"
    assert packet.applicability_gate_state.value == "UNASSESSED"
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False


def test_synthesis_packet_records_cegis_and_sygus_as_strong_parents() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    parent_ids = {parent["parent_id"] for parent in doc["strongest_parents"]}
    assert "CEGIS_program_sketching" in parent_ids
    assert "SyGuS_grammar_guided_synthesis" in parent_ids
    assert "incumbent_orion_residual_invention" in parent_ids


def test_grammar_failure_is_not_semantic_impossibility() -> None:
    doc = json.loads(PACKET.read_text(encoding="utf-8"))
    joined = " ".join(doc["assumptions"] + doc["hard_gate_obligations"] + [doc["oracle_or_lower_bound"]])
    assert "no solution in grammar is not semantic impossibility" in joined
    assert "grammar failure not semantic impossibility" in joined


def test_negative_knowledge_has_three_distinct_authority_tiers() -> None:
    row = _amend()["basis_expanded_before_execution"]["verified_failure_constraint_compilation_v1"]
    assert row["required_new_authority_tiers"] == [
        "FAILED_ATTEMPT_WARNING",
        "LOCAL_VERIFIED_NOGOOD",
        "INDUCTIVE_BLOCKING_INVARIANT",
    ]
    assert "PDR_IC3_property_directed_reachability" in row["required_new_parents"]


def test_operational_map_basis_adds_active_model_queries() -> None:
    row = _amend()["basis_expanded_before_execution"]["operational_map_belief_v1"]
    assert "Angluin_Lstar_membership_equivalence_query_learning" in row["required_new_parent_or_mode"]
    assert set(row["required_new_query_types"]) == {
        "membership_query",
        "equivalence_query_with_counterexample",
    }
