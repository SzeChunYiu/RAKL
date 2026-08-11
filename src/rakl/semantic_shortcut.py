from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
from itertools import combinations
from typing import Mapping, Sequence, Tuple


class ShortcutMode(str, Enum):
    SEARCH = "SEARCH"
    JUMP = "JUMP"
    GLUE = "GLUE"
    LIFT = "LIFT"
    CANNOT_CHECK = "CANNOT_CHECK"


class RouteSearchStatus(str, Enum):
    MATCHES_FOUND = "MATCHES_FOUND"
    NO_VIABLE_MATCH = "NO_VIABLE_MATCH"
    NOT_RUN = "NOT_RUN"


class ShortcutReviewVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


class TransformationEpisodeAuthority(str, Enum):
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    SOURCE_EVENT_VERIFIED = "SOURCE_EVENT_VERIFIED"
    VERIFIED_LOCAL = "VERIFIED_LOCAL"
    PROOF_BACKED = "PROOF_BACKED"
    SUPERSEDED = "SUPERSEDED"


_VERIFIED_SOURCE_AUTHORITIES = frozenset(
    {
        TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED,
        TransformationEpisodeAuthority.VERIFIED_LOCAL,
        TransformationEpisodeAuthority.PROOF_BACKED,
    }
)


@dataclass(frozen=True)
class ObstructionFingerprint:
    """Vocabulary-light structural description of one active obstruction.

    The coordinates intentionally describe *roles and relations* rather than
    domain nouns.  This lets a mathematical proof obstruction be compared with
    structurally equivalent episodes from science, engineering, organizations,
    games, journalism, or ordinary life without treating embedding proximity as
    a structural witness.
    """

    obstruction_id: str
    domain: str
    roles: Tuple[str, ...]
    relations: Tuple[str, ...]
    constraints: Tuple[str, ...]
    failure_mechanisms: Tuple[str, ...]
    invariants_to_preserve: Tuple[str, ...]
    desired_transition: Tuple[str, ...]
    forbidden_losses: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ObstructionTransformationEpisode:
    """One recorded ``obstruction -> transformation -> changed state`` episode.

    A source episode is reusable experience, not target authority.  Even a
    proof-backed source still requires a target StructuralMappingWitness and
    target-domain validation before it can justify a candidate move.
    """

    episode_id: str
    source_domain: str
    source_context: str
    source_obstruction: ObstructionFingerprint
    transformation_name: str
    operation: str
    preconditions: Tuple[str, ...]
    resulting_relations: Tuple[str, ...]
    preserved_invariants: Tuple[str, ...]
    relaxed_or_broken_constraints: Tuple[str, ...]
    known_breakpoints: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    authority: TransformationEpisodeAuthority
    artifact_hash: str
    lineage_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ObstructionTransformationMemory:
    """Content-bound memory of reusable transformation episodes.

    This is distinct from the success-tool inventory and failure lattice.  Those
    memories answer "what worked?" and "what failed?".  This memory compiles the
    relational unit RAKL needs for semantic shortcuts:

        O --T--> O'

    It may contain proposal-only extracted episodes, but proposal-only episodes
    are never considered viable routes by the strict shortcut gate.
    """

    memory_id: str
    source_universe: Tuple[str, ...]
    episodes: Tuple[ObstructionTransformationEpisode, ...]
    evidence_pointers: Tuple[str, ...]
    snapshot_hash: str = ""


@dataclass(frozen=True)
class StructuralMappingWitness:
    """Explicit source-to-target relational witness for SEARCH/JUMP/GLUE."""

    witness_id: str
    episode_id: str
    target_obstruction_id: str
    role_mapping: Tuple[Tuple[str, str], ...]
    shared_relations: Tuple[str, ...]
    shared_constraints: Tuple[str, ...]
    precondition_mapping: Tuple[Tuple[str, str], ...]
    unmatched_source_preconditions: Tuple[str, ...]
    disanalogies: Tuple[str, ...]
    target_validation_obligations: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True)
class TransformationCompositionWitness:
    """Compatibility/interface witness for composing partial transformations."""

    composition_id: str
    target_obstruction_id: str
    episode_ids: Tuple[str, ...]
    operation_order: Tuple[str, ...]
    interface_obligations: Tuple[str, ...]
    incompatibilities_checked: Tuple[str, ...]
    target_validation_obligations: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True)
class ExhaustionWitness:
    """Bounded evidence that invention is considered only after prior lanes.

    ``coverage_receipt_hash`` binds the "no viable route" statement to an
    explicit cross-problem search universe.  It prevents a local failed search
    from being silently upgraded into "recorded knowledge has no answer".
    """

    target_obstruction_id: str
    search_boundary: str
    searched_domains: Tuple[str, ...]
    searched_method_families: Tuple[str, ...]
    rejected_direct_episode_ids: Tuple[str, ...]
    rejected_jump_episode_ids: Tuple[str, ...]
    rejected_glue_composition_ids: Tuple[str, ...]
    rejection_reasons: Tuple[str, ...]
    residual_failure_ids: Tuple[str, ...]
    repeated_residual_features: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str
    coverage_receipt_hash: str


