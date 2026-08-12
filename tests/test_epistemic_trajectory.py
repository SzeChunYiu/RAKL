from dataclasses import replace

from rakl.epistemic_trajectory import (
    EpistemicStepFamily,
    EpistemicTrajectoryCase,
    GoldEpistemicStep,
    ObservedEpistemicStep,
    TrajectoryVerdict,
    evaluate_epistemic_trajectory,
    summarize_trajectory_panel,
)


def _clean_case(case_id="case-clean", *, twin=None):
    return EpistemicTrajectoryCase(
        case_id=case_id,
        initial_authority_fingerprint="A0",
        gold_steps=(
            GoldEpistemicStep(
                step_id="s1-search",
                family=EpistemicStepFamily.SEARCH_ROUTING,
                licensed_action="RUN_DISCRIMINATOR",
                required_evidence_ids=(),
                required_root_ids=(),
                authority_change_licensed=False,
                latest_safe_sequence=1,
            ),
            GoldEpistemicStep(
                step_id="s2-update",
                family=EpistemicStepFamily.LEGITIMATE_UPDATE_CONTROL,
                licensed_action="COMMIT_SUPPORTED",
                required_evidence_ids=("obs-1",),
                required_root_ids=("root-1",),
                authority_change_licensed=True,
                expected_authority_after="A1",
                positive_update_opportunity=True,
                latest_safe_sequence=2,
            ),
            GoldEpistemicStep(
                step_id="s3-history",
                family=EpistemicStepFamily.REVISION_SUPERSESSION,
                licensed_action="PRESERVE_NEGATIVE_HISTORY",
                required_evidence_ids=("obs-1",),
                required_root_ids=("root-1",),
                required_negative_history_ids=("failure-old",),
                authority_change_licensed=False,
                latest_safe_sequence=3,
            ),
        ),
        known_answer_validated=True,
        frozen_before_output=True,
        twin_family_id=twin,
    )


def _clean_observed():
    return (
        ObservedEpistemicStep(
            step_id="s1-search",
            family=EpistemicStepFamily.SEARCH_ROUTING,
            action="RUN_DISCRIMINATOR",
            evidence_ids=(),
            root_ids=(),
            negative_history_ids=(),
            authority_before="A0",
            authority_after="A0",
            sequence_index=1,
        ),
        ObservedEpistemicStep(
            step_id="s2-update",
            family=EpistemicStepFamily.LEGITIMATE_UPDATE_CONTROL,
            action="COMMIT_SUPPORTED",
            evidence_ids=("obs-1",),
            root_ids=("root-1",),
            negative_history_ids=(),
            authority_before="A0",
            authority_after="A1",
            sequence_index=2,
        ),
        ObservedEpistemicStep(
            step_id="s3-history",
            family=EpistemicStepFamily.REVISION_SUPERSESSION,
            action="PRESERVE_NEGATIVE_HISTORY",
            evidence_ids=("obs-1",),
            root_ids=("root-1",),
            negative_history_ids=("failure-old",),
            authority_before="A1",
            authority_after="A1",
            sequence_index=3,
        ),
    )


def test_clean_multistep_trajectory_passes_and_grants_no_authority():
    result = evaluate_epistemic_trajectory(_clean_case(), _clean_observed())
    assert result.verdict is TrajectoryVerdict.PASS
    assert result.passed is True
    assert result.continuity_correct is True
    assert all(step.passed for step in result.steps)
    assert result.grants_scientific_authority is False


