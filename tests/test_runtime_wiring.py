"""Runtime wiring for engineering fibers E9 and E4.

E9 the problem-solving runtime must call the EpistemicStatus gate
E4 the incumbent decision heads must be wired into the runtime

The gate must be able to refuse and have that refusal survive into the output:
a gate whose refusal disappears is not a gate.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from rakl.project_runtime import RAKLProject


@dataclass
class _Status:
    project_snapshot_id: str = "snap-1"
    status_id: str = "st-1"


class _AvailableGate:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def current_status(self, *, project_id: str, target_id: str, fiber_id: str) -> _Status:
        self.calls.append((project_id, target_id, fiber_id))
        return _Status()


class _RefusingGate:
    def current_status(self, *, project_id: str, target_id: str, fiber_id: str):
        raise LookupError("no EpistemicStatus for current snapshot")


class _Heads:
    def next_action(self) -> str:
        return "SOLVE_CURRENT"


class _SilentHeads:
    next_action = None


@pytest.fixture()
def project(tmp_path):
    return RAKLProject.create(tmp_path, project_id="p1")


# --- E9 -----------------------------------------------------------------


def test_runtime_calls_the_epistemic_gate(project) -> None:
    gate = _AvailableGate()
    out = project.status(epistemic_service=gate, target_id="t1", fiber_id="f1")
    assert gate.calls == [("p1", "t1", "f1")]
    assert out["epistemic_gate"]["consulted"] is True
    assert out["epistemic_gate"]["available"] is True
    assert out["epistemic_gate"]["project_snapshot_id"] == "snap-1"


def test_a_refusing_gate_is_reported_not_swallowed(project) -> None:
    out = project.status(epistemic_service=_RefusingGate(), target_id="t1", fiber_id="f1")
    gate = out["epistemic_gate"]
    assert gate["consulted"] is True
    assert gate["available"] is False
    assert "no EpistemicStatus" in gate["reason"]


def test_status_without_a_service_is_unchanged(project) -> None:
    out = project.status()
    assert "epistemic_gate" not in out
    assert "decision_heads" not in out
    assert out["project_id"] == "p1"
    assert out["healthy"] is True


def test_the_gate_never_makes_the_project_claim_health_it_lacks(project) -> None:
    """A refusing gate must not flip healthy, and must not be hidden by it."""

    out = project.status(epistemic_service=_RefusingGate(), target_id="t", fiber_id="f")
    assert out["healthy"] is True  # payload health is a different question
    assert out["epistemic_gate"]["available"] is False  # and the refusal survives


# --- E4 -----------------------------------------------------------------


def test_decision_heads_are_wired_into_the_runtime(project) -> None:
    out = project.status(heads=_Heads())
    assert out["decision_heads"]["wired"] is True
    assert out["decision_heads"]["next_action"] == "SOLVE_CURRENT"


def test_silent_heads_report_no_action_rather_than_inventing_one(project) -> None:
    out = project.status(heads=_SilentHeads())
    assert out["decision_heads"]["next_action"] is None
    assert out["decision_heads"]["wired"] is False
    assert out["decision_heads"]["resolved_by"] == "none"


def test_the_runtime_grants_no_authority_through_the_heads(project) -> None:
    out = project.status(heads=_Heads())
    assert out["decision_heads"]["grants_scientific_authority"] is False


def test_a_callable_head_is_accepted(project) -> None:
    """The engineering layer supplies the projection as a module function.

    The first version duck-typed `.next_action` off the shipped
    IncumbentStateHeads, which has no such attribute, and reported `wired: True`
    while carrying nothing.
    """

    out = project.status(heads=lambda: "REPAIR_INTERFACE")
    assert out["decision_heads"]["wired"] is True
    assert out["decision_heads"]["resolved_by"] == "callable"
    assert out["decision_heads"]["next_action"] == "REPAIR_INTERFACE"


def test_real_incumbent_heads_do_not_falsely_report_wired(project) -> None:
    """Regression against the real object that exposed the defect."""

    from rakl.engineering_integration import IncumbentStateHeads

    heads = IncumbentStateHeads(
        project_id="p",
        evidence_cutoff="2026-08-15",
        semantic_state_revision="r",
        metric_ledger_head="m",
        episode_store_head="e",
        saturation_basis_ids=("b",),
        authority_projection_revision="a",
        controller_epoch_id="c",
    )
    out = project.status(heads=heads)
    assert out["decision_heads"]["wired"] is False
    assert out["decision_heads"]["next_action"] is None


def test_both_wirings_compose(project) -> None:
    out = project.status(
        epistemic_service=_AvailableGate(), target_id="t", fiber_id="f", heads=_Heads()
    )
    assert out["epistemic_gate"]["available"] is True
    assert out["decision_heads"]["next_action"] == "SOLVE_CURRENT"
