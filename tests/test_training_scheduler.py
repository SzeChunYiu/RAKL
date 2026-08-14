from dataclasses import replace

from rakl.structural_types import BoundaryCondition, StructuralObject, StructuralRelation, StructuralRole
from rakl.training_projection import (
    MasteryCoordinate,
    StructuralMasteryEstimate,
    TrainingAllocationCandidate,
    TrainingUtilityVector,
    build_training_projection,
    structural_catalog_digest,
)
from rakl.training_scheduler import (
    AllocationVerdict,
    choose_adaptive_training_batch,
)


def _structure():
    return StructuralObject(
        structure_id="reachability",
        domain="synthetic",
        qoi="reachability_validity",
        context_id="p4-phase2",
        roles=(StructuralRole("state", "node"), StructuralRole("edge", "relation")),
        relations=(StructuralRelation("state", "connected_by", "state"),),
        invariants=frozenset({"directed_reachability"}),
        boundaries=(BoundaryCondition("regime", "finite_directed_graph"),),
        evidence_ids=("phase1-v2-7b",),
    )


def _coords(**overrides):
    values = {
        MasteryCoordinate.PRINCIPLE: 0.94,
        MasteryCoordinate.COMPOSITION: 0.62,
        MasteryCoordinate.BOUNDARY: 0.88,
        MasteryCoordinate.REPRESENTATION: 0.70,
        MasteryCoordinate.TRANSFER: 0.50,
        MasteryCoordinate.RETENTION: 0.82,
    }
    values.update(overrides)
    return tuple((coordinate, values[coordinate]) for coordinate in MasteryCoordinate)


def _mastery(**overrides):
    values = dict(
        structure_id="reachability",
        model_checkpoint_hash="qwen25-7b-exp2",
        probe_family_hash="p4-phase2-probes",
        coordinate_values=_coords(),
        measured_case_ids=tuple(f"probe-{i}" for i in range(12)),
        frozen_before_allocation=True,
    )
    values.update(overrides)
    return StructuralMasteryEstimate(**values)


def _utility(*, principle=0.05, composition=0.2, boundary=0.1, representation=0.15,
             transfer=0.4, retention=0.1, forgetting=0.03, negative=0.03, cost=1.0):
    return TrainingUtilityVector(
        expected_principle_gain=principle,
        expected_composition_gain=composition,
        expected_boundary_gain=boundary,
        expected_representation_gain=representation,
        expected_transfer_gain=transfer,
        expected_retention_gain=retention,
        forgetting_risk=forgetting,
        negative_transfer_risk=negative,
        estimated_total_cost=cost,
    )


def _candidate(i, **utility):
    return TrainingAllocationCandidate(
        candidate_id=f"cand-{i}",
        raw_item_id=f"raw-{i}",
        derived_view_id=f"view-{i}",
        structure_id="reachability",
        model_checkpoint_hash="qwen25-7b-exp2",
        utility=_utility(**utility),
        data_provenance_ids=(f"source-{i}",),
    )


def _snapshot(*, mastery=None, candidates=None, repetition_floor=0.25, frozen=True):
    structure = _structure()
    if mastery is None:
        mastery = _mastery()
    if candidates is None:
        candidates = (
            _candidate(1, principle=0.30, transfer=0.10),
            _candidate(2, principle=0.20, transfer=0.80),
            _candidate(3, principle=0.10, transfer=0.70),
            _candidate(4, principle=0.08, transfer=0.60),
            _candidate(5, principle=0.07, transfer=0.50),
            _candidate(6, principle=0.06, transfer=0.40),
        )
    return build_training_projection(
        projection_id="p4-phase2-projection",
        model_checkpoint_hash="qwen25-7b-exp2",
        structural_catalog_hash=structural_catalog_digest((structure,)),
        probe_family_hash="p4-phase2-probes",
        structural_objects=(structure,),
        mastery_estimates=(mastery,),
        candidates=tuple(candidates),
        repetition_floor=repetition_floor,
        frozen_before_outcome_access=frozen,
    )


