"""Production-engineering state contracts for ORION/RAKL.

This module is deliberately authority-neutral.  It provides content-identified
snapshots, epistemic-status read models, and state-transition receipts that can
be shared by a human observatory and a machine controller without creating a
second scientific-authority system.

The contracts are additive.  Existing RAKL scientific authority, saturation,
metric, episode, and governance objects remain the sources of authority.  These
objects bind and transport their identities; they never upgrade them.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence, Tuple


SCHEMA_VERSION = "orion-engineering-state-v2"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=lambda item: item.value if isinstance(item, Enum) else item,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256(_canonical_json_bytes(value)).hexdigest()


def _require_text(value: str, name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def _require_sha256(value: str, name: str) -> str:
    _require_text(value, name)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _require_unique(values: Sequence[str], name: str) -> None:
    if any(not item or not item.strip() for item in values):
        raise ValueError(f"{name} cannot contain empty values")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")


def _require_utc_timestamp(value: str, name: str) -> None:
    _require_text(value, name)
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{name} must be UTC")


class TransitionStatus(str, Enum):
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


class NextActionClass(str, Enum):
    CONTINUE_SEARCH = "CONTINUE_SEARCH"
    PROCEED_OBJECT_WORK = "PROCEED_OBJECT_WORK"
    TARGETED_REFRESH_REQUIRED = "TARGETED_REFRESH_REQUIRED"
    FRESHNESS_REFRESH_REQUIRED = "FRESHNESS_REFRESH_REQUIRED"
    COMPILE_SOLVER_VIEW = "COMPILE_SOLVER_VIEW"
    VERIFY_SOLUTION = "VERIFY_SOLUTION"
    RUN_DISCRIMINATOR = "RUN_DISCRIMINATOR"
    REPAIR_EPISTEMIC_CUT = "REPAIR_EPISTEMIC_CUT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ProjectSnapshot:
    """Content-identified boundary for one coherent ORION project state.

    A snapshot stores identities/cutoffs, not the full state payload.  Canonical
    evidence, semantic state, metrics, episodes and authority remain in their
    existing stores; this object binds the exact heads/revisions a controller or
    solver view was allowed to observe.
    """

    project_id: str
    sequence: int
    previous_snapshot_id: str | None
    evidence_cutoff: str
    semantic_state_revision: str
    metric_ledger_head: str
    episode_store_head: str
    saturation_basis_ids: Tuple[str, ...]
    authority_projection_revision: str
    controller_epoch_id: str
    created_at_utc: str
    schema_version: str = SCHEMA_VERSION
    snapshot_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.project_id, "project_id")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if self.sequence == 0 and self.previous_snapshot_id is not None:
            raise ValueError("initial snapshot cannot have a previous_snapshot_id")
        if self.sequence > 0 and not self.previous_snapshot_id:
            raise ValueError("non-initial snapshot requires previous_snapshot_id")
        for name in (
            "evidence_cutoff",
            "semantic_state_revision",
            "metric_ledger_head",
            "episode_store_head",
            "authority_projection_revision",
            "controller_epoch_id",
        ):
            _require_text(getattr(self, name), name)
        _require_unique(self.saturation_basis_ids, "saturation_basis_ids")
        _require_utc_timestamp(self.created_at_utc, "created_at_utc")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported engineering state schema: {self.schema_version}")
        expected = self.derived_snapshot_id
        if self.snapshot_id and self.snapshot_id != expected:
            raise ValueError("snapshot_id does not match canonical snapshot content")
        if not self.snapshot_id:
            object.__setattr__(self, "snapshot_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "sequence": self.sequence,
            "previous_snapshot_id": self.previous_snapshot_id,
            "evidence_cutoff": self.evidence_cutoff,
            "semantic_state_revision": self.semantic_state_revision,
            "metric_ledger_head": self.metric_ledger_head,
            "episode_store_head": self.episode_store_head,
            "saturation_basis_ids": list(self.saturation_basis_ids),
            "authority_projection_revision": self.authority_projection_revision,
            "controller_epoch_id": self.controller_epoch_id,
            "created_at_utc": self.created_at_utc,
        }

    @property
    def derived_snapshot_id(self) -> str:
        return "snapshot:" + canonical_sha256(self.identity_payload)

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "snapshot_id": self.snapshot_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ProjectSnapshot":
        return cls(
            project_id=str(value["project_id"]),
            sequence=int(value["sequence"]),
            previous_snapshot_id=(None if value.get("previous_snapshot_id") is None else str(value["previous_snapshot_id"])),
            evidence_cutoff=str(value["evidence_cutoff"]),
            semantic_state_revision=str(value["semantic_state_revision"]),
            metric_ledger_head=str(value["metric_ledger_head"]),
            episode_store_head=str(value["episode_store_head"]),
            saturation_basis_ids=tuple(str(item) for item in value.get("saturation_basis_ids", ())),
            authority_projection_revision=str(value["authority_projection_revision"]),
            controller_epoch_id=str(value["controller_epoch_id"]),
            created_at_utc=str(value["created_at_utc"]),
            schema_version=str(value.get("schema_version", SCHEMA_VERSION)),
            snapshot_id=str(value.get("snapshot_id", "")),
        )


@dataclass(frozen=True)
class EpistemicAxisStatus:
    axis: str
    bounded_flat: bool
    recent_retained_novelty: int
    independent_flat_routes: Tuple[str, ...] = ()
    reopen_residual_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.axis, "axis")
        if self.recent_retained_novelty < 0:
            raise ValueError("recent_retained_novelty cannot be negative")
        _require_unique(self.independent_flat_routes, "independent_flat_routes")
        _require_unique(self.reopen_residual_ids, "reopen_residual_ids")
        if self.reopen_residual_ids and self.bounded_flat:
            raise ValueError("an axis reopened by a residual cannot be bounded_flat")

    def to_dict(self) -> dict[str, object]:
        return {
            "axis": self.axis,
            "bounded_flat": self.bounded_flat,
            "recent_retained_novelty": self.recent_retained_novelty,
            "independent_flat_routes": list(self.independent_flat_routes),
            "reopen_residual_ids": list(self.reopen_residual_ids),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "EpistemicAxisStatus":
        return cls(
            axis=str(value["axis"]),
            bounded_flat=bool(value["bounded_flat"]),
            recent_retained_novelty=int(value["recent_retained_novelty"]),
            independent_flat_routes=tuple(str(item) for item in value.get("independent_flat_routes", ())),
            reopen_residual_ids=tuple(str(item) for item in value.get("reopen_residual_ids", ())),
        )


@dataclass(frozen=True)
class EpistemicStatus:
    """Canonical read model shared by the controller, UI and audit tooling."""

    project_snapshot_id: str
    target_id: str
    fiber_id: str
    axis_statuses: Tuple[EpistemicAxisStatus, ...]
    required_routes: Tuple[str, ...]
    covered_routes: Tuple[str, ...]
    missing_routes: Tuple[str, ...]
    active_residual_ids: Tuple[str, ...]
    freshness_stale: bool
    required_authority: int
    available_support_paths: int
    blocking_cut_ids: Tuple[str, ...]
    hard_gate_ids: Tuple[str, ...]
    next_action: NextActionClass
    reasons: Tuple[str, ...]
    metric_receipt_ids: Tuple[str, ...]
    basis_fingerprints: Tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    status_id: str = ""

    def __post_init__(self) -> None:
        for name in ("project_snapshot_id", "target_id", "fiber_id"):
            _require_text(getattr(self, name), name)
        if self.required_authority < 0 or self.available_support_paths < 0:
            raise ValueError("authority and path counts must be non-negative")
        axes = [item.axis for item in self.axis_statuses]
        if len(axes) != len(set(axes)):
            raise ValueError("axis_statuses must contain each axis at most once")
        for name in (
            "required_routes",
            "covered_routes",
            "missing_routes",
            "active_residual_ids",
            "blocking_cut_ids",
            "hard_gate_ids",
            "metric_receipt_ids",
            "basis_fingerprints",
        ):
            _require_unique(getattr(self, name), name)
        required = set(self.required_routes)
        if set(self.missing_routes) - required:
            raise ValueError("missing_routes must be a subset of required_routes")
        if set(self.covered_routes) & set(self.missing_routes):
            raise ValueError("covered_routes and missing_routes must be disjoint")
        if set(self.required_routes) - set(self.covered_routes) != set(self.missing_routes):
            raise ValueError("missing_routes must equal required_routes minus covered_routes")
        if not self.reasons:
            raise ValueError("EpistemicStatus requires reconstructable reasons")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported engineering state schema: {self.schema_version}")
        expected = self.derived_status_id
        if self.status_id and self.status_id != expected:
            raise ValueError("status_id does not match canonical status content")
        if not self.status_id:
            object.__setattr__(self, "status_id", expected)

    @property
    def bounded_saturated(self) -> bool:
        return bool(self.axis_statuses) and all(item.bounded_flat for item in self.axis_statuses)

    @property
    def grants_absolute_completeness(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_snapshot_id": self.project_snapshot_id,
            "target_id": self.target_id,
            "fiber_id": self.fiber_id,
            "axis_statuses": [item.to_dict() for item in self.axis_statuses],
            "required_routes": list(self.required_routes),
            "covered_routes": list(self.covered_routes),
            "missing_routes": list(self.missing_routes),
            "active_residual_ids": list(self.active_residual_ids),
            "freshness_stale": self.freshness_stale,
            "required_authority": self.required_authority,
            "available_support_paths": self.available_support_paths,
            "blocking_cut_ids": list(self.blocking_cut_ids),
            "hard_gate_ids": list(self.hard_gate_ids),
            "next_action": self.next_action.value,
            "reasons": list(self.reasons),
            "metric_receipt_ids": list(self.metric_receipt_ids),
            "basis_fingerprints": list(self.basis_fingerprints),
        }

    @property
    def derived_status_id(self) -> str:
        return "epistemic-status:" + canonical_sha256(self.identity_payload)

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "status_id": self.status_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "EpistemicStatus":
        return cls(
            project_snapshot_id=str(value["project_snapshot_id"]),
            target_id=str(value["target_id"]),
            fiber_id=str(value["fiber_id"]),
            axis_statuses=tuple(EpistemicAxisStatus.from_dict(item) for item in value.get("axis_statuses", ())),
            required_routes=tuple(str(item) for item in value.get("required_routes", ())),
            covered_routes=tuple(str(item) for item in value.get("covered_routes", ())),
            missing_routes=tuple(str(item) for item in value.get("missing_routes", ())),
            active_residual_ids=tuple(str(item) for item in value.get("active_residual_ids", ())),
            freshness_stale=bool(value["freshness_stale"]),
            required_authority=int(value["required_authority"]),
            available_support_paths=int(value["available_support_paths"]),
            blocking_cut_ids=tuple(str(item) for item in value.get("blocking_cut_ids", ())),
            hard_gate_ids=tuple(str(item) for item in value.get("hard_gate_ids", ())),
            next_action=NextActionClass(str(value["next_action"])),
            reasons=tuple(str(item) for item in value.get("reasons", ())),
            metric_receipt_ids=tuple(str(item) for item in value.get("metric_receipt_ids", ())),
            basis_fingerprints=tuple(str(item) for item in value.get("basis_fingerprints", ())),
            schema_version=str(value.get("schema_version", SCHEMA_VERSION)),
            status_id=str(value.get("status_id", "")),
        )


@dataclass(frozen=True)
class StateTransitionRequest:
    project_id: str
    before_snapshot_id: str
    action: str
    action_payload_hash: str
    idempotency_key: str
    process_identity: str
    read_set: Tuple[str, ...]
    write_set: Tuple[str, ...]
    created_at_utc: str

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "before_snapshot_id",
            "action",
            "idempotency_key",
            "process_identity",
        ):
            _require_text(getattr(self, name), name)
        _require_sha256(self.action_payload_hash, "action_payload_hash")
        _require_unique(self.read_set, "read_set")
        _require_unique(self.write_set, "write_set")
        _require_utc_timestamp(self.created_at_utc, "created_at_utc")

    @property
    def request_hash(self) -> str:
        return canonical_sha256(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "before_snapshot_id": self.before_snapshot_id,
            "action": self.action,
            "action_payload_hash": self.action_payload_hash,
            "idempotency_key": self.idempotency_key,
            "process_identity": self.process_identity,
            "read_set": list(self.read_set),
            "write_set": list(self.write_set),
            "created_at_utc": self.created_at_utc,
        }


@dataclass(frozen=True)
class StateTransitionReceipt:
    project_id: str
    before_snapshot_id: str
    after_snapshot_id: str | None
    action: str
    action_payload_hash: str
    idempotency_key: str
    request_hash: str
    process_identity: str
    read_set: Tuple[str, ...]
    write_set: Tuple[str, ...]
    produced_artifact_ids: Tuple[str, ...]
    metric_receipt_ids: Tuple[str, ...]
    residual_ids: Tuple[str, ...]
    status: TransitionStatus
    reasons: Tuple[str, ...]
    created_at_utc: str
    schema_version: str = SCHEMA_VERSION
    transition_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "before_snapshot_id",
            "action",
            "idempotency_key",
            "request_hash",
            "process_identity",
        ):
            _require_text(getattr(self, name), name)
        _require_sha256(self.request_hash, "request_hash")
        _require_sha256(self.action_payload_hash, "action_payload_hash")
        _require_unique(self.read_set, "read_set")
        _require_unique(self.write_set, "write_set")
        _require_unique(self.produced_artifact_ids, "produced_artifact_ids")
        _require_unique(self.metric_receipt_ids, "metric_receipt_ids")
        _require_unique(self.residual_ids, "residual_ids")
        if not self.reasons:
            raise ValueError("transition receipt requires reasons")
        _require_utc_timestamp(self.created_at_utc, "created_at_utc")
        if self.status is TransitionStatus.COMMITTED and not self.after_snapshot_id:
            raise ValueError("COMMITTED transition requires after_snapshot_id")
        if self.status is not TransitionStatus.COMMITTED and self.after_snapshot_id is not None:
            raise ValueError("non-COMMITTED transition cannot claim an after snapshot")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported engineering state schema: {self.schema_version}")
        expected = self.derived_transition_id
        if self.transition_id and self.transition_id != expected:
            raise ValueError("transition_id does not match canonical receipt content")
        if not self.transition_id:
            object.__setattr__(self, "transition_id", expected)

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "before_snapshot_id": self.before_snapshot_id,
            "after_snapshot_id": self.after_snapshot_id,
            "action": self.action,
            "action_payload_hash": self.action_payload_hash,
            "idempotency_key": self.idempotency_key,
            "request_hash": self.request_hash,
            "process_identity": self.process_identity,
            "read_set": list(self.read_set),
            "write_set": list(self.write_set),
            "produced_artifact_ids": list(self.produced_artifact_ids),
            "metric_receipt_ids": list(self.metric_receipt_ids),
            "residual_ids": list(self.residual_ids),
            "status": self.status.value,
            "reasons": list(self.reasons),
            "created_at_utc": self.created_at_utc,
        }

    @property
    def derived_transition_id(self) -> str:
        return "transition:" + canonical_sha256(self.identity_payload)

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "transition_id": self.transition_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "StateTransitionReceipt":
        return cls(
            project_id=str(value["project_id"]),
            before_snapshot_id=str(value["before_snapshot_id"]),
            after_snapshot_id=(None if value.get("after_snapshot_id") is None else str(value["after_snapshot_id"])),
            action=str(value["action"]),
            action_payload_hash=str(value["action_payload_hash"]),
            idempotency_key=str(value["idempotency_key"]),
            request_hash=str(value["request_hash"]),
            process_identity=str(value["process_identity"]),
            read_set=tuple(str(item) for item in value.get("read_set", ())),
            write_set=tuple(str(item) for item in value.get("write_set", ())),
            produced_artifact_ids=tuple(str(item) for item in value.get("produced_artifact_ids", ())),
            metric_receipt_ids=tuple(str(item) for item in value.get("metric_receipt_ids", ())),
            residual_ids=tuple(str(item) for item in value.get("residual_ids", ())),
            status=TransitionStatus(str(value["status"])),
            reasons=tuple(str(item) for item in value.get("reasons", ())),
            created_at_utc=str(value["created_at_utc"]),
            schema_version=str(value.get("schema_version", SCHEMA_VERSION)),
            transition_id=str(value.get("transition_id", "")),
        )


def status_from_saturation_vector(
    *,
    project_snapshot_id: str,
    target_id: str,
    fiber_id: str,
    saturation_report: object,
    required_routes: Iterable[str],
    covered_routes: Iterable[str],
    active_residual_ids: Iterable[str] = (),
    freshness_stale: bool = False,
    required_authority: int = 0,
    available_support_paths: int = 0,
    blocking_cut_ids: Iterable[str] = (),
    hard_gate_ids: Iterable[str] = (),
    next_action: NextActionClass = NextActionClass.CANNOT_CHECK,
    reasons: Iterable[str] = ("adapter_requires_explicit_controller_reason",),
    metric_receipt_ids: Iterable[str] = (),
    basis_fingerprints: Iterable[str] = (),
) -> EpistemicStatus:
    """Project the existing RAKL saturation-vector report into the shared read model.

    The adapter is intentionally structural/duck-typed so this module does not
    create an import cycle with the current saturation packages during the
    package refactor.  It expects the established report contract:
    ``axis_reports`` with ``axis``, ``flat``, ``recent_retained_novelty``,
    ``independent_flat_route_families`` and ``reopen_residuals``.
    """

    reports = tuple(getattr(saturation_report, "axis_reports"))
    axes: list[EpistemicAxisStatus] = []
    for report in reports:
        axis_object = getattr(report, "axis")
        axis = str(getattr(axis_object, "value", axis_object))
        axes.append(
            EpistemicAxisStatus(
                axis=axis,
                bounded_flat=bool(getattr(report, "flat")),
                recent_retained_novelty=int(getattr(report, "recent_retained_novelty")),
                independent_flat_routes=tuple(
                    str(item) for item in getattr(report, "independent_flat_route_families")
                ),
                reopen_residual_ids=tuple(str(item) for item in getattr(report, "reopen_residuals")),
            )
        )
    required = tuple(dict.fromkeys(str(item) for item in required_routes))
    covered = tuple(dict.fromkeys(str(item) for item in covered_routes))
    missing = tuple(item for item in required if item not in set(covered))
    return EpistemicStatus(
        project_snapshot_id=project_snapshot_id,
        target_id=target_id,
        fiber_id=fiber_id,
        axis_statuses=tuple(axes),
        required_routes=required,
        covered_routes=covered,
        missing_routes=missing,
        active_residual_ids=tuple(dict.fromkeys(str(item) for item in active_residual_ids)),
        freshness_stale=freshness_stale,
        required_authority=required_authority,
        available_support_paths=available_support_paths,
        blocking_cut_ids=tuple(dict.fromkeys(str(item) for item in blocking_cut_ids)),
        hard_gate_ids=tuple(dict.fromkeys(str(item) for item in hard_gate_ids)),
        next_action=next_action,
        reasons=tuple(dict.fromkeys(str(item) for item in reasons)),
        metric_receipt_ids=tuple(dict.fromkeys(str(item) for item in metric_receipt_ids)),
        basis_fingerprints=tuple(dict.fromkeys(str(item) for item in basis_fingerprints)),
    )
