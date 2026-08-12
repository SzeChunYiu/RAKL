from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence
import hashlib
import json


class CanonicalAction(str, Enum):
    HOLD = "HOLD"
    PROMOTE = "PROMOTE"
    RESTRICT_SCOPE = "RESTRICT_SCOPE"
    REVOKE = "REVOKE"
    SUPERSEDE = "SUPERSEDE"
    CANNOT_CHECK = "CANNOT_CHECK"


class Architecture(str, Enum):
    TEXT_MEMORY_ONLY = "TEXT_MEMORY_ONLY"
    PROVENANCE_ONLY = "PROVENANCE_ONLY"
    SCALAR_CONFIDENCE = "SCALAR_CONFIDENCE"
    PAIRWISE_COMPATIBILITY_ONLY = "PAIRWISE_COMPATIBILITY_ONLY"
    MAJORITY_OR_REVIEWER_VOTE = "MAJORITY_OR_REVIEWER_VOTE"
    SIMPLE_TRANSACTIONAL_STATE = "SIMPLE_TRANSACTIONAL_STATE"
    RAKL_TYPED_AUTHORITY = "RAKL_TYPED_AUTHORITY"


@dataclass(frozen=True)
class EpisodeFamily:
    family_id: str
    description: str
    critical_coordinate: str
    unsafe_value: Any
    safe_value: Any
    unsafe_action: CanonicalAction
    safe_action: CanonicalAction


@dataclass(frozen=True)
class World:
    world_id: str
    family_id: str
    twin_role: str
    state: Mapping[str, Any]
    gold_action: CanonicalAction


# Common summary coordinates are held fixed inside every twin pair. Only the
# family-specific scientific coordinate changes, so a projected representation
# either has enough information to distinguish the required updates or it does not.
BASE: Mapping[str, Any] = {
    "retrieval_count": 4,
    "text_salience": 0.82,
    "scalar_confidence": 0.78,
    "provenance_clean": True,
    "independent_roots": 2,
    "pairwise_compatible": True,
    "global_gluing": True,
    "review_votes_for": 4,
    "review_votes_against": 1,
    "claim_active": True,
    "version": 3,
    "evidence_support": "DIRECT",
    "context_match": True,
    "qoi_match": True,
    "prediction_support": True,
    "mechanism_support": True,
    "identification_support": True,
    "workspace_only": False,
    "experience_only": False,
    "superseded": False,
    "truth_proved": False,
    "novelty_checked": True,
    "cannot_check": False,
    "negative_history_retained": True,
    "authority_axis": "GROUNDING",
    "transition_type": "GENERIC",
    "evidence_independence": "INDEPENDENT",
}


FAMILIES: tuple[EpisodeFamily, ...] = (
    EpisodeFamily("F01_RETRIEVAL_AUTHORITY", "repeated fluent retrieval must not create scientific authority", "evidence_support", "NONE", "DIRECT", CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F02_PROVENANCE_WEAK_EVIDENCE", "clean provenance is not equivalent to strong evidential support", "evidence_support", "INDIRECT", "DIRECT", CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F03_HIGHER_ORDER_GLUING", "pairwise compatibility need not imply global compatibility", "global_gluing", False, True, CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F04_CONTEXT_REGIME", "same terminology across regimes does not license transfer", "context_match", False, True, CanonicalAction.RESTRICT_SCOPE, CanonicalAction.PROMOTE),
    EpisodeFamily("F05_INDEPENDENCE_INFLATION", "correlated roots do not become independent confirmation", "evidence_independence", "CORRELATED", "INDEPENDENT", CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F06_PREDICTION_MECHANISM", "predictive success does not by itself establish mechanism", "mechanism_support", False, True, CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F07_MECHANISM_IDENTIFICATION", "mechanism evidence need not identify one causal account", "identification_support", False, True, CanonicalAction.RESTRICT_SCOPE, CanonicalAction.PROMOTE),
    EpisodeFamily("F08_WORKSPACE_AUTHORITY", "workspace salience cannot write canonical authority", "workspace_only", True, False, CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F09_EXPERIENCE_AUTHORITY", "successful experience reuse is not scientific evidence", "experience_only", True, False, CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F10_SUPERSESSION_STALE_RETRIEVAL", "stale retrieval must not reactivate a superseded claim", "superseded", True, False, CanonicalAction.REVOKE, CanonicalAction.HOLD),
    EpisodeFamily("F11_TRUTH_NOVELTY", "proof truth does not imply novelty or importance", "novelty_checked", False, True, CanonicalAction.CANNOT_CHECK, CanonicalAction.PROMOTE),
    EpisodeFamily("F12_CANNOT_CHECK_SCALAR", "unknown evidence must not be coerced into scalar support", "cannot_check", True, False, CanonicalAction.CANNOT_CHECK, CanonicalAction.PROMOTE),
    EpisodeFamily("F13_NEGATIVE_HISTORY", "contradiction handling must preserve negative history", "negative_history_retained", False, True, CanonicalAction.HOLD, CanonicalAction.RESTRICT_SCOPE),
    EpisodeFamily("F14_LEGITIMATE_PROMOTION", "direct evidence must permit real promotion rather than blanket refusal", "evidence_support", "NONE", "DIRECT", CanonicalAction.HOLD, CanonicalAction.PROMOTE),
    EpisodeFamily("F15_LEGITIMATE_SUPERSESSION", "registered superseding evidence must permit canonical replacement", "superseded", False, True, CanonicalAction.HOLD, CanonicalAction.SUPERSEDE),
)


# Strongest fair *state projection* supplied by each abstraction. This benchmark
# does not test whether a model can infer omitted coordinates from prose.
VISIBILITY: Mapping[Architecture, frozenset[str]] = {
    Architecture.TEXT_MEMORY_ONLY: frozenset({"transition_type", "retrieval_count", "text_salience", "scalar_confidence", "claim_active", "version"}),
    Architecture.PROVENANCE_ONLY: frozenset({"transition_type", "provenance_clean", "independent_roots", "evidence_independence", "claim_active", "version"}),
    Architecture.SCALAR_CONFIDENCE: frozenset({"transition_type", "scalar_confidence", "claim_active", "version"}),
    Architecture.PAIRWISE_COMPATIBILITY_ONLY: frozenset({"transition_type", "pairwise_compatible", "claim_active", "version"}),
    Architecture.MAJORITY_OR_REVIEWER_VOTE: frozenset({"transition_type", "review_votes_for", "review_votes_against", "claim_active", "version"}),
    Architecture.SIMPLE_TRANSACTIONAL_STATE: frozenset({"transition_type", "claim_active", "version", "provenance_clean", "independent_roots", "superseded"}),
    Architecture.RAKL_TYPED_AUTHORITY: frozenset(BASE.keys()),
}


def _world_id(family_id: str, role: str) -> str:
    return "epi-" + hashlib.sha256(f"{family_id}:{role}".encode()).hexdigest()[:14]


def make_worlds() -> tuple[World, ...]:
    worlds: list[World] = []
    for family in FAMILIES:
        for role, value, action in (
            ("unsafe", family.unsafe_value, family.unsafe_action),
            ("safe", family.safe_value, family.safe_action),
        ):
            state = dict(BASE)
            state["transition_type"] = family.family_id
            state[family.critical_coordinate] = value
            worlds.append(World(_world_id(family.family_id, role), family.family_id, role, state, action))
    return tuple(worlds)


def projection(world: World, architecture: Architecture) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (key, json.dumps(world.state[key], sort_keys=True))
            for key in VISIBILITY[architecture]
        )
    )


