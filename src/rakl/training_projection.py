"""Proposal-only training-time projection for RAKL (#455, #461).

This module adds the *state contract* required to discuss a future weight-updating
RAKL extension without conflating it with either scientific authority or the
currently deployed external-state learning loop.

The separation is structural::

    pi_epi(R_t)              -> what is scientifically licensed?
    pi_search(R_t)           -> what should be inspected next?
    pi_train(R_t, theta_t)   -> what may be useful to train on next?

A training projection is bound to an exact model checkpoint and frozen probe
family.  Its mastery and utility coordinates are computational/experimental
objects only.  They never mint scientific evidence, scientific authority,
structural-transfer authority, or a claim that a scheduler is effective.

No adaptive scheduler is implemented here.  Issue #461 owns the cheap
exposure-curve experiment that must establish a learner-conditioned structural
signal before allocation-policy efficacy can be studied.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from math import isfinite
from typing import Mapping, Sequence, Tuple

from .structural_types import StructuralObject

__all__ = [
    "MasteryCoordinate",
    "ProjectionAssessment",
    "ProjectionVerdict",
    "StructuralMasteryEstimate",
    "TrainingAllocationCandidate",
    "TrainingProjectionSnapshot",
    "TrainingUtilityVector",
    "assess_training_projection",
    "build_training_projection",
    "structural_catalog_digest",
]


class MasteryCoordinate(str, Enum):
    PRINCIPLE = "PRINCIPLE"
    COMPOSITION = "COMPOSITION"
    BOUNDARY = "BOUNDARY"
    REPRESENTATION = "REPRESENTATION"
    TRANSFER = "TRANSFER"
    RETENTION = "RETENTION"


_COORDINATE_ORDER: Tuple[MasteryCoordinate, ...] = tuple(MasteryCoordinate)


class ProjectionVerdict(str, Enum):
    READY_FOR_EXPERIMENTAL_ALLOCATION = "READY_FOR_EXPERIMENTAL_ALLOCATION"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class StructuralMasteryEstimate:
    """Checkpoint- and probe-bound estimate of structural learning state.

    Values are operational probe results in [0, 1], never probabilities of
    scientific truth. ``None`` means the coordinate is unmeasured; it is not
    coerced to zero. The vector is deliberately non-scalar because principle
    acquisition does not imply composition, boundary, transfer or retention
    mastery.
    """

    structure_id: str
    model_checkpoint_hash: str
    probe_family_hash: str
    coordinate_values: Tuple[Tuple[MasteryCoordinate, float | None], ...]
    measured_case_ids: Tuple[str, ...]
    frozen_before_allocation: bool | None

    def __post_init__(self) -> None:
        if not self.structure_id.strip():
            raise ValueError("mastery estimate requires structure identity")
        if not self.model_checkpoint_hash.strip() or not self.probe_family_hash.strip():
            raise ValueError("mastery estimate requires checkpoint/probe hashes")
        keys = [key for key, _ in self.coordinate_values]
        if tuple(keys) != _COORDINATE_ORDER:
            raise ValueError("mastery coordinates must appear exactly once in canonical order")
        for _, value in self.coordinate_values:
            if value is not None and (not isfinite(value) or not 0.0 <= value <= 1.0):
                raise ValueError("measured mastery values must be finite and in [0,1]")
        if not self.measured_case_ids or any(not item.strip() for item in self.measured_case_ids):
            raise ValueError("mastery estimate requires non-empty measured case identities")
        if len(set(self.measured_case_ids)) != len(self.measured_case_ids):
            raise ValueError("measured case identities must be unique")

    @property
    def values(self) -> Mapping[MasteryCoordinate, float | None]:
        return dict(self.coordinate_values)

    @property
    def fully_measured(self) -> bool:
        return all(value is not None for _, value in self.coordinate_values)

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_structural_transfer_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class TrainingUtilityVector:
    """Vector-valued *hypothesis* about training value, oriented high=useful.

    No scalarization is canonically defined. The final two coordinates are
    burdens/risks and therefore must not be mixed into a scientific-authority
    score. These values are routing/allocation features only until a registered
    experiment validates a policy that uses them.
    """

    expected_principle_gain: float
    expected_composition_gain: float
    expected_boundary_gain: float
    expected_representation_gain: float
    expected_transfer_gain: float
    expected_retention_gain: float
    forgetting_risk: float
    negative_transfer_risk: float
    estimated_total_cost: float

    def __post_init__(self) -> None:
        for name in (
            "expected_principle_gain",
            "expected_composition_gain",
            "expected_boundary_gain",
            "expected_representation_gain",
            "expected_transfer_gain",
            "expected_retention_gain",
            "forgetting_risk",
            "negative_transfer_risk",
        ):
            value = getattr(self, name)
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0,1]")
        if not isfinite(self.estimated_total_cost) or self.estimated_total_cost < 0:
            raise ValueError("estimated training cost must be finite and non-negative")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class TrainingAllocationCandidate:
    """Derived training view over a raw item; raw identity remains canonical."""

    candidate_id: str
    raw_item_id: str
    derived_view_id: str
    structure_id: str
    model_checkpoint_hash: str
    utility: TrainingUtilityVector
    data_provenance_ids: Tuple[str, ...]
    confirmatory_target_leak: bool = False

    def __post_init__(self) -> None:
        for value in (
            self.candidate_id,
            self.raw_item_id,
            self.derived_view_id,
            self.structure_id,
            self.model_checkpoint_hash,
        ):
            if not value.strip():
                raise ValueError("training candidate identities cannot be blank")
        if not self.data_provenance_ids or any(not item.strip() for item in self.data_provenance_ids):
            raise ValueError("training candidate requires data provenance identities")
        if len(set(self.data_provenance_ids)) != len(self.data_provenance_ids):
            raise ValueError("training candidate provenance identities must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def is_raw_corpus_replacement(self) -> bool:
        return False


@dataclass(frozen=True)
class TrainingProjectionSnapshot:
    """Immutable candidate projection ``pi_train(R_t, theta_t)``.

    The snapshot is an experimental allocation view. It owns neither raw-data
    semantics nor scientific authority and is stale as soon as the bound model
    checkpoint changes.
    """

    projection_id: str
    model_checkpoint_hash: str
    structural_catalog_hash: str
    probe_family_hash: str
    mastery_estimates: Tuple[StructuralMasteryEstimate, ...]
    candidates: Tuple[TrainingAllocationCandidate, ...]
    repetition_floor: float
    frozen_before_outcome_access: bool | None
    snapshot_hash: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def claims_adaptive_training_works(self) -> bool:
        return False

    def is_stale_for_checkpoint(self, checkpoint_hash: str) -> bool:
        return checkpoint_hash != self.model_checkpoint_hash


@dataclass(frozen=True)
class ProjectionAssessment:
    verdict: ProjectionVerdict
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _structural_object_row(item: StructuralObject) -> tuple[object, ...]:
    """Canonical content row for one registered structural object."""

    return (
        item.structure_id,
        item.domain,
        item.qoi,
        item.context_id,
        tuple((role.role_id, role.kind) for role in item.roles),
        tuple(relation.signature for relation in item.relations),
        tuple(sorted(item.invariants)),
        tuple((boundary.key, boundary.value) for boundary in item.boundaries),
        tuple(item.evidence_ids),
    )


def structural_catalog_digest(structural_objects: Sequence[StructuralObject]) -> str:
    """Content-bind a structural catalog independently of caller naming.

    The digest sorts by structural identity but preserves role/relation/boundary
    order *within* each object because that order is part of the registered
    representation. Scientific authority is unaffected by this digest.
    """

    rows = tuple(sorted((_structural_object_row(item) for item in structural_objects), key=lambda row: str(row[0])))
    return sha256(repr(("RAKL_TRAINING_STRUCTURAL_CATALOG_V1", rows)).encode("utf-8")).hexdigest()


def _snapshot_hash(
    projection_id: str,
    checkpoint_hash: str,
    structural_catalog_hash: str,
    probe_family_hash: str,
    mastery_estimates: Sequence[StructuralMasteryEstimate],
    candidates: Sequence[TrainingAllocationCandidate],
    repetition_floor: float,
    frozen_before_outcome_access: bool | None,
) -> str:
    payload = repr(
        (
            "RAKL_TRAINING_PROJECTION_V1",
            projection_id,
            checkpoint_hash,
            structural_catalog_hash,
            probe_family_hash,
            tuple(mastery_estimates),
            tuple(candidates),
            repetition_floor,
            frozen_before_outcome_access,
        )
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def build_training_projection(
    *,
    projection_id: str,
    model_checkpoint_hash: str,
    structural_catalog_hash: str,
    probe_family_hash: str,
    structural_objects: Sequence[StructuralObject],
    mastery_estimates: Sequence[StructuralMasteryEstimate],
    candidates: Sequence[TrainingAllocationCandidate],
    repetition_floor: float,
    frozen_before_outcome_access: bool | None,
) -> TrainingProjectionSnapshot:
    """Construct an immutable proposal-only training projection.

    This validates identity/binding only. It neither estimates mastery nor
    selects a batch. Those are empirical mechanisms owned by #461/#455.
    """

    if not projection_id.strip():
        raise ValueError("training projection requires identity")
    if not model_checkpoint_hash.strip() or not structural_catalog_hash.strip() or not probe_family_hash.strip():
        raise ValueError("training projection requires checkpoint/catalog/probe hashes")
    if not isfinite(repetition_floor) or not 0.0 <= repetition_floor <= 1.0:
        raise ValueError("repetition floor must be finite and in [0,1]")

    structure_ids = [item.structure_id for item in structural_objects]
    if len(structure_ids) != len(set(structure_ids)):
        raise ValueError("structural catalog ids must be unique")
    expected_catalog_hash = structural_catalog_digest(structural_objects)
    if structural_catalog_hash != expected_catalog_hash:
        raise ValueError("structural catalog hash does not match supplied structural objects")
    known_structures = set(structure_ids)

    estimate_ids = [item.structure_id for item in mastery_estimates]
    if len(estimate_ids) != len(set(estimate_ids)):
        raise ValueError("one mastery estimate per structure is permitted")
    for estimate in mastery_estimates:
        if estimate.structure_id not in known_structures:
            raise ValueError("mastery estimate refers to unknown structural object")
        if estimate.model_checkpoint_hash != model_checkpoint_hash:
            raise ValueError("mastery estimate checkpoint does not match projection checkpoint")
        if estimate.probe_family_hash != probe_family_hash:
            raise ValueError("mastery estimate probe family does not match projection probe family")

    candidate_ids = [item.candidate_id for item in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("training candidate ids must be unique")
    raw_ids = [item.raw_item_id for item in candidates]
    if len(raw_ids) != len(set(raw_ids)):
        raise ValueError("one derived allocation candidate per raw item is permitted in v1")
    for candidate in candidates:
        if candidate.structure_id not in known_structures:
            raise ValueError("training candidate refers to unknown structural object")
        if candidate.model_checkpoint_hash != model_checkpoint_hash:
            raise ValueError("training candidate checkpoint does not match projection checkpoint")

    return TrainingProjectionSnapshot(
        projection_id=projection_id,
        model_checkpoint_hash=model_checkpoint_hash,
        structural_catalog_hash=structural_catalog_hash,
        probe_family_hash=probe_family_hash,
        mastery_estimates=tuple(mastery_estimates),
        candidates=tuple(candidates),
        repetition_floor=repetition_floor,
        frozen_before_outcome_access=frozen_before_outcome_access,
        snapshot_hash=_snapshot_hash(
            projection_id,
            model_checkpoint_hash,
            structural_catalog_hash,
            probe_family_hash,
            mastery_estimates,
            candidates,
            repetition_floor,
            frozen_before_outcome_access,
        ),
    )


def assess_training_projection(snapshot: TrainingProjectionSnapshot) -> ProjectionAssessment:
    """Fail-closed readiness check for *experimental* allocation use only."""

    expected_hash = _snapshot_hash(
        snapshot.projection_id,
        snapshot.model_checkpoint_hash,
        snapshot.structural_catalog_hash,
        snapshot.probe_family_hash,
        snapshot.mastery_estimates,
        snapshot.candidates,
        snapshot.repetition_floor,
        snapshot.frozen_before_outcome_access,
    )
    if snapshot.snapshot_hash != expected_hash:
        return ProjectionAssessment(
            ProjectionVerdict.INVALID,
            ("training_projection_content_hash_mismatch",),
        )
    if snapshot.frozen_before_outcome_access is None:
        return ProjectionAssessment(
            ProjectionVerdict.CANNOT_CHECK,
            ("projection_freeze_chronology_unknown",),
        )
    if snapshot.frozen_before_outcome_access is False:
        return ProjectionAssessment(
            ProjectionVerdict.INVALID,
            ("training_projection_defined_after_outcome_access",),
        )
    if any(item.confirmatory_target_leak for item in snapshot.candidates):
        return ProjectionAssessment(
            ProjectionVerdict.INVALID,
            ("confirmatory_target_leak_in_training_candidate",),
        )
    if any(item.frozen_before_allocation is None for item in snapshot.mastery_estimates):
        return ProjectionAssessment(
            ProjectionVerdict.CANNOT_CHECK,
            ("mastery_probe_freeze_chronology_unknown",),
        )
    if any(item.frozen_before_allocation is False for item in snapshot.mastery_estimates):
        return ProjectionAssessment(
            ProjectionVerdict.INVALID,
            ("mastery_estimate_defined_posthoc",),
        )
    if any(not item.fully_measured for item in snapshot.mastery_estimates):
        return ProjectionAssessment(
            ProjectionVerdict.CANNOT_CHECK,
            ("one_or_more_mastery_coordinates_unmeasured",),
        )
    if not snapshot.candidates:
        return ProjectionAssessment(
            ProjectionVerdict.CANNOT_CHECK,
            ("no_training_candidates_materialized",),
        )
    return ProjectionAssessment(
        ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION,
        ("identity_and_chronology_contract_complete; no efficacy claim implied",),
    )
