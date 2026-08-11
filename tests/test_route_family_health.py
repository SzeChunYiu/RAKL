"""Freeze tests for issue #135 longitudinal route-family health.

All histories below are hand-written FIXTURE / SYNTHETIC controls.  No real
lineage was replayed and no route was classified for the record.
"""

from __future__ import annotations

import dataclasses

import pytest

from rakl.route_family_health import (
    DEFAULT_CONTINUITY_POLICY,
    DEFAULT_NON_COMPENSATORY,
    ChronologyKind,
    ChronologyRecord,
    ContinuityCoordinate,
    ContinuityPolicy,
    ContinuityVerdict,
    ProgrammeHealthVector,
    ProgressKind,
    RootPreservationStatus,
    RouteEpisodeDescriptor,
    RouteFamilyLineage,
    RouteHealthFailureMode,
    RouteHealthState,
    RouteWindowObservation,
    SurrogateImprovement,
    assess_route_family_health,
    classify_surrogate_improvement,
    same_route_family,
)


class _FixtureEstablishedInterface:
    """SYNTHETIC #124 stand-in that establishes preservation for one scope."""

    def __init__(self, established_scope: str = "FIXTURE_SCOPE") -> None:
        self._scope = established_scope

    def preservation_status(
        self, *, surrogate_id: str, root_goal_id: str, scope: str
    ) -> RootPreservationStatus:
        if scope == self._scope:
            return RootPreservationStatus.PRESERVATION_INTERFACE_ESTABLISHED
        return RootPreservationStatus.PRESERVATION_INTERFACE_ABSENT


def _fixture_lineage(episodes: int = 8) -> RouteFamilyLineage:
    ids = tuple(f"FIXTURE_EP_{i}" for i in range(episodes))
    return RouteFamilyLineage(
        lineage_id="FIXTURE_LINEAGE",
        root_goal_id="FIXTURE_ROOT_GOAL",
        route_family_id="spectral_positive_norm_to_root_sign",
        core_representation_or_mechanism="spectral_norm_representation",
        root_bridge_hypothesis="norm_to_sign_faithfulness",
        founding_episode_id=ids[0],
        episode_ids_in_chronology=ids,
        continuity_policy_id=DEFAULT_CONTINUITY_POLICY.policy_id,
    )


def _fixture_observation(**overrides: object) -> RouteWindowObservation:
    payload: dict[str, object] = dict(
        lineage_id="FIXTURE_LINEAGE",
        window_episode_ids=tuple(f"FIXTURE_EP_{i}" for i in range(8)),
        root_obligations_verified_closed=0,
        root_reachable_states_from_verified_root_work=0,
        residual_contraction=0.0,
        discriminating_falsifiers_yielded=0,
        representation_gain=0.0,
        retrieval_gain=0.0,
        verified_local_results=0,
        auxiliary_assumptions_added_after_failure=0,
        exception_classes_added=0,
        route_specific_repair_lemmas=0,
        interfaces_opened=0,
        interfaces_closed=0,
        repeated_failure_redundancy=0.0,
        root_bridge_stability=1.0,
        verification_debt_growth=0.0,
        cost_per_epistemic_gain=1.0,
        exploration_diversity=0.5,
        actions_blocked_externally=0,
        actions_attempted=10,
        named_external_blockers=(),
        search_space_eliminated=0.0,
        stable_obstruction_identified=False,
        forced_productive_representation_reset=False,
        representation_reset_declared=False,
    )
    payload.update(overrides)
    return RouteWindowObservation(**payload)  # type: ignore[arg-type]


# -- the module cannot emit a truth verdict ----------------------------------


def test_the_eight_descriptive_states_are_frozen_and_exclude_false_programme() -> None:
    """A later addition of a truth verdict must break CI here."""

    assert {member.value for member in RouteHealthState} == {
        "PROGRESSIVE_SIGNAL",
        "LOCALLY_PROGRESSIVE_ROOT_STALLED",
        "STAGNANT_SIGNAL",
        "PATCH_ACCUMULATION_SIGNAL",
        "RESTRUCTURING_SIGNAL",
        "EXTERNALLY_BLOCKED",
        "INSUFFICIENT_HISTORY",
        "CANNOT_CHECK",
    }
    assert len(RouteHealthState) == 8


