"""Tests for Typed Morphism Registry (M3) minimal validator prototype."""

import pytest

from rakl.typed_morphism_registry import (
    TypedMorphismRegistry,
    MorphismWitness,
    ValidatorDecision,
    ValidatorCertificate,
    CausalStructure,
    AlgebraicStructure,
    create_minimal_registry,
)


class TestCausalExactAbstraction:
    """Tests for causal exact abstraction validator."""

    def test_type_mismatch_rejected(self):
        registry = create_minimal_registry()
        source = CausalStructure(
            structure_id="source",
            relations=frozenset({("a", "rel", "b")}),
            invariants=frozenset({"inv1"}),
            boundary_conditions=frozenset({("bound1", 10)}),
        )
        target = {"not": "a_structure"}  # Wrong type
        witness = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="causal_exact_abstraction",
            preconditions=frozenset(),
            preserved_invariants=frozenset({"inv1"}),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1",),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.REJECTED
        assert "type_mismatch" in result.reasons

    def test_invariant_not_preserved_rejected(self):
        registry = create_minimal_registry()
        source = CausalStructure(
            structure_id="source",
            relations=frozenset({("a", "rel", "b")}),
            invariants=frozenset({"inv1", "inv2"}),
            boundary_conditions=frozenset(),
        )
        target = CausalStructure(
            structure_id="target",
            relations=frozenset({("a", "rel", "b")}),
            invariants=frozenset({"inv1"}),  # Missing inv2
            boundary_conditions=frozenset(),
        )
        witness = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="causal_exact_abstraction",
            preconditions=frozenset(),
            preserved_invariants=frozenset({"inv1", "inv2"}),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1",),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.REJECTED
        assert "invariant_not_preserved:inv2" in result.reasons

    def test_forbidden_loss_detected(self):
        registry = create_minimal_registry()
        source = CausalStructure(
            structure_id="source",
            relations=frozenset({("a", "rel", "b")}),
            invariants=frozenset(),
            boundary_conditions=frozenset(),
        )
        target = CausalStructure(
            structure_id="target",
            relations=frozenset(),  # Relation lost
            invariants=frozenset(),
            boundary_conditions=frozenset(),
        )
        witness = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="causal_exact_abstraction",
            preconditions=frozenset(),
            preserved_invariants=frozenset(),
            forbidden_losses=frozenset({("a", "rel", "b")}),  # This relation must be preserved
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1",),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.REJECTED
        assert result.violated_forbidden_losses == frozenset({("a", "rel", "b")})
        assert any("forbidden_loss" in r for r in result.reasons)

    def test_valid_transfer_licensed(self):
        registry = create_minimal_registry()
        source = CausalStructure(
            structure_id="source",
            relations=frozenset({("a", "rel", "b")}),
            invariants=frozenset({"inv1"}),
            boundary_conditions=frozenset({("bound1", 10)}),
        )
        target = CausalStructure(
            structure_id="target",
            relations=frozenset({("a", "rel", "b")}),
            invariants=frozenset({"inv1"}),
            boundary_conditions=frozenset({("bound1", 10)}),
        )
        witness = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="causal_exact_abstraction",
            preconditions=frozenset(),
            preserved_invariants=frozenset({"inv1"}),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1", "evidence2"),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.LICENSED
        assert len(result.reasons) == 0


