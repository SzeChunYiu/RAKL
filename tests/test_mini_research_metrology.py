from __future__ import annotations

import json

from rakl.mini_research_metrology import receipt_json, run_mini_research_metrology


def test_pendulum_metrology_separates_expansion_density_flat_and_replication():
    receipt = run_mini_research_metrology()
    points = {point.round_id: point for point in receipt.points}
    transitions = {(item.from_round, item.to_round): item for item in receipt.transitions}

    assert points["R0"].atom_count == 8
    assert points["R0"].occupied_volume_cells == 7
    assert points["R0"].atom_cell_density == 1.142857
    assert points["R0"].evidence_binding_count == 21

    assert points["R1"].atom_count == 9
    assert points["R1"].occupied_volume_cells == 7
    assert points["R1"].atom_cell_density == 1.285714
    assert points["R1"].evidence_binding_count == 26

    assert points["R3"].atom_count == 9
    assert points["R3"].occupied_volume_cells == 7
    assert points["R3"].evidence_binding_count == 27
    assert points["R3"].distinct_evidence_sources == 8

    assert transitions[("EMPTY", "R0")].growth_class == "EXPANSION"
    assert transitions[("EMPTY", "R0")].volume_delta_cells == 7
    assert transitions[("R0", "R1")].growth_class == "MIXED_DENSIFICATION"
    assert transitions[("R0", "R1")].volume_delta_cells == 0
    assert transitions[("R0", "R1")].atom_delta == 1
    assert transitions[("R0", "R1")].witness_delta == 3
    assert transitions[("R1", "R2")].growth_class == "FLAT"
    assert transitions[("R2", "R3")].growth_class == "EVIDENCE_DENSIFICATION"
    assert transitions[("R2", "R3")].atom_delta == 0
    assert transitions[("R2", "R3")].evidence_binding_delta == 1
    assert receipt.proves_scientific_superiority is False


def test_metrology_receipt_is_machine_readable_and_explicitly_non_euclidean():
    data = json.loads(receipt_json())
    assert data["demo_id"] == "PENDULUM_CONTEXT_ATLAS_001_METROLOGY_V1"
    assert "not Euclidean" in data["volume_definition"]
    assert data["proves_scientific_superiority"] is False