def test_correct_action_with_wrong_evidence_ids_fails_evidence_binding():
    observed = list(_clean_observed())
    observed[1] = replace(observed[1], evidence_ids=("obs-wrong",))
    result = evaluate_epistemic_trajectory(_clean_case(), observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert result.steps[1].action_correct is True
    assert result.steps[1].evidence_binding_correct is False
    assert "evidence_binding_mismatch" in result.steps[1].reasons


def test_wrong_root_accounting_fails_even_when_evidence_id_is_right():
    observed = list(_clean_observed())
    observed[1] = replace(observed[1], root_ids=("derivative-paper",))
    result = evaluate_epistemic_trajectory(_clean_case(), observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert result.steps[1].evidence_binding_correct is True
    assert result.steps[1].root_accounting_correct is False


def test_authority_inert_search_step_cannot_change_authority():
    observed = list(_clean_observed())
    observed[0] = replace(observed[0], authority_after="A-LEAK")
    observed[1] = replace(observed[1], authority_before="A-LEAK")
    result = evaluate_epistemic_trajectory(_clean_case(), observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert result.steps[0].authority_leak is True
    assert "unlicensed_authority_change" in result.steps[0].reasons


def test_licensed_positive_update_must_reach_exact_expected_authority_fingerprint():
    observed = list(_clean_observed())
    observed[1] = replace(observed[1], authority_after="A-WRONG")
    observed[2] = replace(observed[2], authority_before="A-WRONG", authority_after="A-WRONG")
    result = evaluate_epistemic_trajectory(_clean_case(), observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert result.steps[1].authority_transition_correct is False
    assert "licensed_authority_transition_result_mismatch" in result.steps[1].reasons


def test_frozen_step_order_is_load_bearing():
    observed = list(_clean_observed())
    observed[0] = replace(observed[0], sequence_index=2)
    observed[1] = replace(observed[1], sequence_index=1)
    result = evaluate_epistemic_trajectory(_clean_case(), observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert "epistemic_step_order_mismatch" in result.reasons


def test_too_late_epistemic_action_fails_timing():
    case = EpistemicTrajectoryCase(
        case_id="timing",
        initial_authority_fingerprint="A0",
        gold_steps=(
            GoldEpistemicStep(
                step_id="check-before-action",
                family=EpistemicStepFamily.SEQUENTIAL_SUFFICIENCY,
                licensed_action="GATHER_MORE_EVIDENCE",
                authority_change_licensed=False,
                latest_safe_sequence=1,
            ),
            GoldEpistemicStep(
                step_id="later-routing",
                family=EpistemicStepFamily.SEARCH_ROUTING,
                licensed_action="ROUTE_NEXT",
                authority_change_licensed=False,
                latest_safe_sequence=2,
            ),
        ),
        known_answer_validated=True,
        frozen_before_output=True,
    )
    observed = (
        ObservedEpistemicStep(
            "check-before-action",
            EpistemicStepFamily.SEQUENTIAL_SUFFICIENCY,
            "GATHER_MORE_EVIDENCE",
            (),
            (),
            (),
            "A0",
            "A0",
            2,
        ),
        ObservedEpistemicStep(
            "later-routing",
            EpistemicStepFamily.SEARCH_ROUTING,
            "ROUTE_NEXT",
            (),
            (),
            (),
            "A0",
            "A0",
            3,
        ),
    )
    result = evaluate_epistemic_trajectory(case, observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert result.steps[0].timing_correct is False
    assert "posthoc_or_too_late_epistemic_action" in result.steps[0].reasons


def test_required_negative_history_cannot_disappear_during_revision():
    observed = list(_clean_observed())
    observed[2] = replace(observed[2], negative_history_ids=())
    result = evaluate_epistemic_trajectory(_clean_case(), observed)
    assert result.verdict is TrajectoryVerdict.FAIL
    assert result.steps[2].negative_history_preserved is False


def _positive_update_case():
    return EpistemicTrajectoryCase(
        case_id="positive-update",
        initial_authority_fingerprint="A0",
        gold_steps=(
            GoldEpistemicStep(
                step_id="legal-update",
                family=EpistemicStepFamily.LEGITIMATE_UPDATE_CONTROL,
                licensed_action="COMMIT_SUPPORTED",
                required_evidence_ids=("obs",),
                required_root_ids=("root",),
                authority_change_licensed=True,
                expected_authority_after="A1",
                positive_update_opportunity=True,
            ),
        ),
        known_answer_validated=True,
        frozen_before_output=True,
    )


def _always_abstain_observed(case_id="positive-update"):
    del case_id
    return (
        ObservedEpistemicStep(
            step_id="legal-update",
            family=EpistemicStepFamily.LEGITIMATE_UPDATE_CONTROL,
            action="ABSTAIN_CANNOT_CHECK",
            evidence_ids=(),
            root_ids=(),
            negative_history_ids=(),
            authority_before="A0",
            authority_after="A0",
            sequence_index=1,
        ),
    )


def test_always_cannot_check_fails_valid_update_control_and_is_detected_panel_wide():
    case = _positive_update_case()
    observed = _always_abstain_observed()
    evaluation = evaluate_epistemic_trajectory(case, observed)
    assert evaluation.verdict is TrajectoryVerdict.FAIL
    assert evaluation.steps[0].premature_abstention is True

    metrics = summarize_trajectory_panel(
        (case,),
        (evaluation,),
        observed_by_case=((case.case_id, observed),),
    )
    assert metrics.valid_update_recall == 0.0
    assert metrics.always_abstain_detected is True
    assert metrics.grants_scientific_authority is False


def test_minimal_twin_flips_discriminator_vs_abstention_and_blanket_policy_cannot_pass_both():
    gather = EpistemicTrajectoryCase(
        case_id="twin-gather",
        initial_authority_fingerprint="A0",
        twin_family_id="availability-twin",
        gold_steps=(
            GoldEpistemicStep(
                "decision",
                EpistemicStepFamily.SEQUENTIAL_SUFFICIENCY,
                "RUN_DISCRIMINATOR",
                forbidden_actions=("ABSTAIN_CANNOT_CHECK",),
                authority_change_licensed=False,
            ),
        ),
        known_answer_validated=True,
        frozen_before_output=True,
    )
    abstain = EpistemicTrajectoryCase(
        case_id="twin-abstain",
        initial_authority_fingerprint="A0",
        twin_family_id="availability-twin",
        gold_steps=(
            GoldEpistemicStep(
                "decision",
                EpistemicStepFamily.SEQUENTIAL_SUFFICIENCY,
                "ABSTAIN_CANNOT_CHECK",
                forbidden_actions=("RUN_DISCRIMINATOR",),
                authority_change_licensed=False,
            ),
        ),
        known_answer_validated=True,
        frozen_before_output=True,
    )
    blanket = (
        ObservedEpistemicStep(
            "decision",
            EpistemicStepFamily.SEQUENTIAL_SUFFICIENCY,
            "ABSTAIN_CANNOT_CHECK",
            (),
            (),
            (),
            "A0",
            "A0",
            1,
        ),
    )
    assert evaluate_epistemic_trajectory(gather, blanket).verdict is TrajectoryVerdict.FAIL
    assert evaluate_epistemic_trajectory(abstain, blanket).verdict is TrajectoryVerdict.PASS


def test_unknown_unvalidated_and_posthoc_gold_fail_closed():
    observed = _clean_observed()
    unknown = evaluate_epistemic_trajectory(
        replace(_clean_case(), known_answer_validated=None),
        observed,
    )
    assert unknown.verdict is TrajectoryVerdict.CANNOT_CHECK

    unvalidated = evaluate_epistemic_trajectory(
        replace(_clean_case(), known_answer_validated=False),
        observed,
    )
    assert unvalidated.verdict is TrajectoryVerdict.CANNOT_CHECK

    posthoc = evaluate_epistemic_trajectory(
        replace(_clean_case(), frozen_before_output=False),
        observed,
    )
    assert posthoc.verdict is TrajectoryVerdict.INVALID


def test_missing_extra_duplicate_step_and_duplicate_sequence_are_invalid():
    case = _clean_case()
    observed = _clean_observed()

    missing = evaluate_epistemic_trajectory(case, observed[:-1])
    assert missing.verdict is TrajectoryVerdict.INVALID
    assert any(reason.startswith("missing_steps:") for reason in missing.reasons)

    extra_step = ObservedEpistemicStep(
        "extra",
        EpistemicStepFamily.SEARCH_ROUTING,
        "ROUTE",
        (),
        (),
        (),
        "A1",
        "A1",
        4,
    )
    extra = evaluate_epistemic_trajectory(case, observed + (extra_step,))
    assert extra.verdict is TrajectoryVerdict.INVALID
    assert any(reason.startswith("unexpected_steps:") for reason in extra.reasons)

    duplicate = evaluate_epistemic_trajectory(case, observed + (observed[0],))
    assert duplicate.verdict is TrajectoryVerdict.INVALID
    assert any(reason.startswith("duplicate_observed_step:") for reason in duplicate.reasons)

    duplicate_sequence = list(observed)
    duplicate_sequence[1] = replace(duplicate_sequence[1], sequence_index=1)
    duplicate_seq_result = evaluate_epistemic_trajectory(case, duplicate_sequence)
    assert duplicate_seq_result.verdict is TrajectoryVerdict.INVALID
    assert "duplicate_sequence_index" in duplicate_seq_result.reasons


def test_panel_metrics_reject_unknown_or_duplicate_observed_case_bindings():
    case = _positive_update_case()
    observed = _always_abstain_observed()
    evaluation = evaluate_epistemic_trajectory(case, observed)

    try:
        summarize_trajectory_panel(
            (case,),
            (evaluation,),
            observed_by_case=(("unknown", observed),),
        )
        raise AssertionError("unknown observed case should be rejected")
    except ValueError as exc:
        assert "unknown case" in str(exc)

    try:
        summarize_trajectory_panel(
            (case,),
            (evaluation,),
            observed_by_case=((case.case_id, observed), (case.case_id, observed)),
        )
        raise AssertionError("duplicate observed case should be rejected")
    except ValueError as exc:
        assert "duplicate observed trajectory case" in str(exc)
