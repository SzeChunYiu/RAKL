"""ARN v2 deterministic reducer: typed extraction + partial-credit mapping + abstention.

Successor to narrative_reducer.py addressing the NEGATIVE__CAPABILITY_ABSENT
result attributed to:
  - Extraction TOO_SPARSE (flat bag-of-words)
  - Mapping FAILED (crude coverage ratio)
  - Abstention NOT_USED (CANNOT_CHECK rate 0.0 despite poor performance)

Improvements (deterministic only, NO language model):
  1. Typed extraction: syntactic roles (SUBJ/OBJ/OBL), relation types (CAUSAL/ENABLE/TEMPORAL/SIMILARITY),
     entity type hints (PERSON/PLACE/THING), negation scope tracking.
  2. Partial-credit mapping: type-preserving correspondence score with type bonus/penalty.
  3. Principled abstention: CANNOT_CHECK when extraction evidence is degenerate or mapping is weak.

Frozen before confirmatory data contact. See PROTOCOL_V2_REDUCER.json for pre-registered parameters.
Proposal-only; grants no authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import re

from .structure_space import ReducedStructure
from .support_solver import Atom, Obstruction, SupportEdge, SupportStructure

# ========== FROZEN LEXICAL RESOURCES (deterministic, no external models) ==========

#: Stopword list (same as parent)
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then else when while of to in on at by for with from
    as is are was were be been being am do does did done have has had having
    will would shall should can could may might must not no nor so than that
    this these those there here it its it's he she they them his her their our
    your my we you i me him us who whom which what where why how all any both
    each few more most other some such only own same too very s t just don now
    """.split()
)

#: Role types (syntactic position heuristics)
class RoleType(str, Enum):
    SUBJ = "SUBJ"  # subject: first capitalized content token
    OBJ = "OBJ"    # object: near verb-like tokens
    OBL = "OBL"    # oblique: after prepositions
    NONE = "NONE"  # untyped (default)

#: Relation types (semantic markers)
class RelationType(str, Enum):
    CAUSAL = "CAUSAL"       # because, therefore, thus, hence, so
    ENABLE = "ENABLE"       # if, when, whenever, provided that
    TEMPORAL = "TEMPORAL"   # before, after, while, during, until
    SIMILARITY = "SIMILARITY"  # like, similar to, unlike
    PLAIN = "PLAIN"        # default (no markers)

#: Entity type hints (lexical proximity)
class EntityType(str, Enum):
    PERSON = "PERSON"  # he, she, man, woman, person
    PLACE = "PLACE"    # here, there, city, house, place
    THING = "THING"    # default

#: Negation/contrast markers (same as parent, expanded)
NEGATION_MARKERS: frozenset[str] = frozenset(
    {"no", "not", "never", "cannot", "cannot", "neither", "nothing", "none",
     "without", "fails", "lacks", "nowhere", "nor", "hardly", "scarcely", "barely"}
)

#: Verb-like tokens (for object heuristic)
VERB_LIKE: frozenset[str] = frozenset(
    {"is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
     "do", "does", "did", "done", "doing", "will", "would", "shall", "should", "can",
     "could", "may", "might", "must", "get", "got", "go", "goes", "went", "come",
     "comes", "came", "make", "makes", "made", "take", "takes", "took", "taken", "see",
     "saw", "seen", "know", "knew", "known", "think", "thought", "say", "said", "tell",
     "told", "ask", "asked", "give", "gave", "given", "find", "found", "use", "used"}
)

#: Prepositions (for oblique heuristic)
PREPOSITIONS: frozenset[str] = frozenset(
    {"after", "in", "on", "at", "by", "for", "with", "from", "to", "under", "over",
     "between", "against", "during", "without", "about", "into", "through", "across"}
)

#: Relation type markers
CAUSAL_MARKERS: frozenset[str] = frozenset(
    {"because", "therefore", "thus", "hence", "so", "consequently", "result"}
)
ENABLE_MARKERS: frozenset[str] = frozenset(
    {"if", "when", "whenever", "provided", "assuming", "unless"}
)
TEMPORAL_MARKERS: frozenset[str] = frozenset(
    {"before", "after", "while", "during", "until", "since", "once", "as", "soon"}
)
SIMILARITY_MARKERS: frozenset[str] = frozenset(
    {"like", "similar", "unlike", "compared", "resembles", "rather", "versus"}
)

#: Person markers (entity type hint)
PERSON_MARKERS: frozenset[str] = frozenset(
    {"he", "she", "him", "her", "his", "their", "who", "someone", "anyone", "everybody",
     "man", "woman", "person", "people", "child", "boy", "girl", "mother", "father"}
)

#: Place markers (entity type hint)
PLACE_MARKERS: frozenset[str] = frozenset(
    {"here", "there", "where", "city", "country", "house", "room", "place", "location",
     "area", "region", "space", "building", "street", "town", "village"}
)