class TestHomomorphismPreservation:
    """Tests for homomorphism preservation validator."""

    def test_type_mismatch_rejected(self):
        registry = create_minimal_registry()
        source = AlgebraicStructure(
            structure_id="source",
            operations=frozenset({("op1", 2)}),
            relations=frozenset(),
            axioms=frozenset({"axiom1"}),
        )
        target = {"not": "algebraic"}  # Wrong type
        witness = MorphismWitness(
            source_type="AlgebraicStructure",
            target_type="AlgebraicStructure",
            morphism_family="homomorphism_preservation",
            preconditions=frozenset(),
            preserved_invariants=frozenset({"axiom1"}),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1",),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.REJECTED
        assert "type_mismatch" in result.reasons

    def test_axiom_not_preserved_rejected(self):
        registry = create_minimal_registry()
        source = AlgebraicStructure(
            structure_id="source",
            operations=frozenset(),
            relations=frozenset(),
            axioms=frozenset({"axiom1", "axiom2"}),
        )
        target = AlgebraicStructure(
            structure_id="target",
            operations=frozenset(),
            relations=frozenset(),
            axioms=frozenset({"axiom1"}),  # Missing axiom2
        )
        witness = MorphismWitness(
            source_type="AlgebraicStructure",
            target_type="AlgebraicStructure",
            morphism_family="homomorphism_preservation",
            preconditions=frozenset(),
            preserved_invariants=frozenset({"axiom1", "axiom2"}),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1",),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.REJECTED
        assert "axiom_not_preserved:axiom2" in result.reasons

    def test_valid_homomorphism_licensed(self):
        registry = create_minimal_registry()
        source = AlgebraicStructure(
            structure_id="source",
            operations=frozenset({("op1", 2), ("op2", 1)}),
            relations=frozenset(),
            axioms=frozenset({"axiom1"}),
        )
        target = AlgebraicStructure(
            structure_id="target",
            operations=frozenset({("op1", 2), ("op2", 1)}),
            relations=frozenset(),
            axioms=frozenset({"axiom1"}),
        )
        witness = MorphismWitness(
            source_type="AlgebraicStructure",
            target_type="AlgebraicStructure",
            morphism_family="homomorphism_preservation",
            preconditions=frozenset(),
            preserved_invariants=frozenset({"axiom1"}),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("evidence1", "evidence2"),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.LICENSED
        assert len(result.reasons) == 0


class TestRegistryOperations:
    """Tests for registry operations."""

    def test_unknown_family_rejected(self):
        registry = create_minimal_registry()
        source = CausalStructure(
            structure_id="source",
            relations=frozenset(),
            invariants=frozenset(),
            boundary_conditions=frozenset(),
        )
        target = CausalStructure(
            structure_id="target",
            relations=frozenset(),
            invariants=frozenset(),
            boundary_conditions=frozenset(),
        )
        witness = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="unknown_family",
            preconditions=frozenset(),
            preserved_invariants=frozenset(),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=(),
        )
        result = registry.validate_witness(source, target, witness)
        assert result.decision == ValidatorDecision.REJECTED
        assert "unknown_morphism_family" in result.reasons

    def test_evidence_completeness_calculation(self):
        registry = create_minimal_registry()
        source = CausalStructure(
            structure_id="source",
            relations=frozenset(),
            invariants=frozenset(),
            boundary_conditions=frozenset(),
        )
        target = CausalStructure(
            structure_id="target",
            relations=frozenset(),
            invariants=frozenset(),
            boundary_conditions=frozenset(),
        )
        
        # Test with 1 evidence pointer
        witness1 = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="causal_exact_abstraction",
            preconditions=frozenset(),
            preserved_invariants=frozenset(),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("e1",),  # Only one evidence
        )
        result1 = registry.validate_witness(source, target, witness1)
        assert result1.evidence_completeness == 0.5  # 1 / 2.0

        # Test with 3 evidence pointers (capped at 1.0)
        witness2 = MorphismWitness(
            source_type="CausalStructure",
            target_type="CausalStructure",
            morphism_family="causal_exact_abstraction",
            preconditions=frozenset(),
            preserved_invariants=frozenset(),
            forbidden_losses=frozenset(),
            required_boundaries=frozenset(),
            evidence_pointers=("e1", "e2", "e3"),
        )
        result2 = registry.validate_witness(source, target, witness2)
        assert result2.evidence_completeness == 1.0  # min(3/2.0, 1.0)
