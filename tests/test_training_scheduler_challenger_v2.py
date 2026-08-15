from __future__ import annotations

from rakl.training_projection import MasteryCoordinate, StructuralMasteryEstimate, TrainingAllocationCandidate, TrainingProjectionSnapshot, TrainingUtilityVector, _snapshot_hash
from rakl.training_scheduler import AllocationVerdict
from rakl.training_scheduler_challenger import choose_marginal_gain_training_batch
from rakl.training_scheduler_challenger_v2 import _apply_expected_candidate_gain, choose_structure_conditioned_training_batch


def _estimate(structure_id: str, composition: float) -> StructuralMasteryEstimate:
    values = {MasteryCoordinate.PRINCIPLE: 0.95, MasteryCoordinate.COMPOSITION: composition, MasteryCoordinate.BOUNDARY: 0.95, MasteryCoordinate.REPRESENTATION: 0.95, MasteryCoordinate.TRANSFER: 0.95, MasteryCoordinate.RETENTION: 0.95}
    return StructuralMasteryEstimate(structure_id=structure_id, model_checkpoint_hash="checkpoint", probe_family_hash="probe", coordinate_values=tuple((c, values[c]) for c in MasteryCoordinate), measured_case_ids=(f"{structure_id}-case",), frozen_before_allocation=True)


def _candidate(candidate_id: str, structure_id: str, composition_gain: float) -> TrainingAllocationCandidate:
    return TrainingAllocationCandidate(candidate_id=candidate_id, raw_item_id=f"raw-{candidate_id}", derived_view_id=f"view-{candidate_id}", structure_id=structure_id, model_checkpoint_hash="checkpoint", utility=TrainingUtilityVector(expected_principle_gain=0.001, expected_composition_gain=composition_gain, expected_boundary_gain=0.001, expected_representation_gain=0.001, expected_transfer_gain=0.001, expected_retention_gain=0.001, forgetting_risk=0.0, negative_transfer_risk=0.0, estimated_total_cost=1.0), data_provenance_ids=(f"prov-{candidate_id}",))


def _snapshot() -> TrainingProjectionSnapshot:
    estimates = (_estimate("S1", 0.10), _estimate("S2", 0.90)); candidates = (_candidate("C1", "S1", 0.20), _candidate("C2", "S2", 0.30))
    kwargs = dict(projection_id="known-world-structure-conditioning", model_checkpoint_hash="checkpoint", structural_catalog_hash="catalog", probe_family_hash="probe", mastery_estimates=estimates, candidates=candidates, repetition_floor=0.0, frozen_before_outcome_access=True)
    return TrainingProjectionSnapshot(**kwargs, snapshot_hash=_snapshot_hash(kwargs["projection_id"], kwargs["model_checkpoint_hash"], kwargs["structural_catalog_hash"], kwargs["probe_family_hash"], kwargs["mastery_estimates"], kwargs["candidates"], kwargs["repetition_floor"], kwargs["frozen_before_outcome_access"]))


def test_known_world_exposes_global_structure_misattribution() -> None:
    snapshot = _snapshot(); v1 = choose_marginal_gain_training_batch(snapshot, batch_size=1); v2 = choose_structure_conditioned_training_batch(snapshot, batch_size=1)
    assert v1.verdict is AllocationVerdict.ALLOCATE and v2.verdict is AllocationVerdict.ALLOCATE
    assert v1.selected_candidate_ids == ("C2",)
    assert v2.selected_candidate_ids == ("C1",)
    assert "mastery_state_preserved_at_structure_id_x_coordinate_resolution" in v2.reasons


def test_expected_gain_updates_only_bound_structure_and_full_vector() -> None:
    snapshot = _snapshot(); believed = {e.structure_id: {c: float(v) for c, v in e.coordinate_values if v is not None} for e in snapshot.mastery_estimates}; before_s2 = dict(believed["S2"])
    _apply_expected_candidate_gain(snapshot.candidates[0], believed)
    assert believed["S1"][MasteryCoordinate.COMPOSITION] > 0.10
    assert believed["S1"][MasteryCoordinate.PRINCIPLE] > 0.95
    assert believed["S2"] == before_s2


def test_v2_never_claims_authority_or_efficacy() -> None:
    decision = choose_structure_conditioned_training_batch(_snapshot(), batch_size=1)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert decision.grants_scientific_authority is False
    assert decision.grants_structural_transfer_authority is False
    assert decision.claims_scheduler_efficacy is False
