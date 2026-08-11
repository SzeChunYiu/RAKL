"""Freeze tests for the issue #141 backward/multi-seed research objects.

All data below is hand-written FIXTURE.  No solver and no LLM was run; these
tests exercise the type boundaries and verdict logic, never arm performance.
"""

from __future__ import annotations

import dataclasses

import pytest

from rakl.backward_multiseed import (
    AlternativePredecessorSearch,
    BackwardObligation,
    BackwardObligationProposal,
    BackwardSeedFailureMode,
    ConnectionHistory,
    ConnectionNode,
    ConnectionNodeKind,
    ConnectionTrial,
    ConnectionVerdict,
    ImplicationStatus,
    MeetInMiddleVerdict,
    SeedFamily,
    SeedOrigin,
    TransitionEvidence,
    WaypointSeed,
    assess_meet_in_middle,
    assess_seed_diversity,
    audit_backward_seed_state,
    compute_bridge_residual,
    evaluate_connection,
    expand_backward,
)
from rakl.problem_solving_algebra import (
    ObstructionKind,
    OperatorFamily,
    ProblemSignature,
    ProblemState,
    ResearchOperator,
)
from rakl.similarity import (
    DistinguishingProbeCertificate,
    MappingAdmissibility,
    ProbeFamily,
    SimilarityRelation,
    SimilarityWitness,
)


def _fixture_obligation(**overrides: object) -> BackwardObligation:
    payload: dict[str, object] = dict(
        obligation_id="FIXTURE_OBLIGATION_1",
        root_goal_id="FIXTURE_ROOT_GOAL",
        statement="FIXTURE: local positivity on every index",
        structural_signature=("positivity", "index_family"),
        sufficient_for=("FIXTURE_ROOT_GOAL",),
        supporting_family=OperatorFamily.INVARIANT,
        supporting_theorem_ids=("FIXTURE_THEOREM_A",),
        assumptions=("FIXTURE_ASSUMPTION",),
        representation="norm_representation",
        scope="FIXTURE_SCOPE",
        source_evidence_ids=("FIXTURE_EVIDENCE",),
        implication_status=ImplicationStatus.CANDIDATE_UNVERIFIED,
        alternative_search=AlternativePredecessorSearch.ALTERNATIVES_RECORDED,
        known_alternative_predecessor_families=("explicit_formula_route",),
    )
    payload.update(overrides)
    return BackwardObligation(**payload)  # type: ignore[arg-type]


def _fixture_seed(seed_id: str, family: SeedFamily) -> WaypointSeed:
    return WaypointSeed(
        seed_id=seed_id,
        root_goal_id="FIXTURE_ROOT_GOAL",
        atom_ids=("FIXTURE_ATOM",),
        family=family,
        statement_or_object=f"FIXTURE object for {family.value}",
        representation="norm_representation",
        structural_signature=("positivity",),
        origin=SeedOrigin.OPERATOR_APPLICATION,
        origin_operator_id="search_invariant",
        expected_useful_connection="expose the norm-to-sign interface",
        falsifier_or_cheapest_connection_test="evaluate on the rank-one boundary case",
        scope="FIXTURE_SCOPE",
    )


def _fixture_witness() -> SimilarityWitness:
    return SimilarityWitness(
        relation=SimilarityRelation.RELATIONALLY_ANALOGOUS,
        source_id="FIXTURE_SOURCE",
        target_id="FIXTURE_TARGET",
        source_domain="FIXTURE_DOMAIN_A",
        target_domain="FIXTURE_DOMAIN_B",
        question_or_qoi="does local positivity transport",
        mapping_pairs=(("norm", "sign"),),
        preserved=("monotonicity",),
        not_preserved=("index_uniformity",),
        regime=("FIXTURE_REGIME",),
        evidence_ids=("FIXTURE_EVIDENCE",),
        mapping_admissibility=MappingAdmissibility(
            family_id="FIXTURE_MAPPING_FAMILY",
            declared_before_fit=True,
            constraints=("no_free_reparameterisation",),
            constraint_violations=(),
            null_calibration_passed=True,
        ),
        probe_family=ProbeFamily(family_id="FIXTURE_PROBES", probe_ids=("p1",)),
    )


# -- Extension A: sufficiency is never necessity -----------------------------


