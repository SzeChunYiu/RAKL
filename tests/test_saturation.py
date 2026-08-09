from rakl.saturation import ResearchRound, SaturationState, SaturationTracker


def rr(
    round_id,
    route,
    context,
    objects=(),
    *,
    independent=False,
    lineage=(),
    lineage_complete=False,
):
    return ResearchRound.from_objects(
        round_id,
        route,
        context,
        objects,
        independent=independent,
        evidence_lineage=lineage,
        lineage_complete=lineage_complete,
    )


def independent_rr(round_id, route, context, objects=(), *, lineage):
    return rr(
        round_id,
        route,
        context,
        objects,
        independent=True,
        lineage=lineage,
        lineage_complete=True,
    )


def test_nonflat_round_prevents_false_saturation():
    tracker = SaturationTracker(frozenset({"FOUNDATIONAL_EXACT"}))
    recorded = tracker.record(rr("r1", "FOUNDATIONAL_EXACT", "ctx", {"M1"}))
    assert not recorded.flat
    assert tracker.state == SaturationState.ACTIVE_NON_FLAT


def test_required_route_coverage_precedes_plateau():
    tracker = SaturationTracker(
        frozenset({"FOUNDATIONAL_EXACT", "FAILURE_COUNTEREXAMPLE"}),
        same_context_flat_required=1,
    )
    tracker.record(rr("r1", "FOUNDATIONAL_EXACT", "ctx", {"M1"}))
    tracker.record(rr("r2", "FOUNDATIONAL_EXACT", "ctx", {"M1"}))
    assert tracker.state == SaturationState.ROUTE_LOCAL_FLAT
    assert tracker.missing_routes == frozenset({"FAILURE_COUNTEREXAMPLE"})


def test_saturation_requires_same_context_and_lineage_independent_flat_rounds():
    routes = frozenset({"FOUNDATIONAL_EXACT", "FAILURE_COUNTEREXAMPLE"})
    tracker = SaturationTracker(routes)

    tracker.record(rr("r1", "FOUNDATIONAL_EXACT", "ctx-a", {"M1"}))
    tracker.record(rr("r2", "FAILURE_COUNTEREXAMPLE", "ctx-a", {"M1"}))
    tracker.record(rr("r3", "FOUNDATIONAL_EXACT", "ctx-a", {"M1"}))
    tracker.record(rr("r4", "FAILURE_COUNTEREXAMPLE", "ctx-a", {"M1"}))
    tracker.record(rr("r5", "FOUNDATIONAL_EXACT", "ctx-a", {"M1"}))
    assert tracker.state == SaturationState.SAME_CONTEXT_PLATEAU

    tracker.record(independent_rr("i1", "FOUNDATIONAL_EXACT", "ctx-i1", {"M1"}, lineage={"D1"}))
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_1
    tracker.record(independent_rr("i2", "FAILURE_COUNTEREXAMPLE", "ctx-i2", {"M1"}, lineage={"D2"}))
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_2
    tracker.record(independent_rr("i3", "FOUNDATIONAL_EXACT", "ctx-i3", {"M1"}, lineage={"D3"}))
    assert tracker.state == SaturationState.SATURATED_SCOPED


def test_new_semantic_object_resets_flat_sequence():
    tracker = SaturationTracker(frozenset({"A"}), same_context_flat_required=1, independent_flat_required=1)
    tracker.record(rr("r1", "A", "ctx", {"M1"}))
    tracker.record(rr("r2", "A", "ctx", {"M1"}))
    tracker.record(independent_rr("i1", "A", "ind", {"M1"}, lineage={"D1"}))
    assert tracker.state == SaturationState.SATURATED_SCOPED

    tracker.record(independent_rr("i2", "A", "ind2", {"M1", "M2"}, lineage={"D2"}))
    assert tracker.state == SaturationState.ACTIVE_NON_FLAT
    assert "M2" in tracker.seen_semantic_objects


def test_native_residual_reopens_saturated_fiber():
    tracker = SaturationTracker(frozenset({"A"}), same_context_flat_required=1, independent_flat_required=1)
    tracker.record(rr("r1", "A", "ctx", {"M1"}))
    tracker.record(rr("r2", "A", "ctx", {"M1"}))
    tracker.record(independent_rr("i1", "A", "ind", {"M1"}, lineage={"D1"}))
    assert tracker.state == SaturationState.SATURATED_SCOPED
    tracker.reopen("new native tail residual")
    assert tracker.state == SaturationState.REOPENED_BY_RESIDUAL


