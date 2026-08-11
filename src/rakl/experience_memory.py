from __future__ import annotations

from typing import Tuple

from .experience_substrate import ExperienceLedger, Lesson, TaskEpisode
from .multires_memory import MemoryView, MemoryViewKind, SourcePin


LESSON_ERASURE_TAGS: Tuple[str, ...] = (
    "full_action_trace",
    "full_observation_payload",
    "full_verification_payload",
    "unselected_context_detail",
)


def episode_memory_view(episode: TaskEpisode) -> MemoryView:
    """Expose an immutable TaskEpisode as a canonical multi-resolution memory root."""

    return MemoryView(
        record_id=episode.episode_id,
        payload_hash=episode.artifact_hash,
        kind=MemoryViewKind.CANONICAL,
    )


def lesson_memory_view(lesson: Lesson, ledger: ExperienceLedger) -> MemoryView:
    """Expose a Lesson as an explicitly lossy view over its episode evidence.

    Even a proof-backed lesson is an abstraction of its source trajectories; it
    therefore never claims exact reconstruction of the underlying episodes.
    Method authority remains inside the Lesson object and is not converted into a
    scientific authority certificate by the memory representation.
    """

    episodes = {episode.episode_id: episode for episode in ledger.episodes}
    source_ids = tuple(
        dict.fromkeys(lesson.supporting_episode_ids + lesson.contradicting_episode_ids)
    )
    missing = set(source_ids) - set(episodes)
    if missing:
        raise ValueError("lesson memory view references unknown episodes: " + ", ".join(sorted(missing)))
    return MemoryView(
        record_id=lesson.lesson_id,
        payload_hash=lesson.artifact_hash,
        kind=MemoryViewKind.DERIVED_LOSSY,
        source_pins=tuple(
            SourcePin(record_id=episode_id, payload_hash=episodes[episode_id].artifact_hash)
            for episode_id in source_ids
        ),
        transform_id=f"rakl-v3:lesson:{lesson.kind.value.lower()}",
        erasure_tags=LESSON_ERASURE_TAGS,
        required_canonical_ids=source_ids,
    )


def experience_memory_views(ledger: ExperienceLedger) -> Tuple[MemoryView, ...]:
    """Materialize the v3 experience ledger into existing memory-view contracts."""

    episode_views = tuple(episode_memory_view(episode) for episode in ledger.episodes)
    lesson_views = tuple(lesson_memory_view(lesson, ledger) for lesson in ledger.lessons)
    return episode_views + lesson_views