def test_candidate_only_has_no_backing_field_and_cannot_be_cleared() -> None:
    obligation = _fixture_obligation()
    assert obligation.candidate_only is True
    assert obligation.establishes_necessity is False
    field_names = {field.name for field in dataclasses.fields(obligation)}
    assert "candidate_only" not in field_names
    with pytest.raises(TypeError):
        dataclasses.replace(obligation, candidate_only=False)  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        BackwardObligation(candidate_only=False)  # type: ignore[call-arg]


def test_no_accessor_inverts_the_sufficiency_direction() -> None:
    """``sufficient_for`` is directional; nothing exposes ``necessary_for``."""

    obligation = _fixture_obligation()
    public = {name for name in dir(obligation) if not name.startswith("_")}
    assert not {name for name in public if "necessary" in name or "necessity" in name} - {
        "establishes_necessity"
    }
    assert obligation.grants_root_progress is False


def test_alternative_search_cannot_express_no_alternatives_exist() -> None:
    members = {member.value for member in AlternativePredecessorSearch}
    assert members == {
        "ALTERNATIVES_RECORDED",
        "ALTERNATIVES_NOT_SEARCHED",
        "BOUNDED_SEARCH_NONE_FOUND",
    }
    assert not any("NO_ALTERNATIVES" in value for value in members)


def test_recorded_alternatives_must_actually_be_recorded() -> None:
    with pytest.raises(ValueError):
        _fixture_obligation(known_alternative_predecessor_families=())


def test_bounded_search_finding_none_must_declare_its_boundary() -> None:
    with pytest.raises(ValueError):
        _fixture_obligation(
            alternative_search=AlternativePredecessorSearch.BOUNDED_SEARCH_NONE_FOUND,
            known_alternative_predecessor_families=(),
            alternative_search_boundary=(),
        )
    survivor = _fixture_obligation(
        alternative_search=AlternativePredecessorSearch.BOUNDED_SEARCH_NONE_FOUND,
        known_alternative_predecessor_families=(),
        alternative_search_boundary=("searched: explicit-formula and trace routes only",),
    )
    assert survivor.establishes_necessity is False


def test_verified_implication_requires_a_checker_identity() -> None:
    with pytest.raises(ValueError):
        _fixture_obligation(
            implication_status=ImplicationStatus.IMPLICATION_VERIFIED,
            implication_checker="",
        )
    verified = _fixture_obligation(
        implication_status=ImplicationStatus.IMPLICATION_VERIFIED,
        implication_checker="FIXTURE_CHECKER",
    )
    # Even a verified implication does not make the predecessor necessary.
    assert verified.establishes_necessity is False


def test_expand_backward_rejects_necessity_claims_and_keeps_them() -> None:
    proposals = (
        BackwardObligationProposal(
            proposal_id="FIXTURE_P_OK",
            statement="FIXTURE sufficient predecessor",
            structural_signature=("positivity",),
            supporting_family=OperatorFamily.INVARIANT,
            representation="norm_representation",
            scope="FIXTURE_SCOPE",
            implication_status=ImplicationStatus.CANDIDATE_UNVERIFIED,
            alternative_search=AlternativePredecessorSearch.ALTERNATIVES_NOT_SEARCHED,
        ),
        BackwardObligationProposal(
            proposal_id="FIXTURE_P_NECESSITY",
            statement="FIXTURE: the only possible route",
            structural_signature=("positivity",),
            supporting_family=OperatorFamily.INVARIANT,
            representation="norm_representation",
            scope="FIXTURE_SCOPE",
            implication_status=ImplicationStatus.CANDIDATE_UNVERIFIED,
            alternative_search=AlternativePredecessorSearch.ALTERNATIVES_NOT_SEARCHED,
            claims_necessity=True,
        ),
    )
    expansion = expand_backward(
        target_id="FIXTURE_ROOT_GOAL",
        root_goal_id="FIXTURE_ROOT_GOAL",
        proposals=proposals,
        generator_id="FIXTURE_GENERATOR",
    )
    assert tuple(item.obligation_id for item in expansion.obligations) == ("FIXTURE_P_OK",)
    assert tuple(item.proposal_id for item in expansion.rejected) == ("FIXTURE_P_NECESSITY",)
    assert (
        BackwardSeedFailureMode.BACKWARD_SUFFICIENCY_AS_NECESSITY
        in expansion.rejected[0].failure_modes
    )
    assert expansion.grants_necessity_authority is False


