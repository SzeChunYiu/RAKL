from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
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


@dataclass(frozen=True)
class ObstructionFingerprint:
    """Vocabulary-light structural description of one active obstruction."""

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
    """Recorded episode in which a transformation breaks a scoped obstruction.

    The source event can be mathematical, scientific, engineering, social,
    organizational, journalistic, or ordinary human knowledge. Source validity
    never makes source-to-target transport valid; transport requires a separate
    StructuralMappingWitness.
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
class StructuralMappingWitness:
    """Explicit source-to-target relational witness for a JUMP proposal."""

    witness_id: str
    episode_id: str
    target_obstruction_id: str
    role_mapping: Tuple[Tuple[str, str], ...]
    shared_relations: Tuple[str, ...]
    shared_constraints: Tuple[str, ...]
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
    """Bounded evidence that invention is considered only after prior lanes."""

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
    coverage_receipt_hash: str = ""


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
    score: int
    matched_relations: Tuple[str, ...]
    matched_constraints: Tuple[str, ...]
    matched_failure_mechanisms: Tuple[str, ...]
    matched_invariants: Tuple[str, ...]
    matched_desired_transition: Tuple[str, ...]


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
    "query_recorded_obstruction_transformation_episodes",
    "record_structural_mapping_or_composition_witnesses",
    "exhaust_search_jump_and_glue_before_lift",
    "freeze_missing_transformation_specification_if_lifted",
    "record_obstruction_transformation_review_in_public_trace",
)


def _nonempty(values: Sequence[str]) -> bool:
    return bool(values) and all(bool(value) for value in values)


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
        "relaxed_or_broken_constraints",
        "known_breakpoints",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(episode, field_name)):
            reasons.append(f"episode_{field_name}_missing")
    return tuple(reasons)


def rank_obstruction_transformations(
    target: ObstructionFingerprint,
    episodes: Sequence[ObstructionTransformationEpisode],
    *,
    top_k: int = 8,
) -> Tuple[StructuralMatch, ...]:
    """Rank structural candidates; never certify source-to-target transport.

    Source and target descriptions must already be normalized into relational
    coordinates. Exact set overlap is intentional: this reference layer does
    not pretend an embedding score is a structural witness. Every retained JUMP
    still needs a StructuralMappingWitness.
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

    for episode in episodes:
        if episode.authority is TransformationEpisodeAuthority.SUPERSEDED:
            continue
        if validate_transformation_episode(episode):
            continue
        source = episode.source_obstruction
        matched_relations = tuple(sorted(target_relations & set(source.relations)))
        matched_constraints = tuple(sorted(target_constraints & set(source.constraints)))
        matched_failures = tuple(sorted(target_failures & set(source.failure_mechanisms)))
        matched_invariants = tuple(
            sorted(target_invariants & set(source.invariants_to_preserve))
        )
        matched_transition = tuple(
            sorted(target_transition & set(source.desired_transition))
        )
        score = (
            4 * len(matched_failures)
            + 3 * len(matched_relations)
            + 3 * len(matched_transition)
            + 2 * len(matched_constraints)
            + len(matched_invariants)
        )
        if score <= 0:
            continue
        match = StructuralMatch(
            episode_id=episode.episode_id,
            score=score,
            matched_relations=matched_relations,
            matched_constraints=matched_constraints,
            matched_failure_mechanisms=matched_failures,
            matched_invariants=matched_invariants,
            matched_desired_transition=matched_transition,
        )
        ranked.append((-score, episode.episode_id, match))
    ranked.sort(key=lambda row: (row[0], row[1]))
    return tuple(match for _, _, match in ranked[:top_k])


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
    return tuple(sorted(feature for feature, count in counter.items() if count >= minimum_support))


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

    This function deliberately does not generate a new operator. It converts
    recurring residual structure into a missing-transformation specification
    that a later typed candidate must satisfy.
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
    target_obstruction_id: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not witness.witness_id or not witness.episode_id or not witness.artifact_hash:
        reasons.append("jump_mapping_identity_missing")
    if witness.target_obstruction_id != target_obstruction_id:
        reasons.append("jump_mapping_target_mismatch")
    if not witness.role_mapping or any(
        not source or not target for source, target in witness.role_mapping
    ):
        reasons.append("jump_role_mapping_missing")
    for field_name in (
        "shared_relations",
        "shared_constraints",
        "disanalogies",
        "target_validation_obligations",
        "evidence_pointers",
    ):
        if not _nonempty(getattr(witness, field_name)):
            reasons.append(f"jump_{field_name}_missing")
    return tuple(reasons)


