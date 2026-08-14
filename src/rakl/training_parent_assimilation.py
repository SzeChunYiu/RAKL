from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import ceil, isfinite
from typing import Mapping, Tuple

from .training_projection import (
    MasteryCoordinate,
    ProjectionVerdict,
    TrainingAllocationCandidate,
    TrainingProjectionSnapshot,
    assess_training_projection,
)
from .training_scheduler import AdaptiveAllocationDecision, AllocationVerdict


@dataclass(frozen=True)
class ParentLearnerValueSignal:
    candidate_id: str
    model_checkpoint_hash: str
    probe_family_hash: str
    source_artifact_hash: str
    learner_value: float
    frozen_before_selection: bool | None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("parent signal requires candidate_id")
        if not self.model_checkpoint_hash.strip() or not self.probe_family_hash.strip():
            raise ValueError("parent signal requires checkpoint/probe binding")
        if len(self.source_artifact_hash) != 64 or any(
            char not in "0123456789abcdef" for char in self.source_artifact_hash
        ):
            raise ValueError("parent signal source_artifact_hash must be sha256 hex")
        if not isfinite(self.learner_value) or not 0.0 <= self.learner_value <= 1.0:
            raise ValueError("parent signal learner_value must be finite in [0,1]")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_training_policy_authority(self) -> bool:
        return False


_GAIN_ATTR: Mapping[MasteryCoordinate, str] = {
    MasteryCoordinate.PRINCIPLE: "expected_principle_gain",
    MasteryCoordinate.COMPOSITION: "expected_composition_gain",
    MasteryCoordinate.BOUNDARY: "expected_boundary_gain",
    MasteryCoordinate.REPRESENTATION: "expected_representation_gain",
    MasteryCoordinate.TRANSFER: "expected_transfer_gain",
    MasteryCoordinate.RETENTION: "expected_retention_gain",
}


def _gain(candidate: TrainingAllocationCandidate, coordinate: MasteryCoordinate) -> float:
    return float(getattr(candidate.utility, _GAIN_ATTR[coordinate]))