# -- Extension B: structured seeds, never free-text noise ---------------------


def test_seed_families_are_a_closed_set_of_thirteen() -> None:
    assert len(SeedFamily) == 13
    assert {member.value for member in SeedFamily} == {
        "CANDIDATE_LEMMA",
        "CANDIDATE_INVARIANT",
        "ALTERNATIVE_REPRESENTATION",
        "AUXILIARY_OBJECT",
        "INTERMEDIATE_BOUND",
        "EXTREME_OR_BOUNDARY_CASE",
        "NORMAL_FORM",
        "REDUCTION_TARGET",
        "KNOWN_THEOREM_INTERFACE",
        "ANALOGY_OR_JUMP_DERIVED",
        "COUNTEREXAMPLE_BOUNDARY",
        "SYMMETRY_OR_DUALITY_COORDINATE",
        "LOCAL_TO_GLOBAL_BRIDGE_CANDIDATE",
    }


def test_a_seed_without_a_cheapest_connection_test_cannot_be_built() -> None:
    with pytest.raises(ValueError):
        WaypointSeed(
            seed_id="FIXTURE_SEED",
            root_goal_id="FIXTURE_ROOT_GOAL",
            atom_ids=(),
            family=SeedFamily.CANDIDATE_LEMMA,
            statement_or_object="FIXTURE interesting statement",
            representation="norm_representation",
            structural_signature=("positivity",),
            origin=SeedOrigin.JUMP,
            origin_operator_id="jump",
            expected_useful_connection="looks promising",
            falsifier_or_cheapest_connection_test="",
        )


def test_seed_is_never_evidence_or_root_progress() -> None:
    seed = _fixture_seed("FIXTURE_SEED_1", SeedFamily.CANDIDATE_LEMMA)
    assert seed.is_evidence is False
    assert seed.grants_root_progress is False
    assert seed.candidate_only is True


def test_single_family_seeding_is_reported_as_collapse() -> None:
    collapsed = assess_seed_diversity(
        [_fixture_seed(f"FIXTURE_SEED_{i}", SeedFamily.CANDIDATE_LEMMA) for i in range(20)]
    )
    assert collapsed.collapsed is True
    assert collapsed.total_seeds == 20
    assert any("SEED_FAMILY_COLLAPSE" in reason for reason in collapsed.reasons)
    assert collapsed.grants_progress_credit is False

    spread = assess_seed_diversity(
        [
            _fixture_seed("FIXTURE_S1", SeedFamily.CANDIDATE_LEMMA),
            _fixture_seed("FIXTURE_S2", SeedFamily.NORMAL_FORM),
            _fixture_seed("FIXTURE_S3", SeedFamily.SYMMETRY_OR_DUALITY_COORDINATE),
        ]
    )
    assert spread.collapsed is False


# -- Extension C: connection testing -----------------------------------------


def _fixture_nodes() -> tuple[ConnectionNode, ConnectionNode]:
    source = ConnectionNode(
        node_id="FIXTURE_FORWARD_1",
        kind=ConnectionNodeKind.FORWARD_FRONTIER_STATE,
        representation="norm_representation",
        structural_signature=("positivity",),
    )
    target = ConnectionNode(
        node_id="FIXTURE_OBLIGATION_1",
        kind=ConnectionNodeKind.BACKWARD_OBLIGATION,
        representation="norm_representation",
        structural_signature=("positivity",),
        required_facts=frozenset({"candidate_invariant"}),
    )
    return source, target


def _fixture_transition(checker: str = "", artifact: str = "") -> TransitionEvidence:
    operator = ResearchOperator(
        "search_invariant",
        OperatorFamily.INVARIANT,
        targets=frozenset({ObstructionKind.MISSING_INVARIANT}),
        clears=frozenset({ObstructionKind.MISSING_INVARIANT}),
        adds_facts=frozenset({"candidate_invariant"}),
    )
    state = ProblemState(
        state_id="FIXTURE_FORWARD_1",
        signature=ProblemSignature(domain="FIXTURE"),
        obstructions=frozenset({ObstructionKind.MISSING_INVARIANT}),
    )
    return TransitionEvidence(
        operator=operator,
        source_state=state,
        checker_id=checker,
        verification_artifact_id=artifact,
    )


