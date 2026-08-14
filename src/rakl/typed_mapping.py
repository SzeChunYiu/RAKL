"""Type-preserving partial-credit mapping for ARN v2 reducer.

Implements the mapping stage of the v2 successor with:
  - Type-preserving correspondence score
  - Bonus for matching role types and relation types
  - Penalty for type mismatches
  - Principled abstention on degenerate type coverage or weak mapping

See PROTOCOL_V2_REDUCER.json for pre-registered parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

from .narrative_reducer_v2 import (
    TypedReducedStructure,
    RoleType,
    RelationType,
    MIN_TYPED_ROLE_FRACTION,
    MIN_TYPED_RELATION_FRACTION,
    MIN_ROLE_COVERAGE_FOR_ACCEPT,
    MIN_RELATION_COVERAGE_FOR_ACCEPT,
)
from .structure_space import MatchVerdict, ProblemStructure


@dataclass(frozen=True)
class MappingResult:
    """Result of type-preserving mapping with abstention controls."""
    decision: str  # "ACCEPT", "REJECT", "CANNOT_CHECK"
    verdict: MatchVerdict
    score: float  # normalized score in [0, 1]
    coverage_details: dict
    abstention_reason: str | None


def compute_type_preserving_score(
    query: TypedReducedStructure,
    candidate: TypedReducedStructure,
) -> tuple[float, dict]:
    """Compute type-preserving correspondence score.

    Returns (normalized_score, details_dict).

    Score formula (from PROTOCOL_V2_REDUCER.json):
      numerator = role_coverage + 2*relation_coverage + type_bonus + type_penalty + relation_type_bonus
      denominator = |query_roles| + 2*|query_relations| + max_possible_bonus
      score = numerator / denominator

    Where:
      - role_coverage = |query_roles ∩ candidate_roles|
      - relation_coverage = |query_relations ∩ candidate_relations|
      - type_bonus = 0.2 per role with matching non-NONE role_type
      - type_penalty = -0.1 per role with mismatched non-NONE role_type
      - relation_type_bonus = 0.15 per relation with matching non-PLAIN relation_type
      - max_possible_bonus = 0.2 * |query_roles| + 0.15 * |query_relations|
    """
    # Basic coverage
    role_coverage = len(query.roles & candidate.roles)
    relation_coverage = len(query.relations & candidate.relations)

    # Type-based bonuses and penalties
    type_bonus = 0.0
    type_penalty = 0.0
    relation_type_bonus = 0.0

    # Role type matching
    for role in query.roles & candidate.roles:
        q_role = query.typed_roles.get(role)
        c_role = candidate.typed_roles.get(role)
        if q_role and c_role:
            if q_role.role_type != RoleType.NONE and c_role.role_type != RoleType.NONE:
                if q_role.role_type == c_role.role_type:
                    type_bonus += 0.2
                else:
                    type_penalty -= 0.1

    # Relation type matching
    query_rel_types = {}  # (s, t) -> RelationType
    for r in query.typed_relations:
        query_rel_types[(r.source, r.target)] = r.relation_type

    candidate_rel_types = {}
    for r in candidate.typed_relations:
        candidate_rel_types[(r.source, r.target)] = r.relation_type

    for rel in query.relations & candidate.relations:
        q_type = query_rel_types.get(rel)
        c_type = candidate_rel_types.get(rel)
        if q_type and c_type:
            if q_type != RelationType.PLAIN and c_type != RelationType.PLAIN:
                if q_type == c_type:
                    relation_type_bonus += 0.15

    # Compute denominator
    max_bonus = 0.2 * len(query.roles) + 0.15 * len(query.typed_relations)
    denominator = len(query.roles) + 2 * len(query.relations) + max_bonus

    # Compute numerator
    numerator = role_coverage + 2 * relation_coverage + type_bonus + type_penalty + relation_type_bonus

    # Normalize
    score = numerator / denominator if denominator > 0 else 0.0

    details = {
        "role_coverage": role_coverage,
        "relation_coverage": relation_coverage,
        "type_bonus": type_bonus,
        "type_penalty": type_penalty,
        "relation_type_bonus": relation_type_bonus,
        "max_bonus": max_bonus,
        "numerator": numerator,
        "denominator": denominator,
        "score": score,
    }

    return score, details


def check_abstention_conditions(
    query: TypedReducedStructure,
    candidate: TypedReducedStructure,
    score: float,
    theta_w: float,
) -> str | None:
    """Check principled abstention conditions.

    Returns reason string if should abstain, None otherwise.

    Conditions (from PROTOCOL_V2_REDUCER.json):
      1. Insufficient extraction evidence (same as parent)
      2. Degenerate type coverage
      3. Low mapping confidence
    """
    # Condition 1: Insufficient extraction evidence (same as parent)
    if (
        len(query.roles) < 2
        or not query.relations
        or len(candidate.roles) < 2
        or not candidate.relations
    ):
        return "insufficient_extraction_evidence"

    # Condition 2: Degenerate type coverage
    if (
        query.typed_role_fraction < MIN_TYPED_ROLE_FRACTION
        and query.typed_relation_fraction < MIN_TYPED_RELATION_FRACTION
    ):
        return f"degenerate_type_coverage: typed_role_fraction={query.typed_role_fraction:.3f} < {MIN_TYPED_ROLE_FRACTION}, typed_relation_fraction={query.typed_relation_fraction:.3f} < {MIN_TYPED_RELATION_FRACTION}"

    # Condition 3: Low mapping confidence
    # Compute raw coverage for this check
    role_cov = len(query.roles & candidate.roles)
    rel_cov = len(query.relations & candidate.relations)
    if score < theta_w and (role_cov < MIN_ROLE_COVERAGE_FOR_ACCEPT or rel_cov < MIN_RELATION_COVERAGE_FOR_ACCEPT):
        return f"low_mapping_confidence: score={score:.3f} < theta_w={theta_w}, role_coverage={role_cov}, relation_coverage={rel_cov}"

    return None


def typed_match_decision(
    query: TypedReducedStructure,
    candidate: TypedReducedStructure,
    theta_w: float,
) -> MappingResult:
    """Make accept/reject decision with type-preserving mapping and abstention.

    Returns MappingResult with decision, verdict, score, details, and abstention reason.
    """
    # Compute type-preserving score
    score, details = compute_type_preserving_score(query, candidate)

    # Check abstention conditions
    abstention_reason = check_abstention_conditions(query, candidate, score, theta_w)

    if abstention_reason:
        return MappingResult(
            decision="CANNOT_CHECK",
            verdict=MatchVerdict.CANNOT_CHECK,
            score=score,
            coverage_details=details,
            abstention_reason=abstention_reason,
        )

    # Make decision based on threshold
    if score >= theta_w:
        return MappingResult(
            decision="ACCEPT",
            verdict=MatchVerdict.LICENSED,
            score=score,
            coverage_details=details,
            abstention_reason=None,
        )
    else:
        return MappingResult(
            decision="REJECT",
            verdict=MatchVerdict.REJECTED,
            score=score,
            coverage_details=details,
            abstention_reason=None,
        )


def convert_to_problem_structure(query: TypedReducedStructure) -> ProblemStructure:
    """Convert TypedReducedStructure to ProblemStructure (for compatibility)."""
    return ProblemStructure(
        problem_id=f"pair::{query.structure.structure_id}",
        qoi="analogical_support",
        required_roles=query.roles,
        required_relations=query.relations,
    )
