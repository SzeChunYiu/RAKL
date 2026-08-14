from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.mechanic_research_packet import MechanicResearchCoverageVerdict
from rakl.mechanic_research_packet_io import (
    load_packet_set,
    packet_set_from_dict,
    validate_packet_set,
)


PACKET_PATH = Path("research/mechanic_research_packets_v1/PAPER5_PAPER6_SUCCESSORS.json")

EXPECTED_VARIANTS = {
    "vtg_lean_geometry_v1",
    "field_cheapest_useful_selector_v1",
    "diagnosis_discriminating_intervention_v2",
    "navigation_lazy_parallel_repair_v2",
    "path_equivalence_local_certification_v2",
    "operational_map_belief_v1",
    "path_cost_algebra_v1",
    "trajectory_to_certificate_assembly_v1",
    "navigation_quotient_validation_v1",
    "verified_solver_compilation_v1",
    "verification_scheduler_v1",
    "capstone_integrated_solver_v1",
}


def _document() -> dict:
    return json.loads(PACKET_PATH.read_text(encoding="utf-8"))


def test_paper5_paper6_successor_universe_has_complete_shadow_coverage() -> None:
    packet_set = load_packet_set(PACKET_PATH)
    assert set(packet_set.required_variant_ids) == EXPECTED_VARIANTS
    assert {packet.variant_id for packet in packet_set.packets} == EXPECTED_VARIANTS
    assert validate_packet_set(packet_set) == ()
    coverage = packet_set.coverage_report()
    assert coverage.verdict is MechanicResearchCoverageVerdict.COMPLETE_SHADOW_COVERAGE
    assert coverage.complete is True
    assert packet_set.grants_scientific_authority is False
    assert packet_set.grants_promotion_authority is False


def test_packet_set_is_fresh_successors_not_retroactive_historical_verdicts() -> None:
    packet_set = load_packet_set(PACKET_PATH)
    historical_variants = {
        "fieldability_given_field",
        "field_construction",
        "field_construction_successor",
        "mechanic_diagnosis",
        "diagnosis_active_successor",
        "navigation_dynamics",
        "navigation_dynamics_successor",
        "navigation_dynamics_parallel",
        "path_equivalence_quotient",
        "tcsq_sq3_successor",
    }
    assert not (historical_variants & set(packet_set.required_variant_ids))
    assert all(packet.mechanism_gate_state.value == "UNASSESSED" for packet in packet_set.packets)
    assert all(packet.applicability_gate_state.value == "UNASSESSED" for packet in packet_set.packets)


def test_packet_set_explicitly_cannot_enforce_or_grant_promotion() -> None:
    document = _document()
    assert document["grants_scientific_authority"] is False
    assert document["grants_promotion_authority"] is False
    assert document["enforces_promotion_gate"] is False

    for forbidden in (
        "grants_scientific_authority",
        "grants_promotion_authority",
        "enforces_promotion_gate",
    ):
        tampered = dict(document)
        tampered[forbidden] = True
        with pytest.raises(ValueError, match=forbidden):
            packet_set_from_dict(tampered)


def test_bundle_tamper_is_detected_by_packet_content_hash() -> None:
    document = _document()
    document["packets"][0]["novelty_residual"] = "post-outcome rewritten residual"
    packet_set = packet_set_from_dict(document)
    reasons = validate_packet_set(packet_set)
    assert any("packet_content_sha256_mismatch" in reason for reason in reasons)


def test_missing_required_variant_fails_shadow_coverage() -> None:
    document = _document()
    document["packets"] = document["packets"][:-1]
    packet_set = packet_set_from_dict(document)
    reasons = validate_packet_set(packet_set)
    assert any("missing_packet:capstone_integrated_solver_v1" in reason for reason in reasons)


def test_duplicate_packet_id_fails_closed_even_if_variant_universe_is_complete() -> None:
    document = _document()
    document["packets"][1]["packet_id"] = document["packets"][0]["packet_id"]
    # Re-hashing is intentionally not performed: both duplicate identity and
    # content tampering are defects. At minimum the duplicate-ID guard must fire.
    packet_set = packet_set_from_dict(document)
    reasons = validate_packet_set(packet_set)
    assert "duplicate_packet_id" in reasons