def test_the_ten_named_failure_modes_are_frozen() -> None:
    assert {member.value for member in RouteHealthFailureMode} == {
        "FAILURE_COUNT_AS_DEGENERATION",
        "LOCAL_PROGRESS_AS_ROOT_PROGRESS",
        "COMPLEXITY_AS_BADNESS",
        "PREMATURE_PROGRAMME_ABANDONMENT",
        "SUCCESS_HINDSIGHT_LEAK",
        "RETROSPECTIVE_PREDICTION_REWRITE",
        "ROUTE_FAMILY_MISCLUSTERING",
        "EXTERNAL_BLOCKER_MISCLASSIFICATION",
        "PHILOSOPHICAL_LABEL_AUTHORITY_LEAK",
        "SHORT_HORIZON_BIAS",
    }


def test_the_report_grants_nothing_and_never_recommends_abandonment() -> None:
    report = assess_route_family_health(_fixture_lineage(), _fixture_observation())
    assert report.grants_scientific_authority is False
    assert report.grants_abandonment_authority is False
    assert report.recommends_abandonment is False
    assert report.is_truth_verdict is False
    assert report.lineage_id == "FIXTURE_LINEAGE"
    assert report.grants_scientific_authority is False


# -- non-compensation is a property of the type ------------------------------


def test_the_health_vector_has_no_scalar_aggregation_at_all() -> None:
    report = assess_route_family_health(_fixture_lineage(), _fixture_observation())
    vector = report.vector
    assert vector is not None
    for forbidden in ("score", "total", "aggregate", "sum", "overall"):
        assert not hasattr(vector, forbidden), forbidden
    with pytest.raises(TypeError):
        float(vector)
    with pytest.raises(TypeError):
        list(vector)
    with pytest.raises(TypeError):
        sum(vector)  # type: ignore[call-overload]


def test_coordinates_do_not_share_a_direction_so_a_sum_would_be_meaningless() -> None:
    report = assess_route_family_health(_fixture_lineage(), _fixture_observation())
    vector = report.vector
    assert vector is not None
    # High stability means the root bridge has NOT moved; high local results mean
    # the opposite kind of thing. They cannot be added.
    assert vector.shows_movement("root_bridge_stability") is False
    with pytest.raises(ValueError):
        vector.shows_movement("cost_per_epistemic_gain")


def test_a_context_only_coordinate_cannot_be_declared_non_compensatory() -> None:
    with pytest.raises(ValueError):
        assess_route_family_health(
            _fixture_lineage(),
            _fixture_observation(),
            non_compensatory_coordinates=("cost_per_epistemic_gain",),
        )


def test_thirty_local_lemmas_cannot_reach_progressive_with_a_motionless_root_bridge() -> None:
    """The load-bearing assertion of issue #135.

    Every compensatory coordinate is pushed to an extreme while the declared
    non-compensatory ones stay still.  No setting reaches PROGRESSIVE_SIGNAL.
    """

    lineage = _fixture_lineage()
    for local_results in (1, 10, 30, 300):
        observation = _fixture_observation(
            verified_local_results=local_results,
            residual_contraction=0.99,
            representation_gain=0.99,
            retrieval_gain=0.99,
            discriminating_falsifiers_yielded=50,
            exploration_diversity=1.0,
            cost_per_epistemic_gain=0.0,
            # non-compensatory coordinates: nothing moved
            root_obligations_verified_closed=0,
            root_reachable_states_from_verified_root_work=0,
            root_bridge_stability=1.0,
        )
        report = assess_route_family_health(lineage, observation)
        assert report.state is not RouteHealthState.PROGRESSIVE_SIGNAL
        assert report.state is RouteHealthState.LOCALLY_PROGRESSIVE_ROOT_STALLED
        assert set(report.stalled_non_compensatory_coordinates) == set(
            DEFAULT_NON_COMPENSATORY
        )


def test_partial_root_movement_still_blocks_progressive() -> None:
    """Two of three non-compensatory coordinates moving is not enough."""

    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            root_obligations_verified_closed=3,
            root_reachable_states_from_verified_root_work=2,
            root_bridge_stability=1.0,
            verified_local_results=5,
        ),
    )
    assert report.state is RouteHealthState.LOCALLY_PROGRESSIVE_ROOT_STALLED
    assert report.stalled_non_compensatory_coordinates == ("root_bridge_stability",)