@dataclass(frozen=True)
class MissingTransformationSpecification:
    """Inverse-invention target emitted by LIFT, never a solved candidate."""

    spec_id: str
    target_obstruction_id: str
    residual_failure_ids: Tuple[str, ...]
    must_preserve: Tuple[str, ...]
    must_break: Tuple[str, ...]
    must_expose: Tuple[str, ...]
    must_reduce: Tuple[str, ...]
    allowed_representation_changes: Tuple[str, ...]
    forbidden_shortcuts: Tuple[str, ...]
    validation_obligations: Tuple[str, ...]
    falsifiers: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]
    artifact_hash: str


@dataclass(frozen=True)
class StructuralMatch:
    episode_id: str
    source_domain: str
    score: int
    matched_relations: Tuple[str, ...]
    matched_constraints: Tuple[str, ...]
    matched_failure_mechanisms: Tuple[str, ...]
    matched_effects: Tuple[str, ...]
    matched_preserved_invariants: Tuple[str, ...]
    forbidden_loss_conflicts: Tuple[str, ...]


@dataclass(frozen=True)
class ShortcutCandidateSet:
    """Deterministic proposal set derived from one memory snapshot."""

    direct_matches: Tuple[StructuralMatch, ...]
    jump_matches: Tuple[StructuralMatch, ...]
    glue_episode_sets: Tuple[Tuple[str, ...], ...]


@dataclass(frozen=True)
class ObstructionTransformationReview:
    """Frozen invention-last semantic-shortcut decision for one math atom."""

    review_id: str
    target_atom_id: str
    target_context_hash: str
    research_memory_review_hash: str
    episode_memory_snapshot_hash: str
    obstruction: ObstructionFingerprint
    direct_search_status: RouteSearchStatus
    jump_search_status: RouteSearchStatus
    glue_search_status: RouteSearchStatus
    selected_mode: ShortcutMode
    direct_candidate_episode_ids: Tuple[str, ...] = ()
    direct_mapping_witnesses: Tuple[StructuralMappingWitness, ...] = ()
    jump_mapping_witnesses: Tuple[StructuralMappingWitness, ...] = ()
    glue_witness: TransformationCompositionWitness | None = None
    selected_episode_ids: Tuple[str, ...] = ()
    exhaustion_witness: ExhaustionWitness | None = None
    missing_transformation_specification: MissingTransformationSpecification | None = None
    unresolved_warnings: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()
    artifact_hash: str = ""


@dataclass(frozen=True)
class ShortcutReviewReport:
    verdict: ShortcutReviewVerdict
    reasons: Tuple[str, ...]
    candidate_route_ready: bool
    selected_mode: ShortcutMode


REQUIRED_SHORTCUT_ACTIONS: Tuple[str, ...] = (
    "fingerprint_active_relational_obstruction",
    "compile_or_load_content_bound_transformation_memory",
    "query_recorded_obstruction_transformation_episodes",
    "record_structural_mapping_or_composition_witnesses",
    "bind_no_match_claims_to_cross_problem_coverage",
    "exhaust_search_jump_and_glue_before_lift",
    "freeze_missing_transformation_specification_if_lifted",
    "record_obstruction_transformation_review_in_public_trace",
)


def _nonempty(values: Sequence[str]) -> bool:
    return bool(values) and all(bool(value) for value in values)


def _sorted_unique(values: Sequence[str]) -> Tuple[str, ...]:
    return tuple(sorted(set(values)))


def _fingerprint_payload(fingerprint: ObstructionFingerprint) -> dict[str, object]:
    return {
        "obstruction_id": fingerprint.obstruction_id,
        "domain": fingerprint.domain,
        "roles": list(fingerprint.roles),
        "relations": list(fingerprint.relations),
        "constraints": list(fingerprint.constraints),
        "failure_mechanisms": list(fingerprint.failure_mechanisms),
        "invariants_to_preserve": list(fingerprint.invariants_to_preserve),
        "desired_transition": list(fingerprint.desired_transition),
        "forbidden_losses": list(fingerprint.forbidden_losses),
    }


def _episode_payload(episode: ObstructionTransformationEpisode) -> dict[str, object]:
    return {
        "episode_id": episode.episode_id,
        "source_domain": episode.source_domain,
        "source_context": episode.source_context,
        "source_obstruction": _fingerprint_payload(episode.source_obstruction),
        "transformation_name": episode.transformation_name,
        "operation": episode.operation,
        "preconditions": list(episode.preconditions),
        "resulting_relations": list(episode.resulting_relations),
        "preserved_invariants": list(episode.preserved_invariants),
        "relaxed_or_broken_constraints": list(episode.relaxed_or_broken_constraints),
        "known_breakpoints": list(episode.known_breakpoints),
        "evidence_pointers": list(episode.evidence_pointers),
        "authority": episode.authority.value,
        "artifact_hash": episode.artifact_hash,
        "lineage_ids": list(episode.lineage_ids),
    }