# ========== PRE-REGISTERED PARAMETERS (from PROTOCOL_V2_REDUCER.json) ==========

MAX_ROLES = 12
RELATION_WINDOW = 4
MIN_TYPED_ROLE_FRACTION = 0.2
MIN_TYPED_RELATION_FRACTION = 0.1
MIN_ROLE_COVERAGE_FOR_ACCEPT = 1
MIN_RELATION_COVERAGE_FOR_ACCEPT = 0

# ========== REGEX PATTERNS ==========

_SENTENCE_SPLIT = re.compile(r"[.!?;]+")
_TOKEN = re.compile(r"[a-z]+")

# ========== DATA STRUCTURES ==========

@dataclass(frozen=True)
class TypedRole:
    """A role with syntactic and entity type information."""
    token: str
    role_type: RoleType
    entity_type: EntityType
    frequency: int

    @property
    def atom_id(self) -> str:
        return self.token


@dataclass(frozen=True)
class TypedRelation:
    """A relation with type and negation scope."""
    source: str
    target: str
    relation_type: RelationType
    negated: bool
    sentence_context: str  # for debugging


@dataclass(frozen=True)
class TypedReducedStructure:
    """Extended ReducedStructure with typing information."""
    structure: SupportStructure
    roles: frozenset[str]  # flat set (for compatibility)
    relations: frozenset[tuple[str, str]]  # flat set (for compatibility)
    typed_roles: dict[str, TypedRole]  # token -> TypedRole
    typed_relations: list[TypedRelation]
    provenance: str = ""

    @property
    def typed_role_count(self) -> int:
        return sum(1 for r in self.typed_roles.values() if r.role_type != RoleType.NONE)

    @property
    def typed_relation_count(self) -> int:
        return sum(1 for r in self.typed_relations if r.relation_type != RelationType.PLAIN)

    @property
    def typed_role_fraction(self) -> float:
        if not self.roles:
            return 0.0
        return self.typed_role_count / len(self.roles)

    @property
    def typed_relation_fraction(self) -> float:
        if not self.typed_relations:
            return 0.0
        return self.typed_relation_count / len(self.typed_relations)


# ========== HELPER FUNCTIONS ==========

def _tokens(text: str) -> list[str]:
    """Lowercase tokens."""
    return _TOKEN.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    """Stopword-filtered content tokens of length >= 3, in order."""
    return [t for t in _tokens(text) if t not in STOPWORDS and len(t) >= 3]


def _detect_entity_type(token: str, sentence_tokens: list[str], token_index: int) -> EntityType:
    """Detect entity type from lexical proximity."""
    token_lower = token.lower()
    # Check if token is a person marker
    if token_lower in PERSON_MARKERS:
        return EntityType.PERSON
    # Check if token is a place marker
    if token_lower in PLACE_MARKERS:
        return EntityType.PLACE
    # Check proximity (window of 3 tokens)
    window_start = max(0, token_index - 3)
    window_end = min(len(sentence_tokens), token_index + 4)
    window = sentence_tokens[window_start:window_end]
    if any(t in PERSON_MARKERS for t in window):
        return EntityType.PERSON
    if any(t in PLACE_MARKERS for t in window):
        return EntityType.PLACE
    return EntityType.THING


def _detect_role_type(token: str, sentence_tokens: list[str], token_index: int) -> RoleType:
    """Detect syntactic role type from position and context."""
    token_lower = token.lower()

    # SUBJ heuristic: first capitalized content token in sentence
    # Check if token is at start of sentence (after sentence-start punctuation)
    is_first_capitalized = False
    if token_index == 0:
        # Check if first letter of original text at this position is capitalized
        # We can't easily do this without the original text, so use a simpler heuristic:
        # If it's the first content token, likely subject
        is_first_capitalized = True
    else:
        # Check if preceded by sentence boundary
        # Look back for sentence-ending punctuation in previous tokens
        prev_window = sentence_tokens[max(0, token_index - 5):token_index]
        # If we see nothing that looks like a sentence end, and we're near start, maybe subject
        if token_index <= 2:
            is_first_capitalized = True

    if is_first_capitalized:
        return RoleType.SUBJ

    # OBJ heuristic: near verb-like tokens (not at sentence start)
    verb_window = sentence_tokens[max(0, token_index - 2):min(len(sentence_tokens), token_index + 3)]
    if any(t in VERB_LIKE for t in verb_window):
        return RoleType.OBJ

    # OBL heuristic: after prepositions
    if token_lower in PREPOSITIONS:
        return RoleType.OBL
    # Check if preceded by preposition
    if token_index > 0 and sentence_tokens[token_index - 1] in PREPOSITIONS:
        return RoleType.OBL

    return RoleType.NONE


