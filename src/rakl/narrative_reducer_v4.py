"""ARN v4 reducer: relational-correspondence with M1 parent (relation-triple alignment).

Revives v3 NEGATIVE__CAPABILITY_ABSENT by fixing the mapping deficit:
  - v3 used flat typed-role/relation features — insufficient signal
  - v4 uses second-order RELATION TRIPLES: (source_role_type, relation_type, target_role_type)
  - Captures structural correspondence: how relations connect typed roles

Extraction: verbatim from v3 (typed roles, typed relations, negation scope).
Mapping: relational-correspondence scoring with triple alignment.

Frozen before confirmatory data contact. See PROTOCOL_V4_REDUCER.json.
Proposal-only; grants no authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable

from .narrative_reducer_v2 import (
    NEGATION_MARKERS, PREPOSITIONS,
    RoleType, RelationType, EntityType,
    TypedRole, TypedRelation, TypedReducedStructure,
    content_tokens, VERB_LIKE,
)
from .support_solver import Atom, Obstruction, SupportEdge, SupportStructure
from .structure_space import ReducedStructure


# Re-export v3 extraction components (no changes)
MAX_ROLES = 12
RELATION_WINDOW = 4
SENTENCE_SPLIT_PATTERN = r'[.!?;]+'


def reduce_narrative_v4(text: str) -> TypedReducedStructure:
    """Reduce a narrative to a typed support structure (v3 extraction, v4 mapping).

    This is an alias for reduce_narrative_v2 — extraction is unchanged.
    The mapping difference is in relational_correspondence.py.
    """
    # Reuse v2 extraction verbatim
    from .narrative_reducer_v2 import reduce_narrative_v2
    return reduce_narrative_v2(text)


# For compatibility with existing admission infrastructure
def reduce_narrative(text: str) -> ReducedStructure:
    """Wrapper for compatibility with admission gate (returns ReducedStructure)."""
    result = reduce_narrative_v4(text)
    return ReducedStructure(
        structure_id=result.structure.structure_id,
        atoms=result.structure.atoms,
        edges=result.structure.edges,
        obstructions=result.structure.obstructions,
        provenance=result.structure.provenance
    )


@dataclass(frozen=True)
class RelationTriple:
    """A relation triple: (source_role_type, relation_type, target_role_type)."""
    source_role_type: RoleType
    relation_type: RelationType
    target_role_type: RoleType

    def __hash__(self) -> int:
        return hash((self.source_role_type, self.relation_type, self.target_role_type))

    def __iter__(self):
        return iter((self.source_role_type, self.relation_type, self.target_role_type))


def extract_relation_triples(query: TypedReducedStructure) -> list[RelationTriple]:
    """Extract relation triples from a reduced structure.

    For each TypedRelation, look up the role types of source and target
    from typed_roles dict to form a triple.

    Returns:
        list of RelationTriple objects
    """
    triples = []
    typed_roles = query.typed_roles

    for rel in query.typed_relations:
        # Look up role types for source and target
        src_role = typed_roles.get(rel.source)
        tgt_role = typed_roles.get(rel.target)

        if src_role and tgt_role:
            triple = RelationTriple(
                source_role_type=src_role.role_type,
                relation_type=rel.relation_type,
                target_role_type=tgt_role.role_type
            )
            triples.append(triple)

    return triples


def triple_correspondence(q_triple: RelationTriple, c_triple: RelationTriple) -> float:
    """Compute correspondence strength between query and candidate relation triples.

    Returns:
        1.0 — exact match (all three components match)
        0.5 — partial match (relation_type matches AND at least one role_type matches)
        0.0 — no structural correspondence
    """
    # Exact match
    if (q_triple.source_role_type == c_triple.source_role_type and
        q_triple.relation_type == c_triple.relation_type and
        q_triple.target_role_type == c_triple.target_role_type):
        return 1.0

    # Partial match: relation type matches AND at least one role type matches
    relation_match = q_triple.relation_type == c_triple.relation_type
    src_match = q_triple.source_role_type == c_triple.source_role_type
    tgt_match = q_triple.target_role_type == c_triple.target_role_type

    if relation_match and (src_match or tgt_match):
        return 0.5

    return 0.0
