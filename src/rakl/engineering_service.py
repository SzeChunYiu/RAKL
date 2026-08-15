"""Shared read projections over canonical ORION engineering state.

The controller and human Observatory deliberately do not recompute epistemic
state independently.  Both are projections of the exact same stored
:class:`EpistemicStatus`, bound to the current project snapshot.

This module is authority-neutral: it transports incumbent status identity and
never upgrades saturation, controller, or scientific-authority claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .engineering_state import EpistemicStatus, NextActionClass
from .engineering_store import EngineeringIntegrityError, EngineeringStateRepository


class EpistemicStatusUnavailable(LookupError):
    """No canonical status exists for the requested current-snapshot coordinates."""


@dataclass(frozen=True)
class ControllerStatusProjection:
    project_id: str
    project_snapshot_id: str
    status_id: str
    target_id: str
    fiber_id: str
    next_action: NextActionClass
    hard_gate_ids: Tuple[str, ...]
    active_residual_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ObservatoryStatusProjection:
    project_id: str
    project_snapshot_id: str
    status_id: str
    target_id: str
    fiber_id: str
    axis_summary: Tuple[Tuple[str, bool, int], ...]
    required_routes: Tuple[str, ...]
    covered_routes: Tuple[str, ...]
    missing_routes: Tuple[str, ...]
    active_residual_ids: Tuple[str, ...]
    freshness_stale: bool
    available_support_paths: int
    blocking_cut_ids: Tuple[str, ...]
    hard_gate_ids: Tuple[str, ...]
    next_action: NextActionClass
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SharedEpistemicRead:
    status: EpistemicStatus
    controller: ControllerStatusProjection
    observatory: ObservatoryStatusProjection

    def __post_init__(self) -> None:
        identities = {
            (self.status.project_snapshot_id, self.status.status_id),
            (self.controller.project_snapshot_id, self.controller.status_id),
            (self.observatory.project_snapshot_id, self.observatory.status_id),
        }
        if len(identities) != 1:
            raise EngineeringIntegrityError(
                "controller and Observatory must project one canonical EpistemicStatus"
            )


class EngineeringReadService:
    """Read one canonical current-snapshot status and project it for two consumers."""

    def __init__(self, state: EngineeringStateRepository) -> None:
        self.state = state

    def current_status(
        self,
        *,
        project_id: str,
        target_id: str,
        fiber_id: str,
    ) -> EpistemicStatus:
        head = self.state.head(project_id)
        status = self.state.latest_epistemic_status(
            project_snapshot_id=head.snapshot_id,
            target_id=target_id,
            fiber_id=fiber_id,
        )
        if status is None:
            raise EpistemicStatusUnavailable(
                f"no EpistemicStatus for current snapshot {head.snapshot_id} "
                f"target={target_id!r} fiber={fiber_id!r}"
            )
        if status.project_snapshot_id != head.snapshot_id:
            # Defensive even though repository lookup is snapshot-scoped.
            raise EngineeringIntegrityError("status is stale relative to current project head")
        return status

    def shared_status(
        self,
        *,
        project_id: str,
        target_id: str,
        fiber_id: str,
    ) -> SharedEpistemicRead:
        status = self.current_status(
            project_id=project_id,
            target_id=target_id,
            fiber_id=fiber_id,
        )
        controller = ControllerStatusProjection(
            project_id=project_id,
            project_snapshot_id=status.project_snapshot_id,
            status_id=status.status_id,
            target_id=status.target_id,
            fiber_id=status.fiber_id,
            next_action=status.next_action,
            hard_gate_ids=status.hard_gate_ids,
            active_residual_ids=status.active_residual_ids,
            reasons=status.reasons,
        )
        observatory = ObservatoryStatusProjection(
            project_id=project_id,
            project_snapshot_id=status.project_snapshot_id,
            status_id=status.status_id,
            target_id=status.target_id,
            fiber_id=status.fiber_id,
            axis_summary=tuple(
                (axis.axis, axis.bounded_flat, axis.recent_retained_novelty)
                for axis in status.axis_statuses
            ),
            required_routes=status.required_routes,
            covered_routes=status.covered_routes,
            missing_routes=status.missing_routes,
            active_residual_ids=status.active_residual_ids,
            freshness_stale=status.freshness_stale,
            available_support_paths=status.available_support_paths,
            blocking_cut_ids=status.blocking_cut_ids,
            hard_gate_ids=status.hard_gate_ids,
            next_action=status.next_action,
            reasons=status.reasons,
        )
        return SharedEpistemicRead(status, controller, observatory)
