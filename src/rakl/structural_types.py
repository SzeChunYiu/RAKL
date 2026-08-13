from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class StructuralRole:
    role_id: str
    kind: str

    def __post_init__(self) -> None:
        if not self.role_id.strip() or not self.kind.strip():
            raise ValueError("structural role identity and kind are required")


@dataclass(frozen=True)
class StructuralRelation:
    source_role: str
    relation_type: str
    target_role: str
    directed: bool = True

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.source_role, self.relation_type, self.target_role)):
            raise ValueError("relation endpoints and type are required")

    @property
    def signature(self) -> tuple[str, str, str, bool]:
        return (self.source_role, self.relation_type, self.target_role, self.directed)


@dataclass(frozen=True)
class BoundaryCondition:
    key: str
    value: str

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.value.strip():
            raise ValueError("boundary key/value are required")


@dataclass(frozen=True)
class StructuralObject:
    """QoI- and context-scoped relational structure.

    The object deliberately separates domain-facing labels from role identifiers so that
    transfer can be evaluated on relations/invariants while retaining the original
    scientific context and evidence.  It is not assumed to be a globally sufficient or
    unique representation of the underlying scientific object.
    """

    structure_id: str
    domain: str
    qoi: str
    context_id: str
    roles: tuple[StructuralRole, ...]
    relations: tuple[StructuralRelation, ...]
    invariants: frozenset[str]
    boundaries: tuple[BoundaryCondition, ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.structure_id, self.domain, self.qoi, self.context_id)):
            raise ValueError("structure identity, domain, QoI and context are required")
        role_ids = [role.role_id for role in self.roles]
        if len(role_ids) != len(set(role_ids)):
            raise ValueError("structural role ids must be unique")
        known = set(role_ids)
        for relation in self.relations:
            if relation.source_role not in known or relation.target_role not in known:
                raise ValueError("relation refers to unknown role")
        relation_signatures = [relation.signature for relation in self.relations]
        if len(relation_signatures) != len(set(relation_signatures)):
            raise ValueError("structural relation signatures must be unique")
        if any(not item.strip() for item in self.invariants):
            raise ValueError("invariants cannot be empty strings")
        boundary_keys = [item.key for item in self.boundaries]
        if len(boundary_keys) != len(set(boundary_keys)):
            raise ValueError("structural boundary keys must be unique")
        if not self.evidence_ids or any(not item.strip() for item in self.evidence_ids):
            raise ValueError("structural object requires evidence identities")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("structural object evidence identities must be unique")

    @property
    def role_ids(self) -> frozenset[str]:
        return frozenset(role.role_id for role in self.roles)

    @property
    def boundary_map(self) -> dict[str, str]:
        return {item.key: item.value for item in self.boundaries}


class TransferDecision(str, Enum):
    LICENSED = "LICENSED"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class StructuralWitness:
    """Directional witness from source structure to target structure.

    A witness is intentionally not an equivalence certificate.  Transfer can be
    directional, QoI-specific, context-specific and non-transitive.
    """

    witness_id: str
    source_structure_id: str
    target_structure_id: str
    role_mapping: tuple[tuple[str, str], ...]
    preserved_invariants: frozenset[str]
    non_preserved_properties: frozenset[str]
    required_target_boundaries: tuple[BoundaryCondition, ...]
    evidence_ids: tuple[str, ...]
    uncertainty_note: str = ""

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.witness_id, self.source_structure_id, self.target_structure_id)
        ):
            raise ValueError("witness and endpoint identities are required")
        src = [a for a, _ in self.role_mapping]
        dst = [b for _, b in self.role_mapping]
        if any(not a.strip() or not b.strip() for a, b in self.role_mapping):
            raise ValueError("witness role mappings cannot contain blank role identities")
        if len(src) != len(set(src)) or len(dst) != len(set(dst)):
            raise ValueError("role mapping must be one-to-one within a witness")
        if any(not item.strip() for item in self.preserved_invariants | self.non_preserved_properties):
            raise ValueError("witness invariant/property names cannot be blank")
        boundary_keys = [item.key for item in self.required_target_boundaries]
        if len(boundary_keys) != len(set(boundary_keys)):
            raise ValueError("witness target-boundary keys must be unique")
        if not self.evidence_ids or any(not item.strip() for item in self.evidence_ids):
            raise ValueError("structural witness requires nonblank evidence identities")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("structural witness evidence identities must be unique")