def test_a_transition_without_a_checker_is_a_candidate_bridge_not_a_road() -> None:
    source, target = _fixture_nodes()
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_1",
            source=source,
            target=target,
            declared_before_outcomes=True,
            transition=_fixture_transition(),
        )
    )
    assert report.verdict is ConnectionVerdict.CANDIDATE_BRIDGE
    assert report.is_road is False
    assert BackwardSeedFailureMode.UNVERIFIED_CONNECTION_AS_ROAD in report.failure_modes


def test_a_checked_transition_is_a_verified_road_without_theorem_authority() -> None:
    source, target = _fixture_nodes()
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_2",
            source=source,
            target=target,
            declared_before_outcomes=True,
            transition=_fixture_transition("FIXTURE_CHECKER", "FIXTURE_ARTIFACT"),
        )
    )
    assert report.verdict is ConnectionVerdict.VERIFIED_TRANSITION
    assert report.is_road is True
    assert report.grants_route_authority is False


def test_unmet_operator_preconditions_refute_the_connection() -> None:
    source, target = _fixture_nodes()
    evidence = _fixture_transition("FIXTURE_CHECKER", "FIXTURE_ARTIFACT")
    stripped = dataclasses.replace(
        evidence,
        source_state=dataclasses.replace(evidence.source_state, obstructions=frozenset()),
    )
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_3",
            source=source,
            target=target,
            declared_before_outcomes=True,
            transition=stripped,
        )
    )
    assert report.verdict is ConnectionVerdict.REFUTED
    assert report.is_negative_history is True


def test_a_bare_similarity_witness_is_analogy_only() -> None:
    source, target = _fixture_nodes()
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_4",
            source=source,
            target=target,
            declared_before_outcomes=True,
            witness=_fixture_witness(),
        )
    )
    assert report.verdict is ConnectionVerdict.ANALOGY_ONLY
    assert report.is_road is False


def test_a_distinguishing_probe_refutes_and_is_retained() -> None:
    source, target = _fixture_nodes()
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_5",
            source=source,
            target=target,
            declared_before_outcomes=True,
            refutation=DistinguishingProbeCertificate(
                probe_id="FIXTURE_PROBE",
                source_id="FIXTURE_FORWARD_1",
                target_id="FIXTURE_OBLIGATION_1",
                discrepancy="sign flips on the rank-one boundary",
                tolerance_or_rule="exact",
                context=("FIXTURE_REGIME",),
                evidence_ids=("FIXTURE_EVIDENCE",),
            ),
        )
    )
    assert report.verdict is ConnectionVerdict.REFUTED
    assert "refutation_retained_as_negative_history" in report.reasons


def test_a_named_missing_dependency_blocks_rather_than_refutes() -> None:
    source, target = _fixture_nodes()
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_6",
            source=source,
            target=target,
            declared_before_outcomes=True,
            blocked_dependency="formal library for the index family",
        )
    )
    assert report.verdict is ConnectionVerdict.BLOCKED


def test_unknown_and_posthoc_chronology_never_read_as_checked_and_fine() -> None:
    source, target = _fixture_nodes()
    unknown = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_7",
            source=source,
            target=target,
            declared_before_outcomes=None,
            transition=_fixture_transition("FIXTURE_CHECKER", "FIXTURE_ARTIFACT"),
        )
    )
    posthoc = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_8",
            source=source,
            target=target,
            declared_before_outcomes=False,
            transition=_fixture_transition("FIXTURE_CHECKER", "FIXTURE_ARTIFACT"),
        )
    )
    assert unknown.verdict is ConnectionVerdict.CANNOT_CHECK
    assert posthoc.verdict is ConnectionVerdict.CANNOT_CHECK
    assert unknown.reasons != posthoc.reasons
    assert unknown.is_road is False and posthoc.is_road is False


def test_a_trial_with_no_evidence_at_all_cannot_check() -> None:
    source, target = _fixture_nodes()
    report = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_9",
            source=source,
            target=target,
            declared_before_outcomes=True,
        )
    )
    assert report.verdict is ConnectionVerdict.CANNOT_CHECK
    assert "no_operator_bridge_path_or_witness_supplied" in report.reasons


