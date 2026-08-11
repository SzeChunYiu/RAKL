from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple


class SubstrateKind(str, Enum):
    EVIDENCE = "EVIDENCE"
    EPISTEMIC = "EPISTEMIC"
    OPERATOR = "OPERATOR"
    EPISODE = "EPISODE"
    OBSTRUCTION = "OBSTRUCTION"
    STRATEGY = "STRATEGY"
    META_METHOD = "META_METHOD"


class SubstrateRelation(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    RESOLVED_BY = "RESOLVED_BY"
    APPLIES_TO = "APPLIES_TO"
    INSTANCE_OF = "INSTANCE_OF"
    USES = "USES"
    PRODUCED = "PRODUCED"
    FAILED_WITH = "FAILED_WITH"
    SUCCEEDED_WITH = "SUCCEEDED_WITH"
    SUPERSEDES = "SUPERSEDES"
    TRANSFERRED_TO = "TRANSFERRED_TO"


class EpisodeOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class LessonKind(str, Enum):
    OPERATOR = "OPERATOR"
    BOUNDARY = "BOUNDARY"
    STRATEGY = "STRATEGY"
    ROUTING = "ROUTING"
    DECOMPOSITION = "DECOMPOSITION"
    REPRESENTATION = "REPRESENTATION"
    META_METHOD = "META_METHOD"


class LessonAuthority(str, Enum):
    CANDIDATE = "CANDIDATE"
    VERIFIED_LOCAL = "VERIFIED_LOCAL"
    CONDITIONALLY_REUSABLE = "CONDITIONALLY_REUSABLE"
    PROOF_BACKED = "PROOF_BACKED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class SubstrateNode:
    node_id: str
    kind: SubstrateKind
    label: str
    payload_hash: str
    source_ids: Tuple[str, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.node_id or not self.label or not self.payload_hash:
            raise ValueError("substrate nodes require id, label, and payload_hash")
        if len({key for key, _ in self.metadata}) != len(self.metadata):
            raise ValueError("substrate node metadata keys must be unique")


@dataclass(frozen=True)
class SubstrateEdge:
    source_id: str
    target_id: str
    relation: SubstrateRelation
    rationale: str
    evidence_pointers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id or not self.rationale:
            raise ValueError("substrate edges require source, target, and rationale")


@dataclass(frozen=True)
class TaskEpisode:
    """Immutable record of what RAKL actually attempted and observed.

    Episodes are evidence roots.  They are never replaced by summaries or lessons.
    Derived abstractions must retain explicit episode lineage.
    """

    episode_id: str
    task_id: str
    atom_id: str
    context_hash: str
    problem_signature: Tuple[str, ...]
    fibre_snapshot_hash: str
    operator_ids: Tuple[str, ...]
    action_trace: Tuple[str, ...]
    observation_ids: Tuple[str, ...]
    verification_ids: Tuple[str, ...]
    outcome: EpisodeOutcome
    residual_signature: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str
    timestamp: str
    cost: float = 0.0

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("episode cost cannot be negative")


@dataclass(frozen=True)
class Lesson:
    """Versioned abstraction derived from immutable experience.

    A lesson can guide future search or routing, but its authority remains explicit.
    Promotion creates a new lesson version and never mutates or deletes episodes.
    """

    lesson_id: str
    kind: LessonKind
    trigger_signature: Tuple[str, ...]
    context_scope: Tuple[str, ...]
    action: str
    expected_effects: Tuple[str, ...]
    boundaries: Tuple[str, ...]
    supporting_episode_ids: Tuple[str, ...]
    contradicting_episode_ids: Tuple[str, ...]
    falsifier: str
    authority: LessonAuthority
    validation_obligations: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str
    parent_lesson_id: str | None = None


@dataclass(frozen=True)
class ExperienceLedger:
    episodes: Tuple[TaskEpisode, ...] = ()
    lessons: Tuple[Lesson, ...] = ()
    nodes: Tuple[SubstrateNode, ...] = ()
    edges: Tuple[SubstrateEdge, ...] = ()


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def validate_episode(episode: TaskEpisode) -> Tuple[str, ...]:
    reasons: list[str] = []
    for name in (
        "episode_id",
        "task_id",
        "atom_id",
        "context_hash",
        "fibre_snapshot_hash",
        "artifact_hash",
    ):
        if not getattr(episode, name):
            reasons.append(f"episode:{name}_missing")
    if _parse_time(episode.timestamp) is None:
        reasons.append("episode:timestamp_missing_or_invalid")
    if not episode.problem_signature:
        reasons.append("episode:problem_signature_missing")
    if not episode.action_trace:
        reasons.append("episode:action_trace_missing")
    if not episode.evidence_pointers:
        reasons.append("episode:evidence_pointers_missing")
    if episode.outcome in {EpisodeOutcome.FAILURE, EpisodeOutcome.PARTIAL_SUCCESS} and not episode.residual_signature:
        reasons.append("episode:residual_signature_required_for_non_success")
    return tuple(reasons)


def validate_lesson(lesson: Lesson) -> Tuple[str, ...]:
    reasons: list[str] = []
    for name in ("lesson_id", "action", "falsifier", "artifact_hash"):
        if not getattr(lesson, name):
            reasons.append(f"lesson:{name}_missing")
    if not lesson.trigger_signature:
        reasons.append("lesson:trigger_signature_missing")
    if not lesson.context_scope:
        reasons.append("lesson:context_scope_missing")
    if not lesson.expected_effects:
        reasons.append("lesson:expected_effects_missing")
    if not lesson.boundaries:
        reasons.append("lesson:boundaries_missing")
    if not lesson.supporting_episode_ids:
        reasons.append("lesson:supporting_episode_ids_missing")
    if not lesson.validation_obligations:
        reasons.append("lesson:validation_obligations_missing")
    if not lesson.evidence_pointers:
        reasons.append("lesson:evidence_pointers_missing")
    return tuple(reasons)


def _node_kind_for_lesson(lesson: Lesson) -> SubstrateKind:
    if lesson.kind is LessonKind.OPERATOR:
        return SubstrateKind.OPERATOR
    if lesson.kind is LessonKind.BOUNDARY:
        return SubstrateKind.OBSTRUCTION
    if lesson.kind is LessonKind.STRATEGY:
        return SubstrateKind.STRATEGY
    return SubstrateKind.META_METHOD


def add_episode(ledger: ExperienceLedger, episode: TaskEpisode) -> ExperienceLedger:
    reasons = validate_episode(episode)
    if reasons:
        raise ValueError("invalid episode: " + ", ".join(reasons))
    if any(item.episode_id == episode.episode_id for item in ledger.episodes):
        raise ValueError(f"duplicate episode id: {episode.episode_id}")
    if any(node.node_id == episode.episode_id for node in ledger.nodes):
        raise ValueError(f"duplicate substrate node id: {episode.episode_id}")
    node = SubstrateNode(
        node_id=episode.episode_id,
        kind=SubstrateKind.EPISODE,
        label=f"episode:{episode.task_id}:{episode.atom_id}",
        payload_hash=episode.artifact_hash,
        metadata=(("outcome", episode.outcome.value), ("context_hash", episode.context_hash)),
    )
    return ExperienceLedger(
        episodes=ledger.episodes + (episode,),
        lessons=ledger.lessons,
        nodes=ledger.nodes + (node,),
        edges=ledger.edges,
    )


def add_lesson(ledger: ExperienceLedger, lesson: Lesson) -> ExperienceLedger:
    reasons = validate_lesson(lesson)
    if reasons:
        raise ValueError("invalid lesson: " + ", ".join(reasons))
    if any(item.lesson_id == lesson.lesson_id for item in ledger.lessons):
        raise ValueError(f"duplicate lesson id: {lesson.lesson_id}")
    episode_ids = {item.episode_id for item in ledger.episodes}
    missing = (set(lesson.supporting_episode_ids) | set(lesson.contradicting_episode_ids)) - episode_ids
    if missing:
        raise ValueError("lesson references unknown episodes: " + ", ".join(sorted(missing)))
    if lesson.parent_lesson_id is not None and lesson.parent_lesson_id not in {item.lesson_id for item in ledger.lessons}:
        raise ValueError("lesson parent_lesson_id does not exist")

    node = SubstrateNode(
        node_id=lesson.lesson_id,
        kind=_node_kind_for_lesson(lesson),
        label=f"lesson:{lesson.kind.value}:{lesson.lesson_id}",
        payload_hash=lesson.artifact_hash,
        source_ids=lesson.supporting_episode_ids + lesson.contradicting_episode_ids,
        metadata=(("authority", lesson.authority.value),),
    )
    edges = list(ledger.edges)
    for episode_id in lesson.supporting_episode_ids:
        edges.append(SubstrateEdge(episode_id, lesson.lesson_id, SubstrateRelation.SUPPORTS, "episode supports derived lesson", lesson.evidence_pointers))
    for episode_id in lesson.contradicting_episode_ids:
        edges.append(SubstrateEdge(episode_id, lesson.lesson_id, SubstrateRelation.CONTRADICTS, "episode contradicts or bounds derived lesson", lesson.evidence_pointers))
    if lesson.parent_lesson_id is not None:
        edges.append(SubstrateEdge(lesson.lesson_id, lesson.parent_lesson_id, SubstrateRelation.SUPERSEDES, "new lesson version supersedes prior abstraction", lesson.evidence_pointers))

    return ExperienceLedger(
        episodes=ledger.episodes,
        lessons=ledger.lessons + (lesson,),
        nodes=ledger.nodes + (node,),
        edges=tuple(edges),
    )


def add_substrate_node(ledger: ExperienceLedger, node: SubstrateNode) -> ExperienceLedger:
    if any(item.node_id == node.node_id for item in ledger.nodes):
        raise ValueError(f"duplicate substrate node id: {node.node_id}")
    return ExperienceLedger(ledger.episodes, ledger.lessons, ledger.nodes + (node,), ledger.edges)


def add_substrate_edge(ledger: ExperienceLedger, edge: SubstrateEdge) -> ExperienceLedger:
    node_ids = {item.node_id for item in ledger.nodes}
    if edge.source_id not in node_ids or edge.target_id not in node_ids:
        raise ValueError("substrate edge endpoints must already exist")
    if edge in ledger.edges:
        return ledger
    return ExperienceLedger(ledger.episodes, ledger.lessons, ledger.nodes, ledger.edges + (edge,))


def query_nodes(ledger: ExperienceLedger, *kinds: SubstrateKind) -> Tuple[SubstrateNode, ...]:
    allowed = set(kinds)
    if not allowed:
        return ledger.nodes
    return tuple(node for node in ledger.nodes if node.kind in allowed)


def episode_portrait(ledger: ExperienceLedger) -> dict[str, object]:
    outcomes: dict[str, int] = {}
    lesson_authority: dict[str, int] = {}
    for episode in ledger.episodes:
        outcomes[episode.outcome.value] = outcomes.get(episode.outcome.value, 0) + 1
    for lesson in ledger.lessons:
        lesson_authority[lesson.authority.value] = lesson_authority.get(lesson.authority.value, 0) + 1
    return {
        "episode_count": len(ledger.episodes),
        "lesson_count": len(ledger.lessons),
        "node_count": len(ledger.nodes),
        "edge_count": len(ledger.edges),
        "outcomes": dict(sorted(outcomes.items())),
        "lesson_authority": dict(sorted(lesson_authority.items())),
    }
