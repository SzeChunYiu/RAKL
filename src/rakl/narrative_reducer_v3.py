"""ARN v3 reducer: instance-paired mapping (inherits v2 extraction).

Revives v2 NEGATIVE__BATTERY_FAILED by fixing the mapping deficit:
  - v2 scoring used label-INDEPENDENT type marginals
  - v3 scoring is strictly instance-paired: every term consumes (q_i, c_j) pairs
  - Shuffling gold labels breaks pairings and collapses advantage BY CONSTRUCTION

Extraction: verbatim from v2 (typed roles, typed relations, negation scope).
Mapping: instance_paired_correspondence with greedy asymmetric matching.

Frozen before confirmatory data contact. See PROTOCOL_V3_REDUCER.json.
Proposal-only; grants no authority.
"""

from __future__ import annotations

import hashlib
from typing import Callable

from .narrative_reducer_v2 import (
    NEGATION_MARKERS, OBL_MARKER_POSITIONS, PREPOSITIONS,
    RoleType, RelationType, EntityType,
    TypedRole, TypedRelation, TypedReducedStructure,
    _detect_role_type, _detect_entity_type, _detect_relation_type,
    _is_negated, _token_is_content, VERB_LIKE,
)
from .support_solver import Atom, Obstruction, SupportEdge, SupportStructure
from .structure_space import ReducedStructure


# Re-export v2 extraction components (no changes)
MAX_ROLES = 12
RELATION_WINDOW = 4
SENTENCE_SPLIT_PATTERN = r'[.!?;]+'


def reduce_narrative_v3(text: str) -> TypedReducedStructure:
    """Reduce a narrative to a typed support structure (v2 extraction, v3 mapping).

    This is an alias for reduce_narrative_v2 — extraction is unchanged.
    The mapping difference is in instance_paired_mapping.py.
    """
    # Reuse v2 extraction verbatim
    from .narrative_reducer_v2 import reduce_narrative_v2
    return reduce_narrative_v2(text)


# Admission gate (reuses v2 reducer, so same admission logic applies)
def admission_check(query_text: str, candidate_text: str, theta_w: float) -> dict:
    """Admission check for v3 reducer (same as v2)."""
    from .instance_paired_mapping import instance_paired_match_decision

    query = reduce_narrative_v3(query_text)
    candidate = reduce_narrative_v3(candidate_text)
    result = instance_paired_match_decision(query, candidate, theta_w)

    return {
        "decision": result.decision,
        "verdict": result.verdict,
        "score": result.score,
        "role_score": result.role_score,
        "relation_score": result.relation_score,
        "abstention_reason": result.abstention_reason
    }


# For compatibility with existing admission infrastructure
def reduce_narrative(text: str) -> ReducedStructure:
    """Wrapper for compatibility with admission gate (returns ReducedStructure)."""
    result = reduce_narrative_v3(text)
    return ReducedStructure(
        structure_id=result.structure.structure_id,
        atoms=result.structure.atoms,
        edges=result.structure.edges,
        obstructions=result.structure.obstructions,
        provenance=result.structure.provenance
    )
