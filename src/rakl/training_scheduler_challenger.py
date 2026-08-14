"""CHALLENGER training allocator: per-slot marginal-gain water-filling.

This module is a versioned CHALLENGER to :mod:`rakl.training_scheduler`, which
remains the production mechanic byte-untouched.  It exists because the Paper IV
failure attribution located both v1 defects in the production allocator:

1. ``_target_coordinate`` selects the argmin mastery LEVEL, while the paper's
   thesis concerns the mastery DERIVATIVE — level and marginal gain
   anti-correlate whenever harder coordinates learn slower;
2. every non-repetition slot is filled from one target coordinate for a whole
   batch, so within-batch saturation is ignored.

The challenger replaces both at once: each slot is allocated to the
(candidate, coordinate) pair with the highest believed marginal gain
``gain × (1 − believed_mastery)``, and the believed state saturates as slots
are spent, so concentration dies out mechanically.  Guard rails are demoted
from budget-consuming targets to constraints: the snapshot's principle
repetition floor and the non-compensatory safety gates are preserved, but
there is no principle-until-threshold target and no whole-batch retention
repair.

Authority boundary: selecting a batch is not efficacy.  This challenger holds
no production authority; ``STATIC_STRUCTURAL`` remains the governed default
(:mod:`rakl.training_policy_authority`), and activation requires the external
``ADAPTIVE_RESIDUAL_SUPPORTED`` path.  Development evidence for the mechanic
lives in ``research/paper4_marginal_gain_challenger_v1/`` and grants no
scientific authority.
"""

from __future__ import annotations

from math import ceil
from typing import Dict, List, Tuple

from .training_projection import (
    MasteryCoordinate,
    ProjectionVerdict,
    TrainingAllocationCandidate,
    TrainingProjectionSnapshot,
    assess_training_projection,
)
from .training_scheduler import (
    AdaptiveAllocationDecision,
    AllocationVerdict,
    _candidate_gain,
    _canonical_mastery,
    _rank_for_coordinate,
    _safe_candidate,
)

#: The challenger never mutates or replaces the production scheduler.
PRODUCTION_SCHEDULER_UNTOUCHED = "rakl.training_scheduler.choose_adaptive_training_batch"


def _worst_mastery(snapshot: TrainingProjectionSnapshot) -> Dict[MasteryCoordinate, float]:
    mastery = _canonical_mastery(snapshot)
    return {
        coordinate: min(values[coordinate] for values in mastery.values())
        for coordinate in MasteryCoordinate
    }


def choose_marginal_gain_training_batch(
    snapshot: TrainingProjectionSnapshot,
    *,
    batch_size: int,
    max_forgetting_risk: float = 0.10,
    max_negative_transfer_risk: float = 0.10,
    minimum_gain: float = 0.0,
) -> AdaptiveAllocationDecision:
    """Select one fail-closed marginal-gain batch (challenger semantics).

    Fail-closed behaviour mirrors the production scheduler exactly: an
    unassessable or invalid projection, an unsatisfiable repetition floor, no
    safe candidate, or an exhausted candidate pool each return
    ``CANNOT_CHECK``/``INVALID`` rather than a best bad choice.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for name, value in (
        ("max_forgetting_risk", max_forgetting_risk),
        ("max_negative_transfer_risk", max_negative_transfer_risk),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0,1]")
    if minimum_gain < 0:
        raise ValueError("minimum_gain must be non-negative")

    assessment = assess_training_projection(snapshot)
    if assessment.verdict is ProjectionVerdict.INVALID:
        return AdaptiveAllocationDecision(
            AllocationVerdict.INVALID, snapshot.snapshot_hash, None, (), (),
            assessment.reasons,
        )
    if assessment.verdict is not ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION:
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, (), (),
            assessment.reasons,
        )

    safe = tuple(
        candidate
        for candidate in snapshot.candidates
        if _safe_candidate(
            candidate,
            max_forgetting_risk=max_forgetting_risk,
            max_negative_transfer_risk=max_negative_transfer_risk,
        )
    )
    if not safe:
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, (), (),
            ("no_candidate_survives_noncompensatory_safety_gates",),
        )

    # Constraint (not target): the snapshot's principle repetition floor.
    repetition_n = min(batch_size, int(ceil(batch_size * snapshot.repetition_floor)))
    principle_ranked = tuple(
        item for item in _rank_for_coordinate(safe, MasteryCoordinate.PRINCIPLE)
        if _candidate_gain(item, MasteryCoordinate.PRINCIPLE) > minimum_gain
    )
    repetition: List[TrainingAllocationCandidate] = list(principle_ranked[:repetition_n])
    if len(repetition) < repetition_n:
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None, (),
            tuple(item.candidate_id for item in repetition),
            ("repetition_floor_cannot_be_satisfied_by_safe_candidates",),
        )

    believed = _worst_mastery(snapshot)
    selected: List[TrainingAllocationCandidate] = list(repetition)
    selected_ids = {item.candidate_id for item in selected}
    slot_coordinates: List[str] = ["PRINCIPLE_FLOOR"] * len(repetition)
    for item in repetition:
        gain = _candidate_gain(item, MasteryCoordinate.PRINCIPLE)
        headroom = 1.0 - believed[MasteryCoordinate.PRINCIPLE]
        believed[MasteryCoordinate.PRINCIPLE] = min(
            0.999, believed[MasteryCoordinate.PRINCIPLE] + gain * headroom
        )

    while len(selected) < batch_size:
        best: Tuple[float, float, float, str] | None = None
        best_pick: Tuple[TrainingAllocationCandidate, MasteryCoordinate] | None = None
        for candidate in safe:
            if candidate.candidate_id in selected_ids:
                continue
            for coordinate in MasteryCoordinate:
                gain = _candidate_gain(candidate, coordinate)
                if gain <= minimum_gain:
                    continue
                score = gain * (1.0 - believed[coordinate])
                key = (
                    -score,
                    candidate.utility.forgetting_risk,
                    candidate.utility.estimated_total_cost,
                    candidate.candidate_id,
                )
                if best is None or key < best:
                    best = key
                    best_pick = (candidate, coordinate)
        if best_pick is None:
            return AdaptiveAllocationDecision(
                AllocationVerdict.CANNOT_CHECK, snapshot.snapshot_hash, None,
                tuple(item.candidate_id for item in selected),
                tuple(item.candidate_id for item in repetition),
                ("insufficient_safe_candidates_with_registered_gain_for_requested_batch",),
            )
        candidate, coordinate = best_pick
        selected.append(candidate)
        selected_ids.add(candidate.candidate_id)
        slot_coordinates.append(coordinate.value)
        gain = _candidate_gain(candidate, coordinate)
        believed[coordinate] = min(0.999, believed[coordinate] + gain * (1.0 - believed[coordinate]))

    return AdaptiveAllocationDecision(
        AllocationVerdict.ALLOCATE,
        snapshot.snapshot_hash,
        None,
        tuple(item.candidate_id for item in selected),
        tuple(item.candidate_id for item in repetition),
        (
            "challenger_marginal_gain_per_slot_water_filling",
            "guard_rails_demoted_to_constraints_repetition_floor_and_safety_gates_only",
            f"production_scheduler_untouched:{PRODUCTION_SCHEDULER_UNTOUCHED}",
            "slot_coordinates:" + ",".join(slot_coordinates),
            "forgetting_and_negative_transfer_hard_gates_passed",
            "principle_repetition_floor_preserved",
        ),
    )