@dataclass(frozen=True)
class TransferAssessment:
    """Assessment of one structural transfer witness.

    Completeness of a preservation claim is SET INCLUSION, not equal
    cardinality (audit I6): with counts alone, "the wrong 3 of the required 3
    relations preserved" is unstatable. The ``required_*``/``preserved_*``
    set fields (additive) carry the actual certified sets;
    ``structurally_complete`` is decided by inclusion over them and FAILS
    CLOSED (False) when the sets are absent. The counts remain as reporting
    coordinates only.
    """

    decision: TransferDecision
    reasons: tuple[str, ...]
    preserved_relation_count: int
    required_relation_count: int
    preserved_invariant_count: int
    required_invariant_count: int
    required_relations: frozenset[str] | None = None
    preserved_relations: frozenset[str] | None = None
    required_invariants: frozenset[str] | None = None
    preserved_invariants: frozenset[str] | None = None

    @property
    def structurally_complete(self) -> bool:
        if (
            self.required_relations is None
            or self.preserved_relations is None
            or self.required_invariants is None
            or self.preserved_invariants is None
        ):
            # Fail closed: completeness is a claim about WHICH relations and
            # invariants were preserved; counts cannot state it (audit I6).
            return False
        return self.required_relations <= self.preserved_relations and self.required_invariants <= self.preserved_invariants

    @property
    def cardinality_complete(self) -> bool:
        """Legacy count comparison. Reporting only: never a completeness license."""
        return (
            self.preserved_relation_count == self.required_relation_count
            and self.preserved_invariant_count == self.required_invariant_count
        )


@dataclass(frozen=True)
class ChartTransitionWitness:
    """Role-level transition map between two charts (audit I6).

    Partial injections compose; this witness is the morphism datum of the
    chart groupoid the papers' atlas language presumes. It certifies nothing
    about triple-overlap coherence by itself — that is the cocycle check.
    """

    witness_id: str
    source_chart_id: str
    target_chart_id: str
    role_mapping: tuple[tuple[str, str], ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.witness_id, self.source_chart_id, self.target_chart_id)):
            raise ValueError("chart transition witness requires witness and chart identities")
        src = [a for a, _ in self.role_mapping]
        dst = [b for _, b in self.role_mapping]
        if any(not a.strip() or not b.strip() for a, b in self.role_mapping):
            raise ValueError("chart transition role mappings cannot contain blank role identities")
        if len(src) != len(set(src)) or len(dst) != len(set(dst)):
            raise ValueError("chart transition role mapping must be one-to-one (a partial injection)")
        if not self.evidence_ids or any(not item.strip() for item in self.evidence_ids):
            raise ValueError("chart transition witness requires nonblank evidence identities")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("chart transition evidence identities must be unique")

    @property
    def mapping(self) -> dict[str, str]:
        return dict(self.role_mapping)


def compose_chart_transitions(
    first: ChartTransitionWitness,
    second: ChartTransitionWitness,
    *,
    witness_id: str,
) -> ChartTransitionWitness:
    """Compose two chart transitions as partial injections (audit I6)."""
    if first.target_chart_id != second.source_chart_id:
        raise ValueError(
            "chart transition composition endpoint mismatch: "
            f"{first.witness_id!r} lands in chart {first.target_chart_id!r} but "
            f"{second.witness_id!r} departs from chart {second.source_chart_id!r}"
        )
    second_map = second.mapping
    composed = tuple(
        (source_role, second_map[middle_role])
        for source_role, middle_role in first.role_mapping
        if middle_role in second_map
    )
    return ChartTransitionWitness(
        witness_id=witness_id,
        source_chart_id=first.source_chart_id,
        target_chart_id=second.target_chart_id,
        role_mapping=composed,
        evidence_ids=tuple(dict.fromkeys(first.evidence_ids + second.evidence_ids)),
    )


@dataclass(frozen=True)
class AtlasCocycleCheck:
    """Triple-overlap coherence check phi_ik = phi_jk o phi_ij (audit I6).

    The standard atlas cocycle condition — the weakest axiom under which a
    multi-chart ("atlas navigability") claim is well formed. ``passed`` holds
    only when, on every role where either side is defined, both sides are
    defined and agree; a role carried by the composite but missing (or
    disagreeing) in the direct transition fails closed, and vice versa.
    """

    check_id: str
    witness_ij: ChartTransitionWitness
    witness_jk: ChartTransitionWitness
    witness_ik: ChartTransitionWitness

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("atlas cocycle check requires an identity")
        if self.witness_ij.target_chart_id != self.witness_jk.source_chart_id:
            raise ValueError("cocycle check chart chain mismatch: ij must land where jk departs")
        if self.witness_ij.source_chart_id != self.witness_ik.source_chart_id:
            raise ValueError("cocycle check chart chain mismatch: ij and ik must share a source chart")
        if self.witness_jk.target_chart_id != self.witness_ik.target_chart_id:
            raise ValueError("cocycle check chart chain mismatch: jk and ik must share a target chart")

    @property
    def mismatched_roles(self) -> tuple[str, ...]:
        composed = compose_chart_transitions(self.witness_ij, self.witness_jk, witness_id=f"{self.check_id}:composed").mapping
        direct = self.witness_ik.mapping
        bad = {role for role in composed.keys() | direct.keys() if composed.get(role) != direct.get(role)}
        return tuple(sorted(bad))

    @property
    def overlap_roles(self) -> tuple[str, ...]:
        composed = compose_chart_transitions(self.witness_ij, self.witness_jk, witness_id=f"{self.check_id}:composed").mapping
        return tuple(sorted(composed.keys() & self.witness_ik.mapping.keys()))

    @property
    def passed(self) -> bool:
        return not self.mismatched_roles

    @property
    def grants_global_geometry_authority(self) -> bool:
        return False
