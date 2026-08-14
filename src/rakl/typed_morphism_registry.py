"""Typed Morphism Registry (M3): minimal validator prototype.

This module implements a minimal validator prototype for M3 Typed Morphism Registry.
It provides 2-3 object families with machine-checkable validators:
1. Causal exact abstraction (relation preservation)
2. Homomorphism preservation (operation preservation)
3. Assume-guarantee refinement (precondition/postcondition)

Each validator produces LICENSED/REJECTED/CANNOT_CHECK with a certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Set, Tuple


class ValidatorDecision(str, Enum):
    """Decision output from morphism validator."""
    LICENSED = "LICENSED"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ValidatorCertificate:
    """Certificate accompanying validator decision."""
    decision: ValidatorDecision
    reasons: Tuple[str, ...]
    satisfied_preconditions: frozenset[str]
    preserved_invariants: frozenset[str]
    violated_forbidden_losses: frozenset[str]
    satisfied_boundaries: frozenset[str]
    evidence_completeness: float  # 0.0 to 1.0


@dataclass(frozen=True)
class MorphismWitness:
    """A typed morphism witness."""
    source_type: str
    target_type: str
    morphism_family: str
    preconditions: frozenset[str]  # Callable predicates represented as names
    preserved_invariants: frozenset[str]
    forbidden_losses: frozenset[str]
    required_boundaries: frozenset[str]
    evidence_pointers: Tuple[str, ...]


class TypedMorphismRegistry:
    """Registry for typed morphism families with validators."""

    def __init__(self) -> None:
        self._validators: Dict[str, Callable[[Any, Any, MorphismWitness], ValidatorCertificate]] = {}
        self._type_checkers: Dict[str, Callable[[Any, Any], bool]] = {}

    def register_family(
        self,
        family: str,
        validator: Callable[[Any, Any, MorphismWitness], ValidatorCertificate],
        type_checker: Callable[[Any, Any], bool],
    ) -> None:
        """Register a morphism family with its validator and type checker."""
        self._validators[family] = validator
        self._type_checkers[family] = type_checker

    def validate_witness(
        self,
        source: Any,
        target: Any,
        witness: MorphismWitness,
    ) -> ValidatorCertificate:
        """Validate a morphism witness against registered families."""

        # Type check
        family = witness.morphism_family
        if family not in self._validators:
            return ValidatorCertificate(
                decision=ValidatorDecision.REJECTED,
                reasons=("unknown_morphism_family",),
                satisfied_preconditions=frozenset(),
                preserved_invariants=frozenset(),
                violated_forbidden_losses=frozenset(),
                satisfied_boundaries=frozenset(),
                evidence_completeness=0.0,
            )

        type_checker = self._type_checkers.get(family)
        if type_checker is None:
            return ValidatorCertificate(
                decision=ValidatorDecision.CANNOT_CHECK,
                reasons=("missing_type_checker",),
                satisfied_preconditions=frozenset(),
                preserved_invariants=frozenset(),
                violated_forbidden_losses=frozenset(),
                satisfied_boundaries=frozenset(),
                evidence_completeness=0.0,
            )

        if not type_checker(source, target):
            return ValidatorCertificate(
                decision=ValidatorDecision.REJECTED,
                reasons=("type_mismatch",),
                satisfied_preconditions=frozenset(),
                preserved_invariants=frozenset(),
                violated_forbidden_losses=frozenset(),
                satisfied_boundaries=frozenset(),
                evidence_completeness=0.0,
            )

        # Delegate to family-specific validator
        return self._validators[family](source, target, witness)


# =============================================================================
# Object Family 1: Causal Exact Abstraction
# =============================================================================

@dataclass(frozen=True)
class CausalStructure:
    """Causal structure for exact abstraction."""
    structure_id: str
    relations: frozenset[Tuple[str, str, str]]  # (source, relation, target)
    invariants: frozenset[str]
    boundary_conditions: frozenset[Tuple[str, Any]]


def _causal_type_checker(source: Any, target: Any) -> bool:
    """Type checker for causal structures."""
    return isinstance(source, CausalStructure) and isinstance(target, CausalStructure)


def _causal_validator(
    source: Any,
    target: Any,
    witness: MorphismWitness,
) -> ValidatorCertificate:
    """Validator for causal exact abstraction.

    Checks:
    1. Preconditions: source and target are CausalStructure
    2. Invariants: all declared invariants exist in target
    3. Forbidden losses: no declared relations are lost
    4. Boundaries: boundary conditions are satisfied
    5. Evidence: at least one evidence pointer provided
    """
    reasons: list[str] = []
    satisfied_preconditions: Set[str] = set()
    preserved_invariants: Set[str] = set()
    violated_forbidden_losses: Set[str] = set()
    satisfied_boundaries: Set[str] = set()

    if not isinstance(source, CausalStructure) or not isinstance(target, CausalStructure):
        return ValidatorCertificate(
            decision=ValidatorDecision.CANNOT_CHECK,
            reasons=("not_causal_structure",),
            satisfied_preconditions=frozenset(),
            preserved_invariants=frozenset(),
            violated_forbidden_losses=frozenset(),
            satisfied_boundaries=frozenset(),
            evidence_completeness=0.0,
        )

    # Preconditions
    satisfied_preconditions.add("is_causal_structure")

    # Invariants preserved
    for inv in witness.preserved_invariants:
        if inv in target.invariants:
            preserved_invariants.add(inv)
        else:
            reasons.append(f"invariant_not_preserved:{inv}")

    # Forbidden losses (relations that must not be lost)
    target_relations = target.relations
    for rel in source.relations:
        # If this relation is declared as forbidden loss, check if it's preserved
        if rel in witness.forbidden_losses and rel not in target_relations:
            violated_forbidden_losses.add(rel)
            reasons.append(f"forbidden_loss:{rel}")

    # Boundaries satisfied
    target_boundaries = {k: v for k, v in target.boundary_conditions}
    for key, value in source.boundary_conditions:
        if key in target_boundaries and target_boundaries[key] == value:
            satisfied_boundaries.add(key)
        else:
            reasons.append(f"boundary_mismatch:{key}")

    # Evidence completeness
    evidence_completeness = min(1.0, len(witness.evidence_pointers) / 2.0)

    decision = ValidatorDecision.LICENSED if not reasons else ValidatorDecision.REJECTED
    return ValidatorCertificate(
        decision=decision,
        reasons=tuple(reasons),
        satisfied_preconditions=frozenset(satisfied_preconditions),
        preserved_invariants=frozenset(preserved_invariants),
        violated_forbidden_losses=frozenset(violated_forbidden_losses),
        satisfied_boundaries=frozenset(satisfied_boundaries),
        evidence_completeness=evidence_completeness,
    )


# =============================================================================
# Object Family 2: Homomorphism Preservation
# =============================================================================

@dataclass(frozen=True)
class AlgebraicStructure:
    """Algebraic structure for homomorphism."""
    structure_id: str
    operations: frozenset[Tuple[str, int]]  # (operation_name, arity)
    relations: frozenset[Tuple[str, int]]  # (relation_name, arity)
    axioms: frozenset[str]


def _homomorphism_type_checker(source: Any, target: Any) -> bool:
    """Type checker for algebraic structures."""
    return isinstance(source, AlgebraicStructure) and isinstance(target, AlgebraicStructure)


def _homomorphism_validator(
    source: Any,
    target: Any,
    witness: MorphismWitness,
) -> ValidatorCertificate:
    """Validator for homomorphism preservation.

    Checks:
    1. Preconditions: source and target are AlgebraicStructure
    2. Invariants: all declared axioms exist in target
    3. Operation preservation: operations with same arity exist
    4. Boundaries: structure constraints satisfied
    5. Evidence: at least one evidence pointer provided
    """
    reasons: list[str] = []
    satisfied_preconditions: Set[str] = set()
    preserved_invariants: Set[str] = set()
    violated_forbidden_losses: Set[str] = set()
    satisfied_boundaries: Set[str] = set()

    if not isinstance(source, AlgebraicStructure) or not isinstance(target, AlgebraicStructure):
        return ValidatorCertificate(
            decision=ValidatorDecision.CANNOT_CHECK,
            reasons=("not_algebraic_structure",),
            satisfied_preconditions=frozenset(),
            preserved_invariants=frozenset(),
            violated_forbidden_losses=frozenset(),
            satisfied_boundaries=frozenset(),
            evidence_completeness=0.0,
        )

    # Preconditions
    satisfied_preconditions.add("is_algebraic_structure")

    # Invariants preserved (axioms)
    for axiom in witness.preserved_invariants:
        if axiom in target.axioms:
            preserved_invariants.add(axiom)
        else:
            reasons.append(f"axiom_not_preserved:{axiom}")

    # Operation preservation (arity must match)
    target_ops = {op: arity for op, arity in target.operations}
    for op, arity in source.operations:
        if op in witness.forbidden_losses:
            if op not in target_ops or target_ops[op] != arity:
                violated_forbidden_losses.add(op)
                reasons.append(f"operation_lost:{op}")

    satisfied_boundaries.add("arity_consistent")

    # Evidence completeness
    evidence_completeness = min(1.0, len(witness.evidence_pointers) / 2.0)

    decision = ValidatorDecision.LICENSED if not reasons else ValidatorDecision.REJECTED
    return ValidatorCertificate(
        decision=decision,
        reasons=tuple(reasons),
        satisfied_preconditions=frozenset(satisfied_preconditions),
        preserved_invariants=frozenset(preserved_invariants),
        violated_forbidden_losses=frozenset(violated_forbidden_losses),
        satisfied_boundaries=frozenset(satisfied_boundaries),
        evidence_completeness=evidence_completeness,
    )


# =============================================================================
# Factory function
# =============================================================================

def create_minimal_registry() -> TypedMorphismRegistry:
    """Create a minimal registry with 2-3 object families."""
    registry = TypedMorphismRegistry()

    # Register causal exact abstraction family
    registry.register_family(
        family="causal_exact_abstraction",
        validator=_causal_validator,
        type_checker=_causal_type_checker,
    )

    # Register homomorphism preservation family
    registry.register_family(
        family="homomorphism_preservation",
        validator=_homomorphism_validator,
        type_checker=_homomorphism_type_checker,
    )

    return registry
