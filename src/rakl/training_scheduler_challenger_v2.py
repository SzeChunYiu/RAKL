"""Research-only structure-conditioned challenger for Paper IV.

This module is a versioned successor to ``training_scheduler_challenger``.
The production scheduler and the v1 challenger remain byte-untouched.

V1 collapses the structure dimension before allocation: its worst-mastery state
uses one minimum per coordinate over all registered structures.  A candidate
bound to structure B can therefore be scored against a low mastery value that
belongs to structure A.  V2 preserves mastery at
``(structure_id, mastery_coordinate)`` resolution and updates only the selected
candidate's bound structure.  This is proposal-only and grants no scientific,
structural-transfer, or training-policy authority.
"""
from __future__ import annotations
from math import ceil
from typing import Dict, List, Mapping, Tuple
from .training_projection import MasteryCoordinate, ProjectionVerdict, TrainingAllocationCandidate, TrainingProjectionSnapshot, assess_training_projection
from .training_scheduler import AdaptiveAllocationDecision, AllocationVerdict, _candidate_gain, _canonical_mastery, _safe_candidate

PARENT_CHALLENGER = "rakl.training_scheduler_challenger.choose_marginal_gain_training_batch"
PRODUCTION_SCHEDULER_UNTOUCHED = "rakl.training_scheduler.choose_adaptive_training_batch"


def _structure_mastery(snapshot: TrainingProjectionSnapshot) -> Dict[str, Dict[MasteryCoordinate, float]]:
    return {sid: dict(values) for sid, values in _canonical_mastery(snapshot).items()}


def _score(candidate: TrainingAllocationCandidate, coordinate: MasteryCoordinate, believed: Mapping[str, Mapping[MasteryCoordinate, float]]) -> float:
    return _candidate_gain(candidate, coordinate) * (1.0 - believed[candidate.structure_id][coordinate])


def _apply_expected_candidate_gain(candidate: TrainingAllocationCandidate, believed: Dict[str, Dict[MasteryCoordinate, float]]) -> None:
    structure = believed[candidate.structure_id]
    for coordinate in MasteryCoordinate:
        gain = _candidate_gain(candidate, coordinate)
        structure[coordinate] = min(0.999, structure[coordinate] + gain * (1.0 - structure[coordinate]))


def choose_structure_conditioned_training_batch(snapshot: TrainingProjectionSnapshot, *, batch_size: int, max_forgetting_risk: float = 0.10, max_negative_transfer_risk: float = 0.10, minimum_gain: float = 0.0) -> AdaptiveAllocationDecision:
    if batch_size <= 0: raise ValueError("batch_size must be positive")
    for name, value in (("max_forgetting_risk", max_forgetting_risk), ("max_negative_transfer_risk", max_negative_transfer_risk)):
        if not 0.0 <= value <= 1.0: raise ValueError(f"{name} must be in [0,1]")
    if minimum_gain < 0: raise ValueError("minimum_gain must be non-negative")
    assessment = assess_training_projection(snapshot)
    if assessment.verdict is ProjectionVerdict.INVALID:
        return AdaptiveAllocationDecision(AllocationVerdict.INVALID, snapshot.snapshot_hash, None, (), (), assessment.reasons)
    if assessment.verdict is not ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION:
        return AdaptiveAllocationDecision(AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, (), (), assessment.reasons)
    safe = tuple(c for c in snapshot.candidates if _safe_candidate(c, max_forgetting_risk=max_forgetting_risk, max_negative_transfer_risk=max_negative_transfer_risk))
    if not safe:
        return AdaptiveAllocationDecision(AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, (), (), ("no_candidate_survives_noncompensatory_safety_gates",))
    believed = _structure_mastery(snapshot)
    repetition_n = min(batch_size, int(ceil(batch_size * snapshot.repetition_floor)))
    principle_ranked = tuple(sorted((c for c in safe if _candidate_gain(c, MasteryCoordinate.PRINCIPLE) > minimum_gain), key=lambda c: (-_score(c, MasteryCoordinate.PRINCIPLE, believed), c.utility.forgetting_risk, c.utility.negative_transfer_risk, c.utility.estimated_total_cost, c.candidate_id)))
    repetition: List[TrainingAllocationCandidate] = list(principle_ranked[:repetition_n])
    if len(repetition) < repetition_n:
        return AdaptiveAllocationDecision(AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, (), tuple(x.candidate_id for x in repetition), ("repetition_floor_cannot_be_satisfied_by_safe_candidates",))
    selected: List[TrainingAllocationCandidate] = []; selected_ids: set[str] = set(); slot_coordinates: List[str] = []
    for candidate in repetition:
        selected.append(candidate); selected_ids.add(candidate.candidate_id); slot_coordinates.append(f"{candidate.structure_id}:{MasteryCoordinate.PRINCIPLE.value}:FLOOR"); _apply_expected_candidate_gain(candidate, believed)
    while len(selected) < batch_size:
        best_key: Tuple[float, float, float, float, str, str] | None = None; best_pick: Tuple[TrainingAllocationCandidate, MasteryCoordinate] | None = None
        for candidate in safe:
            if candidate.candidate_id in selected_ids: continue
            for coordinate in MasteryCoordinate:
                gain = _candidate_gain(candidate, coordinate)
                if gain <= minimum_gain: continue
                key = (-_score(candidate, coordinate, believed), candidate.utility.forgetting_risk, candidate.utility.negative_transfer_risk, candidate.utility.estimated_total_cost, candidate.candidate_id, coordinate.value)
                if best_key is None or key < best_key: best_key, best_pick = key, (candidate, coordinate)
        if best_pick is None:
            return AdaptiveAllocationDecision(AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, tuple(x.candidate_id for x in selected), tuple(x.candidate_id for x in repetition), ("insufficient_safe_structure_conditioned_candidates_with_registered_gain_for_requested_batch",))
        candidate, coordinate = best_pick; selected.append(candidate); selected_ids.add(candidate.candidate_id); slot_coordinates.append(f"{candidate.structure_id}:{coordinate.value}"); _apply_expected_candidate_gain(candidate, believed)
    return AdaptiveAllocationDecision(AllocationVerdict.ALLOCATE, snapshot.snapshot_hash, None, tuple(x.candidate_id for x in selected), tuple(x.candidate_id for x in repetition), ("research_challenger_structure_conditioned_vector_water_filling", "mastery_state_preserved_at_structure_id_x_coordinate_resolution", "candidate_effect_updates_only_its_bound_structure_identity", f"parent_challenger_untouched:{PARENT_CHALLENGER}", f"production_scheduler_untouched:{PRODUCTION_SCHEDULER_UNTOUCHED}", "slot_coordinates:" + ",".join(slot_coordinates), "forgetting_and_negative_transfer_hard_gates_passed", "principle_repetition_floor_preserved"))