def test_vector_rejects_missing_or_unknown_coordinates() -> None:
    with pytest.raises(ValueError):
        ProgrammeHealthVector(
            coordinates=(("root_critical_obligations_closed", 1.0),),
            non_compensatory_coordinates=("root_critical_obligations_closed",),
            window_episode_ids=(),
        )


# -- no-alarm and hostile controls -------------------------------------------


def test_no_alarm_control_a_genuinely_progressive_route_scores_progressive() -> None:
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            root_obligations_verified_closed=2,
            root_reachable_states_from_verified_root_work=3,
            root_bridge_stability=0.4,
            residual_contraction=0.5,
            verified_local_results=4,
            discriminating_falsifiers_yielded=3,
            chronology_records=(
                ChronologyRecord(
                    record_id="FIXTURE_PRED_1",
                    episode_id="FIXTURE_EP_2",
                    kind=ChronologyKind.PROSPECTIVE_DISCRIMINATOR,
                    declared_before_outcome=True,
                    survived=True,
                ),
            ),
        ),
    )
    assert report.state is RouteHealthState.PROGRESSIVE_SIGNAL
    assert report.stalled_non_compensatory_coordinates == ()


def test_hostile_control_a_locally_busy_root_disconnected_route_is_root_stalled() -> None:
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            verified_local_results=12,
            representation_gain=0.8,
            retrieval_gain=0.6,
            residual_contraction=0.3,
            discriminating_falsifiers_yielded=4,
            root_obligations_verified_closed=0,
            root_reachable_states_from_verified_root_work=0,
            root_bridge_stability=1.0,
        ),
    )
    assert report.state is RouteHealthState.LOCALLY_PROGRESSIVE_ROOT_STALLED
    assert report.state is not RouteHealthState.PROGRESSIVE_SIGNAL


# -- failures are not degeneration -------------------------------------------


def test_a_high_failure_but_informative_route_is_not_stagnant() -> None:
    """FAILURE_COUNT_AS_DEGENERATION: elimination and obstruction are value."""

    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            verified_local_results=0,
            repeated_failure_redundancy=0.0,
            search_space_eliminated=0.75,
            stable_obstruction_identified=True,
            discriminating_falsifiers_yielded=6,
            root_bridge_stability=1.0,
        ),
    )
    assert report.state is not RouteHealthState.STAGNANT_SIGNAL
    assert report.state is RouteHealthState.LOCALLY_PROGRESSIVE_ROOT_STALLED


def test_a_route_with_no_new_information_at_all_is_stagnant() -> None:
    """Contrast control: without elimination or local results, stagnation shows."""

    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            search_space_eliminated=0.0,
            stable_obstruction_identified=False,
            discriminating_falsifiers_yielded=0,
            verified_local_results=0,
            repeated_failure_redundancy=0.9,
        ),
    )
    assert report.state is RouteHealthState.STAGNANT_SIGNAL
    assert report.recommends_abandonment is False


def test_external_blocking_pre_empts_stagnation() -> None:
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            actions_blocked_externally=8,
            actions_attempted=10,
            named_external_blockers=("missing formal library for the index family",),
            search_space_eliminated=0.0,
            verified_local_results=0,
        ),
    )
    assert report.state is RouteHealthState.EXTERNALLY_BLOCKED
    assert report.state is not RouteHealthState.STAGNANT_SIGNAL


def test_patch_accumulation_needs_posthoc_repair_without_prospective_success() -> None:
    patchy = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            auxiliary_assumptions_added_after_failure=4,
            exception_classes_added=3,
            interfaces_opened=5,
            interfaces_closed=1,
            chronology_records=(
                ChronologyRecord(
                    record_id="FIXTURE_REPAIR_1",
                    episode_id="FIXTURE_EP_3",
                    kind=ChronologyKind.POSTHOC_REPAIR,
                    declared_before_outcome=False,
                ),
            ),
        ),
    )
    assert patchy.state is RouteHealthState.PATCH_ACCUMULATION_SIGNAL

    # Same complexity growth, but the route also predicted and survived a new
    # discriminating test: complexity alone is not badness.
    earning = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            auxiliary_assumptions_added_after_failure=4,
            exception_classes_added=3,
            interfaces_opened=5,
            interfaces_closed=1,
            verified_local_results=2,
            chronology_records=(
                ChronologyRecord(
                    record_id="FIXTURE_REPAIR_1",
                    episode_id="FIXTURE_EP_3",
                    kind=ChronologyKind.POSTHOC_REPAIR,
                    declared_before_outcome=False,
                ),
                ChronologyRecord(
                    record_id="FIXTURE_PRED_1",
                    episode_id="FIXTURE_EP_4",
                    kind=ChronologyKind.PROSPECTIVE_DISCRIMINATOR,
                    declared_before_outcome=True,
                    survived=True,
                ),
            ),
        ),
    )
    assert earning.state is not RouteHealthState.PATCH_ACCUMULATION_SIGNAL


