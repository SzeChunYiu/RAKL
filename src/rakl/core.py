from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence


class Relationship(str, Enum):
    COMPLEMENTARY = "COMPLEMENTARY"
    EXACT_ISOMORPHISM = "EXACT_ISOMORPHISM"
    GENERATOR_EQUIVALENCE = "GENERATOR_EQUIVALENCE"
    OBSERVATIONAL_EQUIVALENCE = "OBSERVATIONAL_EQUIVALENCE"
    ASYMPTOTIC_EQUIVALENCE = "ASYMPTOTIC_EQUIVALENCE"
    QOI_EQUIVALENCE = "QOI_EQUIVALENCE"
    APPROXIMATE_REPRESENTATION = "APPROXIMATE_REPRESENTATION"
    CONTEXT_DEPENDENT_DIFFERENCE = "CONTEXT_DEPENDENT_DIFFERENCE"
    CONTRADICTION = "CONTRADICTION"
    ANALOGY_ONLY = "ANALOGY_ONLY"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


TRANSITIVE_EQUIVALENCE_RELATIONSHIPS = frozenset(
    {
        Relationship.EXACT_ISOMORPHISM,
        Relationship.GENERATOR_EQUIVALENCE,
        Relationship.OBSERVATIONAL_EQUIVALENCE,
        Relationship.ASYMPTOTIC_EQUIVALENCE,
        Relationship.QOI_EQUIVALENCE,
    }
)


class Authority(str, Enum):
    SOURCE_PROJECTION = "SOURCE_PROJECTION"
    NORMALIZED_CLAIM = "NORMALIZED_CLAIM"
    EQUIVALENCE_CLASS = "EQUIVALENCE_CLASS"
    PREDICTIVE_SURVIVOR = "PREDICTIVE_SURVIVOR"
    MECHANISTICALLY_DERIVED = "MECHANISTICALLY_DERIVED"
    IDENTIFIED_OR_BOUNDED = "IDENTIFIED_OR_BOUNDED"
    DECISION_USABLE = "DECISION_USABLE"


@dataclass(frozen=True)
class Context:
    population: str | None = None
    scale: str | None = None
    horizon: str | None = None
    observation_model: str | None = None
    units: str | None = None
    assumptions: tuple[str, ...] = ()
    intervention: str | None = None
    method: str | None = None

    def comparable_key(
        self,
        fields: Sequence[str] = (
            "population",
            "scale",
            "horizon",
            "observation_model",
            "units",
            "assumptions",
            "intervention",
        ),
    ) -> tuple:
        return tuple(getattr(self, name) for name in fields)


@dataclass(frozen=True)
class Projection:
    projection_id: str
    object_id: str
    facets: tuple[str, ...]
    claim: str
    source: str
    context: Context = Context()
    authority: Authority = Authority.SOURCE_PROJECTION
    mathematical_object: str | None = None
    mechanism_interpretation: str | None = None
    projection_operator: str | None = None
    cannot_see: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Relation:
    left: str
    right: str
    relationship: Relationship
    scope: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Discriminator:
    discriminator_id: str
    hypotheses: tuple[str, ...]
    separation_score: float
    cost: float
    prediction_frozen: bool = False
    identified_set_shrinkage: float = 0.0
    required_data: tuple[str, ...] = ()

    def utility(self, shrinkage_weight: float = 1.0) -> float:
        if self.cost <= 0:
            raise ValueError("cost must be positive")
        penalty = 1.0 if self.prediction_frozen else 0.5
        return penalty * (
            self.separation_score + shrinkage_weight * self.identified_set_shrinkage
        ) / self.cost


def _components_from_relations(relations: Iterable[Relation]) -> list[set[str]]:
    """Connected components for one already-compatible relation layer."""
    edges = list(relations)
    nodes = {endpoint for relation in edges for endpoint in (relation.left, relation.right)}
    parent = {node: node for node in nodes}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for relation in edges:
        union(relation.left, relation.right)

    groups: dict[str, set[str]] = {}
    for node in parent:
        groups.setdefault(find(node), set()).add(node)
    return [group for group in groups.values() if len(group) > 1]


