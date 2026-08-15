from dataclasses import dataclass
from enum import Enum

from rakl.engineering_integration import (
    IncumbentStateHeads,
    SnapshotBoundSolverView,
    SolverViewFreshness,
    epistemic_status_from_incumbent,
    next_action_from_incumbent,
    project_snapshot_from_heads,
    solver_view_freshness,
)
from rakl.engineering_state import NextActionClass


class Axis(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"


@dataclass(frozen=True)
class AxisReport:
    axis: Axis
    flat: bool
    independent_flat_route_families: tuple[str, ...]
    recent_retained_novelty: int
    reopen_residuals: tuple[str, ...]


@dataclass(frozen=True)
class SaturationReport:
    axis_reports: tuple[AxisReport, ...]


class Decision(str, Enum):
    CONTINUE_SEARCH = "CONTINUE_SEARCH"
    PROCEED_OBJECT_WORK = "PROCEED_OBJECT_WORK"
    TARGETED_REFRESH_REQUIRED = "TARGETED_REFRESH_REQUIRED"
    FRESHNESS_REFRESH_REQUIRED = "FRESHNESS_REFRESH_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class KnowledgeAssessment:
    decision: Decision
    reasons: tuple[str, ...]
    covered_route_families: tuple[str, ...]
    missing_route_families: tuple[str, ...]


class Outcome(str, Enum):
    REACHED = "REACHED"
    CUT = "CUT"
    UNREACHABLE_IN_PRINCIPLE = "UNREACHABLE_IN_PRINCIPLE"


@dataclass(frozen=True)
class Cut:
    elements: tuple[str, ...]


@dataclass(frozen=True)
class SolveReport:
    outcome: Outcome
    cut: Cut | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Gate:
    gate_id: str


def heads():
    return IncumbentStateHeads(
        project_id="project:demo",
        evidence_cutoff="evidence:head",
        semantic_state_revision="semantic:head",
        metric_ledger_head="metric:head",
        episode_store_head="episode:head",
        saturation_basis_ids=("basis:knowledge",),
        authority_projection_revision="authority:head",
        controller_epoch_id="epoch:1",
    )


def test_snapshot_adapter_chains_exact_heads():
    s0 = project_snapshot_from_heads(heads(), created_at_utc="2026-08-15T15:00:00+00:00")
    s1 = project_snapshot_from_heads(heads(), created_at_utc="2026-08-15T15:01:00+00:00", previous=s0)
    assert s1.sequence == 1
    assert s1.previous_snapshot_id == s0.snapshot_id
    assert s1.metric_ledger_head == "metric:head"


def test_knowledge_decision_and_solver_terminal_map_noncompensatorily():
    base = KnowledgeAssessment(Decision.PROCEED_OBJECT_WORK, ("flat",), ("R1",), ())
    assert next_action_from_incumbent(base) is NextActionClass.COMPILE_SOLVER_VIEW
    assert next_action_from_incumbent(base, solve_report=SolveReport(Outcome.REACHED)) is NextActionClass.VERIFY_SOLUTION
    assert next_action_from_incumbent(base, solve_report=SolveReport(Outcome.CUT, Cut(("x->y",)))) is NextActionClass.REPAIR_EPISTEMIC_CUT
    assert next_action_from_incumbent(base, solve_report=SolveReport(Outcome.UNREACHABLE_IN_PRINCIPLE)) is NextActionClass.CANNOT_CHECK


def test_epistemic_status_combines_real_controller_solver_and_gate_shapes():
    snapshot = project_snapshot_from_heads(heads(), created_at_utc="2026-08-15T15:00:00+00:00")
    assessment = KnowledgeAssessment(
        Decision.PROCEED_OBJECT_WORK,
        ("bounded_knowledge_saturation_established",),
        ("FOUNDATIONAL", "ALIEN"),
        (),
    )
    saturation = SaturationReport((AxisReport(Axis.KNOWLEDGE, True, ("FOUNDATIONAL", "ALIEN"), 0, ()),))
    status = epistemic_status_from_incumbent(
        snapshot=snapshot,
        target_id="target:qoi",
        fiber_id="fiber:knowledge",
        saturation_report=saturation,
        knowledge_assessment=assessment,
        solve_report=SolveReport(Outcome.CUT, Cut(("edge:a->b",)), ("no_licensed_route",)),
        hard_gates=(Gate("bounded_saturation_gate"),),
        metric_receipt_ids=("metric:sat",),
        basis_fingerprints=("basis:fingerprint",),
    )
    assert status.next_action is NextActionClass.REPAIR_EPISTEMIC_CUT
    assert status.blocking_cut_ids[0].startswith("cut:")
    assert status.required_routes == ("FOUNDATIONAL", "ALIEN")
    assert status.hard_gate_ids == ("bounded_saturation_gate",)


def test_snapshot_bound_solver_view_becomes_stale_on_head_change():
    s0 = project_snapshot_from_heads(heads(), created_at_utc="2026-08-15T15:00:00+00:00")
    s1 = project_snapshot_from_heads(heads(), created_at_utc="2026-08-15T15:01:00+00:00", previous=s0)
    view = SnapshotBoundSolverView(
        project_snapshot_id=s0.snapshot_id,
        problem_id="problem:1",
        target_id="target:1",
        support_structure_id="support:1",
        compiler_identity="compiler:sha",
        required_authority=1,
        atom_ids=("a", "b"),
        relation_ids=("a->b",),
    )
    assert solver_view_freshness(view, s0) is SolverViewFreshness.CURRENT
    assert solver_view_freshness(view, s1) is SolverViewFreshness.STALE


def test_explicit_freshness_survives_higher_priority_residual_decision():
    snapshot = project_snapshot_from_heads(
        heads(), created_at_utc="2026-08-15T15:00:00+00:00"
    )
    assessment = KnowledgeAssessment(
        Decision.TARGETED_REFRESH_REQUIRED,
        ("native_knowledge_residual_reopens_fiber",),
        ("R1",),
        (),
    )
    saturation = SaturationReport(
        (AxisReport(Axis.KNOWLEDGE, False, (), 0, ("residual:1",)),)
    )
    status = epistemic_status_from_incumbent(
        snapshot=snapshot,
        target_id="target:q",
        fiber_id="fiber:k",
        saturation_report=saturation,
        knowledge_assessment=assessment,
        active_residual_ids=("residual:1",),
        freshness_stale=True,
    )
    assert status.freshness_stale is True
    assert status.next_action is NextActionClass.TARGETED_REFRESH_REQUIRED
