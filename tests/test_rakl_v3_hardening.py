from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from rakl.experience_learning import LessonConsolidationEvidence
from rakl.experience_substrate import (
    EpisodeOutcome,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    episode_content_bytes,
    lesson_content_bytes,
)
from rakl.saturation_vector import NoveltyRound, SaturationAxis, assess_saturation_vector
from rakl.v3_runtime import RAKLV3State, consolidate_lesson, record_task_episode


def _episode() -> TaskEpisode:
    draft = TaskEpisode(
        episode_id="E1",
        task_id="task",
        atom_id="A1",
        context_hash="ctx",
        problem_signature=("structure",),
        fibre_snapshot_hash="fibre",
        operator_ids=("op",),
        action_trace=("act",),
        observation_ids=("obs",),
        verification_ids=("verify",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("artifact:E1",),
        artifact_hash="",
        timestamp="2026-08-11T08:55:00+00:00",
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def _lesson() -> Lesson:
    draft = Lesson(
        lesson_id="L1",
        kind=LessonKind.OPERATOR,
        trigger_signature=("structure",),
        context_scope=("ctx",),
        action="apply op",
        expected_effects=("solve",),
        boundaries=("scope-bound",),
        supporting_episode_ids=("E1",),
        contradicting_episode_ids=(),
        falsifier="registered counterexample",
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=("verify",),
        evidence_pointers=("artifact:E1",),
        artifact_hash="",
    )
    return replace(draft, artifact_hash=sha256(lesson_content_bytes(draft)).hexdigest())


def test_recent_retained_novelty_prevents_axis_flatness() -> None:
    zero = tuple((axis, 0) for axis in SaturationAxis)
    novel = tuple(
        (axis, 1 if axis is SaturationAxis.KNOWLEDGE else 0)
        for axis in SaturationAxis
    )
    report = assess_saturation_vector(
        (
            NoveltyRound("R1", "historical", True, zero),
            NoveltyRound("R2", "alien-domain", True, zero),
            NoveltyRound("R3", "fresh", True, novel),
        ),
        required_axes=(SaturationAxis.KNOWLEDGE,),
    )
    assert not report.flat(SaturationAxis.KNOWLEDGE)
    assert not report.bounded_saturated
    assert "KNOWLEDGE:recent_retained_novelty" in report.reasons


def test_consolidation_rejects_same_lesson_id_with_different_content() -> None:
    state = record_task_episode(RAKLV3State(), _episode())
    original = _lesson()
    first = consolidate_lesson(
        state,
        original,
        LessonConsolidationEvidence(supporting_episode_ids=("E1",)),
        promoted_lesson_id="unused",
        promoted_artifact_hash="unused",
    )
    assert first.promoted_lesson_id is None

    spoofed = replace(original, action="different action under same immutable id")
    with pytest.raises(ValueError, match="identity already exists with different content"):
        consolidate_lesson(
            first.state,
            spoofed,
            LessonConsolidationEvidence(supporting_episode_ids=("E1",)),
            promoted_lesson_id="unused-2",
            promoted_artifact_hash="unused-2",
        )
