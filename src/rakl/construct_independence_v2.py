"""Construct-independence v2: predeclared stratum homogeneity for aggregate instruments.

Version 1 remains frozen in :mod:`rakl.construct_independence`.  It checks
channel separation, author separation, gold independence and a permutation null.
Merged validation in #731 exposed a defect that all four checks can miss: a
statistic can be valid within each channel and still be non-probative in the
aggregate because pre-existing strata carry opposite effects that cancel.

V2 is deliberately additive.  It never changes a v1 verdict.  For a v1-admissible
instrument it asks one extra, pre-outcome question: if the design registers a
blocking factor and intends to report an aggregate estimand, are all registered
strata present and sufficiently homogeneous for that aggregate to be meaningful?
An explicitly stratified estimand may report heterogeneous strata; the defect is
silently using their aggregate as the decision-bearing statistic.

This remains pursuit-side measurement admission.  It grants no scientific or
method-promotion authority and projects into the existing Recursive Framework
Audit rather than introducing another decision chain.
"""

from __future__ import annotations

from dataclasses import dataclass

from .construct_independence import (
    ConstructIndependenceDecision,
    ConstructVerdict,
    InstrumentDesign,
    assess_construct_independence,
)
from .recursive_framework_audit import (
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    RecursiveAuditDecision,
    decide,
)


@dataclass(frozen=True)
class StratumEffect:
    """One predeclared stratum's signed effect under the instrument statistic."""

    stratum_id: str
    effect: float
    n: int

    def __post_init__(self) -> None:
        if not self.stratum_id:
            raise ValueError("a stratum effect requires an id")
        if self.n <= 0:
            raise ValueError("a stratum effect requires n > 0")


@dataclass(frozen=True)
class StratumHomogeneityWitness:
    """Evidence for one blocking factor registered before outcome access.

    ``aggregate_primary`` distinguishes two legitimate estimands.  When true,
    the aggregate is decision-bearing and material heterogeneity invalidates the
    aggregate instrument.  When false, the strata themselves are the registered
    estimands, so heterogeneity is reportable rather than silently averaged away.
    """

    factor_id: str
    registered_strata: tuple[str, ...]
    effects: tuple[StratumEffect, ...]
    aggregate_effect: float
    material_effect_floor: float = 0.05
    max_spread: float = 0.10
    aggregate_primary: bool = True
    evidence_id: str = ""

    def __post_init__(self) -> None:
        if not self.factor_id:
            raise ValueError("a stratum witness requires a blocking-factor id")
        if not self.registered_strata:
            raise ValueError("a blocking factor requires predeclared strata")
        if len(set(self.registered_strata)) != len(self.registered_strata):
            raise ValueError("registered strata must be unique")
        observed = [row.stratum_id for row in self.effects]
        if len(set(observed)) != len(observed):
            raise ValueError("observed stratum effects must be unique")
        if self.material_effect_floor < 0 or self.max_spread < 0:
            raise ValueError("effect floor and spread threshold must be non-negative")

    @property
    def observed_strata(self) -> tuple[str, ...]:
        return tuple(row.stratum_id for row in self.effects)

    @property
    def missing_strata(self) -> tuple[str, ...]:
        observed = set(self.observed_strata)
        return tuple(s for s in self.registered_strata if s not in observed)

    @property
    def unexpected_strata(self) -> tuple[str, ...]:
        registered = set(self.registered_strata)
        return tuple(s for s in self.observed_strata if s not in registered)

    @property
    def spread(self) -> float:
        if not self.effects:
            return 0.0
        values = [row.effect for row in self.effects]
        return max(values) - min(values)

    @property
    def opposite_material_signs(self) -> bool:
        positive = any(row.effect >= self.material_effect_floor for row in self.effects)
        negative = any(row.effect <= -self.material_effect_floor for row in self.effects)
        return positive and negative

    @property
    def aggregate_masks_material_strata(self) -> bool:
        return (
            abs(self.aggregate_effect) < self.material_effect_floor
            and any(abs(row.effect) >= self.material_effect_floor for row in self.effects)
        )

    @property
    def aggregate_homogeneous(self) -> bool:
        return (
            not self.opposite_material_signs
            and not self.aggregate_masks_material_strata
            and self.spread <= self.max_spread
        )


@dataclass(frozen=True)
class InstrumentDesignV2:
    """A v1 design plus blocking factors frozen before the outcome-bearing epoch."""

    base: InstrumentDesign
    blocking_factors: tuple[str, ...] = ()
    stratum_witnesses: tuple[StratumHomogeneityWitness, ...] = ()

    def __post_init__(self) -> None:
        if len(set(self.blocking_factors)) != len(self.blocking_factors):
            raise ValueError("blocking factors must be unique")
        witness_ids = [w.factor_id for w in self.stratum_witnesses]
        if len(set(witness_ids)) != len(witness_ids):
            raise ValueError("each blocking factor may have at most one witness")
        unexpected = set(witness_ids) - set(self.blocking_factors)
        if unexpected:
            raise ValueError(f"witness supplied for unregistered blocking factor(s): {sorted(unexpected)}")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    def witness_for(self, factor_id: str) -> StratumHomogeneityWitness | None:
        for witness in self.stratum_witnesses:
            if witness.factor_id == factor_id:
                return witness
        return None


