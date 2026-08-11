from __future__ import annotations

import pytest

from rakl.paper2_experience_root_cause import (
    CONDITION_LADDER,
    ORACLE_PASS_MIN_SUCCESS_RATE,
    RootCauseDiagnosticArm,
    VerifiedDevelopmentFeedback,
    admit_verified_development_lesson,
    append_failed_episode_without_lesson,
    oracle_procedure_upper_bound,
    selective_experience_view,
)


def _state() -> dict:
    return {
        "schema_version": "rakl-experience-benchmark-initial-state-v1",
        "state_kind": "RESET_BASELINE_STATE",
        "episodes": [],
        "lessons": [],
        "failure_lattice_entries": [],
        "tools": [],
    }


def _task() -> dict:
    return {
        "task_id": "D1",
        "phase": "DEVELOPMENT_SEQUENCE",
        "stratum": "REPEATED_FAMILY",
        "title": "Calibration-bound temperature claim",
    }


def test_failed_episode_does_not_create_reusable_lesson() -> None:
    state = append_failed_episode_without_lesson(
        _state(),
        task=_task(),
        predicted={
            "verdict": "CONTEXT_MISALIGNED",
            "selected_evidence_ids": ["E1"],
            "rejected_evidence_ids": [],
            "rationale_tags": [],
        },
        score=0.25,
        failure_signature=("verdict_mismatch", "reject_recall_incomplete"),
        output_hash="a" * 64,
    )
    assert len(state["episodes"]) == 1
    assert len(state["failure_lattice_entries"]) == 1
    assert state["lessons"] == []
    assert state["episodes"][0]["sealed_answer_included"] is False


def test_verified_feedback_requires_frozen_output_and_evaluator() -> None:
    with pytest.raises(ValueError, match="development_output_not_frozen"):
        admit_verified_development_lesson(
            _state(),
            VerifiedDevelopmentFeedback(
                source_task_id="D1",
                source_output_hash="a" * 64,
                evaluator_receipt_hash="b" * 64,
                principle="Prefer a currently calibrated instrument for the registered quantity.",
                stratum="REPEATED_FAMILY",
                output_frozen=False,
                evaluator_verified=True,
            ),
        )

    with pytest.raises(ValueError, match="development_feedback_not_verified"):
        admit_verified_development_lesson(
            _state(),
            VerifiedDevelopmentFeedback(
                source_task_id="D1",
                source_output_hash="a" * 64,
                evaluator_receipt_hash="b" * 64,
                principle="Prefer a currently calibrated instrument for the registered quantity.",
                stratum="REPEATED_FAMILY",
                output_frozen=True,
                evaluator_verified=False,
            ),
        )


def test_verified_feedback_rejects_task_local_or_transfer_label_leakage() -> None:
    for principle, pattern in (
        ("Select E1 when calibrated.", "task_local_evidence_id"),
        ("On T1 choose calibrated evidence.", "transfer_task_identifier"),
    ):
        with pytest.raises(ValueError, match=pattern):
            admit_verified_development_lesson(
                _state(),
                VerifiedDevelopmentFeedback(
                    source_task_id="D1",
                    source_output_hash="a" * 64,
                    evaluator_receipt_hash="b" * 64,
                    principle=principle,
                    stratum="REPEATED_FAMILY",
                    output_frozen=True,
                    evaluator_verified=True,
                ),
            )


def test_verified_development_lesson_is_method_only_and_selective() -> None:
    state = admit_verified_development_lesson(
        _state(),
        VerifiedDevelopmentFeedback(
            source_task_id="D1",
            source_output_hash="a" * 64,
            evaluator_receipt_hash="b" * 64,
            principle="Prefer a currently calibrated instrument measuring the registered quantity; reject stale calibration.",
            stratum="REPEATED_FAMILY",
            output_frozen=True,
            evaluator_verified=True,
        ),
    )
    lesson = state["lessons"][0]
    assert lesson["authority"] == "VERIFIED_DEVELOPMENT_METHOD_ONLY"
    assert lesson["grants_scientific_authority"] is False

    view = selective_experience_view(state, target_stratum="REPEATED_FAMILY")
    assert view.lesson_ids == (lesson["lesson_id"],)
    assert len(view.rendered_state["verified_development_lessons"]) == 1
    assert view.grants_scientific_authority is False


def test_oracle_upper_bound_contains_no_task_specific_ids() -> None:
    procedure = oracle_procedure_upper_bound()
    joined = " ".join(procedure)
    assert "E1" not in joined
    assert "T1" not in joined
    assert len(procedure) == 3


def test_condition_ladder_runs_oracle_first() -> None:
    """ORACLE must be arm 1: a later-arm null is uninterpretable without it."""
    assert CONDITION_LADDER[0] is RootCauseDiagnosticArm.ORACLE_PROCEDURE_UPPER_BOUND


def test_condition_ladder_covers_every_arm_exactly_once() -> None:
    assert len(CONDITION_LADDER) == len(set(CONDITION_LADDER))
    assert set(CONDITION_LADDER) == set(RootCauseDiagnosticArm)


def test_condition_ladder_orders_full_rakl_last() -> None:
    """FULL_RAKL_SELECTIVE is authorized only after the bottleneck is localized."""
    assert CONDITION_LADDER[-1] is RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE


def test_oracle_pass_gate_is_two_of_three_and_frozen() -> None:
    """Gate is frozen before execution so it cannot be re-tuned after the result."""
    assert ORACLE_PASS_MIN_SUCCESS_RATE == pytest.approx(2.0 / 3.0)
    # two-sided: 1/3 must fail the gate and 2/3 must clear it
    assert (1.0 / 3.0) < ORACLE_PASS_MIN_SUCCESS_RATE
    assert (2.0 / 3.0) >= ORACLE_PASS_MIN_SUCCESS_RATE