def test_vector_mastery_targets_transfer_after_principle_mastery():
    decision = choose_adaptive_training_batch(_snapshot(), batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert decision.target_coordinate is MasteryCoordinate.TRANSFER
    assert decision.selected_candidate_ids[0] == "cand-1"  # repetition floor
    assert "cand-2" in decision.selected_candidate_ids  # strongest transfer candidate
    assert decision.grants_scientific_authority is False
    assert decision.claims_scheduler_efficacy is False


def test_principle_below_mastery_threshold_has_priority_over_other_low_coordinates():
    mastery = _mastery(coordinate_values=_coords(**{MasteryCoordinate.PRINCIPLE: 0.70, MasteryCoordinate.TRANSFER: 0.20}))
    decision = choose_adaptive_training_batch(_snapshot(mastery=mastery), batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert decision.target_coordinate is MasteryCoordinate.PRINCIPLE
    assert decision.selected_candidate_ids[:2] == ("cand-1", "cand-2")


def test_retention_hard_floor_preempts_other_unsaturated_coordinates():
    mastery = _mastery(coordinate_values=_coords(**{MasteryCoordinate.RETENTION: 0.60, MasteryCoordinate.TRANSFER: 0.20}))
    candidates = (
        _candidate(1, principle=0.30, retention=0.05, transfer=0.9),
        _candidate(2, principle=0.20, retention=0.80, transfer=0.1),
        _candidate(3, principle=0.10, retention=0.70, transfer=0.2),
        _candidate(4, principle=0.08, retention=0.60, transfer=0.3),
        _candidate(5, principle=0.07, retention=0.50, transfer=0.4),
    )
    decision = choose_adaptive_training_batch(_snapshot(mastery=mastery, candidates=candidates), batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert decision.target_coordinate is MasteryCoordinate.RETENTION
    assert "cand-2" in decision.selected_candidate_ids


def test_forgetting_risk_is_noncompensatory_even_with_high_gain():
    candidates = (
        _candidate(1, principle=0.3, transfer=0.1),
        _candidate(2, transfer=1.0, forgetting=0.50),
        _candidate(3, transfer=0.8),
        _candidate(4, transfer=0.7),
        _candidate(5, transfer=0.6),
    )
    decision = choose_adaptive_training_batch(_snapshot(candidates=candidates), batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert "cand-2" not in decision.selected_candidate_ids


def test_negative_transfer_risk_is_noncompensatory_even_with_high_gain():
    candidates = (
        _candidate(1, principle=0.3, transfer=0.1),
        _candidate(2, transfer=1.0, negative=0.50),
        _candidate(3, transfer=0.8),
        _candidate(4, transfer=0.7),
        _candidate(5, transfer=0.6),
    )
    decision = choose_adaptive_training_batch(_snapshot(candidates=candidates), batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert "cand-2" not in decision.selected_candidate_ids


def test_repetition_floor_is_preserved_not_optimized_away():
    decision = choose_adaptive_training_batch(_snapshot(repetition_floor=0.50), batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert len(decision.repetition_candidate_ids) == 2
    assert decision.repetition_candidate_ids == ("cand-1", "cand-2")


def test_missing_safe_repetition_candidates_fails_closed():
    candidates = (
        _candidate(1, principle=0.0, transfer=0.9),
        _candidate(2, principle=0.0, transfer=0.8),
        _candidate(3, principle=0.0, transfer=0.7),
        _candidate(4, principle=0.0, transfer=0.6),
    )
    decision = choose_adaptive_training_batch(_snapshot(candidates=candidates, repetition_floor=0.25), batch_size=4)
    assert decision.verdict is AllocationVerdict.CANNOT_CHECK
    assert "repetition_floor_cannot_be_satisfied_by_safe_candidates" in decision.reasons


def test_unmeasured_mastery_coordinate_remains_cannot_check():
    mastery = _mastery(coordinate_values=_coords(**{MasteryCoordinate.TRANSFER: None}))
    decision = choose_adaptive_training_batch(_snapshot(mastery=mastery), batch_size=4)
    assert decision.verdict is AllocationVerdict.CANNOT_CHECK
    assert "one_or_more_mastery_coordinates_unmeasured" in decision.reasons


def test_posthoc_projection_is_invalid_not_allocated():
    decision = choose_adaptive_training_batch(_snapshot(frozen=False), batch_size=4)
    assert decision.verdict is AllocationVerdict.INVALID
    assert not decision.selected_candidate_ids


def test_confirmatory_target_leak_is_rejected_by_projection_before_scheduler():
    bad = replace(_candidate(2), confirmatory_target_leak=True)
    candidates = (_candidate(1), bad, _candidate(3), _candidate(4), _candidate(5))
    snapshot = _snapshot(candidates=candidates)
    decision = choose_adaptive_training_batch(snapshot, batch_size=4)
    assert decision.verdict is AllocationVerdict.INVALID
    assert "confirmatory_target_leak_in_training_candidate" in decision.reasons


def test_all_unsafe_candidates_yield_cannot_check_not_best_bad_choice():
    candidates = tuple(_candidate(i, transfer=1.0, forgetting=0.5) for i in range(1, 6))
    decision = choose_adaptive_training_batch(_snapshot(candidates=candidates), batch_size=4)
    assert decision.verdict is AllocationVerdict.CANNOT_CHECK
    assert "no_candidate_survives_noncompensatory_safety_gates" in decision.reasons


def test_scheduler_does_not_expose_scalar_mastery_or_authority_surface():
    decision = choose_adaptive_training_batch(_snapshot(), batch_size=4)
    assert not hasattr(decision, "mastery_score")
    assert not hasattr(decision, "utility_score")
    assert decision.grants_structural_transfer_authority is False
