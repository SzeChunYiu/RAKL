"""Instance-paired correspondence scoring for ARN v3.

Every score term consumes a specific (query-instance, candidate-instance) pair.
No marginal components computable from one narrative alone.

This fixes the v2 deficit where type marginals survived gold label shuffling,
causing B3_shuffled_gold to show advantage 0.121 when it should be ~0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .narrative_reducer_v2 import (
    RoleType, RelationType, TypedRelation, TypedRole, TypedReducedStructure,
)


@dataclass(frozen=True)
class CorrespondenceResult:
    """Result of instance-paired mapping."""
    decision: str  # ACCEPT, REJECT, CANNOT_CHECK
    verdict: str  # LICENSED, REJECTED, CANNOT_CHECK
    score: float  # normalized [0, 1]
    role_score: float  # component for roles
    relation_score: float  # component for relations
    coverage_details: dict
    abstention_reason: str | None = None


def role_correspondence(q_role: TypedRole, c_role: TypedRole) -> float:
    """Compute correspondence strength between a query role and candidate role.

    Returns:
        1.0 if tokens match exactly
        0.4 if tokens differ but role_types match (both non-NONE)
        0.0 otherwise
    """
    if q_role.token == c_role.token:
        return 1.0
    if (q_role.role_type != RoleType.NONE and
        c_role.role_type != RoleType.NONE and
        q_role.role_type == c_role.role_type):
        return 0.4
    return 0.0


def relation_correspondence(q_rel: TypedRelation, c_rel: TypedRelation) -> float:
    """Compute correspondence strength between query and candidate relations.

    Returns:
        1.0 if source AND target tokens match exactly
        0.5 if tokens differ BUT role_types match pairwise AND relation_types match
        0.0 otherwise
    """
    # Exact token match
    if (q_rel.source == c_rel.source and q_rel.target == c_rel.target):
        return 1.0

    # Partial match: role types and relation type align
    src_role_match = (q_rel.source_role_type != RoleType.NONE and
                      c_rel.source_role_type != RoleType.NONE and
                      q_rel.source_role_type == c_rel.source_role_type)
    tgt_role_match = (q_rel.target_role_type != RoleType.NONE and
                      c_rel.target_role_type != RoleType.NONE and
                      q_rel.target_role_type == c_rel.target_role_type)
    rel_type_match = (q_rel.relation_type != RelationType.PLAIN and
                     c_rel.relation_type != RelationType.PLAIN and
                     q_rel.relation_type == c_rel.relation_type)

    if src_role_match and tgt_role_match and rel_type_match:
        return 0.5

    return 0.0


def greedy_match(query_instances: list, candidate_instances: list,
                 correspondence_fn: Callable) -> list[tuple]:
    """Greedy asymmetric matching: each query instance matches at most one candidate.

    Args:
        query_instances: list of query-side instances (roles or relations)
        candidate_instances: list of candidate-side instances
        correspondence_fn: function computing correspondence strength

    Returns:
        list of (query_idx, candidate_idx, correspondence_value) tuples
    """
    matched_candidates = set()
    matches = []

    # Process query instances in order (deterministic)
    for q_idx, q_inst in enumerate(query_instances):
        best_corr = 0.0
        best_c_idx = -1

        # Find the best unmatched candidate
        for c_idx, c_inst in enumerate(candidate_instances):
            if c_idx in matched_candidates:
                continue
            corr = correspondence_fn(q_inst, c_inst)
            if corr > best_corr:
                best_corr = corr
                best_c_idx = c_idx

        if best_c_idx >= 0 and best_corr > 0:
            matches.append((q_idx, best_c_idx, best_corr))
            matched_candidates.add(best_c_idx)

    return matches


def compute_instance_paired_score(query: TypedReducedStructure,
                                  candidate: TypedReducedStructure) -> tuple[float, float, float]:
    """Compute instance-paired correspondence score.

    Returns:
        (score, role_score, relation_score) where score in [0, 1]
    """
    query_roles = query.typed_roles
    candidate_roles = candidate.typed_roles
    query_relations = query.typed_relations
    candidate_relations = candidate.typed_relations

    # Role matching
    role_matches = greedy_match(query_roles, candidate_roles, role_correspondence)
    role_corr_sum = sum(corr for _, _, corr in role_matches)
    role_score = role_corr_sum / len(query_roles) if query_roles else 0.0

    # Relation matching
    rel_matches = greedy_match(query_relations, candidate_relations, relation_correspondence)
    rel_corr_sum = sum(corr for _, _, corr in rel_matches)
    relation_score = rel_corr_sum / len(query_relations) if query_relations else 0.0

    # Combined score (equal weight)
    score = 0.5 * role_score + 0.5 * relation_score

    return score, role_score, relation_score


def check_abstention_conditions(query: TypedReducedStructure,
                                candidate: TypedReducedStructure,
                                score: float,
                                theta_w: float) -> str | None:
    """Check if we should abstain (CANNOT_CHECK). Returns reason string or None."""
    query_roles = query.typed_roles
    candidate_roles = candidate.typed_roles
    query_relations = query.typed_relations
    candidate_relations = candidate.typed_relations

    # Insufficient extraction evidence
    if len(query_roles) < 2 or len(query_relations) == 0:
        return "insufficient_extraction_evidence_query"
    if len(candidate_roles) < 2 or len(candidate_relations) == 0:
        return "insufficient_extraction_evidence_candidate"

    # Degenerate type coverage
    typed_q_roles = sum(1 for r in query_roles if r.role_type != RoleType.NONE)
    typed_q_rels = sum(1 for r in query_relations if r.relation_type != RelationType.PLAIN)
    if (typed_q_roles / len(query_roles) < 0.2 and
        typed_q_rels / len(query_relations) < 0.1):
        return "degenerate_type_coverage"

    # Zero correspondence (instance-paired specific)
    role_score, rel_score = compute_instance_paired_score(query, candidate)[1:]
    if role_score == 0 and rel_score == 0:
        return "zero_correspondence"

    return None


def instance_paired_match_decision(query: TypedReducedStructure,
                                    candidate: TypedReducedStructure,
                                    theta_w: float) -> CorrespondenceResult:
    """Make mapping decision using instance-paired correspondence.

    Args:
        query: reduced query structure
        candidate: reduced candidate structure
        theta_w: acceptance threshold (fitted on dev set)

    Returns:
        CorrespondenceResult with decision, score, and details
    """
    # Compute scores
    score, role_score, relation_score = compute_instance_paired_score(query, candidate)

    # Check abstention conditions
    abstention_reason = check_abstention_conditions(query, candidate, score, theta_w)

    if abstention_reason:
        return CorrespondenceResult(
            decision="CANNOT_CHECK",
            verdict="CANNOT_CHECK",
            score=score,
            role_score=role_score,
            relation_score=relation_score,
            coverage_details={"role_score": role_score, "relation_score": relation_score},
            abstention_reason=abstention_reason
        )

    # Apply threshold
    if score >= theta_w:
        decision = "ACCEPT"
        verdict = "LICENSED"
    else:
        decision = "REJECT"
        verdict = "REJECTED"

    return CorrespondenceResult(
        decision=decision,
        verdict=verdict,
        score=score,
        role_score=role_score,
        relation_score=relation_score,
        coverage_details={"role_score": role_score, "relation_score": relation_score},
        abstention_reason=None
    )
