from dataclasses import replace
from hashlib import sha256

from rakl.experience_substrate import (
    EpisodeOutcome,
    LessonAuthority,
    TaskEpisode,
    episode_content_bytes,
)
from rakl.trajectory_lesson_induction import (
    TrajectoryInductionVerdict,
    induce_candidate_lesson_from_trajectory,
)


def _episode(
    i: int,
    *,
    action=("SEARCH", "JUMP"),
    outcome=EpisodeOutcome.SUCCESS,
    context="ctx-a",
    signature=("obstruction-a", "qoi-a"),
    verified=True,
    residual=(),
):
    draft = TaskEpisode(
        episode_id=f"ep-{i}",
        task_id=f"task-{i}",
        atom_id="atom-a",
        context_hash=context,
        problem_signature=tuple(signature),
        fibre_snapshot_hash=sha256(f"fibre-{i}".encode()).hexdigest(),
        operator_ids=("op-a",),
        action_trace=tuple(action),
        observation_ids=(f"obs-{i}",),
        verification_ids=((f"ver-{i}",) if verified else ()),
        outcome=outcome,
        residual_signature=tuple(residual),
        evidence_pointers=(f"evidence-{i}",),
        artifact_hash="",
        timestamp=f"2026-08-14T0{i % 9}:00:00+00:00",
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def test_two_verified_successes_induce_candidate_only():
    report = induce_candidate_lesson_from_trajectory(
        (_episode(1), _episode(2)), lesson_id="lesson-a"
    )
    assert report.verdict is TrajectoryInductionVerdict.INDUCED_CANDIDATE
    assert report.candidate is not None
    assert report.candidate.authority is LessonAuthority.CANDIDATE
    assert report.candidate.action == "SEARCH -> JUMP"
    assert report.grants_scientific_authority is False
    assert report.grants_reuse_authority is False


def test_single_or_unverified_success_fails_closed():
    assert induce_candidate_lesson_from_trajectory(
        (_episode(1),), lesson_id="lesson-a"
    ).verdict is TrajectoryInductionVerdict.CANNOT_CHECK
    report = induce_candidate_lesson_from_trajectory(
        (_episode(1), _episode(2, verified=False)), lesson_id="lesson-b"
    )
    assert report.verdict is TrajectoryInductionVerdict.CANNOT_CHECK
    assert any("missing_verification" in reason for reason in report.reasons)


def test_same_action_failure_contradicts_candidate():
    report = induce_candidate_lesson_from_trajectory(
        (
            _episode(1),
            _episode(2),
            _episode(3, outcome=EpisodeOutcome.FAILURE, residual=("boundary-b",)),
        ),
        lesson_id="lesson-a",
    )
    assert report.verdict is TrajectoryInductionVerdict.CANNOT_CHECK
    assert "ep-3" in report.negative_history_episode_ids
    assert "boundary-b" in report.boundary_residuals


def test_old_failed_action_does_not_suppress_verified_successor_and_is_retained():
    report = induce_candidate_lesson_from_trajectory(
        (
            _episode(1, action=("SEARCH",), outcome=EpisodeOutcome.FAILURE, residual=("bad-old",)),
            _episode(2, action=("JUMP",)),
            _episode(3, action=("JUMP",)),
        ),
        lesson_id="successor",
    )
    assert report.verdict is TrajectoryInductionVerdict.INDUCED_CANDIDATE
    assert report.candidate is not None
    assert report.candidate.action == "JUMP"
    assert report.negative_history_episode_ids == ("ep-1",)
    assert report.candidate.contradicting_episode_ids == ("ep-1",)
    assert "bad-old" in report.candidate.boundaries


def test_partial_and_blocked_are_negative_history_not_positive_support():
    report = induce_candidate_lesson_from_trajectory(
        (
            _episode(1),
            _episode(2),
            _episode(3, outcome=EpisodeOutcome.PARTIAL_SUCCESS, residual=("partial-bound",)),
            _episode(4, outcome=EpisodeOutcome.BLOCKED, residual=("resource-bound",)),
        ),
        lesson_id="bounded",
    )
    assert report.verdict is TrajectoryInductionVerdict.INDUCED_CANDIDATE
    assert report.supporting_episode_ids == ("ep-1", "ep-2")
    assert report.negative_history_episode_ids == ("ep-3", "ep-4")
    assert set(report.boundary_residuals) == {"partial-bound", "resource-bound"}


def test_mixed_context_problem_or_success_actions_fail_closed():
    mixed_context = induce_candidate_lesson_from_trajectory(
        (_episode(1), _episode(2, context="ctx-b")), lesson_id="mixed-context"
    )
    assert mixed_context.verdict is TrajectoryInductionVerdict.CANNOT_CHECK

    mixed_problem = induce_candidate_lesson_from_trajectory(
        (_episode(1), _episode(2, signature=("other",))), lesson_id="mixed-problem"
    )
    assert mixed_problem.verdict is TrajectoryInductionVerdict.CANNOT_CHECK

    mixed_actions = induce_candidate_lesson_from_trajectory(
        (
            _episode(1, action=("A",)),
            _episode(2, action=("A",)),
            _episode(3, action=("B",)),
            _episode(4, action=("B",)),
        ),
        lesson_id="mixed-actions",
    )
    assert mixed_actions.verdict is TrajectoryInductionVerdict.CANNOT_CHECK


def test_tampered_episode_identity_blocks_induction():
    good = _episode(1)
    tampered = replace(_episode(2), context_hash="tampered-without-rehash")
    report = induce_candidate_lesson_from_trajectory((good, tampered), lesson_id="tampered")
    assert report.verdict is TrajectoryInductionVerdict.CANNOT_CHECK
    assert any("artifact_hash_mismatch" in reason for reason in report.reasons)
