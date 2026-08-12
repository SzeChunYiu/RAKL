from __future__ import annotations

from collections import defaultdict

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import (
    FAMILIES,
    ITEM_TYPES,
    components,
    generate,
    mechanism_predict,
    mutate_hidden_metadata,
    verify,
)


# Instrument-correctness seed only. This is not the registered development seed
# 2026081211 and no aggregate development statistic is computed in this test.
INSTRUMENT_TEST_SEED = 1729


def _one_per_cell():
    tasks = generate(INSTRUMENT_TEST_SEED, 1)
    picked = {}
    for task in tasks:
        picked.setdefault((task.family, task.item_type), task)
    return picked


def test_all_six_registered_families_and_strata_are_constructible() -> None:
    picked = _one_per_cell()
    assert set(family for family, _ in picked) == set(FAMILIES)
    for family in FAMILIES:
        assert {item_type for fam, item_type in picked if fam == family} == set(ITEM_TYPES)


def test_hidden_perturbation_metadata_cannot_change_gold() -> None:
    for task in generate(INSTRUMENT_TEST_SEED, 1):
        assert verify(mutate_hidden_metadata(task)) == verify(task)


def test_valid_and_unknown_controls_have_registered_gold_semantics() -> None:
    picked = _one_per_cell()
    for family in FAMILIES:
        assert verify(picked[(family, "VALID_DISTANT_TRANSFER")]) is Decision.ACCEPT
        assert verify(picked[(family, "VALID_NEAR_CONTROL")]) is Decision.ACCEPT
        assert verify(picked[(family, "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK")]) is Decision.CANNOT_CHECK


def test_hostile_invalid_strata_are_rejected_by_full_contract() -> None:
    picked = _one_per_cell()
    for family in FAMILIES:
        assert verify(picked[(family, "SEMANTIC_NEAR_MISS_INVALID_TRANSFER")]) is Decision.REJECT
        assert verify(picked[(family, "INVALID_DISTANT_CONTROL")]) is Decision.REJECT
        assert verify(picked[(family, "DIRECTION_REVERSED_INVALID")]) is Decision.REJECT
        assert verify(picked[(family, "BOUNDARY_QOI_MISMATCH")]) is Decision.REJECT


def test_mechanism_projection_is_strictly_weaker_in_every_family() -> None:
    tasks = generate(INSTRUMENT_TEST_SEED, 1)
    by_family = defaultdict(list)
    for task in tasks:
        by_family[task.family].append(task)
    for family in FAMILIES:
        assert any(mechanism_predict(task) != verify(task) for task in by_family[family]), family


def test_full_component_merge_is_noncompensatory() -> None:
    for task in generate(INSTRUMENT_TEST_SEED, 1):
        assessment = components(task)
        statuses = (
            assessment.qoi,
            assessment.boundary,
            assessment.direction,
            assessment.relation,
            assessment.precondition,
            assessment.effect,
        )
        if Decision.REJECT in statuses:
            assert assessment.full is Decision.REJECT
        elif Decision.CANNOT_CHECK in statuses:
            assert assessment.full is Decision.CANNOT_CHECK
        else:
            assert assessment.full is Decision.ACCEPT
