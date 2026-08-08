from rakl.saturation import ResearchRound, SaturationState, SaturationTracker


def rr(round_id, route, context, objects=(), *, independent=False):
    return ResearchRound.from_objects(
        round_id,
        route,
        context,
        objects,
        independent=independent,
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


def test_saturation_requires_same_context_and_independent_flat_rounds():
    routes = frozenset({"FOUNDATIONAL_EXACT", "FAILURE_COUNTEREXAMPLE"})
    tracker = SaturationTracker(routes)

    tracker.record(rr("r1", "FOUNDATIONAL_EXACT", "ctx-a", {"M1"}))
    tracker.record(rr("r2", "FAILURE_COUNTEREXAMPLE", "ctx-a", {"M1"}))
    tracker.record(rr("r3", "FOUNDATIONAL_EXACT", "ctx-a", {"M1"}))
    tracker.record(rr("r4", "FAILURE_COUNTEREXAMPLE", "ctx-a", {"M1"}))
    tracker.record(rr("r5", "FOUNDATIONAL_EXACT", "ctx-a", {"M1"}))
    assert tracker.state == SaturationState.SAME_CONTEXT_PLATEAU

    tracker.record(rr("i1", "FOUNDATIONAL_EXACT", "ctx-i1", {"M1"}, independent=True))
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_1
    tracker.record(rr("i2", "FAILURE_COUNTEREXAMPLE", "ctx-i2", {"M1"}, independent=True))
    assert tracker.state == SaturationState.INDEPENDENT_FLAT_2
    tracker.record(rr("i3", "FOUNDATIONAL_EXACT", "ctx-i3", {"M1"}, independent=True))
    assert tracker.state == SaturationState.SATURATED_SCOPED


def test_new_semantic_object_resets_flat_sequence():
    tracker = SaturationTracker(frozenset({"A"}), same_context_flat_required=1, independent_flat_required=1)
    tracker.record(rr("r1", "A", "ctx", {"M1"}))
    tracker.record(rr("r2", "A", "ctx", {"M1"}))
    tracker.record(rr("i1", "A", "ind", {"M1"}, independent=True))
    assert tracker.state == SaturationState.SATURATED_SCOPED

    tracker.record(rr("i2", "A", "ind2", {"M1", "M2"}, independent=True))
    assert tracker.state == SaturationState.ACTIVE_NON_FLAT
    assert "M2" in tracker.seen_semantic_objects


def test_native_residual_reopens_saturated_fiber():
    tracker = SaturationTracker(frozenset({"A"}), same_context_flat_required=1, independent_flat_required=1)
    tracker.record(rr("r1", "A", "ctx", {"M1"}))
    tracker.record(rr("r2", "A", "ctx", {"M1"}))
    tracker.record(rr("i1", "A", "ind", {"M1"}, independent=True))
    assert tracker.state == SaturationState.SATURATED_SCOPED
    tracker.reopen("new native tail residual")
    assert tracker.state == SaturationState.REOPENED_BY_RESIDUAL


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