def test_restructuring_is_reported_rather_than_compared_across_the_reset() -> None:
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(representation_reset_declared=True),
    )
    assert report.state is RouteHealthState.RESTRUCTURING_SIGNAL
    assert any("new_lineage" in reason for reason in report.reasons)


def test_a_short_window_is_insufficient_history_not_stagnation() -> None:
    """SHORT_HORIZON_BIAS: two episodes cannot show a route is going nowhere."""

    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(window_episode_ids=("FIXTURE_EP_0", "FIXTURE_EP_1")),
    )
    assert report.state is RouteHealthState.INSUFFICIENT_HISTORY


# -- root progress must be bound (#124) --------------------------------------


def test_surrogate_gain_without_a_preservation_interface_is_local_progress() -> None:
    improvement = SurrogateImprovement(
        improvement_id="FIXTURE_IMP_1",
        surrogate_id="FIXTURE_SURROGATE",
        root_goal_id="FIXTURE_ROOT_GOAL",
        scope="FIXTURE_SCOPE",
    )
    classification = classify_surrogate_improvement(improvement, None)
    assert classification.kind is ProgressKind.LOCAL_PROGRESS

    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(surrogate_improvements=(improvement,) * 30),
    )
    assert report.state is not RouteHealthState.PROGRESSIVE_SIGNAL
    assert report.vector is not None
    assert report.vector.value("new_root_reachable_states") == 0.0
    assert report.vector.value("new_verified_local_results") == 30.0


def test_surrogate_gain_behind_an_established_interface_counts_as_root_progress() -> None:
    improvement = SurrogateImprovement(
        improvement_id="FIXTURE_IMP_1",
        surrogate_id="FIXTURE_SURROGATE",
        root_goal_id="FIXTURE_ROOT_GOAL",
        scope="FIXTURE_SCOPE",
    )
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            surrogate_improvements=(improvement,),
            root_obligations_verified_closed=1,
            root_bridge_stability=0.5,
        ),
        preservation_interface=_FixtureEstablishedInterface(),
    )
    assert report.vector is not None
    assert report.vector.value("new_root_reachable_states") == 1.0
    assert report.state is RouteHealthState.PROGRESSIVE_SIGNAL


def test_out_of_scope_preservation_does_not_transfer_to_root_progress() -> None:
    improvement = SurrogateImprovement(
        improvement_id="FIXTURE_IMP_1",
        surrogate_id="FIXTURE_SURROGATE",
        root_goal_id="FIXTURE_ROOT_GOAL",
        scope="OTHER_SCOPE",
    )
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(surrogate_improvements=(improvement,)),
        preservation_interface=_FixtureEstablishedInterface("FIXTURE_SCOPE"),
    )
    assert report.vector is not None
    assert report.vector.value("new_root_reachable_states") == 0.0


# -- continuity is a research problem, not a root-id match --------------------


def test_sharing_only_a_root_goal_is_not_route_family_continuity() -> None:
    left = RouteEpisodeDescriptor(
        episode_id="FIXTURE_EP_0",
        root_goal_id="FIXTURE_ROOT_GOAL",
        core_representation_or_mechanism="spectral_norm",
        root_bridge_hypothesis="norm_to_sign",
    )
    right = RouteEpisodeDescriptor(
        episode_id="FIXTURE_EP_9",
        root_goal_id="FIXTURE_ROOT_GOAL",
        core_representation_or_mechanism="combinatorial_cover",
        root_bridge_hypothesis="cover_to_cost",
    )
    report = same_route_family(left, right)
    assert report.verdict is ContinuityVerdict.DIFFERENT_ROUTE_FAMILY
    assert set(report.mismatched) == {
        ContinuityCoordinate.CORE_REPRESENTATION_OR_MECHANISM,
        ContinuityCoordinate.ROOT_BRIDGE_HYPOTHESIS,
    }


