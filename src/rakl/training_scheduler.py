from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Mapping, Tuple

from .training_projection import (
    MasteryCoordinate,
    ProjectionVerdict,
    TrainingAllocationCandidate,
    TrainingProjectionSnapshot,
    assess_training_projection,
)


class AllocationVerdict(str, Enum):
    ALLOCATE = "ALLOCATE"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class AdaptiveAllocationDecision:
    verdict: AllocationVerdict
    projection_snapshot_hash: str
    target_coordinate: MasteryCoordinate | None
    selected_candidate_ids: Tuple[str, ...]
    repetition_candidate_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_structural_transfer_authority(self) -> bool:
        return False

    @property
    def claims_scheduler_efficacy(self) -> bool:
        return False


_GAIN_ATTR: Mapping[MasteryCoordinate, str] = {
    MasteryCoordinate.PRINCIPLE: "expected_principle_gain",
    MasteryCoordinate.COMPOSITION: "expected_composition_gain",
    MasteryCoordinate.BOUNDARY: "expected_boundary_gain",
    MasteryCoordinate.REPRESENTATION: "expected_representation_gain",
    MasteryCoordinate.TRANSFER: "expected_transfer_gain",
    MasteryCoordinate.RETENTION: "expected_retention_gain",
}


def _candidate_gain(candidate: TrainingAllocationCandidate, coordinate: MasteryCoordinate) -> float:
    return float(getattr(candidate.utility, _GAIN_ATTR[coordinate]))


def _safe_candidate(
    candidate: TrainingAllocationCandidate,
    *,
    max_forgetting_risk: float,
    max_negative_transfer_risk: float,
) -> bool:
    return (
        candidate.utility.forgetting_risk <= max_forgetting_risk
        and candidate.utility.negative_transfer_risk <= max_negative_transfer_risk
        and not candidate.confirmatory_target_leak
    )


def _rank_for_coordinate(
    candidates: Tuple[TrainingAllocationCandidate, ...],
    coordinate: MasteryCoordinate,
) -> Tuple[TrainingAllocationCandidate, ...]:
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                -_candidate_gain(item, coordinate),
                item.utility.forgetting_risk,
                item.utility.negative_transfer_risk,
                item.utility.estimated_total_cost,
                item.candidate_id,
            ),
        )
    )


def _canonical_mastery(snapshot: TrainingProjectionSnapshot) -> Mapping[str, Mapping[MasteryCoordinate, float]]:
    out: dict[str, Mapping[MasteryCoordinate, float]] = {}
    for estimate in snapshot.mastery_estimates:
        values = estimate.values
        # assess_training_projection has already ruled out None.
        out[estimate.structure_id] = {key: float(value) for key, value in values.items() if value is not None}
    return out


def _target_coordinate(
    snapshot: TrainingProjectionSnapshot,
    *,
    principle_mastery_threshold: float,
    retention_floor: float,
) -> MasteryCoordinate:
    mastery = _canonical_mastery(snapshot)
    # The allocator is not permitted to scalarize the six-dimensional state.
    # Aggregate by worst observed structure for each coordinate so one weak
    # structure cannot be hidden by an average over stronger structures.
    worst = {
        coordinate: min(values[coordinate] for values in mastery.values())
        for coordinate in MasteryCoordinate
    }
    if worst[MasteryCoordinate.PRINCIPLE] < principle_mastery_threshold:
        return MasteryCoordinate.PRINCIPLE
    if worst[MasteryCoordinate.RETENTION] < retention_floor:
        return MasteryCoordinate.RETENTION
    eligible = tuple(
        coordinate
        for coordinate in MasteryCoordinate
        if coordinate is not MasteryCoordinate.PRINCIPLE
    )
    return min(eligible, key=lambda coordinate: (worst[coordinate], coordinate.value))


