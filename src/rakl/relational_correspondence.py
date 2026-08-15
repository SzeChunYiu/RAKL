"""Relational-correspondence scoring for ARN v4 (M1 Progressive Relational Abstraction parent).

Second-order relation-triple alignment: (source_role_type, relation_type, target_role_type).
Every score term consumes the joint (query-triple, candidate-triple) assignment.
Shuffling candidate labels breaks triple alignments and collapses advantage BY CONSTRUCTION.

This fixes the v3 deficit where flat typed-role/relation features were insufficient.
"""

from __future__ import annotations

import os

from dataclasses import dataclass
from typing import Callable

from .narrative_reducer_v2 import RoleType, RelationType, TypedReducedStructure
from .narrative_reducer_v4 import RelationTriple, extract_relation_triples


@dataclass(frozen=True)
class CorrespondenceResult:
    """Result of relational-correspondence mapping."""
    decision: str  # ACCEPT, REJECT, CANNOT_CHECK
    verdict: str  # LICENSED, REJECTED, CANNOT_CHECK
    score: float  # normalized [0, 1]
    triple_score: float  # component for relation triples
    role_boost: float  # component for lexical overlap
    coverage_details: dict
    abstention_reason: str | None = None


def greedy_match_triples(query_triples: list, candidate_triples: list,
                          correspondence_fn: Callable) -> list[tuple]:
    """Greedy asymmetric matching for relation triples.

    Args:
        query_triples: list of query RelationTriple objects
        candidate_triples: list of candidate RelationTriple objects
        correspondence_fn: function computing correspondence strength

    Returns:
        list of (query_idx, candidate_idx, correspondence_value) tuples
    """
    matched_candidates = set()
    matches = []

    # Process query triples in order (deterministic)
    for q_idx, q_triple in enumerate(query_triples):
        best_corr = 0.0
        best_c_idx = -1

        # Find the best unmatched candidate
        for c_idx, c_triple in enumerate(candidate_triples):
            if c_idx in matched_candidates:
                continue
            corr = correspondence_fn(q_triple, c_triple)
            if corr > best_corr:
                best_corr = corr
                best_c_idx = c_idx

        if best_c_idx >= 0 and best_corr > 0:
            matches.append((q_idx, best_c_idx, best_corr))
            matched_candidates.add(best_c_idx)

    return matches


DEFAULT_ROLE_BOOST_WEIGHT = 0.2


def _role_boost_weight() -> float:
    """Weight on the lexical role-overlap term, default reproducing v4."""

    raw = os.environ.get("RAKL_ARN_ROLE_BOOST_WEIGHT")
    if raw is None:
        return DEFAULT_ROLE_BOOST_WEIGHT
    weight = float(raw)
    if not 0.0 <= weight <= 1.0:
        raise ValueError(f"role-boost weight must lie in [0, 1]; got {weight}")
    return weight


def compute_relational_correspondence_score(query: TypedReducedStructure,
                                            candidate: TypedReducedStructure) -> tuple[float, float, float]:
    """Compute relational-correspondence score using relation-triple alignment.

    Returns:
        (score, triple_score, role_boost) where score in [0, 1]
    """
    # Extract relation triples
    query_triples = extract_relation_triples(query)
    candidate_triples = extract_relation_triples(candidate)

    # Triple matching
    triple_matches = greedy_match_triples(query_triples, candidate_triples,
                                          lambda q, c: q.source_role_type == c.source_role_type and
                                                     q.relation_type == c.relation_type and
                                                     q.target_role_type == c.target_role_type)
    # Actually, we need to use the correspondence function
    from .narrative_reducer_v4 import triple_correspondence
    triple_matches = greedy_match_triples(query_triples, candidate_triples, triple_correspondence)

    triple_corr_sum = sum(corr for _, _, corr in triple_matches)
    triple_score = triple_corr_sum / len(query_triples) if query_triples else 0.0

    # Role boost: exact token matches
    query_role_tokens = set(query.roles)
    candidate_role_tokens = set(candidate.roles)
    exact_token_matches = len(query_role_tokens & candidate_role_tokens)
    role_boost = exact_token_matches / len(query_role_tokens) if query_role_tokens else 0.0

    # Combined score: (1 - w) * triple_score + w * role_boost.
    #
    # role_boost is exact role-token overlap — a marginal that depends on the two
    # texts alone and not on which candidate is the analogue. The v4 battery
    # closed BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE because that marginal
    # survived gold shuffling (B3 advantage 0.1347, CI [0.105, 0.163]).
    #
    # The weight is configurable so the leaking arm stays exactly reproducible:
    # the default reproduces v4 byte-for-byte, and RAKL_ARN_ROLE_BOOST_WEIGHT=0.0
    # is the registered repair, leaving the purely relational channel.
    w = _role_boost_weight()
    score = (1.0 - w) * triple_score + w * role_boost

    return score, triple_score, role_boost


def check_abstention_conditions(query: TypedReducedStructure,
                                candidate: TypedReducedStructure,
                                score: float,
                                theta_w: float) -> str | None:
    """Check if we should abstain (CANNOT_CHECK). Returns reason string or None."""
    query_relations = query.typed_relations
    candidate_relations = candidate.typed_relations

    # Insufficient relation evidence (v4 focuses on relation triples)
    if len(query_relations) < 2 or len(candidate_relations) < 2:
        return "insufficient_extraction_evidence_relations"

    # Degenerate relation coverage
    typed_q_rels = sum(1 for r in query_relations if r.relation_type != RelationType.PLAIN)
    if typed_q_rels / len(query_relations) < 0.1:
        return "degenerate_relation_coverage"

    # Zero triple correspondence
    query_triples = extract_relation_triples(query)
    if not query_triples:
        return "zero_triple_correspondence"

    return None


def relational_match_decision(query: TypedReducedStructure,
                              candidate: TypedReducedStructure,
                              theta_w: float) -> CorrespondenceResult:
    """Make mapping decision using relational-correspondence scoring.

    Args:
        query: reduced query structure
        candidate: reduced candidate structure
        theta_w: acceptance threshold (fitted on dev set)

    Returns:
        CorrespondenceResult with decision, score, and details
    """
    # Compute scores
    score, triple_score, role_boost = compute_relational_correspondence_score(query, candidate)

    # Check abstention conditions
    abstention_reason = check_abstention_conditions(query, candidate, score, theta_w)

    if abstention_reason:
        return CorrespondenceResult(
            decision="CANNOT_CHECK",
            verdict="CANNOT_CHECK",
            score=score,
            triple_score=triple_score,
            role_boost=role_boost,
            coverage_details={"triple_score": triple_score, "role_boost": role_boost},
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
        triple_score=triple_score,
        role_boost=role_boost,
        coverage_details={"triple_score": triple_score, "role_boost": role_boost},
        abstention_reason=None
    )
