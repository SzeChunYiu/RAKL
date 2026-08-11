from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Tuple

from .v3_authority import (
    AttestationPurpose,
    ProtectedAuthorityContext,
    canonical_json_bytes,
    resolve_protected_attestation,
)


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
    authority_attestation_id: str | None = None
    authority_subject_hash: str | None = None
    authority_evidence_packet_hash: str | None = None
    promotion_attestation_id: str | None = None
    authority_evidence_packet_artifact_id: str | None = None


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


def _is_sha256_hexdigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def episode_content_bytes(episode: TaskEpisode) -> bytes:
    """Canonical exact bytes whose digest is the episode identity."""

    return canonical_json_bytes(
        {
            "episode_id": episode.episode_id,
            "task_id": episode.task_id,
            "atom_id": episode.atom_id,
            "context_hash": episode.context_hash,
            "problem_signature": list(episode.problem_signature),
            "fibre_snapshot_hash": episode.fibre_snapshot_hash,
            "operator_ids": list(episode.operator_ids),
            "action_trace": list(episode.action_trace),
            "observation_ids": list(episode.observation_ids),
            "verification_ids": list(episode.verification_ids),
            "outcome": episode.outcome.value,
            "residual_signature": list(episode.residual_signature),
            "evidence_pointers": list(episode.evidence_pointers),
            "timestamp": episode.timestamp,
            "cost": episode.cost,
        }
    )


def lesson_content_bytes(lesson: Lesson) -> bytes:
    """Canonical exact bytes whose digest is the lesson-version identity."""

    payload: dict[str, object] = {
            "lesson_id": lesson.lesson_id,
            "kind": lesson.kind.value,
            "trigger_signature": list(lesson.trigger_signature),
            "context_scope": list(lesson.context_scope),
            "action": lesson.action,
            "expected_effects": list(lesson.expected_effects),
            "boundaries": list(lesson.boundaries),
            "supporting_episode_ids": list(lesson.supporting_episode_ids),
            "contradicting_episode_ids": list(lesson.contradicting_episode_ids),
            "falsifier": lesson.falsifier,
            "authority": lesson.authority.value,
            "validation_obligations": list(lesson.validation_obligations),
            "evidence_pointers": list(lesson.evidence_pointers),
            "parent_lesson_id": lesson.parent_lesson_id,
            "authority_attestation_id": lesson.authority_attestation_id,
            "authority_subject_hash": lesson.authority_subject_hash,
            "authority_evidence_packet_hash": lesson.authority_evidence_packet_hash,
        }
    # Preserve candidate hashes from the pre-promotion substrate while binding
    # the exact final promotion receipt into every promoted lesson version.
    if lesson.promotion_attestation_id is not None or lesson.authority_evidence_packet_artifact_id is not None:
        payload["promotion_attestation_id"] = lesson.promotion_attestation_id
        payload["authority_evidence_packet_artifact_id"] = lesson.authority_evidence_packet_artifact_id
    return canonical_json_bytes(payload)


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
    if episode.outcome in {EpisodeOutcome.FAILURE, EpisodeOutcome.PARTIAL_SUCCESS, EpisodeOutcome.BLOCKED} and not episode.residual_signature:
        reasons.append("episode:residual_signature_required_for_non_success")
    if episode.artifact_hash and not _is_sha256_hexdigest(episode.artifact_hash):
        reasons.append("episode:artifact_hash_invalid")
    elif episode.artifact_hash and sha256(episode_content_bytes(episode)).hexdigest() != episode.artifact_hash:
        reasons.append("episode:artifact_hash_mismatch")
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
    if lesson.artifact_hash and not _is_sha256_hexdigest(lesson.artifact_hash):
        reasons.append("lesson:artifact_hash_invalid")
    elif lesson.artifact_hash and sha256(lesson_content_bytes(lesson)).hexdigest() != lesson.artifact_hash:
        reasons.append("lesson:artifact_hash_mismatch")
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