def test_shared_dataset_triplicate_cannot_fake_three_independent_rounds():
    tracker = SaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=3,
    )
    tracker.record(rr("seed", "A", "ctx", {"M1"}))
    tracker.record(rr("flat", "A", "ctx", {"M1"}))
    for idx in range(3):
        tracker.record(
            independent_rr(
                f"i{idx}",
                "A",
                f"ctx-i{idx}",
                {"M1"},
                lineage={"dataset:shared"},
            )
        )

    diagnostic = tracker.independence_diagnostic()
    assert diagnostic["declared_process_independent_flat_rounds"] == 3
    assert diagnostic["conservative_full_independent_rounds"] == 1
    assert diagnostic["status"] == "DEPENDENCE_IDENTIFIED"
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_1


def test_three_disjoint_complete_lineages_receive_three_full_credits():
    tracker = SaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=3,
    )
    tracker.record(rr("seed", "A", "ctx", {"M1"}))
    tracker.record(rr("flat", "A", "ctx", {"M1"}))
    for idx, lineage in enumerate(({"D1"}, {"D2"}, {"D3"})):
        tracker.record(independent_rr(f"i{idx}", "A", f"ctx-{idx}", {"M1"}, lineage=lineage))

    diagnostic = tracker.independence_diagnostic()
    assert diagnostic["status"] == "FULL_LINEAGE_DISJOINT"
    assert diagnostic["conservative_full_independent_rounds"] == 3
    assert tracker.state == SaturationState.SATURATED_SCOPED


def test_partial_overlap_preserves_two_independent_branches_instead_of_forcing_zero_or_three():
    tracker = SaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=3,
    )
    tracker.record(rr("seed", "A", "ctx", {"M1"}))
    tracker.record(rr("flat", "A", "ctx", {"M1"}))
    tracker.record(independent_rr("A", "A", "ctx-a", {"M1"}, lineage={"D1"}))
    tracker.record(independent_rr("B", "A", "ctx-b", {"M1"}, lineage={"D1", "D2"}))
    tracker.record(independent_rr("C", "A", "ctx-c", {"M1"}, lineage={"D3"}))

    diagnostic = tracker.independence_diagnostic()
    assert diagnostic["status"] == "DEPENDENCE_IDENTIFIED"
    assert diagnostic["conservative_full_independent_rounds"] == 2
    assert set(diagnostic["credited_round_ids"]) in ({"A", "C"}, {"B", "C"})
    assert diagnostic["overlap_pairs"] == [
        {"left": "A", "right": "B", "shared_lineage": ["D1"]}
    ]
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_2


def test_unknown_lineage_is_partial_identification_not_full_independence():
    tracker = SaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=1,
    )
    tracker.record(rr("seed", "A", "ctx", {"M1"}))
    tracker.record(rr("flat", "A", "ctx", {"M1"}))
    tracker.record(rr("i1", "A", "ctx-i", {"M1"}, independent=True))

    diagnostic = tracker.independence_diagnostic()
    assert diagnostic["status"] == "PARTIALLY_IDENTIFIED_LINEAGE"
    assert diagnostic["unknown_or_incomplete_lineage_rounds"] == ["i1"]
    assert diagnostic["conservative_full_independent_rounds"] == 0
    assert tracker.state == SaturationState.SAME_CONTEXT_PLATEAU


def test_complete_lineage_requires_nonempty_canonical_ancestry():
    try:
        rr("bad", "A", "ctx", {"M1"}, independent=True, lineage_complete=True)
    except ValueError as exc:
        assert "lineage_complete" in str(exc)
    else:
        raise AssertionError("empty complete lineage should be rejected")


def test_large_lineage_collection_uses_conservative_lower_bound_not_false_exactness():
    tracker = SaturationTracker(
        frozenset({"A"}),
        same_context_flat_required=1,
        independent_flat_required=3,
        lineage_exact_limit=2,
    )
    tracker.record(rr("seed", "A", "ctx", {"M1"}))
    tracker.record(rr("flat", "A", "ctx", {"M1"}))
    tracker.record(independent_rr("i1", "A", "c1", {"M1"}, lineage={"D1"}))
    tracker.record(independent_rr("i2", "A", "c2", {"M1"}, lineage={"D2"}))
    tracker.record(independent_rr("i3", "A", "c3", {"M1"}, lineage={"D3"}))

    diagnostic = tracker.independence_diagnostic()
    assert diagnostic["count_method"] == "greedy_lower_bound"
    assert diagnostic["exact_count"] is False
    assert diagnostic["conservative_full_independent_rounds"] == 3


def test_unseen_mass_is_explicitly_diagnostic_only():
    tracker = SaturationTracker(frozenset({"A"}))
    tracker.record(rr("r1", "A", "ctx", {"M1", "M2"}))
    tracker.record(rr("r2", "A", "ctx", {"M1", "M3"}))
    result = tracker.unseen_mass_diagnostic()
    assert result["diagnostic_only"] is True
    assert result["adaptive_non_iid_warning"] is True
    assert result["observed_semantic_objects"] == 3
    assert result["singletons_f1"] == 2
    assert result["doubletons_f2"] == 1
