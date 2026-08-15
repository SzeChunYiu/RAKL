"""Adapters that connect incumbent RAKL state to engineering closure contracts.

This module is intentionally projection-only.  It consumes existing saturation,
knowledge-acquisition, metric-gate and solver reports and binds them to an exact
``ProjectSnapshot``.  It does not create a second controller or grant authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence, Tuple

from .engineering_state import (
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
    canonical_sha256,
    status_from_saturation_vector,
)


def _value(item: object) -> str:
    value = getattr(item, "value", item)
    return str(value)


def _unique(items: Iterable[object]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(item) for item in items if str(item)))


@dataclass(frozen=True)
class IncumbentStateHeads:
    """Exact incumbent heads required to construct a coherent project snapshot."""

    project_id: str
    evidence_cutoff: str
    semantic_state_revision: str
    metric_ledger_head: str
    episode_store_head: str
    saturation_basis_ids: Tuple[str, ...]
    authority_projection_revision: str
    controller_epoch_id: str

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "evidence_cutoff",
            "semantic_state_revision",
            "metric_ledger_head",
            "episode_store_head",
            "authority_projection_revision",
            "controller_epoch_id",
        ):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if len(self.saturation_basis_ids) != len(set(self.saturation_basis_ids)):
            raise ValueError("saturation basis ids must be unique")


def project_snapshot_from_heads(
    heads: IncumbentStateHeads,
    *,
    created_at_utc: str,
    previous: ProjectSnapshot | None = None,
) -> ProjectSnapshot:
    if previous is not None and previous.project_id != heads.project_id:
        raise ValueError("previous snapshot belongs to a different project")
    return ProjectSnapshot(
        project_id=heads.project_id,
        sequence=0 if previous is None else previous.sequence + 1,
        previous_snapshot_id=None if previous is None else previous.snapshot_id,
        evidence_cutoff=heads.evidence_cutoff,
        semantic_state_revision=heads.semantic_state_revision,
        metric_ledger_head=heads.metric_ledger_head,
        episode_store_head=heads.episode_store_head,
        saturation_basis_ids=heads.saturation_basis_ids,
        authority_projection_revision=heads.authority_projection_revision,
        controller_epoch_id=heads.controller_epoch_id,
        created_at_utc=created_at_utc,
    )


class SolverViewFreshness(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class SnapshotBoundSolverView:
    """Disposable solver view compiled from one exact canonical snapshot."""

    project_snapshot_id: str
    problem_id: str
    target_id: str
    support_structure_id: str
    compiler_identity: str
    required_authority: int
    atom_ids: Tuple[str, ...]
    relation_ids: Tuple[str, ...] = ()
    chart_ids: Tuple[str, ...] = ()
    obstruction_ids: Tuple[str, ...] = ()
    source_evidence_ids: Tuple[str, ...] = ()
    view_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "project_snapshot_id",
            "problem_id",
            "target_id",
            "support_structure_id",
            "compiler_identity",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.required_authority < 0:
            raise ValueError("required_authority cannot be negative")
        if not self.atom_ids:
            raise ValueError("solver view requires at least one source atom")
        for name in (
            "atom_ids",
            "relation_ids",
            "chart_ids",
            "obstruction_ids",
            "source_evidence_ids",
        ):
            values = getattr(self, name)
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique")
        expected = "solver-view:" + canonical_sha256(self.identity_payload)
        if self.view_id and self.view_id != expected:
            raise ValueError("solver view id does not match content")
        if not self.view_id:
            object.__setattr__(self, "view_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "project_snapshot_id": self.project_snapshot_id,
            "problem_id": self.problem_id,
            "target_id": self.target_id,
            "support_structure_id": self.support_structure_id,
            "compiler_identity": self.compiler_identity,
            "required_authority": self.required_authority,
            "atom_ids": list(self.atom_ids),
            "relation_ids": list(self.relation_ids),
            "chart_ids": list(self.chart_ids),
            "obstruction_ids": list(self.obstruction_ids),
            "source_evidence_ids": list(self.source_evidence_ids),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "view_id": self.view_id}


def solver_view_freshness(
    view: SnapshotBoundSolverView,
    current_snapshot: ProjectSnapshot | None,
) -> SolverViewFreshness:
    if current_snapshot is None:
        return SolverViewFreshness.CANNOT_CHECK
    return (
        SolverViewFreshness.CURRENT
        if view.project_snapshot_id == current_snapshot.snapshot_id
        else SolverViewFreshness.STALE
    )


def next_action_from_incumbent(
    knowledge_assessment: object,
    *,
    solve_report: object | None = None,
) -> NextActionClass:
    """Map existing typed controller/solver terminals without scalarizing them."""

    decision = _value(getattr(knowledge_assessment, "decision", "CANNOT_CHECK"))
    direct = {
        "CONTINUE_SEARCH": NextActionClass.CONTINUE_SEARCH,
        "TARGETED_REFRESH_REQUIRED": NextActionClass.TARGETED_REFRESH_REQUIRED,
        "FRESHNESS_REFRESH_REQUIRED": NextActionClass.FRESHNESS_REFRESH_REQUIRED,
        "CANNOT_CHECK": NextActionClass.CANNOT_CHECK,
    }
    if decision in direct:
        return direct[decision]
    if decision != "PROCEED_OBJECT_WORK":
        return NextActionClass.CANNOT_CHECK
    if solve_report is None:
        return NextActionClass.COMPILE_SOLVER_VIEW

    outcome = _value(getattr(solve_report, "outcome", "CANNOT_CHECK"))
    if outcome == "REACHED":
        return NextActionClass.VERIFY_SOLUTION
    if outcome == "CUT":
        return NextActionClass.REPAIR_EPISTEMIC_CUT
    # UNREACHABLE_IN_PRINCIPLE is not automatically a knowledge gap: it may be a
    # representation/decomposition/operator issue.  Fail closed rather than reopening
    # literature globally without a typed diagnosis.
    return NextActionClass.CANNOT_CHECK


def _cut_ids(solve_report: object | None) -> tuple[str, ...]:
    if solve_report is None:
        return ()
    cut = getattr(solve_report, "cut", None)
    if cut is None:
        return ()
    elements = tuple(str(item) for item in getattr(cut, "elements", ()))
    if not elements:
        return ()
    return ("cut:" + canonical_sha256({"elements": list(elements)}),)


def epistemic_status_from_incumbent(
    *,
    snapshot: ProjectSnapshot,
    target_id: str,
    fiber_id: str,
    saturation_report: object,
    knowledge_assessment: object,
    active_residual_ids: Iterable[str] = (),
    required_authority: int = 0,
    support_path_count: int = 0,
    solve_report: object | None = None,
    hard_gates: Sequence[object] = (),
    metric_receipt_ids: Iterable[str] = (),
    basis_fingerprints: Iterable[str] = (),
    freshness_stale: bool | None = None,
) -> EpistemicStatus:
    covered = _unique(getattr(knowledge_assessment, "covered_route_families", ()))
    missing = _unique(getattr(knowledge_assessment, "missing_route_families", ()))
    required = _unique((*covered, *missing))

    reasons = list(str(item) for item in getattr(knowledge_assessment, "reasons", ()))
    if solve_report is not None:
        reasons.extend(str(item) for item in getattr(solve_report, "reasons", ()))
        outcome = _value(getattr(solve_report, "outcome", "CANNOT_CHECK"))
        reasons.append(f"solver_outcome:{outcome}")
    if not reasons:
        reasons.append("incumbent_adapter_no_reason_available")

    gate_ids = _unique(getattr(gate, "gate_id", "") for gate in hard_gates)
    return status_from_saturation_vector(
        project_snapshot_id=snapshot.snapshot_id,
        target_id=target_id,
        fiber_id=fiber_id,
        saturation_report=saturation_report,
        required_routes=required,
        covered_routes=covered,
        active_residual_ids=active_residual_ids,
        freshness_stale=(
            bool(freshness_stale)
            if freshness_stale is not None
            else bool(
                _value(getattr(knowledge_assessment, "decision", ""))
                == "FRESHNESS_REFRESH_REQUIRED"
            )
        ),
        required_authority=required_authority,
        available_support_paths=support_path_count,
        blocking_cut_ids=_cut_ids(solve_report),
        hard_gate_ids=gate_ids,
        next_action=next_action_from_incumbent(
            knowledge_assessment, solve_report=solve_report
        ),
        reasons=_unique(reasons),
        metric_receipt_ids=_unique(metric_receipt_ids),
        basis_fingerprints=_unique(basis_fingerprints),
    )
