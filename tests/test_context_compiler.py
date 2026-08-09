import random

import pytest

from rakl.context_compiler import (
    ContextCompileRequest,
    ContextCompileVerdict,
    ContextItem,
    compile_epistemic_context,
)


def test_critical_refutation_survives_noise_and_noise_is_not_filler_selected():
    items = [
        ContextItem(
            record_id="critical-refutation",
            token_cost=3,
            coverage_atoms=("falsifier",),
            fiber_ids=("mechanism",),
            mandatory=True,
        )
    ]
    items.extend(
        ContextItem(
            record_id=f"noise-{i:03d}",
            token_cost=1,
            coverage_atoms=(),
            fiber_ids=("mechanism",),
        )
        for i in range(100)
    )
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(
            budget_tokens=20,
            target_fibers=("mechanism",),
            required_coverage_atoms=("falsifier",),
        ),
    )
    assert report.verdict == ContextCompileVerdict.COMPILED
    assert report.selected_record_ids == ("critical-refutation",)
    assert report.used_tokens == 3


def test_mandatory_over_budget_fails_closed_instead_of_truncating():
    items = [
        ContextItem("a", 4, ("scope",), mandatory=True),
        ContextItem("b", 3, ("negative",), mandatory=True),
    ]
    report = compile_epistemic_context(items, ContextCompileRequest(budget_tokens=5))
    assert report.verdict == ContextCompileVerdict.CANNOT_COMPILE
    assert report.reasons == ("mandatory_over_budget",)
    assert report.selected_record_ids == ("a", "b")
    assert report.used_tokens == 7


def test_duplicate_semantic_coverage_is_not_double_selected():
    items = [
        ContextItem("claim-a", 4, ("same-semantic-object",), fiber_ids=("claim",)),
        ContextItem("claim-b", 4, ("same-semantic-object",), fiber_ids=("claim",)),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(budget_tokens=12, target_fibers=("claim",)),
    )
    assert report.verdict == ContextCompileVerdict.COMPILED
    assert len(report.selected_record_ids) == 1
    assert report.selected_record_ids == ("claim-a",)


def test_both_sides_of_registered_contradiction_can_be_mandatory():
    items = [
        ContextItem("side-a", 5, ("contradiction:A",), mandatory=True),
        ContextItem("side-b", 5, ("contradiction:B",), mandatory=True),
        ContextItem("commentary", 4, ("commentary",)),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(
            budget_tokens=14,
            required_coverage_atoms=("contradiction:A", "contradiction:B"),
        ),
    )
    assert report.verdict == ContextCompileVerdict.COMPILED
    assert set(report.selected_record_ids) >= {"side-a", "side-b"}


def test_mechanism_authority_prerequisites_are_fail_closed_when_not_materialized():
    items = [
        ContextItem("mechanism", 3, ("mechanism-claim",), fiber_ids=("mechanism",)),
        ContextItem("ancestry", 8, ("mechanism-ancestry",), fiber_ids=("mechanism",)),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(
            budget_tokens=5,
            target_fibers=("mechanism",),
            required_coverage_atoms=("mechanism-claim", "mechanism-ancestry"),
        ),
    )
    assert report.verdict == ContextCompileVerdict.CANNOT_COMPILE
    assert report.missing_required_atoms == ("mechanism-ancestry",)
    assert "required_coverage_not_materialized" in report.reasons


def test_query_specific_fiber_excludes_unrelated_high_coverage_items():
    items = [
        ContextItem("target", 4, ("target-facet",), fiber_ids=("fiber-A",)),
        ContextItem(
            "unrelated",
            1,
            ("x1", "x2", "x3", "x4", "x5"),
            fiber_ids=("fiber-B",),
        ),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(budget_tokens=10, target_fibers=("fiber-A",)),
    )
    assert report.selected_record_ids == ("target",)
    assert "unrelated" in report.omitted_record_ids


def test_compact_views_require_rehydration_and_lossy_erasure_metadata():
    with pytest.raises(ValueError, match="source_record_ids"):
        ContextItem("bad-summary", 2, compact_view=True)
    with pytest.raises(ValueError, match="erasure_tags"):
        ContextItem(
            "bad-lossy-summary",
            2,
            compact_view=True,
            lossy=True,
            source_record_ids=("raw-1",),
        )

    summary = ContextItem(
        "summary",
        2,
        ("overview",),
        compact_view=True,
        lossy=True,
        source_record_ids=("raw-1", "raw-2"),
        erasure_tags=("exact-numeric-detail",),
    )
    report = compile_epistemic_context([summary], ContextCompileRequest(budget_tokens=4))
    assert report.verdict == ContextCompileVerdict.COMPILED
    assert report.rehydration_record_ids == ("raw-1", "raw-2")


def test_negative_history_replay_guard_is_kept_even_outside_target_fiber_when_mandatory():
    items = [
        ContextItem(
            "old-falsifier",
            3,
            ("negative-history",),
            fiber_ids=("old-fiber",),
            mandatory=True,
        ),
        ContextItem("new-proposal", 3, ("proposal",), fiber_ids=("new-fiber",)),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(
            budget_tokens=8,
            target_fibers=("new-fiber",),
            required_coverage_atoms=("negative-history", "proposal"),
        ),
    )
    assert report.verdict == ContextCompileVerdict.COMPILED
    assert set(report.selected_record_ids) == {"old-falsifier", "new-proposal"}


def test_selection_is_deterministic_under_input_permutation():
    base = [
        ContextItem("a", 2, ("x",), fiber_ids=("f",)),
        ContextItem("b", 2, ("y",), fiber_ids=("f",)),
        ContextItem("c", 2, ("z",), fiber_ids=("f",)),
    ]
    expected = compile_epistemic_context(
        base,
        ContextCompileRequest(budget_tokens=4, target_fibers=("f",)),
    ).selected_record_ids
    for seed in range(20):
        shuffled = list(base)
        random.Random(seed).shuffle(shuffled)
        actual = compile_epistemic_context(
            shuffled,
            ContextCompileRequest(budget_tokens=4, target_fibers=("f",)),
        ).selected_record_ids
        assert actual == expected


def test_budget_is_spent_by_marginal_weighted_coverage_per_token():
    items = [
        ContextItem("expensive", 6, ("a", "b", "c"), fiber_ids=("f",)),
        ContextItem("cheap-a", 2, ("a", "d"), fiber_ids=("f",)),
        ContextItem("cheap-b", 2, ("b", "e"), fiber_ids=("f",)),
        ContextItem("cheap-c", 2, ("c", "f"), fiber_ids=("f",)),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(budget_tokens=6, target_fibers=("f",)),
    )
    assert report.selected_record_ids == ("cheap-a", "cheap-b", "cheap-c")
    assert set(report.covered_atoms) == {"a", "b", "c", "d", "e", "f"}


def test_empty_relevant_set_does_not_add_filler():
    items = [
        ContextItem("other", 2, ("other",), fiber_ids=("other-fiber",)),
    ]
    report = compile_epistemic_context(
        items,
        ContextCompileRequest(budget_tokens=8, target_fibers=("target-fiber",)),
    )
    assert report.verdict == ContextCompileVerdict.COMPILED
    assert report.selected_record_ids == ()
    assert report.used_tokens == 0
