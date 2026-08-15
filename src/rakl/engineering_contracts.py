"""The ladder-named abstractions that the packet specified and the code lacked.

`CONFORMANCE_AUDIT_V1.json` recorded these as ABSENT on the named-surface axis:

    IMPLEMENTATION_LADDER.md wave E2   BlobStore, SnapshotRepository,
                                       SemanticRepository, MetrologyRepository,
                                       TransitionRepository
    IMPLEMENTATION_LADDER.md wave E5   ResearchWorkflowEngine
    IMPLEMENTATION_LADDER.md wave E8   the eight allowed terminals

The concrete reference implementations existed; the *interfaces the ladder named*
did not, so nothing stated which classes were interchangeable, and nothing could
be substituted for a production backend without reading every call site.

This module is deliberately thin. It adds no behaviour. Its whole value is that
`tests/test_engineering_conformance.py` asserts the existing concrete classes
against it — a `Protocol` nobody is checked against is decoration, not a contract.

One negative is recorded here rather than smoothed over: the two reference
workflow engines are NOT interchangeable. `SqliteReferenceWorkflowEngine`
(deterministic in-process history) and `SqliteWorkerWorkflowEngine` (leases,
heartbeats, crash recovery) share only `activity`/`events`/`verify_history`, and
even those return different types. `ResearchWorkflowEngine` therefore names the
E5 surface that the reference engine provides, and `WorkflowHistory` names the
smaller surface both provide. Substituting one for the other is a typed error,
not a configuration choice.

`runtime_checkable` Protocols check method PRESENCE, not signatures. The tests
assert the load-bearing signatures separately.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable

from rakl.engineering_store import BlobStore

__all__ = [
    "BlobStore", "MetrologyRepository", "ResearchWorkflowEngine", "SemanticRepository",
    "SnapshotRepository", "TransitionRepository", "WaveE8Terminal", "WorkflowHistory",
]


# ---------------------------------------------------------------------------
# Wave E2 -- repository interfaces
# ---------------------------------------------------------------------------


@runtime_checkable
class SnapshotRepository(Protocol):
    """ARCHITECTURE 2: the ProjectSnapshot consistency boundary.

    A production backend substituted here must preserve snapshot identity: the
    same logical state may not receive two incompatible snapshot ids (the E1
    falsifier).
    """

    def initialize_project(self, snapshot: Any) -> Any: ...

    def head(self, project_id: str) -> Any: ...

    def get_snapshot(self, snapshot_id: str) -> Any: ...


@runtime_checkable
class TransitionRepository(Protocol):
    """ARCHITECTURE 4: every consequential mutation yields a StateTransitionReceipt.

    The reference backend implements this with a project-head compare-and-swap.
    A production backend must preserve the semantics under a stronger multi-worker
    transaction backend, including on the non-committed terminals -- a refusal is
    still a receipt.
    """

    def commit_transition(self, request: Any, after_snapshot: Any, **kwargs: Any) -> Any: ...

    def record_noncommitted_transition(self, request: Any, **kwargs: Any) -> Any: ...

    def transition_receipt(self, project_id: str, idempotency_key: str) -> Any: ...


@runtime_checkable
class SemanticRepository(Protocol):
    """ARCHITECTURE 3: fibres / atoms / atom_versions / relations / witnesses.

    Immutable versions with explicit supersession. The E3 falsifier is that a
    restart loses atoms/relations/charts, or a relation references a missing atom.
    """

    def add_fiber(self, fiber: Any, *, valid_from_snapshot_id: str) -> Any: ...

    def add_atom_version(self, version: Any, *, valid_from_snapshot_id: str) -> Any: ...

    def add_witness_version(self, version: Any, *, valid_from_snapshot_id: str) -> Any: ...

    def atom_versions_at(self, sequence: int) -> Any: ...

    def witness_versions_at(self, sequence: int) -> Any: ...

    def semantic_revision(self, sequence: int) -> str: ...

    def commit_batch(self, batch: Any, *, committed_snapshot_id: str,
                     expected_semantic_revision: str) -> Any: ...


@runtime_checkable
class MetrologyRepository(Protocol):
    """ARCHITECTURE 4: metric receipts, saturation certificates, hard gates, decisions.

    The E4 falsifier is that a resumed decision cannot reconstruct its exact
    metric/saturation basis, so a conforming implementation must return the stored
    canonical payload, not a recomputation of it.
    """

    def record(self, projection: Any) -> Any: ...

    def records(self, project_snapshot_id: str, **kwargs: Any) -> Any: ...

    def control_revision(self, project_snapshot_id: str) -> str: ...


# ---------------------------------------------------------------------------
# Wave E5 -- workflow engine
# ---------------------------------------------------------------------------


@runtime_checkable
class WorkflowHistory(Protocol):
    """The inspection surface both reference engines share.

    Replayable history is the point: `verify_history` must detect a tampered or
    truncated event chain rather than returning a plausible prefix.
    """

    def activity(self, workflow_id: str, activity_id: str) -> Any: ...

    def events(self, workflow_id: str) -> Any: ...

    def verify_history(self, workflow_id: str, **kwargs: Any) -> bool: ...


@runtime_checkable
class ResearchWorkflowEngine(WorkflowHistory, Protocol):
    """IMPLEMENTATION_LADDER wave E5.

    Deterministic workflow history separated from external activities. Every
    external activity carries activity_id, an idempotency key where possible,
    `retry_safe`, an attempt number, a timeout/heartbeat, its exact snapshot
    input, and terminates in a receipt or RECOVERY_REQUIRED.

    `recover_ambiguous_activity` is the load-bearing member: an activity whose
    external effect may have landed before the worker died must reach an explicit
    recovery state, never a blind retry.
    """

    def schedule_activity(self, workflow_id: str, spec: Any) -> Any: ...

    def begin_activity(self, workflow_id: str, activity_id: str) -> Any: ...

    def complete_activity(self, workflow_id: str, activity_id: str, *, result_digest: str) -> Any: ...

    def fail_activity(self, workflow_id: str, activity_id: str, *, error: str, retryable: bool) -> Any: ...

    def recover_ambiguous_activity(self, workflow_id: str, activity_id: str) -> Any: ...


# ---------------------------------------------------------------------------
# Wave E8 -- the allowed terminal vocabulary
# ---------------------------------------------------------------------------


class WaveE8Terminal(str, Enum):
    """The only terminals IMPLEMENTATION_LADDER wave E8 permits a release to report.

    Held in code so a release terminal is a typed value rather than free prose.
    Membership grants nothing: naming a terminal is not producing the evidence for
    it, and `PRODUCTION_READY_SCOPED` in particular requires the full
    HOSTILE_TEST_MATRIX executed on a clean deployment and a frozen release
    identity.
    """

    PRODUCTION_READY_SCOPED = "PRODUCTION_READY_SCOPED"
    SINGLE_NODE_READY_ONLY = "SINGLE_NODE_READY_ONLY"
    DURABILITY_READY_CONTROL_INTEGRATION_OPEN = "DURABILITY_READY_CONTROL_INTEGRATION_OPEN"
    CONTROL_READY_DISTRIBUTED_RUNTIME_OPEN = "CONTROL_READY_DISTRIBUTED_RUNTIME_OPEN"
    SECURITY_OR_RECOVERY_BLOCKED = "SECURITY_OR_RECOVERY_BLOCKED"
    PERFORMANCE_ENVELOPE_EXCEEDED = "PERFORMANCE_ENVELOPE_EXCEEDED"
    MIGRATION_PARITY_FAILED = "MIGRATION_PARITY_FAILED"
    CANNOT_CHECK_RESOURCE_BOUND = "CANNOT_CHECK_RESOURCE_BOUND"

    @property
    def grants_scientific_authority(self) -> bool:
        return False
