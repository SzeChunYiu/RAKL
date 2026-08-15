"""Construct-independence admission gate — tests.

The gate's whole purpose is to fail closed, so most of these check that it
refuses rather than that it passes. Two cases are replays of real frontier
terminals: a statistic that survived label shuffling (ARN v2/v4) and a design
that declares nothing (the modal registered design, per the census).
"""

from __future__ import annotations

import pytest

from rakl.construct_independence import (
    ConstructObligation,
    ConstructVerdict,
    InstrumentDesign,
    ObligationDeclaration,
    PermutationNullWitness,
    assess_construct_independence,
    decide_from_construct_verdict,
    to_audit_residual,
)
from rakl.recursive_framework_audit import AuditAction, AuditCoordinate


def good_witness(**overrides: object) -> PermutationNullWitness:
    fields: dict[str, object] = dict(
        statistic_id="paired-advantage",
        observed=0.72,
        shuffled_mean=0.50,
        chance_level=0.50,
        tolerance=0.02,
        permutations=1000,
    )
    fields.update(overrides)
    return PermutationNullWitness(**fields)  # type: ignore[arg-type]


def full_design(**overrides: object) -> InstrumentDesign:
    declarations = (
        ObligationDeclaration(ConstructObligation.CHANNEL_SEPARATION, True, "gold column never read during extraction"),
        ObligationDeclaration(ConstructObligation.AUTHOR_SEPARATION, True, "third-party labels; features authored separately"),
        ObligationDeclaration(ConstructObligation.GOLD_INDEPENDENCE, True, "gold is a function of substantive state alone"),
        ObligationDeclaration(
            ConstructObligation.PERMUTATION_NULL, True, "1000-permutation shuffle", witness=good_witness()
        ),
    )
    fields: dict[str, object] = dict(instrument_id="probe-v1", declarations=declarations)
    fields.update(overrides)
    return InstrumentDesign(**fields)  # type: ignore[arg-type]


def without(obligation: ConstructObligation) -> InstrumentDesign:
    kept = tuple(d for d in full_design().declarations if d.obligation is not obligation)
    return InstrumentDesign(instrument_id="probe-v1", declarations=kept)


# --- admission --------------------------------------------------------------


def test_a_fully_declared_and_witnessed_design_is_admissible() -> None:
    decision = assess_construct_independence(full_design())
    assert decision.verdict is ConstructVerdict.ADMISSIBLE
    assert decision.admissible is True
    assert decision.undeclared == ()
    assert decision.violated == ()
    assert decision.grants_scientific_authority is False
    assert decision.grants_method_promotion_authority is False


def test_every_missing_obligation_yields_cannot_check_not_a_pass() -> None:
    for obligation in ConstructObligation:
        decision = assess_construct_independence(without(obligation))
        assert decision.verdict is ConstructVerdict.CANNOT_CHECK, obligation
        assert decision.undeclared == (obligation.value,)
        assert decision.admissible is False


def test_the_modal_registered_design_declares_nothing_and_cannot_be_admitted() -> None:
    decision = assess_construct_independence(InstrumentDesign(instrument_id="undeclared-v1"))
    assert decision.verdict is ConstructVerdict.CANNOT_CHECK
    assert set(decision.undeclared) == {o.value for o in ConstructObligation}


# --- refusal ----------------------------------------------------------------


def test_a_declared_violation_is_inadmissible() -> None:
    kept = tuple(d for d in full_design().declarations if d.obligation is not ConstructObligation.AUTHOR_SEPARATION)
    design = InstrumentDesign(
        instrument_id="single-author-v1",
        declarations=kept
        + (
            ObligationDeclaration(
                ConstructObligation.AUTHOR_SEPARATION, False, "renderer and extractor share an author"
            ),
        ),
    )
    decision = assess_construct_independence(design)
    assert decision.verdict is ConstructVerdict.INADMISSIBLE
    assert decision.violated == (ConstructObligation.AUTHOR_SEPARATION.value,)


