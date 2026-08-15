"""H30: a working set with zero context because the budget excluded everything is CANNOT_COMPILE,
never a compiled-empty packet. Both directions, at the compiler and through RAKLProject."""

from __future__ import annotations

from rakl.context_compiler import (
    ContextCompileRequest, ContextCompileVerdict, ContextItem, compile_epistemic_context,
)
from rakl.project_runtime import RAKLProject, TaskPacketVerdict


def test_budget_that_excludes_all_relevant_context_is_cannot_compile() -> None:
    items = [ContextItem(f"r{i}", 400, (f"a{i}",), fiber_ids=("f",)) for i in range(30)]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=5, target_fibers=("f",)))
    assert report.verdict is ContextCompileVerdict.CANNOT_COMPILE
    assert report.reasons == ("context_over_budget",)
    assert report.selected_record_ids == ()
    assert len(report.omitted_record_ids) == 30


def test_mandatory_path_is_unchanged() -> None:
    items = [ContextItem(f"m{i}", 400, (f"a{i}",), fiber_ids=("f",), mandatory=True) for i in range(5)]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=5, target_fibers=("f",)))
    assert report.verdict is ContextCompileVerdict.CANNOT_COMPILE
    assert report.reasons == ("mandatory_over_budget",)


def test_records_that_fit_are_compiled() -> None:
    items = [ContextItem(f"r{i}", 10, (f"a{i}",), fiber_ids=("f",)) for i in range(3)]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=100, target_fibers=("f",)))
    assert report.verdict is ContextCompileVerdict.COMPILED
    assert len(report.selected_record_ids) == 3
    assert report.reasons == ()


def test_partial_fit_is_compiled_not_over_budget() -> None:
    """Some context fits: that is normal selection, not a capacity refusal."""
    items = [ContextItem("small", 4, ("a",), fiber_ids=("f",)), ContextItem("big", 400, ("b",), fiber_ids=("f",))]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=5, target_fibers=("f",)))
    assert report.verdict is ContextCompileVerdict.COMPILED
    assert report.selected_record_ids == ("small",)


def test_nothing_relevant_stays_compiled_empty_not_over_budget() -> None:
    """No relevant context is an honest empty working set; it is not 'over budget'."""
    items = [ContextItem("other", 2, ("o",), fiber_ids=("other-fiber",))]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=8, target_fibers=("f",)))
    assert report.verdict is ContextCompileVerdict.COMPILED
    assert report.selected_record_ids == () and report.reasons == ()


def test_zero_marginal_candidates_are_not_over_budget() -> None:
    """Candidates that carry no coverage value cannot be 'excluded by budget'."""
    items = [ContextItem("nocov", 400, (), fiber_ids=("f",))]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=5, target_fibers=("f",)))
    assert report.verdict is ContextCompileVerdict.COMPILED


def test_project_runtime_packet_is_not_ready_with_zero_context(tmp_path) -> None:
    proj = RAKLProject.create(tmp_path / "proj", project_id="p")
    for i in range(30):
        proj.ingest_bytes(record_id=f"r{i}", payload=(f"record {i} " * 200).encode(), token_cost=400,
                          fiber_ids=("f",), coverage_atoms=(f"a{i}",))
    rep = proj.compile_task_packet(operation="SOLVE", question="q", budget_tokens=5, target_fibers=("f",))
    assert rep.verdict is TaskPacketVerdict.CANNOT_COMPILE
    assert "context_over_budget" in rep.issues
    assert rep.packet is None or not rep.packet.get("selected_records")


def test_project_runtime_packet_is_ready_when_context_fits(tmp_path) -> None:
    proj = RAKLProject.create(tmp_path / "proj", project_id="p")
    for i in range(3):
        proj.ingest_bytes(record_id=f"r{i}", payload=b"small", token_cost=10, fiber_ids=("f",), coverage_atoms=(f"a{i}",))
    rep = proj.compile_task_packet(operation="SOLVE", question="q", budget_tokens=100, target_fibers=("f",))
    assert rep.verdict is TaskPacketVerdict.READY
    assert len(rep.compile_report.selected_record_ids) == 3
