from __future__ import annotations

from rakl.paper3_witness_decoupling import (
    decoupling_from_benchmark_cases,
    decoupling_rate,
    item_is_decoupled,
    witness_and,
)


def test_witness_and_and_decoupling_flags() -> None:
    coupled = {
        "invariant_preserved": True,
        "boundary_matched": True,
        "qoi_matched": True,
        "directional_mapping_complete": True,
        "transfer_valid": True,
    }
    assert witness_and(coupled) is True
    assert item_is_decoupled(coupled) is False

    decoupled = dict(coupled)
    decoupled["transfer_valid"] = False
    assert item_is_decoupled(decoupled) is True

    incomplete = dict(coupled)
    incomplete["qoi_matched"] = None
    assert witness_and(incomplete) is None
    assert item_is_decoupled(incomplete) is None


def test_decoupling_rate_definitionally_determined() -> None:
    items = [
        {
            "invariant_preserved": True,
            "boundary_matched": True,
            "qoi_matched": True,
            "directional_mapping_complete": True,
            "transfer_valid": True,
        },
        {
            "invariant_preserved": False,
            "boundary_matched": True,
            "qoi_matched": True,
            "directional_mapping_complete": True,
            "transfer_valid": False,
        },
    ]
    receipt = decoupling_rate(items)
    assert receipt["decoupling_rate"] == 0.0
    assert receipt["status"] == "DEFINITIONALLY_DETERMINED"
    assert receipt["witnessed_structure_authority"] == "NOT_INFORMATIVE"


def test_decoupling_rate_informative_when_any_mismatch() -> None:
    items = [
        {
            "invariant_preserved": True,
            "boundary_matched": True,
            "qoi_matched": True,
            "directional_mapping_complete": True,
            "transfer_valid": True,
        },
        {
            "invariant_preserved": True,
            "boundary_matched": True,
            "qoi_matched": True,
            "directional_mapping_complete": True,
            "transfer_valid": False,
        },
    ]
    receipt = decoupling_rate(items)
    assert receipt["decoupling_rate"] == 0.5
    assert receipt["status"] == "DECOUPLED_SUBSET_PRESENT"
    assert receipt["witnessed_structure_authority"] == "INFORMATIVE_CANDIDATE"


def test_decoupling_from_benchmark_cases() -> None:
    cases = [
        {
            "case_id": "a",
            "invariant_preserved": True,
            "boundary_matched": True,
            "qoi_matched": True,
            "directional_mapping_complete": True,
            "transfer_valid": True,
        }
    ]
    receipt = decoupling_from_benchmark_cases(cases)
    assert receipt["assessed_item_count"] == 1
    assert receipt["decoupling_rate"] == 0.0