def choose_adaptive_training_batch(
    snapshot: TrainingProjectionSnapshot,
    *,
    batch_size: int,
    principle_mastery_threshold: float = 0.90,
    retention_floor: float = 0.80,
    max_forgetting_risk: float = 0.10,
    max_negative_transfer_risk: float = 0.10,
    minimum_gain: float = 0.0,
) -> AdaptiveAllocationDecision:
    """Select one fail-closed learner-conditioned structural training batch.

    The mechanic is intentionally narrower than an efficacy claim.  It consumes
    an already-frozen :class:`TrainingProjectionSnapshot`, targets one weak
    mastery coordinate at a time, enforces forgetting/negative-transfer as hard
    constraints, and preserves the snapshot's non-zero principle repetition
    floor.  It never changes scientific authority and it cannot validate its own
    utility estimates.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for name, value in (
        ("principle_mastery_threshold", principle_mastery_threshold),
        ("retention_floor", retention_floor),
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
            AllocationVerdict.INVALID,
            snapshot.snapshot_hash,
            None,
            (),
            (),
            assessment.reasons,
        )
    if assessment.verdict is not ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION:
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            None,
            (),
            (),
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
            AllocationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            None,
            (),
            (),
            ("no_candidate_survives_noncompensatory_safety_gates",),
        )

    coordinate = _target_coordinate(
        snapshot,
        principle_mastery_threshold=principle_mastery_threshold,
        retention_floor=retention_floor,
    )
    target_ranked = tuple(
        item for item in _rank_for_coordinate(safe, coordinate)
        if _candidate_gain(item, coordinate) > minimum_gain
    )
    if not target_ranked:
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            coordinate,
            (),
            (),
            (f"no_safe_candidate_with_registered_gain:{coordinate.value}",),
        )

    repetition_n = min(batch_size, int(ceil(batch_size * snapshot.repetition_floor)))
    principle_ranked = tuple(
        item for item in _rank_for_coordinate(safe, MasteryCoordinate.PRINCIPLE)
        if _candidate_gain(item, MasteryCoordinate.PRINCIPLE) > minimum_gain
    )
    repetition: list[TrainingAllocationCandidate] = []
    if repetition_n:
        for item in principle_ranked:
            if len(repetition) >= repetition_n:
                break
            repetition.append(item)
        if len(repetition) < repetition_n:
            return AdaptiveAllocationDecision(
                AllocationVerdict.CANNOT_CHECK,
                snapshot.snapshot_hash,
                coordinate,
                (),
                tuple(item.candidate_id for item in repetition),
                ("repetition_floor_cannot_be_satisfied_by_safe_candidates",),
            )

    selected: list[TrainingAllocationCandidate] = list(repetition)
    selected_ids = {item.candidate_id for item in selected}
    for item in target_ranked:
        if len(selected) >= batch_size:
            break
        if item.candidate_id in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(item.candidate_id)

    # If the target coordinate is PRINCIPLE, use remaining principle-ranked
    # candidates before refusing.  Do not silently substitute another coordinate.
    if coordinate is MasteryCoordinate.PRINCIPLE:
        for item in principle_ranked:
            if len(selected) >= batch_size:
                break
            if item.candidate_id not in selected_ids:
                selected.append(item)
                selected_ids.add(item.candidate_id)

    if len(selected) < batch_size:
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            coordinate,
            tuple(item.candidate_id for item in selected),
            tuple(item.candidate_id for item in repetition),
            ("insufficient_safe_candidates_for_requested_batch",),
        )

    return AdaptiveAllocationDecision(
        AllocationVerdict.ALLOCATE,
        snapshot.snapshot_hash,
        coordinate,
        tuple(item.candidate_id for item in selected),
        tuple(item.candidate_id for item in repetition),
        (
            f"target_lowest_noncompensated_coordinate:{coordinate.value}",
            "forgetting_and_negative_transfer_hard_gates_passed",
            "principle_repetition_floor_preserved",
        ),
    )