@dataclass
class KnowledgeFiber:
    fiber_id: str
    object_id: str
    atomic_step: str
    projections: dict[str, Projection] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    dimensions: dict[str, set[str]] = field(default_factory=dict)
    required_facets: set[str] = field(default_factory=set)
    child_fibers: set[str] = field(default_factory=set)

    def add_projection(self, projection: Projection) -> None:
        if projection.object_id != self.object_id:
            raise ValueError(
                f"projection object {projection.object_id!r} does not match "
                f"fiber object {self.object_id!r}"
            )
        if not projection.projection_id:
            raise ValueError("projection_id cannot be empty")

        existing = self.projections.get(projection.projection_id)
        if existing is not None:
            if existing == projection:
                # Event replay/retry is safe and does not duplicate semantic state.
                return
            raise ValueError(
                f"projection_id {projection.projection_id!r} already exists with "
                "different content; projection identity is immutable"
            )

        self.projections[projection.projection_id] = projection
        self.dimensions.setdefault("facets", set()).update(projection.facets)

    def add_relation(self, relation: Relation) -> None:
        missing = {relation.left, relation.right} - self.projections.keys()
        if missing:
            raise KeyError(f"relation references missing projections: {sorted(missing)}")
        self.relations.append(relation)

    def covered_facets(self) -> set[str]:
        covered: set[str] = set()
        for projection in self.projections.values():
            covered.update(projection.facets)
        return covered

    def missing_facets(self) -> set[str]:
        return set(self.required_facets) - self.covered_facets()

    def projections_for_facet(self, facet: str) -> list[Projection]:
        return [p for p in self.projections.values() if facet in p.facets]

    def relation_map(self) -> dict[frozenset[str], Relation]:
        result: dict[frozenset[str], Relation] = {}
        for relation in self.relations:
            result[frozenset((relation.left, relation.right))] = relation
        return result

    def unresolved_pairs(self) -> list[tuple[str, str]]:
        """Pairs sharing a facet but lacking an explicit semantic relationship."""
        relation_map = self.relation_map()
        ids = sorted(self.projections)
        unresolved: list[tuple[str, str]] = []
        for i, left_id in enumerate(ids):
            left = self.projections[left_id]
            for right_id in ids[i + 1 :]:
                right = self.projections[right_id]
                if not set(left.facets).intersection(right.facets):
                    continue
                if frozenset((left_id, right_id)) not in relation_map:
                    unresolved.append((left_id, right_id))
        return unresolved

    def contradictions(self) -> list[Relation]:
        return [
            relation
            for relation in self.relations
            if relation.relationship == Relationship.CONTRADICTION
        ]

    def context_dependent_differences(self) -> list[Relation]:
        return [
            relation
            for relation in self.relations
            if relation.relationship == Relationship.CONTEXT_DEPENDENT_DIFFERENCE
        ]

    def equivalence_layers(self) -> list[dict]:
        """Return transitive equivalence components without crossing type or scope.

        A chain may be closed transitively only inside one relationship type and one
        declared scope. This prevents an exact-isomorphism edge followed by a
        QoI-equivalence edge from silently becoming a stronger three-way equivalence.
        Approximation is deliberately excluded because pairwise approximation is not
        generally transitive.
        """
        grouped: dict[tuple[Relationship, str | None], list[Relation]] = {}
        for relation in self.relations:
            if relation.relationship not in TRANSITIVE_EQUIVALENCE_RELATIONSHIPS:
                continue
            grouped.setdefault((relation.relationship, relation.scope), []).append(relation)

        layers: list[dict] = []
        for (relationship, scope), relations in sorted(
            grouped.items(), key=lambda item: (item[0][0].value, item[0][1] or "")
        ):
            for group in _components_from_relations(relations):
                layers.append(
                    {
                        "relationship": relationship.value,
                        "scope": scope,
                        "members": sorted(group),
                    }
                )
        return layers

    def equivalence_classes(
        self,
        relationship: Relationship = Relationship.EXACT_ISOMORPHISM,
        *,
        scope: str | None = None,
    ) -> list[set[str]]:
        """Connected components for one equivalence layer.

        The safe default is exact isomorphism. When ``scope`` is omitted, components
        from all scopes of the selected relationship are returned, but each scope is
        still closed separately. Cross-type or cross-scope transitive closure is never
        inferred.
        """
        if relationship not in TRANSITIVE_EQUIVALENCE_RELATIONSHIPS:
            raise ValueError(
                f"{relationship.value} is not licensed for transitive equivalence closure"
            )

        grouped: dict[str | None, list[Relation]] = {}
        for relation in self.relations:
            if relation.relationship != relationship:
                continue
            if scope is not None and relation.scope != scope:
                continue
            grouped.setdefault(relation.scope, []).append(relation)

        groups: list[set[str]] = []
        for relation_scope in sorted(grouped, key=lambda value: value or ""):
            groups.extend(_components_from_relations(grouped[relation_scope]))
        return groups

    def approximate_relationships(self) -> list[Relation]:
        """Return approximation edges pairwise rather than treating them as closure."""
        return [
            relation
            for relation in self.relations
            if relation.relationship == Relationship.APPROXIMATE_REPRESENTATION
        ]

    def global_portrait(self) -> dict:
        """Compact evidence-preserving Apple/Knowledge-Atlas synthesis."""
        by_facet = {
            facet: [p.projection_id for p in self.projections_for_facet(facet)]
            for facet in sorted(self.covered_facets())
        }
        return {
            "object_id": self.object_id,
            "fiber_id": self.fiber_id,
            "atomic_step": self.atomic_step,
            "facets": by_facet,
            "missing_facets": sorted(self.missing_facets()),
            # Compatibility alias with a deliberately safe meaning: exact-only.
            "equivalence_classes": [
                sorted(group) for group in self.equivalence_classes()
            ],
            "equivalence_layers": self.equivalence_layers(),
            "approximate_relationships": [
                {
                    "left": relation.left,
                    "right": relation.right,
                    "scope": relation.scope,
                    "evidence": list(relation.evidence),
                }
                for relation in self.approximate_relationships()
            ],
            "contradictions": [
                {
                    "left": relation.left,
                    "right": relation.right,
                    "scope": relation.scope,
                    "evidence": list(relation.evidence),
                }
                for relation in self.contradictions()
            ],
            "context_dependent_differences": [
                {
                    "left": relation.left,
                    "right": relation.right,
                    "scope": relation.scope,
                }
                for relation in self.context_dependent_differences()
            ],
            "unresolved_pairs": [
                {"left": left, "right": right}
                for left, right in self.unresolved_pairs()
            ],
        }

    def reflection_tasks(self) -> list[dict]:
        """Generate deterministic research tasks for an LLM or human researcher."""
        tasks: list[dict] = []
        for facet in sorted(self.missing_facets()):
            tasks.append(
                {
                    "kind": "EXPAND_MISSING_FACET",
                    "facet": facet,
                    "prompt": (
                        f"Find semantically distinct projections and mechanisms for "
                        f"missing facet {facet!r} of object {self.object_id!r}."
                    ),
                }
            )

        for left, right in self.unresolved_pairs():
            tasks.append(
                {
                    "kind": "CLASSIFY_RELATIONSHIP",
                    "projections": [left, right],
                    "prompt": (
                        "Determine whether these projections are complementary, equivalent, "
                        "context-dependent, contradictory, or incomparable. Align context "
                        "before deciding."
                    ),
                }
            )

        for relation in self.contradictions():
            tasks.append(
                {
                    "kind": "DESIGN_DISCRIMINATOR",
                    "projections": [relation.left, relation.right],
                    "scope": relation.scope,
                    "prompt": (
                        "Propose the cheapest high-information observation or experiment "
                        "that separates the aligned contradictory projections. Freeze "
                        "predictions before testing."
                    ),
                }
            )

        for relation in self.context_dependent_differences():
            tasks.append(
                {
                    "kind": "EXPAND_CONTEXT_COORDINATE",
                    "projections": [relation.left, relation.right],
                    "scope": relation.scope,
                    "prompt": (
                        "Identify the omitted context coordinate that makes the two "
                        "projections jointly coherent and add it to the object portrait."
                    ),
                }
            )
        return tasks