def _memory_hash(
    memory_id: str,
    source_universe: Sequence[str],
    episodes: Sequence[ObstructionTransformationEpisode],
    evidence_pointers: Sequence[str],
) -> str:
    payload = {
        "memory_id": memory_id,
        "source_universe": list(source_universe),
        "episodes": [
            _episode_payload(episode)
            for episode in sorted(episodes, key=lambda item: item.episode_id)
        ],
        "evidence_pointers": list(evidence_pointers),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_obstruction_fingerprint(
    fingerprint: ObstructionFingerprint,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not fingerprint.obstruction_id:
        reasons.append("obstruction_id_missing")
    if not fingerprint.domain:
        reasons.append("obstruction_domain_missing")
    for field_name in (
        "roles",
        "relations",
        "constraints",
        "failure_mechanisms",
        "invariants_to_preserve",
        "desired_transition",
    ):
        if not _nonempty(getattr(fingerprint, field_name)):
            reasons.append(f"obstruction_{field_name}_missing")
    if any(not item for item in fingerprint.forbidden_losses):
        reasons.append("obstruction_forbidden_losses_contains_empty_value")
    return tuple(reasons)


def validate_transformation_episode(
    episode: ObstructionTransformationEpisode,
) -> Tuple[str, ...]:
    reasons = list(validate_obstruction_fingerprint(episode.source_obstruction))
    for field_name in (
        "episode_id",
        "source_domain",
        "source_context",
        "transformation_name",
        "operation",
        "artifact_hash",
    ):
        if not getattr(episode, field_name):
            reasons.append(f"episode_{field_name}_missing")
    for field_name in (
        "preconditions",
        "resulting_relations",
        "preserved_invariants",
        "known_breakpoints",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(episode, field_name)):
            reasons.append(f"episode_{field_name}_missing")
    if any(not value for value in episode.relaxed_or_broken_constraints):
        reasons.append("episode_relaxed_or_broken_constraints_contains_empty_value")
    return tuple(reasons)


def build_transformation_memory(
    *,
    memory_id: str,
    source_universe: Tuple[str, ...],
    episodes: Tuple[ObstructionTransformationEpisode, ...],
    evidence_pointers: Tuple[str, ...],
) -> ObstructionTransformationMemory:
    if not memory_id:
        raise ValueError("transformation memory requires a memory_id")
    if not _nonempty(source_universe):
        raise ValueError("transformation memory requires a bound source_universe")
    if not _nonempty(evidence_pointers):
        raise ValueError("transformation memory requires evidence pointers")
    ids = [episode.episode_id for episode in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError("transformation memory episode ids must be unique")
    invalid = [
        f"{episode.episode_id}:{','.join(validate_transformation_episode(episode))}"
        for episode in episodes
        if validate_transformation_episode(episode)
    ]
    if invalid:
        raise ValueError("invalid transformation episode(s): " + "; ".join(invalid))
    return ObstructionTransformationMemory(
        memory_id=memory_id,
        source_universe=source_universe,
        episodes=episodes,
        evidence_pointers=evidence_pointers,
        snapshot_hash=_memory_hash(memory_id, source_universe, episodes, evidence_pointers),
    )


def validate_transformation_memory(
    memory: ObstructionTransformationMemory | None,
) -> Tuple[str, ...]:
    if memory is None:
        return ("transformation_memory_missing",)
    reasons: list[str] = []
    if not memory.memory_id:
        reasons.append("transformation_memory_id_missing")
    if not _nonempty(memory.source_universe):
        reasons.append("transformation_memory_source_universe_missing")
    if not _nonempty(memory.evidence_pointers):
        reasons.append("transformation_memory_evidence_missing")
    ids = [episode.episode_id for episode in memory.episodes]
    if len(ids) != len(set(ids)):
        reasons.append("transformation_memory_duplicate_episode_id")
    for episode in memory.episodes:
        reasons.extend(
            f"{episode.episode_id}:{reason}"
            for reason in validate_transformation_episode(episode)
        )
    expected = _memory_hash(
        memory.memory_id,
        memory.source_universe,
        memory.episodes,
        memory.evidence_pointers,
    )
    if not memory.snapshot_hash:
        reasons.append("transformation_memory_snapshot_hash_missing")
    elif memory.snapshot_hash != expected:
        reasons.append("transformation_memory_snapshot_hash_mismatch")
    return tuple(reasons)


def add_transformation_episode(
    memory: ObstructionTransformationMemory,
    episode: ObstructionTransformationEpisode,
) -> ObstructionTransformationMemory:
    reasons = validate_transformation_memory(memory)
    if reasons:
        raise ValueError("invalid transformation memory: " + ", ".join(reasons))
    episode_reasons = validate_transformation_episode(episode)
    if episode_reasons:
        raise ValueError("invalid transformation episode: " + ", ".join(episode_reasons))
    if any(existing.episode_id == episode.episode_id for existing in memory.episodes):
        raise ValueError(f"duplicate transformation episode id: {episode.episode_id}")
    return build_transformation_memory(
        memory_id=memory.memory_id,
        source_universe=memory.source_universe,
        episodes=memory.episodes + (episode,),
        evidence_pointers=memory.evidence_pointers,
    )


def replace_transformation_episode(
    memory: ObstructionTransformationMemory,
    episode: ObstructionTransformationEpisode,
) -> ObstructionTransformationMemory:
    """Version-preserving replacement for authority/supersession updates."""

    reasons = validate_transformation_memory(memory)
    if reasons:
        raise ValueError("invalid transformation memory: " + ", ".join(reasons))
    episode_reasons = validate_transformation_episode(episode)
    if episode_reasons:
        raise ValueError("invalid transformation episode: " + ", ".join(episode_reasons))
    if not any(existing.episode_id == episode.episode_id for existing in memory.episodes):
        raise ValueError(f"unknown transformation episode id: {episode.episode_id}")
    episodes = tuple(
        episode if existing.episode_id == episode.episode_id else existing
        for existing in memory.episodes
    )
    return build_transformation_memory(
        memory_id=memory.memory_id,
        source_universe=memory.source_universe,
        episodes=episodes,
        evidence_pointers=memory.evidence_pointers,
    )


def find_transformation_episode(
    memory: ObstructionTransformationMemory,
    episode_id: str,
) -> ObstructionTransformationEpisode | None:
    for episode in memory.episodes:
        if episode.episode_id == episode_id:
            return episode
    return None


def rank_obstruction_transformations(
    target: ObstructionFingerprint,
    episodes: Sequence[ObstructionTransformationEpisode],
    *,
    top_k: int = 12,
) -> Tuple[StructuralMatch, ...]:
    """Rank normalized relational candidates without certifying transport.

    The score emphasizes the *failure mechanism* and the *effect of the source
    transformation*, not lexical similarity.  Forbidden target losses are a
    hard negative signal.  Every retained candidate still needs an explicit
    target mapping witness.
    """

    target_reasons = validate_obstruction_fingerprint(target)
    if target_reasons:
        raise ValueError("invalid target obstruction: " + ", ".join(target_reasons))
    if top_k < 1:
        raise ValueError("top_k must be positive")

    ranked: list[tuple[int, str, StructuralMatch]] = []
    target_relations = set(target.relations)
    target_constraints = set(target.constraints)
    target_failures = set(target.failure_mechanisms)
    target_invariants = set(target.invariants_to_preserve)
    target_transition = set(target.desired_transition)
    target_forbidden = set(target.forbidden_losses)

    for episode in episodes:
        if episode.authority is TransformationEpisodeAuthority.SUPERSEDED:
            continue
        if validate_transformation_episode(episode):
            continue
        source = episode.source_obstruction
        matched_relations = _sorted_unique(target_relations & set(source.relations))
        matched_constraints = _sorted_unique(target_constraints & set(source.constraints))
        matched_failures = _sorted_unique(
            target_failures & set(source.failure_mechanisms)
        )
        matched_effects = _sorted_unique(
            target_transition & set(episode.resulting_relations)
        )
        matched_invariants = _sorted_unique(
            target_invariants & set(episode.preserved_invariants)
        )
        forbidden_conflicts = _sorted_unique(
            target_forbidden & set(episode.relaxed_or_broken_constraints)
        )
        score = (
            5 * len(matched_failures)
            + 4 * len(matched_effects)
            + 3 * len(matched_relations)
            + 2 * len(matched_constraints)
            + 2 * len(matched_invariants)
            - 8 * len(forbidden_conflicts)
        )
        if score <= 0:
            continue
        match = StructuralMatch(
            episode_id=episode.episode_id,
            source_domain=episode.source_domain,
            score=score,
            matched_relations=matched_relations,
            matched_constraints=matched_constraints,
            matched_failure_mechanisms=matched_failures,
            matched_effects=matched_effects,
            matched_preserved_invariants=matched_invariants,
            forbidden_loss_conflicts=forbidden_conflicts,
        )
        ranked.append((-score, episode.episode_id, match))
    ranked.sort(key=lambda row: (row[0], row[1]))
    return tuple(match for _, _, match in ranked[:top_k])


def _source_episode_viable(
    match: StructuralMatch,
    episode: ObstructionTransformationEpisode,
) -> bool:
    return bool(
        episode.authority in _VERIFIED_SOURCE_AUTHORITIES
        and match.matched_failure_mechanisms
        and match.matched_effects
        and not match.forbidden_loss_conflicts
    )


def discover_shortcut_candidates(
    target: ObstructionFingerprint,
    memory: ObstructionTransformationMemory,
    *,
    top_k: int = 12,
) -> ShortcutCandidateSet:
    """Derive SEARCH/JUMP/GLUE proposal candidates from one frozen memory.

    SEARCH is deliberately conservative: it is a viable same-domain episode.
    JUMP is a viable structurally similar episode from another registered domain.
    GLUE candidates are pairs whose *combined verified source effects* cover the
    desired transition.  Interface compatibility is not assumed; an explicit
    TransformationCompositionWitness remains mandatory.
    """

    memory_reasons = validate_transformation_memory(memory)
    if memory_reasons:
        raise ValueError("invalid transformation memory: " + ", ".join(memory_reasons))

    matches = rank_obstruction_transformations(target, memory.episodes, top_k=top_k)
    viable: list[StructuralMatch] = []
    for match in matches:
        episode = find_transformation_episode(memory, match.episode_id)
        if episode is not None and _source_episode_viable(match, episode):
            viable.append(match)

    direct = tuple(match for match in viable if match.source_domain == target.domain)
    jump = tuple(match for match in viable if match.source_domain != target.domain)

    desired = set(target.desired_transition)
    glue_sets: list[Tuple[str, ...]] = []
    partial = tuple(
        match
        for match in viable
        if match.matched_effects and set(match.matched_effects) != desired
    )
    for left, right in combinations(partial, 2):
        if set(left.matched_effects) | set(right.matched_effects) >= desired:
            glue_sets.append(tuple(sorted((left.episode_id, right.episode_id))))

    return ShortcutCandidateSet(
        direct_matches=direct,
        jump_matches=jump,
        glue_episode_sets=tuple(sorted(set(glue_sets))),
    )


def repeated_residual_features(
    residual_signatures: Mapping[str, Sequence[str]],
    *,
    minimum_support: int = 2,
) -> Tuple[str, ...]:
    """Return residual coordinates repeated across distinct failed attempts."""

    if minimum_support < 2:
        raise ValueError("minimum_support must be at least 2")
    counter: Counter[str] = Counter()
    for features in residual_signatures.values():
        counter.update(set(features))
    return tuple(
        sorted(feature for feature, count in counter.items() if count >= minimum_support)
    )


def synthesize_missing_transformation_specification(
    target: ObstructionFingerprint,
    *,
    spec_id: str,
    residual_signatures: Mapping[str, Sequence[str]],
    must_reduce: Tuple[str, ...],
    allowed_representation_changes: Tuple[str, ...],
    validation_obligations: Tuple[str, ...],
    falsifiers: Tuple[str, ...],
    evidence_pointers: Tuple[str, ...],
    artifact_hash: str,
) -> MissingTransformationSpecification:
    """Turn repeated failures into constraints for downstream invention.

    The output is an *inverse specification* for a missing transformation.  It
    does not invent an operator and does not grant authority.  A downstream
    mechanism-invention lane can now synthesize candidate definitions,
    representations, auxiliary objects, invariants or operators against a
    frozen contract instead of free-form creativity.
    """

    reasons = validate_obstruction_fingerprint(target)
    if reasons:
        raise ValueError("invalid target obstruction: " + ", ".join(reasons))
    repeated = repeated_residual_features(residual_signatures)
    if len(residual_signatures) < 2 or not repeated:
        raise ValueError(
            "LIFT requires at least two failed attempts sharing a residual feature"
        )
    for name, values in (
        ("must_reduce", must_reduce),
        ("allowed_representation_changes", allowed_representation_changes),
        ("validation_obligations", validation_obligations),
        ("falsifiers", falsifiers),
        ("evidence_pointers", evidence_pointers),
    ):
        if not _nonempty(values):
            raise ValueError(f"{name} must be nonempty")
    if not spec_id or not artifact_hash:
        raise ValueError("spec_id and artifact_hash must be nonempty")

    forbidden = target.forbidden_losses or (
        "authority_escalation_without_target_validation",
    )
    return MissingTransformationSpecification(
        spec_id=spec_id,
        target_obstruction_id=target.obstruction_id,
        residual_failure_ids=tuple(sorted(residual_signatures)),
        must_preserve=target.invariants_to_preserve,
        must_break=repeated,
        must_expose=target.desired_transition,
        must_reduce=must_reduce,
        allowed_representation_changes=allowed_representation_changes,
        forbidden_shortcuts=forbidden,
        validation_obligations=validation_obligations,
        falsifiers=falsifiers,
        evidence_pointers=evidence_pointers,
        artifact_hash=artifact_hash,
    )


def _validate_mapping(
    witness: StructuralMappingWitness,
    *,
    target: ObstructionFingerprint,
    episode: ObstructionTransformationEpisode | None,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not witness.witness_id or not witness.episode_id or not witness.artifact_hash:
        reasons.append("mapping_identity_missing")
    if witness.target_obstruction_id != target.obstruction_id:
        reasons.append("mapping_target_mismatch")
    if episode is None:
        reasons.append("mapping_episode_not_in_bound_memory")
        return tuple(reasons)
    if episode.authority not in _VERIFIED_SOURCE_AUTHORITIES:
        reasons.append("mapping_source_episode_not_verified")
    if not witness.role_mapping or any(
        not source or not mapped for source, mapped in witness.role_mapping
    ):
        reasons.append("mapping_role_mapping_missing")
    source_roles = {source for source, _ in witness.role_mapping}
    if not source_roles.issubset(set(episode.source_obstruction.roles)):
        reasons.append("mapping_source_role_not_in_episode")
    target_roles = {mapped for _, mapped in witness.role_mapping}
    if not target_roles.issubset(set(target.roles)):
        reasons.append("mapping_target_role_not_in_obstruction")
    if not _nonempty(witness.shared_relations):
        reasons.append("mapping_shared_relations_missing")
    elif not set(witness.shared_relations).issubset(
        set(episode.source_obstruction.relations) & set(target.relations)
    ):
        reasons.append("mapping_shared_relations_not_jointly_present")
    if not _nonempty(witness.shared_constraints):
        reasons.append("mapping_shared_constraints_missing")
    elif not set(witness.shared_constraints).issubset(
        set(episode.source_obstruction.constraints) & set(target.constraints)
    ):
        reasons.append("mapping_shared_constraints_not_jointly_present")
    if not witness.precondition_mapping or any(
        not source or not mapped for source, mapped in witness.precondition_mapping
    ):
        reasons.append("mapping_precondition_mapping_missing")
    mapped_source_preconditions = {source for source, _ in witness.precondition_mapping}
    accounted_preconditions = mapped_source_preconditions | set(
        witness.unmatched_source_preconditions
    )
    if accounted_preconditions != set(episode.preconditions):
        reasons.append("mapping_source_preconditions_not_fully_accounted")
    if witness.unmatched_source_preconditions:
        reasons.append("mapping_has_unrepaired_source_preconditions")
    for field_name in (
        "disanalogies",
        "target_validation_obligations",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(witness, field_name)):
            reasons.append(f"mapping_{field_name}_missing")
    match = rank_obstruction_transformations(target, (episode,), top_k=1)
    if not match or not _source_episode_viable(match[0], episode):
        reasons.append("mapping_episode_not_structurally_viable_for_target")
    return tuple(reasons)


def _validate_glue(
    witness: TransformationCompositionWitness,
    *,
    target: ObstructionFingerprint,
    memory: ObstructionTransformationMemory,
    candidates: ShortcutCandidateSet,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not witness.composition_id or not witness.artifact_hash:
        reasons.append("glue_identity_missing")
    if witness.target_obstruction_id != target.obstruction_id:
        reasons.append("glue_target_mismatch")
    if len(witness.episode_ids) < 2 or len(set(witness.episode_ids)) != len(
        witness.episode_ids
    ):
        reasons.append("glue_requires_at_least_two_distinct_episodes")
    if tuple(witness.operation_order) != tuple(witness.episode_ids):
        reasons.append("glue_operation_order_must_bind_selected_episode_order")
    if tuple(sorted(witness.episode_ids)) not in set(candidates.glue_episode_sets):
        reasons.append("glue_episode_set_not_supported_by_memory_query")
    if any(find_transformation_episode(memory, item) is None for item in witness.episode_ids):
        reasons.append("glue_episode_not_in_bound_memory")
    for field_name in (
        "interface_obligations",
        "incompatibilities_checked",
        "target_validation_obligations",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(witness, field_name)):
            reasons.append(f"glue_{field_name}_missing")
    return tuple(reasons)


def _validate_exhaustion(
    witness: ExhaustionWitness,
    *,
    target: ObstructionFingerprint,
    candidates: ShortcutCandidateSet,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if witness.target_obstruction_id != target.obstruction_id:
        reasons.append("exhaustion_target_mismatch")
    if not witness.search_boundary:
        reasons.append("exhaustion_search_boundary_missing")
    for field_name in (
        "searched_domains",
        "searched_method_families",
        "rejection_reasons",
        "residual_failure_ids",
        "repeated_residual_features",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(witness, field_name)):
            reasons.append(f"exhaustion_{field_name}_missing")
    if len(set(witness.searched_domains)) < 2:
        reasons.append("exhaustion_cross_domain_search_missing")
    if target.domain not in set(witness.searched_domains):
        reasons.append("exhaustion_target_domain_not_searched")
    if len(set(witness.searched_method_families)) < 2:
        reasons.append("exhaustion_method_family_diversity_missing")
    if len(set(witness.residual_failure_ids)) < 2:
        reasons.append("exhaustion_requires_multiple_distinct_failures")
    if not witness.coverage_receipt_hash:
        reasons.append("exhaustion_cross_problem_coverage_receipt_hash_missing")
    if not witness.artifact_hash:
        reasons.append("exhaustion_artifact_hash_missing")

    direct_ids = {match.episode_id for match in candidates.direct_matches}
    jump_ids = {match.episode_id for match in candidates.jump_matches}
    if not direct_ids.issubset(set(witness.rejected_direct_episode_ids)):
        reasons.append("exhaustion_did_not_account_for_all_direct_candidates")
    if not jump_ids.issubset(set(witness.rejected_jump_episode_ids)):
        reasons.append("exhaustion_did_not_account_for_all_jump_candidates")
    candidate_glue_ids = {
        "+".join(items) for items in candidates.glue_episode_sets
    }
    if not candidate_glue_ids.issubset(set(witness.rejected_glue_composition_ids)):
        reasons.append("exhaustion_did_not_account_for_all_glue_candidates")
    return tuple(reasons)


def _validate_lift_spec(
    spec: MissingTransformationSpecification,
    *,
    target_obstruction_id: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not spec.spec_id or not spec.artifact_hash:
        reasons.append("lift_spec_identity_missing")
    if spec.target_obstruction_id != target_obstruction_id:
        reasons.append("lift_spec_target_mismatch")
    for field_name in (
        "residual_failure_ids",
        "must_preserve",
        "must_break",
        "must_expose",
        "must_reduce",
        "allowed_representation_changes",
        "forbidden_shortcuts",
        "validation_obligations",
        "falsifiers",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(spec, field_name)):
            reasons.append(f"lift_spec_{field_name}_missing")
    if len(set(spec.residual_failure_ids)) < 2:
        reasons.append("lift_spec_requires_multiple_distinct_failures")
    return tuple(reasons)


def _validate_status_against_candidates(
    review: ObstructionTransformationReview,
    candidates: ShortcutCandidateSet,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    direct_found = bool(candidates.direct_matches)
    jump_found = bool(candidates.jump_matches)
    glue_found = bool(candidates.glue_episode_sets)

    expected_direct = (
        RouteSearchStatus.MATCHES_FOUND if direct_found else RouteSearchStatus.NO_VIABLE_MATCH
    )
    if review.direct_search_status is not expected_direct:
        reasons.append("direct_search_status_disagrees_with_bound_memory_query")

    # JUMP and GLUE can be structurally found but later rejected by mapping or
    # interface checks.  Their status records whether a *viable witnessed route*
    # survived, so we only reject impossible positive claims here.
    if review.jump_search_status is RouteSearchStatus.MATCHES_FOUND and not jump_found:
        reasons.append("jump_match_claimed_without_structural_memory_candidate")
    if review.glue_search_status is RouteSearchStatus.MATCHES_FOUND and not glue_found:
        reasons.append("glue_match_claimed_without_composable_memory_candidate")
    return tuple(reasons)


def audit_obstruction_transformation_review(
    review: ObstructionTransformationReview | None,
    *,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
    transformation_memory: ObstructionTransformationMemory | None,
) -> ShortcutReviewReport:
    """Fail-closed audit of the SEARCH -> JUMP -> GLUE -> LIFT ladder."""

    if review is None:
        return ShortcutReviewReport(
            ShortcutReviewVerdict.CANNOT_CHECK,
            ("obstruction_transformation_review_missing",),
            False,
            ShortcutMode.CANNOT_CHECK,
        )

    reasons: list[str] = []
    if not review.review_id:
        reasons.append("shortcut_review_id_missing")
    if review.target_atom_id != atom_id:
        reasons.append("shortcut_review_atom_mismatch")
    if review.target_context_hash != context_hash:
        reasons.append("shortcut_review_context_mismatch")
    if review.research_memory_review_hash != research_memory_review_hash:
        reasons.append("shortcut_review_memory_review_mismatch")
    if not review.evidence_pointers:
        reasons.append("shortcut_review_evidence_missing")
    if not review.artifact_hash:
        reasons.append("shortcut_review_artifact_hash_missing")
    reasons.extend(validate_obstruction_fingerprint(review.obstruction))

    memory_reasons = validate_transformation_memory(transformation_memory)
    reasons.extend(memory_reasons)
    if transformation_memory is None or memory_reasons:
        return ShortcutReviewReport(
            ShortcutReviewVerdict.FAIL if reasons else ShortcutReviewVerdict.CANNOT_CHECK,
            tuple(reasons) or ("transformation_memory_cannot_be_checked",),
            False,
            review.selected_mode,
        )
    if review.episode_memory_snapshot_hash != transformation_memory.snapshot_hash:
        reasons.append("shortcut_episode_memory_snapshot_hash_mismatch")

    candidates = discover_shortcut_candidates(review.obstruction, transformation_memory)
    reasons.extend(_validate_status_against_candidates(review, candidates))

    mode = review.selected_mode
    target = review.obstruction

    if mode is ShortcutMode.CANNOT_CHECK:
        if reasons:
            return ShortcutReviewReport(
                ShortcutReviewVerdict.FAIL, tuple(reasons), False, mode
            )
        return ShortcutReviewReport(
            ShortcutReviewVerdict.CANNOT_CHECK,
            ("semantic_shortcut_route_not_yet_resolved",),
            False,
            mode,
        )

    if mode is ShortcutMode.SEARCH:
        if review.direct_search_status is not RouteSearchStatus.MATCHES_FOUND:
            reasons.append("search_mode_without_direct_match")
        direct_ids = {match.episode_id for match in candidates.direct_matches}
        if not review.direct_candidate_episode_ids:
            reasons.append("search_mode_direct_candidate_missing")
        elif not set(review.direct_candidate_episode_ids).issubset(direct_ids):
            reasons.append("search_direct_candidate_not_supported_by_memory_query")
        witness_ids: set[str] = set()
        for witness in review.direct_mapping_witnesses:
            episode = find_transformation_episode(transformation_memory, witness.episode_id)
            reasons.extend(_validate_mapping(witness, target=target, episode=episode))
            witness_ids.add(witness.episode_id)
        if not review.selected_episode_ids:
            reasons.append("search_mode_selected_episode_missing")
        elif not set(review.selected_episode_ids).issubset(witness_ids):
            reasons.append("search_selected_episode_lacks_applicability_mapping")
        elif not set(review.selected_episode_ids).issubset(
            set(review.direct_candidate_episode_ids)
        ):
            reasons.append("search_selected_episode_not_in_direct_candidates")

    elif mode is ShortcutMode.JUMP:
        if review.direct_search_status is not RouteSearchStatus.NO_VIABLE_MATCH:
            reasons.append("jump_requires_direct_search_exhausted")
        if review.jump_search_status is not RouteSearchStatus.MATCHES_FOUND:
            reasons.append("jump_mode_without_structural_match")
        jump_ids = {match.episode_id for match in candidates.jump_matches}
        witness_episode_ids: set[str] = set()
        for witness in review.jump_mapping_witnesses:
            if witness.episode_id not in jump_ids:
                reasons.append("jump_mapping_episode_not_in_cross_domain_candidates")
            episode = find_transformation_episode(transformation_memory, witness.episode_id)
            reasons.extend(_validate_mapping(witness, target=target, episode=episode))
            witness_episode_ids.add(witness.episode_id)
        if not review.jump_mapping_witnesses:
            reasons.append("jump_mapping_witness_missing")
        if not review.selected_episode_ids:
            reasons.append("jump_selected_episode_missing")
        elif not set(review.selected_episode_ids).issubset(witness_episode_ids):
            reasons.append("jump_selected_episode_lacks_mapping_witness")

    elif mode is ShortcutMode.GLUE:
        if review.direct_search_status is not RouteSearchStatus.NO_VIABLE_MATCH:
            reasons.append("glue_requires_direct_search_exhausted")
        if review.jump_search_status is not RouteSearchStatus.NO_VIABLE_MATCH:
            reasons.append("glue_requires_single_jump_search_exhausted")
        if review.glue_search_status is not RouteSearchStatus.MATCHES_FOUND:
            reasons.append("glue_mode_without_composition_match")
        mapped_ids: set[str] = set()
        for witness in review.jump_mapping_witnesses:
            episode = find_transformation_episode(transformation_memory, witness.episode_id)
            reasons.extend(_validate_mapping(witness, target=target, episode=episode))
            mapped_ids.add(witness.episode_id)
        if review.glue_witness is None:
            reasons.append("glue_witness_missing")
        else:
            reasons.extend(
                _validate_glue(
                    review.glue_witness,
                    target=target,
                    memory=transformation_memory,
                    candidates=candidates,
                )
            )
            if tuple(review.selected_episode_ids) != tuple(review.glue_witness.episode_ids):
                reasons.append("glue_selected_episodes_do_not_match_composition")
            if not set(review.glue_witness.episode_ids).issubset(mapped_ids):
                reasons.append("glue_component_episode_lacks_mapping_witness")

    elif mode is ShortcutMode.LIFT:
        for stage_name, status in (
            ("direct", review.direct_search_status),
            ("jump", review.jump_search_status),
            ("glue", review.glue_search_status),
        ):
            if status is not RouteSearchStatus.NO_VIABLE_MATCH:
                reasons.append(f"lift_requires_{stage_name}_route_exhausted")
        if review.selected_episode_ids:
            reasons.append("lift_must_not_select_existing_episode")
        if review.exhaustion_witness is None:
            reasons.append("lift_exhaustion_witness_missing")
        else:
            reasons.extend(
                _validate_exhaustion(
                    review.exhaustion_witness,
                    target=target,
                    candidates=candidates,
                )
            )
        if review.missing_transformation_specification is None:
            reasons.append("lift_missing_transformation_specification")
        else:
            reasons.extend(
                _validate_lift_spec(
                    review.missing_transformation_specification,
                    target_obstruction_id=target.obstruction_id,
                )
            )
        if (
            review.exhaustion_witness is not None
            and review.missing_transformation_specification is not None
        ):
            exhaustion_failures = set(review.exhaustion_witness.residual_failure_ids)
            spec_failures = set(review.missing_transformation_specification.residual_failure_ids)
            if not spec_failures.issubset(exhaustion_failures):
                reasons.append("lift_spec_uses_failures_outside_exhaustion_witness")
            if not set(review.missing_transformation_specification.must_break).issubset(
                set(review.exhaustion_witness.repeated_residual_features)
            ):
                reasons.append(
                    "lift_spec_break_target_not_supported_by_repeated_residuals"
                )
    else:
        reasons.append("shortcut_mode_unrecognized")

    if reasons:
        return ShortcutReviewReport(
            ShortcutReviewVerdict.FAIL, tuple(reasons), False, mode
        )

    return ShortcutReviewReport(
        ShortcutReviewVerdict.PASS,
        (
            f"semantic_shortcut_{mode.value.lower()}_route_frozen_before_candidate_generation",
            "route_is_proposal_only_and_requires_target_validation",
        ),
        True,
        mode,
    )