def test_history_retains_failures_and_counts_repeated_attempts() -> None:
    source, target = _fixture_nodes()
    refuted = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_TRIAL_A",
            source=source,
            target=target,
            declared_before_outcomes=True,
            transition=dataclasses.replace(
                _fixture_transition("c", "a"),
                source_state=dataclasses.replace(
                    _fixture_transition().source_state, obstructions=frozenset()
                ),
            ),
        )
    )
    retry = dataclasses.replace(refuted, trial_id="FIXTURE_TRIAL_B")
    history = ConnectionHistory().record(refuted).record(retry)
    assert history.is_known_failure("FIXTURE_FORWARD_1", "FIXTURE_OBLIGATION_1")
    assert history.repeated_known_failure_count() == 1
    assert history.failed_bridge_ids == ("FIXTURE_TRIAL_A", "FIXTURE_TRIAL_B")


# -- Extension D: meet in the middle -----------------------------------------


def _road(trial_id: str, source_id: str, target_id: str) -> object:
    source = ConnectionNode(
        node_id=source_id,
        kind=ConnectionNodeKind.FORWARD_FRONTIER_STATE,
        representation="r",
        structural_signature=("positivity",),
    )
    target = ConnectionNode(
        node_id=target_id,
        kind=ConnectionNodeKind.BACKWARD_OBLIGATION,
        representation="r",
        structural_signature=("positivity",),
        required_facts=frozenset({"candidate_invariant"}),
    )
    return evaluate_connection(
        ConnectionTrial(
            trial_id=trial_id,
            source=source,
            target=target,
            declared_before_outcomes=True,
            transition=_fixture_transition("FIXTURE_CHECKER", "FIXTURE_ARTIFACT"),
        )
    )


def test_one_unverified_link_prevents_a_meet_in_middle_glue() -> None:
    verified = _road("FIXTURE_L1", "FIXTURE_FORWARD_1", "FIXTURE_MID")
    source = ConnectionNode(
        node_id="FIXTURE_MID",
        kind=ConnectionNodeKind.WAYPOINT_SEED,
        representation="r",
        structural_signature=("positivity",),
    )
    target = ConnectionNode(
        node_id="FIXTURE_OBLIGATION_1",
        kind=ConnectionNodeKind.BACKWARD_OBLIGATION,
        representation="r",
        structural_signature=("positivity",),
        required_facts=frozenset({"candidate_invariant"}),
    )
    unverified = evaluate_connection(
        ConnectionTrial(
            trial_id="FIXTURE_L2",
            source=source,
            target=target,
            declared_before_outcomes=True,
            transition=_fixture_transition(),
        )
    )
    report = assess_meet_in_middle(
        [verified, unverified],
        forward_frontier_ids=("FIXTURE_FORWARD_1",),
        backward_obligation_ids=("FIXTURE_OBLIGATION_1",),
    )
    assert report.verdict is MeetInMiddleVerdict.CANDIDATE_GLUE_UNVERIFIED
    assert BackwardSeedFailureMode.MEET_IN_MIDDLE_FALSE_GLUE in report.failure_modes
    assert report.grants_solution_authority is False


def test_a_fully_verified_chain_glues_without_granting_solution_authority() -> None:
    report = assess_meet_in_middle(
        [
            _road("FIXTURE_L1", "FIXTURE_FORWARD_1", "FIXTURE_MID"),
            _road("FIXTURE_L2", "FIXTURE_MID", "FIXTURE_OBLIGATION_1"),
        ],
        forward_frontier_ids=("FIXTURE_FORWARD_1",),
        backward_obligation_ids=("FIXTURE_OBLIGATION_1",),
    )
    assert report.verdict is MeetInMiddleVerdict.VERIFIED_GLUE
    assert report.grants_solution_authority is False