def rank_discriminators(
    discriminators: Iterable[Discriminator],
    *,
    shrinkage_weight: float = 1.0,
) -> list[Discriminator]:
    """Rank by separation plus identified-set shrinkage per cost."""
    return sorted(
        discriminators,
        key=lambda discriminator: discriminator.utility(
            shrinkage_weight=shrinkage_weight
        ),
        reverse=True,
    )


def compare_contexts(
    left: Context,
    right: Context,
    *,
    fields: Sequence[str] = (
        "population",
        "scale",
        "horizon",
        "observation_model",
        "units",
        "assumptions",
        "intervention",
    ),
) -> dict[str, tuple[object, object]]:
    """Return context coordinates that may explain an apparent conflict."""
    differences: dict[str, tuple[object, object]] = {}
    for field_name in fields:
        left_value, right_value = getattr(left, field_name), getattr(right, field_name)
        if left_value != right_value:
            differences[field_name] = (left_value, right_value)
    return differences


def semantic_gain(
    before: Mapping[str, Iterable[str]],
    after: Mapping[str, Iterable[str]],
) -> dict[str, list[str]]:
    """Return newly retained semantic objects by category."""
    gain: dict[str, list[str]] = {}
    keys = set(before) | set(after)
    for key in sorted(keys):
        previous = set(before.get(key, ()))
        current = set(after.get(key, ()))
        new_items = sorted(current - previous)
        if new_items:
            gain[key] = new_items
    return gain
