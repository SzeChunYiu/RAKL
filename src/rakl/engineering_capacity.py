"""Non-compensatory capacity/SLO reference policy for ORION engineering state.

Capacity is an engineering control plane, never an epistemic score.  Exceeding a
registered hard envelope blocks or degrades execution; it cannot be compensated
by high scientific utility.  Canonical history is preserved while rebuildable
views/caches may be compacted or delayed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class CapacityVerdict(str, Enum):
    WITHIN_ENVELOPE = "WITHIN_ENVELOPE"
    COMPACT_REBUILDABLE_VIEWS = "COMPACT_REBUILDABLE_VIEWS"
    BLOCK_NEW_WORK = "BLOCK_NEW_WORK"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class EngineeringCapacityPolicy:
    policy_id: str
    max_metadata_bytes: int
    max_active_blob_bytes: int
    max_nonterminal_workflows: int
    max_index_lag_snapshots: int
    max_context_tokens: int

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("capacity policy id is required")
        if min(
            self.max_metadata_bytes,
            self.max_active_blob_bytes,
            self.max_nonterminal_workflows,
            self.max_index_lag_snapshots,
            self.max_context_tokens,
        ) < 0:
            raise ValueError("capacity limits must be non-negative")


@dataclass(frozen=True)
class EngineeringCapacityObservation:
    project_snapshot_id: str
    metadata_bytes: int | None
    active_blob_bytes: int | None
    nonterminal_workflows: int | None
    index_lag_snapshots: int | None
    context_tokens: int | None

    def __post_init__(self) -> None:
        if not self.project_snapshot_id.strip():
            raise ValueError("snapshot identity is required")
        values = (
            self.metadata_bytes,
            self.active_blob_bytes,
            self.nonterminal_workflows,
            self.index_lag_snapshots,
            self.context_tokens,
        )
        if any(value is not None and value < 0 for value in values):
            raise ValueError("capacity observations cannot be negative")


@dataclass(frozen=True)
class CapacityAssessment:
    verdict: CapacityVerdict
    reasons: Tuple[str, ...]
    preserve_canonical_history: bool = True

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_engineering_capacity(
    observation: EngineeringCapacityObservation,
    policy: EngineeringCapacityPolicy,
) -> CapacityAssessment:
    coordinates = {
        "metadata_bytes": (observation.metadata_bytes, policy.max_metadata_bytes),
        "active_blob_bytes": (observation.active_blob_bytes, policy.max_active_blob_bytes),
        "nonterminal_workflows": (
            observation.nonterminal_workflows,
            policy.max_nonterminal_workflows,
        ),
        "index_lag_snapshots": (observation.index_lag_snapshots, policy.max_index_lag_snapshots),
        "context_tokens": (observation.context_tokens, policy.max_context_tokens),
    }
    missing = tuple(name for name, (value, _) in coordinates.items() if value is None)
    if missing:
        return CapacityAssessment(
            CapacityVerdict.CANNOT_CHECK,
            tuple(f"missing_capacity_observation:{name}" for name in missing),
        )

    exceeded = tuple(
        name for name, (value, limit) in coordinates.items()
        if value is not None and value > limit
    )
    if not exceeded:
        return CapacityAssessment(
            CapacityVerdict.WITHIN_ENVELOPE,
            ("all_registered_capacity_coordinates_within_envelope",),
        )

    # Rebuildable/view-only pressure may be handled by compaction. Canonical
    # metadata/history pressure, workflow overload, or context overflow blocks new
    # work until an operator acts; nothing is silently deleted.
    view_only = set(exceeded) <= {"index_lag_snapshots", "active_blob_bytes"}
    if view_only:
        return CapacityAssessment(
            CapacityVerdict.COMPACT_REBUILDABLE_VIEWS,
            tuple(f"capacity_exceeded:{name}" for name in exceeded)
            + ("canonical_history_must_not_be_deleted",),
        )
    return CapacityAssessment(
        CapacityVerdict.BLOCK_NEW_WORK,
        tuple(f"capacity_exceeded:{name}" for name in exceeded)
        + ("operator_intervention_required_before_new_work",),
    )
