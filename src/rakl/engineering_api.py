"""Versioned in-process service facade for ORION engineering state.

This is intentionally a *reference service boundary*, not a network server.  It
pins the semantics that a later HTTP/gRPC adapter must preserve: reads are
snapshot-bound, plans consume the canonical EpistemicStatus, and every mutation
requires a caller-supplied idempotency key, before-snapshot identity and content
hash for the intended action payload.

A transport adapter may add authentication, serialization and rate limiting; it
may not weaken these state/identity requirements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from .engineering_service import EngineeringReadService, SharedEpistemicRead
from .engineering_state import (
    ProjectSnapshot,
    StateTransitionReceipt,
    StateTransitionRequest,
    TransitionStatus,
)
from .engineering_store import EngineeringStateRepository


API_VERSION = "orion-engineering-api-v1"


@dataclass(frozen=True)
class ActionPlan:
    api_version: str
    project_id: str
    project_snapshot_id: str
    status_id: str
    target_id: str
    fiber_id: str
    next_action: str
    reasons: Tuple[str, ...]
    hard_gate_ids: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


class EngineeringServiceFacade:
    """Small transport-neutral surface suitable for CLI/HTTP adapters."""

    def __init__(self, state: EngineeringStateRepository) -> None:
        self.state = state
        self.reads = EngineeringReadService(state)

    def snapshot(self, *, project_id: str, snapshot_id: str | None = None) -> ProjectSnapshot:
        if snapshot_id is None:
            return self.state.head(project_id)
        snapshot = self.state.get_snapshot(snapshot_id)
        if snapshot.project_id != project_id:
            raise ValueError("snapshot belongs to a different project")
        return snapshot

    def epistemic_status(
        self, *, project_id: str, target_id: str, fiber_id: str
    ) -> SharedEpistemicRead:
        return self.reads.shared_status(
            project_id=project_id, target_id=target_id, fiber_id=fiber_id
        )

    def plan_action(self, *, project_id: str, target_id: str, fiber_id: str) -> ActionPlan:
        shared = self.epistemic_status(
            project_id=project_id, target_id=target_id, fiber_id=fiber_id
        )
        status = shared.status
        return ActionPlan(
            api_version=API_VERSION,
            project_id=project_id,
            project_snapshot_id=status.project_snapshot_id,
            status_id=status.status_id,
            target_id=status.target_id,
            fiber_id=status.fiber_id,
            next_action=status.next_action.value,
            reasons=status.reasons,
            hard_gate_ids=status.hard_gate_ids,
        )

    def commit_metadata_transition(
        self,
        *,
        request: StateTransitionRequest,
        after_snapshot: ProjectSnapshot,
        created_at_utc: str,
        produced_artifact_ids: Tuple[str, ...] = (),
        metric_receipt_ids: Tuple[str, ...] = (),
        residual_ids: Tuple[str, ...] = (),
    ) -> StateTransitionReceipt:
        # The repository enforces project/snapshot CAS and idempotent replay.
        if request.before_snapshot_id == after_snapshot.snapshot_id:
            raise ValueError("transition must not commit a snapshot to itself")
        return self.state.commit_transition(
            request,
            after_snapshot,
            produced_artifact_ids=produced_artifact_ids,
            metric_receipt_ids=metric_receipt_ids,
            residual_ids=residual_ids,
            created_at_utc=created_at_utc,
        )

    def record_recovery_required(
        self,
        *,
        request: StateTransitionRequest,
        reasons: Tuple[str, ...],
        created_at_utc: str,
    ) -> StateTransitionReceipt:
        if not reasons:
            raise ValueError("RECOVERY_REQUIRED requires explicit reasons")
        return self.state.record_noncommitted_transition(
            request,
            status=TransitionStatus.RECOVERY_REQUIRED,
            reasons=reasons,
            created_at_utc=created_at_utc,
        )