def test_a_statistic_that_survives_shuffling_is_inadmissible() -> None:
    """Replay of the ARN v2/v4 terminal: label-independent marginals."""

    kept = tuple(d for d in full_design().declarations if d.obligation is not ConstructObligation.PERMUTATION_NULL)
    design = InstrumentDesign(
        instrument_id="arn-v2-replay",
        declarations=kept
        + (
            ObligationDeclaration(
                ConstructObligation.PERMUTATION_NULL,
                True,
                "shuffle run",
                witness=good_witness(observed=0.71, shuffled_mean=0.68),
            ),
        ),
    )
    decision = assess_construct_independence(design)
    assert decision.verdict is ConstructVerdict.INADMISSIBLE
    assert decision.violated == (ConstructObligation.PERMUTATION_NULL.value,)
    assert "survives label shuffling" in " ".join(decision.reasons)


def test_a_statistic_indistinguishable_from_its_own_null_is_inadmissible() -> None:
    kept = tuple(d for d in full_design().declarations if d.obligation is not ConstructObligation.PERMUTATION_NULL)
    design = InstrumentDesign(
        instrument_id="flat-v1",
        declarations=kept
        + (
            ObligationDeclaration(
                ConstructObligation.PERMUTATION_NULL,
                True,
                "shuffle run",
                witness=good_witness(observed=0.505, shuffled_mean=0.50),
            ),
        ),
    )
    decision = assess_construct_independence(design)
    assert decision.verdict is ConstructVerdict.INADMISSIBLE
    assert "indistinguishable from its own null" in " ".join(decision.reasons)


def test_a_violation_outranks_a_missing_declaration() -> None:
    design = InstrumentDesign(
        instrument_id="mixed-v1",
        declarations=(
            ObligationDeclaration(ConstructObligation.CHANNEL_SEPARATION, False, "answer shares the input channel"),
        ),
    )
    decision = assess_construct_independence(design)
    assert decision.verdict is ConstructVerdict.INADMISSIBLE
    assert decision.violated == (ConstructObligation.CHANNEL_SEPARATION.value,)
    # The unrun checks are still reported; the verdict just is not softened to CANNOT_CHECK.
    assert len(decision.undeclared) == 3


def test_permutation_satisfaction_without_a_witness_is_treated_as_unrun() -> None:
    kept = tuple(d for d in full_design().declarations if d.obligation is not ConstructObligation.PERMUTATION_NULL)
    design = InstrumentDesign(
        instrument_id="claimed-v1",
        declarations=kept
        + (ObligationDeclaration(ConstructObligation.PERMUTATION_NULL, True, "we ran one, trust us"),),
    )
    decision = assess_construct_independence(design)
    assert decision.verdict is ConstructVerdict.CANNOT_CHECK
    assert decision.undeclared == (ConstructObligation.PERMUTATION_NULL.value,)


# --- construction guards ----------------------------------------------------


def test_a_satisfaction_claim_requires_evidence() -> None:
    with pytest.raises(ValueError, match="without evidence"):
        ObligationDeclaration(ConstructObligation.GOLD_INDEPENDENCE, True, "")


def test_a_witness_must_record_its_permutations() -> None:
    with pytest.raises(ValueError, match="how many permutations"):
        good_witness(permutations=0)


def test_obligations_cannot_be_declared_twice() -> None:
    duplicated = full_design().declarations + (
        ObligationDeclaration(ConstructObligation.GOLD_INDEPENDENCE, True, "again"),
    )
    with pytest.raises(ValueError, match="at most once"):
        InstrumentDesign(instrument_id="dup-v1", declarations=duplicated)


# --- integration ------------------------------------------------------------


def test_verdicts_route_through_the_frozen_chain() -> None:
    inadmissible = assess_construct_independence(
        InstrumentDesign(
            instrument_id="bad-v1",
            declarations=(
                ObligationDeclaration(ConstructObligation.GOLD_INDEPENDENCE, False, "gold derived from the candidate"),
            ),
        )
    )
    residual = to_audit_residual(inadmissible)
    assert residual.plausible_causes == (AuditCoordinate.MEASUREMENT,)
    assert decide_from_construct_verdict(inadmissible).action is AuditAction.REVISE_MEASUREMENT

    unchecked = assess_construct_independence(InstrumentDesign(instrument_id="unknown-v1"))
    assert to_audit_residual(unchecked).resource_bound is True
    assert decide_from_construct_verdict(unchecked).action is AuditAction.CANNOT_CHECK

    admissible = assess_construct_independence(full_design())
    assert to_audit_residual(admissible).plausible_causes == ()
    assert decide_from_construct_verdict(admissible).action is AuditAction.SOLVE_CURRENT
