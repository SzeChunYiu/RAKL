from __future__ import annotations

import pytest

from rakl.context_compiler import (
    ContextCompileRequest,
    ContextCompileVerdict,
    ContextItem,
    compile_epistemic_context,
)
from rakl.context_efficiency import measure_context_efficiency


def _base_items():
    return (
        ContextItem(
            record_id="negative-history",
            token_cost=10,
            coverage_atoms=("negative_history",),
            fiber_ids=("spot",),
            mandatory=True,
        ),
        ContextItem(
            record_id="target-a",
            token_cost=20,
            coverage_atoms=("A",),
            fiber_ids=("spot",),
        ),
        ContextItem(
            record_id="target-b",
            token_cost=20,
            coverage_atoms=("B",),
            fiber_ids=("spot",),
        ),
    )


def _compile(items):
    return compile_epistemic_context(
        items,
        ContextCompileRequest(
            budget_tokens=100,
            target_fibers=("spot",),
            required_coverage_atoms=("negative_history", "A", "B"),
        ),
    )


def test_archive_scale_invariance_under_unrelated_fiber_growth():
    base = _base_items()
    reference = _compile(base)
    assert reference.verdict is ContextCompileVerdict.COMPILED
    assert reference.selected_record_ids == ("negative-history", "target-a", "target-b")
    assert reference.used_tokens == 50

    for count in (10, 100, 1000):
        distractors = tuple(
            ContextItem(
                record_id=f"other-{i:04d}",
                token_cost=1,
                coverage_atoms=(f"other_atom_{i}",),
                fiber_ids=("unrelated",),
            )
            for i in range(count)
        )
        report = _compile(base + distractors)
        assert report.verdict is ContextCompileVerdict.COMPILED
        assert report.selected_record_ids == reference.selected_record_ids
        assert report.used_tokens == reference.used_tokens
        efficiency = measure_context_efficiency(
            base + distractors,
            report,
            required_coverage_atoms=("negative_history", "A", "B"),
        )
        assert efficiency.mandatory_recall == 1.0
        assert efficiency.required_coverage_recall == 1.0
        assert efficiency.zero_marginal_selected_optional_ids == ()
        assert efficiency.active_tokens == 50


def test_same_fiber_redundant_growth_does_not_pad_prompt():
    redundant = tuple(
        ContextItem(
            record_id=f"redundant-{i:04d}",
            token_cost=1,
            coverage_atoms=("A",),
            fiber_ids=("spot",),
        )
        for i in range(100)
    )
    report = _compile(_base_items() + redundant)
    assert report.verdict is ContextCompileVerdict.COMPILED
    # One cheap redundant A-view may win instead of target-a, but once A is
    # covered the remaining redundant records cannot be filler-selected.
    selected_redundant = [rid for rid in report.selected_record_ids if rid.startswith("redundant-")]
    assert len(selected_redundant) == 1
    efficiency = measure_context_efficiency(
        _base_items() + redundant,
        report,
        required_coverage_atoms=("negative_history", "A", "B"),
    )
    assert efficiency.zero_marginal_selected_optional_ids == ()
    assert efficiency.required_coverage_recall == 1.0


def test_new_required_same_fiber_coverage_grows_context_only_for_registered_need():
    extra = ContextItem(
        record_id="target-c",
        token_cost=15,
        coverage_atoms=("C",),
        fiber_ids=("spot",),
    )
    items = _base_items() + (extra,)
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(
            budget_tokens=100,
            target_fibers=("spot",),
            required_coverage_atoms=("negative_history", "A", "B", "C"),
        ),
    )
    assert report.verdict is ContextCompileVerdict.COMPILED
    assert "target-c" in report.selected_record_ids
    assert report.used_tokens == 65


def test_mandatory_overflow_fails_closed():
    items = (
        ContextItem("m1", 60, mandatory=True, coverage_atoms=("x",)),
        ContextItem("m2", 60, mandatory=True, coverage_atoms=("y",)),
    )
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=100))
    assert report.verdict is ContextCompileVerdict.CANNOT_COMPILE
    assert "mandatory_over_budget" in report.reasons


def test_lossy_view_without_rehydration_lineage_is_invalid():
    with pytest.raises(ValueError, match="source_record_ids"):
        ContextItem(
            record_id="lossy",
            token_cost=10,
            compact_view=True,
            lossy=True,
            erasure_tags=("detail",),
        )


def test_efficiency_report_is_engineering_only():
    items = _base_items()
    report = _compile(items)
    efficiency = measure_context_efficiency(
        items,
        report,
        required_coverage_atoms=("negative_history", "A", "B"),
    )
    assert efficiency.grants_scientific_authority is False
    assert efficiency.archive_context_ratio == 1.0
    assert efficiency.active_budget_ratio == 0.5