def test_bridge_residual_must_name_the_cheapest_discriminating_action() -> None:
    expansion = expand_backward(
        target_id="FIXTURE_ROOT_GOAL",
        root_goal_id="FIXTURE_ROOT_GOAL",
        proposals=(
            BackwardObligationProposal(
                proposal_id="FIXTURE_P1",
                statement="FIXTURE predecessor",
                structural_signature=("sign_transport",),
                supporting_family=OperatorFamily.INVARIANT,
                representation="norm_representation",
                scope="FIXTURE_SCOPE",
                implication_status=ImplicationStatus.CANDIDATE_UNVERIFIED,
                alternative_search=AlternativePredecessorSearch.ALTERNATIVES_NOT_SEARCHED,
            ),
        ),
        generator_id="FIXTURE_GENERATOR",
    )
    with pytest.raises(ValueError):
        compute_bridge_residual(
            residual_id="FIXTURE_RESIDUAL",
            root_goal_id="FIXTURE_ROOT_GOAL",
            forward_frontier_signature=("positivity",),
            expansion=expansion,
            history=ConnectionHistory(),
            cheapest_discriminating_action="",
        )
    residual = compute_bridge_residual(
        residual_id="FIXTURE_RESIDUAL",
        root_goal_id="FIXTURE_ROOT_GOAL",
        forward_frontier_signature=("positivity",),
        expansion=expansion,
        history=ConnectionHistory(),
        cheapest_discriminating_action="test sign transport on the rank-one boundary",
    )
    assert residual.missing_coordinates == ("sign_transport",)
    assert residual.frontier_overlap == 0.0
    assert residual.opens_atom_only is True
    assert residual.grants_root_progress is False


# -- Failure-mode audit ------------------------------------------------------


def test_audit_reports_no_alarm_on_a_clean_state() -> None:
    """No-alarm control: a well-formed state must not trip any failure mode."""

    diversity = assess_seed_diversity(
        [
            _fixture_seed("FIXTURE_S1", SeedFamily.CANDIDATE_LEMMA),
            _fixture_seed("FIXTURE_S2", SeedFamily.NORMAL_FORM),
            _fixture_seed("FIXTURE_S3", SeedFamily.REDUCTION_TARGET),
        ]
    )
    history = ConnectionHistory().record(
        _road("FIXTURE_L1", "FIXTURE_FORWARD_1", "FIXTURE_OBLIGATION_1")  # type: ignore[arg-type]
    )
    report = audit_backward_seed_state(
        diversity=diversity,
        history=history,
        connections_cited_as_roads=("FIXTURE_L1",),
        root_progress_claimed_from_seed_ids=(),
        root_obligations_verified_closed=1,
        gold_path_exposed=False,
    )
    assert report.clean is True
    assert report.triggered == ()


def test_audit_flags_seed_derived_root_progress_and_unverified_roads() -> None:
    diversity = assess_seed_diversity(
        [_fixture_seed(f"FIXTURE_S{i}", SeedFamily.CANDIDATE_LEMMA) for i in range(5)]
    )
    report = audit_backward_seed_state(
        diversity=diversity,
        history=ConnectionHistory(),
        necessity_claims=("FIXTURE_OBLIGATION_1",),
        connections_cited_as_roads=("FIXTURE_UNVERIFIED",),
        root_progress_claimed_from_seed_ids=("FIXTURE_S1",),
        root_obligations_verified_closed=0,
        gold_path_exposed=True,
    )
    assert set(report.triggered) == {
        BackwardSeedFailureMode.BACKWARD_SUFFICIENCY_AS_NECESSITY,
        BackwardSeedFailureMode.GOLD_PATH_LEAK,
        BackwardSeedFailureMode.SEED_FAMILY_COLLAPSE,
        BackwardSeedFailureMode.UNVERIFIED_CONNECTION_AS_ROAD,
        BackwardSeedFailureMode.LOCAL_WAYPOINT_AS_ROOT_PROGRESS,
    }
    assert report.grants_scientific_authority is False


def test_the_ten_named_failure_modes_are_frozen() -> None:
    assert {member.value for member in BackwardSeedFailureMode} == {
        "BACKWARD_SUFFICIENCY_AS_NECESSITY",
        "GOLD_PATH_LEAK",
        "RANDOM_SEED_NOISE",
        "WAYPOINT_INTERESTINGNESS_OVERREACH",
        "UNVERIFIED_CONNECTION_AS_ROAD",
        "LOCAL_WAYPOINT_AS_ROOT_PROGRESS",
        "SEED_FAMILY_COLLAPSE",
        "FRONTIER_REPRESENTATION_MISMATCH",
        "MEET_IN_MIDDLE_FALSE_GLUE",
        "CONNECTION_AUTHORITY_LEAK",
    }
