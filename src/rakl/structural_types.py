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
        if any(not item.strip() for item in self.invariants):
            raise ValueError("invariants cannot be empty strings")
        if not self.evidence_ids or any(not item.strip() for item in self.evidence_ids):
            raise ValueError("structural object requires evidence identities")

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
        if len(src) != len(set(src)) or len(dst) != len(set(dst)):
            raise ValueError("role mapping must be one-to-one within a witness")
        if not self.evidence_ids:
            raise ValueError("structural witness requires evidence")


@dataclass(frozen=True)
class TransferAssessment:
    decision: TransferDecision
    reasons: tuple[str, ...]
    preserved_relation_count: int
    required_relation_count: int
    preserved_invariant_count: int
    required_invariant_count: int

    @property
    def structurally_complete(self) -> bool:
        return (
            self.preserved_relation_count == self.required_relation_count
            and self.preserved_invariant_count == self.required_invariant_count
        )