def _detect_relation_type(sentence_tokens: list[str], source_idx: int, target_idx: int) -> RelationType:
    """Detect relation type from markers between source and target."""
    # Check the window between source and target for markers
    start, end = min(source_idx, target_idx), max(source_idx, target_idx)
    window = sentence_tokens[start:end + 1]

    window_lower = [t.lower() for t in window]

    if any(t in CAUSAL_MARKERS for t in window_lower):
        return RelationType.CAUSAL
    if any(t in ENABLE_MARKERS for t in window_lower):
        return RelationType.ENABLE
    if any(t in TEMPORAL_MARKERS for t in window_lower):
        return RelationType.TEMPORAL
    if any(t in SIMILARITY_MARKERS for t in window_lower):
        return RelationType.SIMILARITY

    return RelationType.PLAIN


def _is_negated(sentence_tokens: list[str], source_idx: int, target_idx: int) -> bool:
    """Check if relation is within negation scope."""
    start, end = min(source_idx, target_idx), max(source_idx, target_idx)
    window = sentence_tokens[start:end + 1]
    return any(t.lower() in NEGATION_MARKERS for t in window)


# ========== MAIN REDUCER ==========

def reduce_narrative_v2(text: str) -> TypedReducedStructure:
    """Reduce narrative to typed support structure. Deterministic; fail-closed.

    Returns TypedReducedStructure with:
      - typed_roles: token -> TypedRole (syntactic + entity type)
      - typed_relations: list of TypedRelation (with relation type and negation)
      - CANNOT_CHECK conditions checked by the witness arm

    Empty or content-free text yields empty structure.
    """
    # 1. Extract content tokens and frequency
    counts: dict[str, int] = {}
    for token in content_tokens(text):
        counts[token] = counts.get(token, 0) + 1

    # 2. Select top MAX_ROLES by frequency (same as parent)
    sorted_tokens = sorted(counts, key=lambda t: (-counts[t], t))
    top_tokens = sorted_tokens[:MAX_ROLES]
    roles = frozenset(top_tokens)

    # 3. Extract typed roles and relations per sentence
    typed_roles: dict[str, TypedRole] = {}
    typed_relations: list[TypedRelation] = []
    obstructions: list[Obstruction] = []

    sentences = _SENTENCE_SPLIT.split(text.lower())

    for sent_index, sentence in enumerate(sentences):
        sent_tokens = _tokens(sentence)

        # Find role positions in this sentence
        role_positions = [
            (pos, token)
            for pos, token in enumerate(sent_tokens)
            if token in roles
        ]

        # Extract typed roles from this sentence
        for pos, token in role_positions:
            if token not in typed_roles:
                role_type = _detect_role_type(token, sent_tokens, pos)
                entity_type = _detect_entity_type(token, sent_tokens, pos)
                typed_roles[token] = TypedRole(
                    token=token,
                    role_type=role_type,
                    entity_type=entity_type,
                    frequency=counts[token]
                )

        # Extract relations (co-occurrence within window)
        for (p1, t1), (p2, t2) in zip(role_positions, role_positions[1:]):
            if t1 != t2 and p2 - p1 <= RELATION_WINDOW:
                relation_type = _detect_relation_type(sent_tokens, p1, p2)
                negated = _is_negated(sent_tokens, p1, p2)

                typed_relations.append(TypedRelation(
                    source=t1,
                    target=t2,
                    relation_type=relation_type,
                    negated=negated,
                    sentence_context=sentence.strip()[:160]
                ))

        # Obstruction harvest (same as parent): sentence with >=2 roles and negation
        sentence_role_set = frozenset(token for _, token in role_positions)
        if len(sentence_role_set) >= 2 and any(
            token in NEGATION_MARKERS for token in sent_tokens
        ):
            obstructions.append(
                Obstruction(
                    obstruction_id=f"contrast::{sent_index}",
                    cover=sentence_role_set,
                    detail=sentence.strip()[:160],
                )
            )

    # 4. Build structure (compatible with parent framework)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    atoms = tuple(Atom(atom_id=role) for role in sorted(roles))

    # Flat relations for compatibility (negated relations still emitted as edges)
    flat_relations = frozenset(
        (r.source, r.target) for r in typed_relations
    )

    edges = tuple(
        SupportEdge(source=s, target=t, cost=1.0, licensed_at=0)
        for s, t in sorted(flat_relations)
    )

    structure = SupportStructure(
        structure_id=f"narrative_v2::{digest[:16]}",
        atoms=atoms,
        edges=edges,
        obstructions=tuple(obstructions),
    )

    return TypedReducedStructure(
        structure=structure,
        roles=roles,
        relations=flat_relations,
        typed_roles=typed_roles,
        typed_relations=typed_relations,
        provenance=f"sha256:{digest}",
    )
