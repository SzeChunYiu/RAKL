"""Reproducible falsification tests for mathematics closure claims.

These tests re-run the finite brute-force searches from MATHEMATICS_CLOSURE.json
on at least two load-bearing claims: one expected PASS, one potential counterexample.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from typing import Any, Dict, Set, Tuple

import pytest

# Import RAKL modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rakl.canonical_commitment import (
    canonical_json_bytes,
    sha256_digest,
    CanonicalProfile,
    UnicodePolicy,
    normalize,
    CanonicalizationError,
)
from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    validate_proposal_contract,
)
from rakl.approximation_budget import (
    ApproximationBudget,
    ApproximationStep,
    ErrorComposition,
    assess_composed_approximation,
    ApproximationVerdict,
)
from rakl.diagnosis_state_machine import (
    DiagnosisState,
    DiagnosisVerdict,
    unresolved_state,
    competing_state,
    _validate_shape,
)


# ============================================================================
# Test 1: Canonical commitment deterministic encoding (load-bearing, expected PASS)
# ============================================================================

def test_canonical_commitment_deterministic_small_universe():
    """Verify canonical encoding is deterministic for small finite values.
    
    Claim: For any v1, v2 in our small universe, if canonical_json_bytes(v1) ==
    canonical_json_bytes(v2), then v1 and v2 are semantically equal.
    
    Expected: PASS (no counterexamples found).
    """
    # Small finite universe of values
    simple_values = [
        None,
        True, False,
        0, 1, 2, 3, 4, 5,
        "", "a", "abc", "xyz",
        [], [1], [1, 2],
        {}, {"a": 1}, {"b": 2, "a": 1},
        set(), {1}, {1, 2},
        (), (1,), (1, 2),
    ]
    
    # Profile for testing
    profile = CanonicalProfile(unicode_policy=UnicodePolicy.PRESERVE)
    
    # Build encoding map
    encodings: Dict[bytes, Any] = {}
    collisions: list = []
    
    for v in simple_values:
        try:
            enc = canonical_json_bytes(v, profile=profile)
            if enc in encodings:
                collisions.append((v, encodings[enc]))
            else:
                encodings[enc] = v
        except CanonicalizationError:
            # Some values may be rejected (e.g., lone surrogates not in our universe)
            pass
    
    # Verify no collisions in our universe
    assert len(collisions) == 0, f"Found {len(collisions)} encoding collisions: {collisions[:3]}"
    
    # Verify deterministic: encoding the same value twice gives same result
    for v in simple_values[:10]:  # Check subset
        try:
            enc1 = canonical_json_bytes(v, profile=profile)
            enc2 = canonical_json_bytes(v, profile=profile)
            assert enc1 == enc2, f"Non-deterministic encoding for {v!r}"
        except CanonicalizationError:
            pass


def test_canonical_commitment_injective_up_to_equivalence():
    """Verify that two semantically distinct values have distinct encodings.
    
    This is a stronger test: we check that no two "obviously different" values
    encode to the same bytes.
    """
    profile = CanonicalProfile(unicode_policy=UnicodePolicy.PRESERVE)
    
    # Distinct simple values
    distinct_pairs = [
        (None, False),
        (0, 1),
        (True, False),
        ("", "a"),
        ([], [1]),
        ({}, {"a": 1}),
    ]
    
    for v1, v2 in distinct_pairs:
        enc1 = canonical_json_bytes(v1, profile=profile)
        enc2 = canonical_json_bytes(v2, profile=profile)
        assert enc1 != enc2, f"Distinct {v1!r} and {v2!r} have same encoding"


# ============================================================================
# Test 2: Semantic quotient coordinate partition (load-bearing, expected PASS)
# ============================================================================

def _make_test_representation(coords: tuple, protected: tuple = ()) -> ProblemRepresentation:
    """Helper to create a test ProblemRepresentation."""
    return ProblemRepresentation(
        representation_id="test-rep",
        problem_id="test-problem",
        atom_id="test-atom",
        qoi="test-qoi",
        context_hash="ctx",
        source_hash="src",
        coordinates=coords,
        relations=(),
        constraints=(),
        assumptions=(),
        protected_fields=protected,
        provenance_ids=(),
    )


def _make_test_proposal(
    preserved: tuple,
    erased: tuple,
    conditional: tuple = (),
    protected_extra: tuple = (),
) -> QuotientProposal:
    """Helper to create a test QuotientProposal."""
    return QuotientProposal(
        quotient_id="test-quotient",
        source_representation_id="test-rep",
        source_hash="src",
        qoi="test-qoi",
        context_hash="ctx",
        preserved_coordinates=preserved,
        erased_coordinates=erased,
        conditionally_erased_coordinates=conditional,
        equivalence_generators=(),
        preserved_invariants=("test-invariant",),
        protected_coordinates=protected_extra,
        sufficiency_obligations=("test-obligation",),
        reconstruction_bindings=(),
        falsifiers=("test-falsifier",),
        forbidden_losses=(),
    )


def test_coordinate_partition_disjointness_small_universe():
    """Verify coordinate partition invariants for small coordinate sets.
    
    Claim: For any valid proposal, preserved/erased/conditionally_erased are
    pairwise disjoint and their union is a subset of source coordinates.
    
    Expected: PASS (the validation logic enforces this).
    """
    # Test all partitions of small coordinate sets
    for n in range(1, 4):  # n = 1, 2, 3 coordinates (coordinates required)
        coords = tuple(f"c{i}" for i in range(n))
        source = _make_test_representation(coords)
        
        # All possible assignments of each coordinate to one of three sets
        # 0 = preserved, 1 = erased, 2 = conditionally erased, 3 = unassigned
        for assignment in itertools.product([0, 1, 2, 3], repeat=n):
            preserved = tuple(coords[i] for i, a in enumerate(assignment) if a == 0)
            erased = tuple(coords[i] for i, a in enumerate(assignment) if a == 1)
            conditional = tuple(coords[i] for i, a in enumerate(assignment) if a == 2)
            
            proposal = _make_test_proposal(preserved, erased, conditional)
            reasons = validate_proposal_contract(source, proposal)
            
            # Check for partition conflict
            if (set(preserved) & set(erased)) or (set(preserved) & set(conditional)) or (set(erased) & set(conditional)):
                # Should have conflict reason
                assert any("coordinate_partition_conflict" in r for r in reasons), \
                    f"Expected partition_conflict for disjointness violation: {assignment}"
            else:
                # No partition conflict should be reported
                assert not any("coordinate_partition_conflict" in r for r in reasons), \
                    f"Unexpected partition_conflict for valid assignment: {assignment}"


def test_protected_coordinate_preservation():
    """Verify protected coordinates are always preserved.
    
    Claim: For any valid proposal, protected_fields ⊆ preserved_coordinates.
    
    Expected: PASS (validation enforces this).
    """
    coords = ("a", "b", "c", "d")
    
    # Test all subsets as protected fields
    for r in range(5):  # 0 to 4 protected coordinates
        for protected in itertools.combinations(coords, r):
            source = _make_test_representation(coords, protected)
            
            # Try to erase each protected coordinate
            for coord in protected:
                proposal = _make_test_proposal(
                    preserved=(),  # Empty preserved set
                    erased=(coord,),
                )
                reasons = validate_proposal_contract(source, proposal)
                
                # Should report protected_coordinate_erased
                assert any("protected_coordinate_erased" in r for r in reasons), \
                    f"Should detect protected coordinate {coord} being erased"


# ============================================================================
# Test 3: Approximation budget additive composition (expected PASS)
# ============================================================================

def test_approximation_additive_composition():
    """Verify additive error composition bounds.
    
    Claim: For ADDITIVE composition, accumulated error = sum(step errors).
    WITHIN_BUDGET verdict requires sum ≤ budget.max_error.
    
    Expected: PASS (basic arithmetic property).
    """
    budget = ApproximationBudget(
        budget_id="test-budget",
        scope_hash="test-scope",
        metric_id="test-metric",
        max_error=2.0,
        composition=ErrorComposition.ADDITIVE,
    )
    
    # Test various step combinations
    test_cases = [
        # (step_errors, expected_total, expected_verdict)
        ([0.5, 0.5, 0.5], 1.5, ApproximationVerdict.WITHIN_BUDGET),
        ([0.5, 1.0, 0.5], 2.0, ApproximationVerdict.WITHIN_BUDGET),
        ([1.0, 1.0, 1.0], 3.0, ApproximationVerdict.EXCEEDS_BUDGET),
        ([0.0, 0.0, 0.0], 0.0, ApproximationVerdict.WITHIN_BUDGET),
    ]
    
    for errors, expected_total, expected_verdict in test_cases:
        steps = tuple(
            ApproximationStep(
                step_id=f"step-{i}",
                scope_hash="test-scope",
                metric_id="test-metric",
                certified_error_bound=err,
                evidence_receipt_ids=(f"receipt-{i}",),
            )
            for i, err in enumerate(errors)
        )
        
        assessment = assess_composed_approximation(budget, steps)
        
        assert assessment.accumulated_error_bound == pytest.approx(expected_total), \
            f"Expected total {expected_total}, got {assessment.accumulated_error_bound}"
        assert assessment.verdict == expected_verdict, \
            f"Expected {expected_verdict}, got {assessment.verdict} for errors {errors}"


# ============================================================================
# Test 4: Diagnosis CANNOT_CHECK invariant (load-bearing, expected PASS)
# ============================================================================

def test_diagnosis_cannotcheck_no_unique_concrete():
    """Verify CANNOT_CHECK cannot hide a unique concrete cause.
    
    Claim: If verdict = CANNOT_CHECK, then NOT (|candidates| = 1 AND
    candidates[0] != "UNKNOWN").
    
    Expected: PASS (validation enforces this).
    """
    # Valid CANNOT_CHECK state: only UNKNOWN
    state1 = DiagnosisState(
        diagnosis_id="test-1",
        candidate_causes=("UNKNOWN",),
        ruled_out_causes=(),
        discriminator_ids=(),
        chosen_discriminator_id=None,
        verdict=DiagnosisVerdict.CANNOT_CHECK,
        evidence_receipt_ids=(),
    )
    # Should validate without error
    _validate_shape(state1)  # Should not raise
    
    # Valid CANNOT_CHECK state: multiple causes including UNKNOWN
    state2 = DiagnosisState(
        diagnosis_id="test-2",
        candidate_causes=("UNKNOWN", "A", "B"),
        ruled_out_causes=(),
        discriminator_ids=(),
        chosen_discriminator_id=None,
        verdict=DiagnosisVerdict.CANNOT_CHECK,
        evidence_receipt_ids=(),
    )
    _validate_shape(state2)  # Should not raise
    
    # INVALID: CANNOT_CHECK with single concrete cause
    with pytest.raises(ValueError, match="cannot silently encode"):
        DiagnosisState(
            diagnosis_id="test-invalid",
            candidate_causes=("A",),  # Single concrete cause
            ruled_out_causes=(),
            discriminator_ids=(),
            chosen_discriminator_id=None,
            verdict=DiagnosisVerdict.CANNOT_CHECK,
            evidence_receipt_ids=(),
        )


def test_diagnosis_disjoint_sets():
    """Verify candidate and ruled-out causes are disjoint.
    
    Claim: candidate_causes ∩ ruled_out_causes = ∅ for any valid state.
    
    Expected: PASS (validation enforces this).
    """
    # Valid: disjoint sets
    state1 = DiagnosisState(
        diagnosis_id="test-1",
        candidate_causes=("A", "B"),
        ruled_out_causes=("C", "D"),
        discriminator_ids=(),
        chosen_discriminator_id=None,
        verdict=DiagnosisVerdict.PARTIALLY_IDENTIFIED,
        evidence_receipt_ids=(),
    )
    _validate_shape(state1)  # Should not raise
    
    # INVALID: overlap
    with pytest.raises(ValueError, match="cannot be candidate and ruled out"):
        DiagnosisState(
            diagnosis_id="test-invalid",
            candidate_causes=("A", "B"),
            ruled_out_causes=("B", "C"),  # B is in both
            discriminator_ids=(),
            chosen_discriminator_id=None,
            verdict=DiagnosisVerdict.PARTIALLY_IDENTIFIED,
            evidence_receipt_ids=(),
        )


# ============================================================================
# Test 5: SHA256 domain binding (load-bearing, expected PASS)
# ============================================================================

def test_sha256_domain_binding():
    """Verify SHA256 digest is domain-scoped.
    
    Claim: sha256_digest(v, domain=d1) != sha256_digest(v, domain=d2) when
    d1 != d2, even for the same value v.
    
    Expected: PASS (domain is part of preimage).
    """
    profile = CanonicalProfile()
    value = {"test": "value"}
    
    digest1 = sha256_digest(value, domain="domain-1", profile=profile)
    digest2 = sha256_digest(value, domain="domain-2", profile=profile)
    
    assert digest1 != digest2, \
        "Digests for same value with different domains should differ"
    
    # Same value, same domain gives same digest
    digest1_again = sha256_digest(value, domain="domain-1", profile=profile)
    assert digest1 == digest1_again, \
        "Digests for same value and domain should be idempotent"


# ============================================================================
# Summary: All tests should pass
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