def test_a_policy_requiring_only_the_root_goal_is_rejected() -> None:
    with pytest.raises(ValueError):
        ContinuityPolicy(
            policy_id="FIXTURE_BAD_POLICY",
            required_coordinates=(ContinuityCoordinate.ROOT_GOAL_ID,),
        )


def test_an_unknown_continuity_coordinate_cannot_check_rather_than_match() -> None:
    left = RouteEpisodeDescriptor(
        episode_id="FIXTURE_EP_0",
        root_goal_id="FIXTURE_ROOT_GOAL",
        core_representation_or_mechanism="spectral_norm",
        root_bridge_hypothesis="",
    )
    right = dataclasses.replace(left, episode_id="FIXTURE_EP_1")
    assert same_route_family(left, right).verdict is ContinuityVerdict.CANNOT_CHECK


def test_the_continuity_policy_is_swappable() -> None:
    strict = ContinuityPolicy(
        policy_id="FIXTURE_STRICT",
        required_coordinates=(
            ContinuityCoordinate.CORE_REPRESENTATION_OR_MECHANISM,
            ContinuityCoordinate.ROOT_BRIDGE_HYPOTHESIS,
            ContinuityCoordinate.OPERATOR_MOTIF,
        ),
    )
    left = RouteEpisodeDescriptor(
        episode_id="FIXTURE_EP_0",
        root_goal_id="FIXTURE_ROOT_GOAL",
        core_representation_or_mechanism="spectral_norm",
        root_bridge_hypothesis="norm_to_sign",
        operator_motif="positivity_then_transport",
    )
    right = dataclasses.replace(
        left, episode_id="FIXTURE_EP_1", operator_motif="cover_then_count"
    )
    assert same_route_family(left, right).verdict is ContinuityVerdict.SAME_ROUTE_FAMILY
    assert (
        same_route_family(left, right, strict).verdict
        is ContinuityVerdict.DIFFERENT_ROUTE_FAMILY
    )


# -- chronology discriminator -------------------------------------------------


def test_a_prediction_written_after_the_outcome_earns_no_prospective_credit() -> None:
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            chronology_records=(
                ChronologyRecord(
                    record_id="FIXTURE_REWRITE",
                    episode_id="FIXTURE_EP_2",
                    kind=ChronologyKind.PROSPECTIVE_DISCRIMINATOR,
                    declared_before_outcome=False,
                    survived=True,
                ),
            )
        ),
    )
    assert report.chronology is not None
    assert report.chronology.prospective_successes == 0
    assert report.chronology.rewritten_predictions == ("FIXTURE_REWRITE",)
    assert any(
        RouteHealthFailureMode.RETROSPECTIVE_PREDICTION_REWRITE.value in reason
        for reason in report.reasons
    )


def test_unknown_chronology_is_cannot_check_and_never_credited() -> None:
    report = assess_route_family_health(
        _fixture_lineage(),
        _fixture_observation(
            chronology_records=(
                ChronologyRecord(
                    record_id="FIXTURE_UNKNOWN",
                    episode_id="FIXTURE_EP_2",
                    kind=ChronologyKind.PROSPECTIVE_DISCRIMINATOR,
                    declared_before_outcome=None,
                ),
            )
        ),
    )
    assert report.state is RouteHealthState.CANNOT_CHECK
    assert report.vector is None


# -- lineage integrity --------------------------------------------------------


def test_a_lineage_must_contain_its_founding_episode() -> None:
    with pytest.raises(ValueError):
        RouteFamilyLineage(
            lineage_id="FIXTURE_LINEAGE",
            root_goal_id="FIXTURE_ROOT_GOAL",
            route_family_id="FIXTURE_FAMILY",
            core_representation_or_mechanism="spectral_norm",
            root_bridge_hypothesis="norm_to_sign",
            founding_episode_id="FIXTURE_EP_MISSING",
            episode_ids_in_chronology=("FIXTURE_EP_0",),
            continuity_policy_id=DEFAULT_CONTINUITY_POLICY.policy_id,
        )


def test_lineage_grants_no_authority() -> None:
    lineage = _fixture_lineage()
    assert lineage.grants_theorem_authority is False
    assert lineage.grants_method_authority is False


def test_an_observation_bound_to_another_lineage_cannot_check() -> None:
    report = assess_route_family_health(
        _fixture_lineage(), _fixture_observation(lineage_id="OTHER_LINEAGE")
    )
    assert report.state is RouteHealthState.CANNOT_CHECK
