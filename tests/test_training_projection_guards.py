from dataclasses import replace

from rakl.structural_types import BoundaryCondition, StructuralObject, StructuralRelation, StructuralRole
from rakl.training_projection import (
    MasteryCoordinate,
    ProjectionVerdict,
    StructuralMasteryEstimate,
    TrainingAllocationCandidate,
    TrainingUtilityVector,
    assess_training_projection,
    build_training_projection,
    structural_catalog_digest,
)


def _snapshot():
    structure = StructuralObject(
        structure_id="s1",
        domain="synthetic",
        qoi="q",
        context_id="ctx",
        roles=(StructuralRole("x", "input"), StructuralRole("y", "output")),
        relations=(StructuralRelation("x", "maps_to", "y"),),
        invariants=frozenset({"i"}),
        boundaries=(BoundaryCondition("regime", "base"),),
        evidence_ids=("generator",),
    )
    structures = (structure,)
    mastery = StructuralMasteryEstimate(
        structure_id="s1",
        model_checkpoint_hash="model-a",
        probe_family_hash="probe-a",
        coordinate_values=tuple((coordinate, 0.5) for coordinate in MasteryCoordinate),
        measured_case_ids=("m1",),
        frozen_before_allocation=True,
    )
    utility = TrainingUtilityVector(
        expected_principle_gain=0.5,
        expected_composition_gain=0.5,
        expected_boundary_gain=0.5,
        expected_representation_gain=0.5,
        expected_transfer_gain=0.5,
        expected_retention_gain=0.5,
        forgetting_risk=0.1,
        negative_transfer_risk=0.1,
        estimated_total_cost=1.0,
    )
    candidate = TrainingAllocationCandidate(
        candidate_id="c1",
        raw_item_id="raw1",
        derived_view_id="view1",
        structure_id="s1",
        model_checkpoint_hash="model-a",
        utility=utility,
        data_provenance_ids=("raw-source",),
    )
    return build_training_projection(
        projection_id="p1",
        model_checkpoint_hash="model-a",
        structural_catalog_hash=structural_catalog_digest(structures),
        probe_family_hash="probe-a",
        structural_objects=structures,
        mastery_estimates=(mastery,),
        candidates=(candidate,),
        repetition_floor=0.1,
        frozen_before_outcome_access=True,
    )


def test_dataclass_replace_cannot_preserve_old_projection_identity():
    snapshot = _snapshot()
    mutated = replace(snapshot, repetition_floor=0.9)
    assessment = assess_training_projection(mutated)
    assert assessment.verdict is ProjectionVerdict.INVALID
    assert "training_projection_content_hash_mismatch" in assessment.reasons


def test_freeze_chronology_is_part_of_projection_identity():
    snapshot = _snapshot()
    mutated = replace(snapshot, frozen_before_outcome_access=False)
    assessment = assess_training_projection(mutated)
    assert assessment.verdict is ProjectionVerdict.INVALID
    assert "training_projection_content_hash_mismatch" in assessment.reasons