def add_lesson(
    ledger: ExperienceLedger,
    lesson: Lesson,
    *,
    authority_context: ProtectedAuthorityContext | None = None,
) -> ExperienceLedger:
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
    if lesson.authority is not LessonAuthority.CANDIDATE:
        if lesson.parent_lesson_id is None:
            raise ValueError("non-candidate lesson requires an exact parent lesson")
        purpose = {
            LessonAuthority.VERIFIED_LOCAL: AttestationPurpose.LESSON_VERIFICATION,
            LessonAuthority.CONDITIONALLY_REUSABLE: AttestationPurpose.LESSON_TRANSFER,
            LessonAuthority.PROOF_BACKED: AttestationPurpose.LESSON_PROOF,
            LessonAuthority.SUPERSEDED: AttestationPurpose.LESSON_VERIFICATION,
        }[lesson.authority]
        if not lesson.authority_subject_hash:
            raise ValueError("non-candidate lesson requires resolved protected authority attestation")
        required_hashes = tuple(
            item.artifact_hash
            for item in ledger.episodes
            if item.episode_id in set(lesson.supporting_episode_ids)
        )
        resolution = resolve_protected_attestation(
            authority_context,
            lesson.authority_attestation_id,
            purpose=purpose,
            subject_hash=lesson.authority_subject_hash,
            required_artifact_hashes=required_hashes,
        )
        if not resolution.valid:
            raise ValueError(
                "non-candidate lesson requires resolved protected authority attestation: "
                + ", ".join(resolution.reasons)
            )
        parent = next(item for item in ledger.lessons if item.lesson_id == lesson.parent_lesson_id)
        immutable_fields = (
            "kind", "trigger_signature", "context_scope", "action",
            "expected_effects", "boundaries", "falsifier", "validation_obligations",
        )
        if any(getattr(lesson, name) != getattr(parent, name) for name in immutable_fields):
            raise ValueError("promoted lesson changes unreviewed parent content")
        if lesson.authority_subject_hash != parent.artifact_hash:
            raise ValueError("promoted lesson authority subject is not its exact parent")
        if not lesson.authority_evidence_packet_hash:
            raise ValueError("promoted lesson exact evidence packet binding is missing")
        if not lesson.promotion_attestation_id or not lesson.authority_evidence_packet_artifact_id:
            raise ValueError("promoted lesson exact-final-content attestation is missing")
        attestation = next(
            item for item in authority_context.attestations
            if item.attestation_id == lesson.authority_attestation_id
        )
        episode_id_by_hash = {item.artifact_hash: item.episode_id for item in ledger.episodes}
        attested_episode_ids = {
            episode_id_by_hash[digest]
            for _, digest in attestation.evidence_bindings
            if digest in episode_id_by_hash
        }
        if attested_episode_ids != set(lesson.supporting_episode_ids):
            raise ValueError("promoted lesson support does not equal attested episode lineage")
        packet_artifact = next(
            (
                item
                for item in authority_context.artifacts
                if item.artifact_id == lesson.authority_evidence_packet_artifact_id
            ),
            None,
        )
        if (
            packet_artifact is None
            or not packet_artifact.content_valid
            or packet_artifact.payload_sha256 != lesson.authority_evidence_packet_hash
        ):
            raise ValueError("promoted lesson exact evidence packet artifact is unresolved")
        promotion = resolve_protected_attestation(
            authority_context,
            lesson.promotion_attestation_id,
            purpose=AttestationPurpose.LESSON_PROMOTION,
            subject_hash=lesson.artifact_hash,
            required_artifact_ids=(lesson.authority_evidence_packet_artifact_id,),
            required_artifact_hashes=(
                parent.artifact_hash,
                lesson.authority_evidence_packet_hash,
            ) + required_hashes,
        )
        if not promotion.valid:
            raise ValueError(
                "promoted lesson requires exact-final-content promotion attestation: "
                + ", ".join(promotion.reasons)
            )

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
