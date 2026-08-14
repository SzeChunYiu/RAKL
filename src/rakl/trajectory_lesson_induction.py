from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Iterable, Tuple

from .experience_substrate import (
    EpisodeOutcome,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    lesson_content_bytes,
    validate_episode,
)


class TrajectoryInductionVerdict(str, Enum):
    INDUCED_CANDIDATE = "INDUCED_CANDIDATE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class TrajectoryInductionReport:
    verdict: TrajectoryInductionVerdict
    reasons: Tuple[str, ...]
    candidate: Lesson | None
    supporting_episode_ids: Tuple[str, ...]
    negative_history_episode_ids: Tuple[str, ...]
    boundary_residuals: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_reuse_authority(self) -> bool:
        return False


def _timestamp_key(episode: TaskEpisode) -> tuple[str, str]:
    # validate_episode has already established an ISO timestamp. Lexicographic
    # order is stable for the repository's normalized UTC timestamps and the
    # episode id deterministically resolves ties.
    return episode.timestamp, episode.episode_id


def _action_key(episode: TaskEpisode) -> Tuple[str, ...]:
    return tuple(episode.action_trace)


def _candidate_lesson(
    *,
    lesson_id: str,
    context_hash: str,
    problem_signature: Tuple[str, ...],
    action: Tuple[str, ...],
    supports: Tuple[TaskEpisode, ...],
    negatives: Tuple[TaskEpisode, ...],
    boundary_residuals: Tuple[str, ...],
) -> Lesson:
    evidence_pointers = tuple(
        dict.fromkeys(
            pointer
            for episode in supports + negatives
            for pointer in episode.evidence_pointers + episode.verification_ids
        )
    )
    draft = Lesson(
        lesson_id=lesson_id,
        kind=LessonKind.STRATEGY,
        trigger_signature=problem_signature,
        context_scope=(context_hash,),
        action=" -> ".join(action),
        expected_effects=("repeat_verified_success_pattern",),
        boundaries=boundary_residuals,
        supporting_episode_ids=tuple(item.episode_id for item in supports),
        contradicting_episode_ids=tuple(item.episode_id for item in negatives),
        falsifier="a fresh canonically verified episode in the same registered scope contradicts the candidate action",
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=(
            "external lesson verification attestation",
            "fresh transfer evidence before reusable authority",
        ),
        evidence_pointers=evidence_pointers,
        artifact_hash="",
    )
    return replace(draft, artifact_hash=sha256(lesson_content_bytes(draft)).hexdigest())