def _validate_glue(
    witness: TransformationCompositionWitness,
    *,
    target_obstruction_id: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not witness.composition_id or not witness.artifact_hash:
        reasons.append("glue_identity_missing")
    if witness.target_obstruction_id != target_obstruction_id:
        reasons.append("glue_target_mismatch")
    if len(witness.episode_ids) < 2 or len(set(witness.episode_ids)) != len(
        witness.episode_ids
    ):
        reasons.append("glue_requires_at_least_two_distinct_episodes")
    if tuple(witness.operation_order) != tuple(witness.episode_ids):
        reasons.append("glue_operation_order_must_bind_selected_episode_order")
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
    target_obstruction_id: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if witness.target_obstruction_id != target_obstruction_id:
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
    if len(set(witness.residual_failure_ids)) < 2:
        reasons.append("exhaustion_requires_multiple_distinct_failures")
    if not witness.artifact_hash:
        reasons.append("exhaustion_artifact_hash_missing")
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


def audit_obstruction_transformation_review(
    review: ObstructionTransformationReview | None,
    *,
    atom_id: str,
    context_hash: str,
    research_memory_review_hash: str,
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
    if not review.episode_memory_snapshot_hash:
        reasons.append("shortcut_episode_memory_snapshot_hash_missing")
    if not review.evidence_pointers:
        reasons.append("shortcut_review_evidence_missing")
    if not review.artifact_hash:
        reasons.append("shortcut_review_artifact_hash_missing")
    reasons.extend(validate_obstruction_fingerprint(review.obstruction))

    mode = review.selected_mode
    target_id = review.obstruction.obstruction_id

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
        if not review.direct_candidate_episode_ids:
            reasons.append("search_mode_direct_candidate_missing")
        if not review.selected_episode_ids:
            reasons.append("search_mode_selected_episode_missing")
        elif not set(review.selected_episode_ids).issubset(
            set(review.direct_candidate_episode_ids)
        ):
            reasons.append("search_selected_episode_not_in_direct_candidates")

    elif mode is ShortcutMode.JUMP:
        if review.direct_search_status is not RouteSearchStatus.NO_VIABLE_MATCH:
            reasons.append("jump_requires_direct_search_exhausted")
        if review.jump_search_status is not RouteSearchStatus.MATCHES_FOUND:
            reasons.append("jump_mode_without_structural_match")
        if not review.jump_mapping_witnesses:
            reasons.append("jump_mapping_witness_missing")
        witness_episode_ids: set[str] = set()
        for witness in review.jump_mapping_witnesses:
            reasons.extend(_validate_mapping(witness, target_obstruction_id=target_id))
            witness_episode_ids.add(witness.episode_id)
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
        if review.glue_witness is None:
            reasons.append("glue_witness_missing")
        else:
            reasons.extend(
                _validate_glue(review.glue_witness, target_obstruction_id=target_id)
            )
            if tuple(review.selected_episode_ids) != tuple(review.glue_witness.episode_ids):
                reasons.append("glue_selected_episodes_do_not_match_composition")

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
                    target_obstruction_id=target_id,
                )
            )
        if review.missing_transformation_specification is None:
            reasons.append("lift_missing_transformation_specification")
        else:
            reasons.extend(
                _validate_lift_spec(
                    review.missing_transformation_specification,
                    target_obstruction_id=target_id,
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
