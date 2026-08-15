from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.mechanic_research_packet import MechanicResearchPacketVerdict, validate_mechanic_research_packet
from rakl.mechanic_research_packet_io import packet_from_dict


PACKETS = (
    "PACKET_construct_independence_stratum_homogeneity_v2.json",
    "PACKET_question_measurement_responsibility_discriminator_v1.json",
    "PACKET_arn_local_vs_parent_discriminator_v2.json",
)


@pytest.mark.parametrize("filename", PACKETS)
def test_wave1c_packets_are_content_bound_and_ready(filename: str) -> None:
    path = Path("research/self_rakl_closure_v1") / filename
    packet = packet_from_dict(json.loads(path.read_text(encoding="utf-8")))
    report = validate_mechanic_research_packet(packet)
    assert report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE, report.reasons
    assert report.eligible_for_existing_promotion_gate is True
    assert packet.grants_scientific_authority is False
    assert packet.grants_promotion_authority is False


def test_arn_v2_is_explicitly_downstream_of_stratum_homogeneity_v2() -> None:
    document = json.loads(
        Path("research/self_rakl_closure_v1/PACKET_arn_local_vs_parent_discriminator_v2.json").read_text(encoding="utf-8")
    )
    obligations = set(document["hard_gate_obligations"])
    assert "construct-independence v2 including STRATUM_HOMOGENEITY passes" in obligations
    assert document["fresh_assurance_benchmark_id"] == "ARN-DISCRIMINATOR-V2-CONFIRM"