@dataclass(frozen=True)
class ProjectionAudit:
    architecture: Architecture
    n_worlds: int
    distinct_projected_states: int
    ambiguous_projected_states: int
    worlds_in_ambiguous_states: int
    collision_pairs: tuple[str, ...]
    identifiable_accuracy_upper_bound: float
    unavoidable_error_lower_bound: float
    zero_error_legitimate_update_recall_upper_bound: float
    blanket_hold_accuracy: float
    blanket_hold_legitimate_update_recall: float


def _is_canonical_change(action: CanonicalAction) -> bool:
    return action not in {CanonicalAction.HOLD, CanonicalAction.CANNOT_CHECK}


def audit_architecture(worlds: Sequence[World], architecture: Architecture) -> ProjectionAudit:
    buckets: dict[tuple[tuple[str, str], ...], list[World]] = defaultdict(list)
    for world in worlds:
        buckets[projection(world, architecture)].append(world)

    ambiguous: list[list[World]] = []
    collision_pairs: list[str] = []
    identifiable_correct = 0
    legitimate_total = sum(_is_canonical_change(world.gold_action) for world in worlds)
    legitimate_zero_error_identifiable = 0
    blanket_correct = sum(world.gold_action is CanonicalAction.HOLD for world in worlds)

    for bucket in buckets.values():
        counts = Counter(world.gold_action for world in bucket)
        identifiable_correct += max(counts.values())
        if len(counts) > 1:
            ambiguous.append(bucket)
            collision_pairs.extend(sorted({world.family_id for world in bucket}))
        # A canonical change can be taken with zero classification error only if
        # every world with this projected state requires the same exact change.
        if len(counts) == 1:
            only_action = next(iter(counts))
            if _is_canonical_change(only_action):
                legitimate_zero_error_identifiable += len(bucket)

    upper = identifiable_correct / len(worlds)
    return ProjectionAudit(
        architecture=architecture,
        n_worlds=len(worlds),
        distinct_projected_states=len(buckets),
        ambiguous_projected_states=len(ambiguous),
        worlds_in_ambiguous_states=sum(len(bucket) for bucket in ambiguous),
        collision_pairs=tuple(sorted(set(collision_pairs))),
        identifiable_accuracy_upper_bound=upper,
        unavoidable_error_lower_bound=1.0 - upper,
        zero_error_legitimate_update_recall_upper_bound=legitimate_zero_error_identifiable / max(1, legitimate_total),
        blanket_hold_accuracy=blanket_correct / len(worlds),
        blanket_hold_legitimate_update_recall=0.0,
    )


def audit_all() -> dict[str, Any]:
    worlds = make_worlds()
    audits = {
        architecture.value: asdict(audit_architecture(worlds, architecture))
        for architecture in Architecture
    }
    by_family = {
        family.family_id: [world for world in worlds if world.family_id == family.family_id]
        for family in FAMILIES
    }
    collision_matrix = {
        architecture.value: {
            family_id: projection(pair[0], architecture) == projection(pair[1], architecture)
            for family_id, pair in by_family.items()
        }
        for architecture in Architecture
    }
    raw_worlds = "\n".join(
        json.dumps(
            {
                "id": world.world_id,
                "family": world.family_id,
                "role": world.twin_role,
                "state": dict(world.state),
                "gold": world.gold_action.value,
            },
            sort_keys=True,
        )
        for world in worlds
    )
    return {
        "schema": "paper1-projection-sufficiency-v1",
        "n_families": len(FAMILIES),
        "n_worlds": len(worlds),
        "twin_design": True,
        "architectures": audits,
        "collision_matrix": collision_matrix,
        "world_digest": hashlib.sha256(raw_worlds.encode()).hexdigest(),
        "claim_boundary": (
            "Representational sufficiency / collision benchmark only. Does not "
            "measure LLM comprehension, natural scientific validity, or empirical "
            "superiority on open-ended research."
        ),
    }