def induce_candidate_lesson_from_trajectory(
    episodes: Iterable[TaskEpisode],
    *,
    lesson_id: str,
    minimum_verified_successes: int = 2,
) -> TrajectoryInductionReport:
    """Induce one bounded candidate lesson from immutable typed episodes.

    This function deliberately stops *before* verification or reusable lesson
    authority. It requires exact-valid episode identities, one context/problem
    scope, at least two fully successful episodes carrying verification ids, and
    one unambiguous successful action after accounting for failures. Failures,
    partial successes and blocked attempts are retained as negative history and
    their residual signatures become explicit candidate boundaries.

    A failure of the same candidate action in the same scope blocks induction.
    A historical failure of another action does not suppress a later verified
    successor action; it remains attached as negative history. Missing
    verification never becomes implicit support.
    """

    ordered = tuple(sorted(tuple(episodes), key=_timestamp_key))
    if not lesson_id.strip():
        raise ValueError("lesson_id is required")
    if minimum_verified_successes < 2:
        raise ValueError("minimum_verified_successes must be at least two")
    if not ordered:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            ("trajectory_empty",),
            None,
            (),
            (),
            (),
        )

    invalid_reasons: list[str] = []
    for episode in ordered:
        invalid_reasons.extend(
            f"{episode.episode_id}:{reason}" for reason in validate_episode(episode)
        )
    if invalid_reasons:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            tuple(invalid_reasons),
            None,
            (),
            tuple(
                episode.episode_id
                for episode in ordered
                if episode.outcome is not EpisodeOutcome.SUCCESS
            ),
            tuple(
                dict.fromkeys(
                    residual
                    for episode in ordered
                    for residual in episode.residual_signature
                )
            ),
        )

    contexts = {episode.context_hash for episode in ordered}
    signatures = {tuple(episode.problem_signature) for episode in ordered}
    negative_history = tuple(
        episode for episode in ordered if episode.outcome is not EpisodeOutcome.SUCCESS
    )
    boundary_residuals = tuple(
        dict.fromkeys(
            residual
            for episode in negative_history
            for residual in episode.residual_signature
        )
    )
    if len(contexts) != 1:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            ("multiple_contexts_in_trajectory",),
            None,
            (),
            tuple(item.episode_id for item in negative_history),
            boundary_residuals,
        )
    if len(signatures) != 1:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            ("multiple_problem_signatures_in_trajectory",),
            None,
            (),
            tuple(item.episode_id for item in negative_history),
            boundary_residuals,
        )

    verified_successes = tuple(
        episode
        for episode in ordered
        if episode.outcome is EpisodeOutcome.SUCCESS and bool(episode.verification_ids)
    )
    unverified_successes = tuple(
        episode
        for episode in ordered
        if episode.outcome is EpisodeOutcome.SUCCESS and not episode.verification_ids
    )
    if unverified_successes:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            tuple(
                f"successful_episode_missing_verification:{item.episode_id}"
                for item in unverified_successes
            ),
            None,
            tuple(item.episode_id for item in verified_successes),
            tuple(item.episode_id for item in negative_history),
            boundary_residuals,
        )

    by_action: dict[Tuple[str, ...], list[TaskEpisode]] = {}
    for episode in verified_successes:
        by_action.setdefault(_action_key(episode), []).append(episode)
    eligible_actions = tuple(
        action
        for action, rows in sorted(by_action.items())
        if len(rows) >= minimum_verified_successes
    )
    if not eligible_actions:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            ("insufficient_repeated_verified_success",),
            None,
            tuple(item.episode_id for item in verified_successes),
            tuple(item.episode_id for item in negative_history),
            boundary_residuals,
        )
    if len(eligible_actions) != 1:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            ("multiple_verified_success_actions",),
            None,
            tuple(item.episode_id for item in verified_successes),
            tuple(item.episode_id for item in negative_history),
            boundary_residuals,
        )

    action = eligible_actions[0]
    same_action_failures = tuple(
        episode
        for episode in negative_history
        if episode.outcome is EpisodeOutcome.FAILURE and _action_key(episode) == action
    )
    if same_action_failures:
        return TrajectoryInductionReport(
            TrajectoryInductionVerdict.CANNOT_CHECK,
            tuple(
                f"same_action_contradicted:{item.episode_id}"
                for item in same_action_failures
            ),
            None,
            tuple(item.episode_id for item in by_action[action]),
            tuple(item.episode_id for item in negative_history),
            boundary_residuals,
        )

    supports = tuple(by_action[action])
    context_hash = next(iter(contexts))
    problem_signature = next(iter(signatures))
    candidate = _candidate_lesson(
        lesson_id=lesson_id,
        context_hash=context_hash,
        problem_signature=problem_signature,
        action=action,
        supports=supports,
        negatives=negative_history,
        boundary_residuals=boundary_residuals,
    )
    return TrajectoryInductionReport(
        TrajectoryInductionVerdict.INDUCED_CANDIDATE,
        (
            "repeated_verified_success_induces_candidate_only",
            "negative_history_and_residual_boundaries_retained",
            "reuse_requires_separate_consolidation_gate",
        ),
        candidate,
        tuple(item.episode_id for item in supports),
        tuple(item.episode_id for item in negative_history),
        boundary_residuals,
    )