@dataclass(frozen=True)
class ConstructIndependenceDecisionV2:
    instrument_id: str
    verdict: ConstructVerdict
    v1_decision: ConstructIndependenceDecision
    blocking_factors: tuple[str, ...] = ()
    unchecked: tuple[str, ...] = ()
    violated: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def admissible(self) -> bool:
        return self.verdict is ConstructVerdict.ADMISSIBLE


def assess_construct_independence_v2(design: InstrumentDesignV2) -> ConstructIndependenceDecisionV2:
    """Apply v1 first, then the frozen stratum-homogeneity successor.

    V1 failure always wins.  V2 cannot rehabilitate a channel/gold/permutation
    defect.  Conversely, a v1-admissible aggregate with a missing stratum check
    is CANNOT_CHECK, not a pass by omission.
    """

    base = assess_construct_independence(design.base)
    if base.verdict is not ConstructVerdict.ADMISSIBLE:
        return ConstructIndependenceDecisionV2(
            instrument_id=design.base.instrument_id,
            verdict=base.verdict,
            v1_decision=base,
            blocking_factors=design.blocking_factors,
            unchecked=base.undeclared,
            violated=base.violated,
            reasons=("v1 construct-independence verdict governs before v2",) + base.reasons,
        )

    if not design.blocking_factors:
        return ConstructIndependenceDecisionV2(
            instrument_id=design.base.instrument_id,
            verdict=ConstructVerdict.ADMISSIBLE,
            v1_decision=base,
            reasons=("no blocking factor was registered before outcome access; v1 verdict preserved",),
        )

    unchecked: list[str] = []
    violated: list[str] = []
    reasons: list[str] = []

    for factor_id in design.blocking_factors:
        witness = design.witness_for(factor_id)
        if witness is None:
            unchecked.append(factor_id)
            reasons.append(f"blocking factor {factor_id!r} has no stratum witness; check unrun")
            continue
        if witness.missing_strata:
            unchecked.append(factor_id)
            reasons.append(
                f"blocking factor {factor_id!r} is missing registered strata {list(witness.missing_strata)}"
            )
            continue
        if witness.unexpected_strata:
            violated.append(factor_id)
            reasons.append(
                f"blocking factor {factor_id!r} produced unregistered strata {list(witness.unexpected_strata)}"
            )
            continue
        if not witness.aggregate_primary:
            reasons.append(
                f"blocking factor {factor_id!r} is explicitly stratified; heterogeneity is reported, not hidden"
            )
            continue
        if not witness.aggregate_homogeneous:
            violated.append(factor_id)
            detail: list[str] = []
            if witness.opposite_material_signs:
                detail.append("opposite material effect signs")
            if witness.aggregate_masks_material_strata:
                detail.append("aggregate masks material stratum effects")
            if witness.spread > witness.max_spread:
                detail.append(f"spread {witness.spread:.6g} > {witness.max_spread:.6g}")
            reasons.append(
                f"blocking factor {factor_id!r} invalidates the aggregate: {', '.join(detail) or 'heterogeneous strata'}"
            )

    if violated:
        return ConstructIndependenceDecisionV2(
            instrument_id=design.base.instrument_id,
            verdict=ConstructVerdict.INADMISSIBLE,
            v1_decision=base,
            blocking_factors=design.blocking_factors,
            unchecked=tuple(unchecked),
            violated=tuple(violated),
            reasons=tuple(reasons),
        )
    if unchecked:
        return ConstructIndependenceDecisionV2(
            instrument_id=design.base.instrument_id,
            verdict=ConstructVerdict.CANNOT_CHECK,
            v1_decision=base,
            blocking_factors=design.blocking_factors,
            unchecked=tuple(unchecked),
            reasons=tuple(reasons),
        )
    return ConstructIndependenceDecisionV2(
        instrument_id=design.base.instrument_id,
        verdict=ConstructVerdict.ADMISSIBLE,
        v1_decision=base,
        blocking_factors=design.blocking_factors,
        reasons=tuple(reasons) + ("all registered blocking factors are valid for their frozen estimand",),
    )


def to_audit_residual_v2(decision: ConstructIndependenceDecisionV2) -> AuditResidual:
    if decision.verdict is ConstructVerdict.INADMISSIBLE:
        return AuditResidual(plausible_causes=(AuditCoordinate.MEASUREMENT,))
    if decision.verdict is ConstructVerdict.CANNOT_CHECK:
        return AuditResidual(resource_bound=True)
    return AuditResidual()


def decide_from_construct_verdict_v2(
    decision: ConstructIndependenceDecisionV2,
    *,
    closure_coordinates_pass: bool = False,
    material_open_residual: bool = True,
) -> RecursiveAuditDecision:
    return decide(
        AuditNode(
            closure_coordinates_pass=closure_coordinates_pass,
            material_open_residual=material_open_residual,
        ),
        to_audit_residual_v2(decision),
    )


__all__ = [
    "ConstructIndependenceDecisionV2",
    "InstrumentDesignV2",
    "StratumEffect",
    "StratumHomogeneityWitness",
    "assess_construct_independence_v2",
    "decide_from_construct_verdict_v2",
    "to_audit_residual_v2",
]
