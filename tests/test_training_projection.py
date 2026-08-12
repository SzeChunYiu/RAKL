import pytest

from rakl.structural_types import BoundaryCondition, StructuralObject, StructuralRelation, StructuralRole
from rakl.training_projection import (
    MasteryCoordinate,
    ProjectionVerdict,
    StructuralMasteryEstimate,
    TrainingAllocationCandidate,
    TrainingUtilityVector,
    assess_training_projection,
    build_training_projection,
)


def _structure(structure_id="s1"):
    return StructuralObject(
        structure_id=structure_id,
        domain="synthetic",
        qoi="target",
        context_id="ctx",
        roles=(StructuralRole("a", "input"), StructuralRole("b", "output")),
        relations=(StructuralRelation("a", "maps_to", "b"),),
        invariants=frozenset({"mapping_preserved"}),
        boundaries=(BoundaryCondition("regime", "base"),),
        evidence_ids=("generator-receipt",),
    )


def _coords(**overrides):
    values = {
        MasteryCoordinate.PRINCIPLE: 0.9,
        MasteryCoordinate.COMPOSITION: 0.2,
        MasteryCoordinate.BOUNDARY: 0.3,
        MasteryCoordinate.REPRESENTATION: 0.4,
        MasteryCoordinate.TRANSFER: 0.25,
        MasteryCoordinate.RETENTION: 0.8,
    }
    values.update(overrides)
    return tuple((coordinate, values[coordinate]) for coordinate in MasteryCoordinate)


def _mastery(**overrides):
    values = dict(
        structure_id="s1",
        model_checkpoint_hash="model-a",
        probe_family_hash="probe-a",
        coordinate_values=_coords(),
        measured_case_ids=("p1", "p2"),
        frozen_before_allocation=True,
    )
    values.update(overrides)
    return StructuralMasteryEstimate(**values)


def _utility(**overrides):
    values = dict(
        expected_principle_gain=0.1,
        expected_composition_gain=0.8,
        expected_boundary_gain=0.7,
        expected_representation_gain=0.6,
        expected_transfer_gain=0.8,
        expected_retention_gain=0.2,
        forgetting_risk=0.1,
        negative_transfer_risk=0.1,
        estimated_total_cost=2.0,
    )
    values.update(overrides)
    return TrainingUtilityVector(**values)


def _candidate(**overrides):
    values = dict(
        candidate_id="cand-1",
        raw_item_id="raw-1",
        derived_view_id="view-1",
        structure_id="s1",
        model_checkpoint_hash="model-a",
        utility=_utility(),
        data_provenance_ids=("raw-source-1",),
    )
    values.update(overrides)
    return TrainingAllocationCandidate(**values)


def _snapshot(**overrides):
    values = dict(
        projection_id="train-proj-1",
        model_checkpoint_hash="model-a",
        structural_catalog_hash="catalog-a",
        probe_family_hash="probe-a",
        structural_objects=(_structure(),),
        mastery_estimates=(_mastery(),),
        candidates=(_candidate(),),
        repetition_floor=0.1,
        frozen_before_outcome_access=True,
    )
    values.update(overrides)
    return build_training_projection(**values)


def test_principle_mastery_does_not_imply_composition_or_transfer_mastery():
    estimate = _mastery()
    assert estimate.values[MasteryCoordinate.PRINCIPLE] == 0.9
    assert estimate.values[MasteryCoordinate.COMPOSITION] == 0.2
    assert estimate.values[MasteryCoordinate.TRANSFER] == 0.25
    assert not hasattr(estimate, "mastered")


def test_training_projection_and_candidates_never_grant_scientific_authority():
    snapshot = _snapshot()
    assert snapshot.grants_scientific_authority is False
    assert snapshot.claims_adaptive_training_works is False
    assert snapshot.mastery_estimates[0].grants_scientific_authority is False
    assert snapshot.mastery_estimates[0].grants_structural_transfer_authority is False
    assert snapshot.candidates[0].grants_scientific_authority is False
    assert snapshot.candidates[0].is_raw_corpus_replacement is False
    assert snapshot.candidates[0].utility.grants_scientific_authority is False


def test_projection_is_checkpoint_bound_and_becomes_stale_after_weight_update():
    snapshot = _snapshot()
    assert snapshot.is_stale_for_checkpoint("model-a") is False
    assert snapshot.is_stale_for_checkpoint("model-b") is True


def test_checkpoint_mismatch_is_invalid_at_construction():
    with pytest.raises(ValueError, match="checkpoint"):
        _snapshot(mastery_estimates=(_mastery(model_checkpoint_hash="model-b"),))
    with pytest.raises(ValueError, match="checkpoint"):
        _snapshot(candidates=(_candidate(model_checkpoint_hash="model-b"),))


def test_unknown_structure_cannot_enter_mastery_or_training_candidate_view():
    with pytest.raises(ValueError, match="unknown structural object"):
        _snapshot(mastery_estimates=(_mastery(structure_id="unknown"),))
    with pytest.raises(ValueError, match="unknown structural object"):
        _snapshot(candidates=(_candidate(structure_id="unknown"),))


def test_unmeasured_coordinate_is_cannot_check_not_zero_mastery():
    estimate = _mastery(
        coordinate_values=_coords(**{MasteryCoordinate.TRANSFER: None}),
    )
    snapshot = _snapshot(mastery_estimates=(estimate,))
    assessment = assess_training_projection(snapshot)
    assert assessment.verdict is ProjectionVerdict.CANNOT_CHECK
    assert "one_or_more_mastery_coordinates_unmeasured" in assessment.reasons


def test_posthoc_projection_or_mastery_estimate_fails_closed():
    posthoc_projection = _snapshot(frozen_before_outcome_access=False)
    assert assess_training_projection(posthoc_projection).verdict is ProjectionVerdict.INVALID

    posthoc_mastery = _snapshot(mastery_estimates=(_mastery(frozen_before_allocation=False),))
    assert assess_training_projection(posthoc_mastery).verdict is ProjectionVerdict.INVALID

    unknown_freeze = _snapshot(frozen_before_outcome_access=None)
    assert assess_training_projection(unknown_freeze).verdict is ProjectionVerdict.CANNOT_CHECK


def test_confirmatory_target_leak_is_invalid_before_any_allocation():
    snapshot = _snapshot(candidates=(_candidate(confirmatory_target_leak=True),))
    assessment = assess_training_projection(snapshot)
    assert assessment.verdict is ProjectionVerdict.INVALID
    assert "confirmatory_target_leak_in_training_candidate" in assessment.reasons


def test_clean_projection_is_only_ready_for_experimental_allocation():
    snapshot = _snapshot()
    assessment = assess_training_projection(snapshot)
    assert assessment.verdict is ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION
    assert assessment.grants_scientific_authority is False


def test_raw_item_and_derived_view_are_distinct_identities():
    candidate = _candidate()
    assert candidate.raw_item_id != candidate.derived_view_id


def test_duplicate_raw_item_cannot_masquerade_as_two_independent_training_candidates():
    with pytest.raises(ValueError, match="raw item"):
        _snapshot(
            candidates=(
                _candidate(candidate_id="c1", raw_item_id="same", derived_view_id="v1"),
                _candidate(candidate_id="c2", raw_item_id="same", derived_view_id="v2"),
            )
        )
