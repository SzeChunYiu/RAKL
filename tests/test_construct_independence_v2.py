from __future__ import annotations

from rakl.construct_independence import (
    ConstructObligation,
    ConstructVerdict,
    InstrumentDesign,
    ObligationDeclaration,
    PermutationNullWitness,
)
from rakl.construct_independence_v2 import (
    InstrumentDesignV2,
    StratumEffect,
    StratumHomogeneityWitness,
    assess_construct_independence_v2,
    decide_from_construct_verdict_v2,
)
from rakl.recursive_framework_audit import AuditAction


def _clean_v1(instrument_id: str = "clean") -> InstrumentDesign:
    return InstrumentDesign(
        instrument_id=instrument_id,
        declarations=(
            ObligationDeclaration(ConstructObligation.CHANNEL_SEPARATION, True, "separate input/output channels"),
            ObligationDeclaration(ConstructObligation.AUTHOR_SEPARATION, True, "generator != evaluator"),
            ObligationDeclaration(ConstructObligation.GOLD_INDEPENDENCE, True, "gold frozen independently"),
            ObligationDeclaration(
                ConstructObligation.PERMUTATION_NULL,
                True,
                "100 permutations",
                PermutationNullWitness(
                    statistic_id="accuracy",
                    observed=0.70,
                    shuffled_mean=0.50,
                    chance_level=0.50,
                    tolerance=0.02,
                    permutations=100,
                ),
            ),
        ),
    )


def test_v2_preserves_v1_when_no_blocking_factor_registered() -> None:
    decision = assess_construct_independence_v2(InstrumentDesignV2(base=_clean_v1()))
    assert decision.verdict is ConstructVerdict.ADMISSIBLE


def test_opposite_signed_registered_strata_invalidate_aggregate() -> None:
    witness = StratumHomogeneityWitness(
        factor_id="distractor_similarity",
        registered_strata=("high", "low"),
        effects=(
            StratumEffect("high", -0.104, 134),
            StratumEffect("low", 0.112, 192),
        ),
        aggregate_effect=0.004,
        material_effect_floor=0.05,
        max_spread=0.10,
        aggregate_primary=True,
        evidence_id="fixture-cancellation",
    )
    decision = assess_construct_independence_v2(
        InstrumentDesignV2(
            base=_clean_v1("cancel"),
            blocking_factors=("distractor_similarity",),
            stratum_witnesses=(witness,),
        )
    )
    assert decision.verdict is ConstructVerdict.INADMISSIBLE
    assert decision.violated == ("distractor_similarity",)
    assert decide_from_construct_verdict_v2(decision).action is AuditAction.REVISE_MEASUREMENT


def test_missing_registered_stratum_fails_closed() -> None:
    witness = StratumHomogeneityWitness(
        factor_id="regime",
        registered_strata=("a", "b"),
        effects=(StratumEffect("a", 0.12, 20),),
        aggregate_effect=0.12,
    )
    decision = assess_construct_independence_v2(
        InstrumentDesignV2(
            base=_clean_v1("missing"),
            blocking_factors=("regime",),
            stratum_witnesses=(witness,),
        )
    )
    assert decision.verdict is ConstructVerdict.CANNOT_CHECK
    assert decision.unchecked == ("regime",)
    assert decide_from_construct_verdict_v2(decision).action is AuditAction.CANNOT_CHECK


def test_explicit_stratified_estimand_may_report_heterogeneity() -> None:
    witness = StratumHomogeneityWitness(
        factor_id="regime",
        registered_strata=("a", "b"),
        effects=(StratumEffect("a", -0.2, 20), StratumEffect("b", 0.2, 20)),
        aggregate_effect=0.0,
        aggregate_primary=False,
    )
    decision = assess_construct_independence_v2(
        InstrumentDesignV2(
            base=_clean_v1("stratified"),
            blocking_factors=("regime",),
            stratum_witnesses=(witness,),
        )
    )
    assert decision.verdict is ConstructVerdict.ADMISSIBLE


def test_homogeneous_registered_strata_remain_admissible() -> None:
    witness = StratumHomogeneityWitness(
        factor_id="regime",
        registered_strata=("a", "b"),
        effects=(StratumEffect("a", 0.12, 20), StratumEffect("b", 0.14, 20)),
        aggregate_effect=0.13,
        max_spread=0.10,
    )
    decision = assess_construct_independence_v2(
        InstrumentDesignV2(
            base=_clean_v1("homogeneous"),
            blocking_factors=("regime",),
            stratum_witnesses=(witness,),
        )
    )
    assert decision.verdict is ConstructVerdict.ADMISSIBLE


def test_v1_defect_out_ranks_v2_homogeneity() -> None:
    base = InstrumentDesign(
        instrument_id="v1-defect",
        declarations=(
            ObligationDeclaration(ConstructObligation.CHANNEL_SEPARATION, False, "shared answer channel"),
        ),
    )
    decision = assess_construct_independence_v2(InstrumentDesignV2(base=base))
    assert decision.verdict is ConstructVerdict.INADMISSIBLE
    assert "CHANNEL_SEPARATION" in decision.violated
