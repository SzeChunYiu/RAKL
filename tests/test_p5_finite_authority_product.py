"""Finite known-world conformance test for Paper V's authority product.

This is not a theorem-prover benchmark and grants no scientific authority.  It
exhaustively checks the smallest Boolean world exposing why mathematical
research authority cannot be replaced by a count/majority of apparently good
coordinates.

Coordinates mirror the Paper-V distinction:
SPECIFICATION, TRUTH, NOVELTY, VALUE, VERIFIER_TRUST.

For a scoped novelty-bearing theorem candidate, specification, theorem truth,
novelty and verifier trust are load-bearing.  VALUE is reported separately: a
true novel theorem may be low-value without becoming false.
"""

from __future__ import annotations

from itertools import product

COORDS = ("specification", "truth", "novelty", "value", "verifier_trust")


def _state(bits: tuple[bool, ...]) -> dict[str, bool]:
    return dict(zip(COORDS, bits, strict=True))


def _product_candidate_gate(state: dict[str, bool]) -> bool:
    return all(
        state[key]
        for key in ("specification", "truth", "novelty", "verifier_trust")
    )


def _intended_claim_is_assured(state: dict[str, bool]) -> bool:
    # Novelty/value do not repair a wrong formalization, false theorem, or
    # untrusted verification chain.
    return all(
        state[key]
        for key in ("specification", "truth", "verifier_trust")
    )


def _four_of_five_scalar_gate(state: dict[str, bool]) -> bool:
    return sum(state.values()) >= 4


def test_product_gate_never_promotes_missing_spec_truth_or_trust() -> None:
    promoted = []
    false_promotions = []
    for bits in product((False, True), repeat=len(COORDS)):
        state = _state(bits)
        if _product_candidate_gate(state):
            promoted.append(state)
            if not _intended_claim_is_assured(state):
                false_promotions.append(state)

    assert len(promoted) == 2  # value false/true; value is a separate coordinate
    assert false_promotions == []


def test_four_of_five_scalarization_has_three_load_bearing_false_promotions() -> None:
    promoted = []
    false_promotions = []
    for bits in product((False, True), repeat=len(COORDS)):
        state = _state(bits)
        if _four_of_five_scalar_gate(state):
            promoted.append(state)
            if not _intended_claim_is_assured(state):
                false_promotions.append(state)

    assert len(promoted) == 6
    assert len(false_promotions) == 3
    assert {key for state in false_promotions for key in COORDS if not state[key]} == {
        "specification",
        "truth",
        "verifier_trust",
    }


def test_truth_can_stay_fixed_while_novelty_decreases() -> None:
    before = {
        "specification": True,
        "truth": True,
        "novelty": True,
        "value": True,
        "verifier_trust": True,
    }
    after_literature_expansion = dict(before, novelty=False)

    assert before["truth"] is after_literature_expansion["truth"] is True
    assert before["novelty"] is True
    assert after_literature_expansion["novelty"] is False
    assert _product_candidate_gate(before) is True
    assert _product_candidate_gate(after_literature_expansion) is False
