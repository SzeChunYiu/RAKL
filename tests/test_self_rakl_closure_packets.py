from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


PACKETS = (
    "PACKET_construct_independence_admission_gate_v1.json",
    "PACKET_arn_local_vs_parent_discriminator_v1.json",
    "PACKET_question_measurement_responsibility_discriminator_v1.json",
)


@pytest.mark.parametrize("filename", PACKETS)
def test_closure_wave1_packet_is_content_bound_and_ready(filename: str) -> None:
    path = Path("research/self_rakl_closure_v1") / filename
    document = json.loads(path.read_text(encoding="utf-8"))
    packet = packet_from_dict(document)
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, report.reasons
    assert report.eligible_for_existing_promotion_gate is True
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False


def test_closure_contract_cannot_force_positive_outcomes() -> None:
    path = Path("research/self_rakl_closure_v1/CLOSURE_CONTRACT.json")
    contract = json.loads(path.read_text(encoding="utf-8"))
    terminals = set(contract["terminal_states"])
    assert {"REFUTED", "NULL", "PARENT_SUFFICIENT", "REGIME_LIMITED"} <= terminals
    assert "threshold relaxation after outcomes" in contract["forbidden_closure_shortcuts"]
    assert contract["grants_scientific_authority"] is False
    assert contract["grants_method_promotion_authority"] is False