def _safe(
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


def _target(
    snapshot: TrainingProjectionSnapshot,
    *,
    principle_mastery_threshold: float,
    retention_floor: float,
) -> MasteryCoordinate:
    values_by_structure = {
        estimate.structure_id: {
            coordinate: float(value)
            for coordinate, value in estimate.coordinate_values
            if value is not None
        }
        for estimate in snapshot.mastery_estimates
    }
    worst = {
        coordinate: min(values[coordinate] for values in values_by_structure.values())
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


def _signal_map(
    snapshot: TrainingProjectionSnapshot,
    signals: Tuple[ParentLearnerValueSignal, ...],
) -> tuple[dict[str, ParentLearnerValueSignal] | None, AllocationVerdict, Tuple[str, ...]]:
    by_id: dict[str, ParentLearnerValueSignal] = {}
    for signal in signals:
        if signal.candidate_id in by_id:
            return None, AllocationVerdict.INVALID, ("duplicate_parent_signal_candidate_id",)
        by_id[signal.candidate_id] = signal
    candidate_ids = {candidate.candidate_id for candidate in snapshot.candidates}
    if set(by_id) != candidate_ids:
        return None, AllocationVerdict.CANNOT_CHECK, ("parent_signal_candidate_set_not_exact",)
    for signal in by_id.values():
        if signal.model_checkpoint_hash != snapshot.model_checkpoint_hash:
            return None, AllocationVerdict.CANNOT_CHECK, (
                f"parent_signal_checkpoint_mismatch:{signal.candidate_id}",
            )
        if signal.probe_family_hash != snapshot.probe_family_hash:
            return None, AllocationVerdict.CANNOT_CHECK, (
                f"parent_signal_probe_family_mismatch:{signal.candidate_id}",
            )
        if signal.frozen_before_selection is not True:
            return None, AllocationVerdict.INVALID, (
                f"parent_signal_not_frozen_before_selection:{signal.candidate_id}",
            )
    return by_id, AllocationVerdict.ALLOCATE, ()


def choose_parent_assimilated_training_batch(
    snapshot: TrainingProjectionSnapshot,
    parent_signals: Tuple[ParentLearnerValueSignal, ...],
    *,
    batch_size: int,
    principle_mastery_threshold: float = 0.90,
    retention_floor: float = 0.80,
    max_forgetting_risk: float = 0.10,
    max_negative_transfer_risk: float = 0.10,
    minimum_gain: float = 0.0,
) -> AdaptiveAllocationDecision:
    """Assimilate a stronger learner-value signal inside ORION hard constraints.

    Parent values rank candidates only *after* the existing vector mastery state
    chooses which structural coordinate needs budget and after noncompensatory
    safety gates are applied. The signal cannot redefine mastery, authorize
    itself, supply post-hoc scores, or activate adaptive training policy.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    assessment = assess_training_projection(snapshot)
    if assessment.verdict is ProjectionVerdict.INVALID:
        return AdaptiveAllocationDecision(
            AllocationVerdict.INVALID, snapshot.snapshot_hash, None, (), (), assessment.reasons
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

    signal_map, signal_verdict, signal_reasons = _signal_map(snapshot, parent_signals)
    if signal_map is None:
        return AdaptiveAllocationDecision(
            signal_verdict, snapshot.snapshot_hash, None, (), (), signal_reasons
        )

    safe = tuple(
        candidate
        for candidate in snapshot.candidates
        if _safe(
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

    coordinate = _target(
        snapshot,
        principle_mastery_threshold=principle_mastery_threshold,
        retention_floor=retention_floor,
    )

    def target_key(candidate: TrainingAllocationCandidate):
        signal = signal_map[candidate.candidate_id]
        return (
            -signal.learner_value,
            -_gain(candidate, coordinate),
            candidate.utility.forgetting_risk,
            candidate.utility.negative_transfer_risk,
            candidate.utility.estimated_total_cost,
            candidate.candidate_id,
        )

    target_ranked = tuple(
        candidate
        for candidate in sorted(safe, key=target_key)
        if _gain(candidate, coordinate) > minimum_gain
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

    def principle_key(candidate: TrainingAllocationCandidate):
        signal = signal_map[candidate.candidate_id]
        return (
            -_gain(candidate, MasteryCoordinate.PRINCIPLE),
            -signal.learner_value,
            candidate.utility.forgetting_risk,
            candidate.utility.negative_transfer_risk,
            candidate.utility.estimated_total_cost,
            candidate.candidate_id,
        )

    principle_ranked = tuple(
        candidate
        for candidate in sorted(safe, key=principle_key)
        if _gain(candidate, MasteryCoordinate.PRINCIPLE) > minimum_gain
    )
    if repetition_n > len(principle_ranked):
        return AdaptiveAllocationDecision(
            AllocationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            coordinate,
            (),
            tuple(item.candidate_id for item in principle_ranked),
            ("repetition_floor_cannot_be_satisfied_by_safe_candidates",),
        )

    repetition = list(principle_ranked[:repetition_n])
    selected = list(repetition)
    selected_ids = {item.candidate_id for item in selected}
    for candidate in target_ranked:
        if len(selected) >= batch_size:
            break
        if candidate.candidate_id in selected_ids:
            continue
        selected.append(candidate)
        selected_ids.add(candidate.candidate_id)

    if coordinate is MasteryCoordinate.PRINCIPLE:
        for candidate in principle_ranked:
            if len(selected) >= batch_size:
                break
            if candidate.candidate_id not in selected_ids:
                selected.append(candidate)
                selected_ids.add(candidate.candidate_id)

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
            f"vector_mastery_target_preserved:{coordinate.value}",
            "parent_learner_value_used_only_with_exact_candidate_checkpoint_probe_binding",
            "forgetting_and_negative_transfer_hard_gates_passed",
            "principle_repetition_floor_preserved",
            "adaptive_policy_authority_not_granted_by_parent_signal",
        ),
    )
