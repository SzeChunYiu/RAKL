from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .formalism import Formalism, SymbolRole


class AvailabilityVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class SymbolAvailability:
    symbol: str
    measurement_offset_seconds: float
    publication_lag_seconds: float = 0.0
    clock_alignment_verified: Optional[bool] = None
    causal_estimator: Optional[bool] = None
    estimator_frozen_before_evaluation: Optional[bool] = None
    evidence_ids: Tuple[str, ...] = ()

    @property
    def effective_availability_offset_seconds(self) -> float:
        return self.measurement_offset_seconds + self.publication_lag_seconds

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("availability symbol is required")
        if self.publication_lag_seconds < 0:
            raise ValueError("publication lag cannot be negative")


@dataclass(frozen=True)
class AvailabilityReport:
    verdict: AvailabilityVerdict
    reasons: Tuple[str, ...]
    checked_symbols: Tuple[str, ...] = ()
    failed_symbols: Tuple[str, ...] = ()
    unresolved_symbols: Tuple[str, ...] = ()


def check_predictive_availability(
    formalism: Formalism,
    *,
    predictive_equation_ids: Tuple[str, ...],
    availability: Tuple[SymbolAvailability, ...],
) -> AvailabilityReport:
    """Fail-closed decision-time filtration check for predictive equations.

    `measurement_offset_seconds` is relative to the prediction decision time. Historical
    values are negative. After source publication/processing lag is added, the effective
    offset must remain <= 0. Latent/regime states additionally require a causal estimator
    frozen before the certifying evaluation.
    """

    equations = {equation.equation_id: equation for equation in formalism.equations}
    missing_equations = [eq_id for eq_id in predictive_equation_ids if eq_id not in equations]
    if missing_equations:
        return AvailabilityReport(
            AvailabilityVerdict.FAIL,
            tuple(f"predictive_equation_missing:{eq_id}" for eq_id in missing_equations),
        )
    if not predictive_equation_ids:
        return AvailabilityReport(
            AvailabilityVerdict.CANNOT_CHECK,
            ("no_predictive_equations_registered",),
        )

    symbol_map = formalism.symbol_map()
    feature_roles = {
        SymbolRole.STATE,
        SymbolRole.LATENT_STATE,
        SymbolRole.OBSERVABLE,
        SymbolRole.CONTROL,
        SymbolRole.REGIME,
        SymbolRole.NOISE,
    }
    used: set[str] = set()
    for eq_id in predictive_equation_ids:
        equation = equations[eq_id]
        # Only RHS inputs are decision-time features. LHS is the prediction target.
        used.update(equation.rhs.referenced_symbols())
    used = {
        name
        for name in used
        if name in symbol_map and symbol_map[name].role in feature_roles
    }

    records = {item.symbol: item for item in availability}
    failed: list[str] = []
    unresolved: list[str] = []
    reasons: list[str] = []
    for symbol in sorted(used):
        record = records.get(symbol)
        if record is None:
            unresolved.append(symbol)
            reasons.append(f"availability_record_missing:{symbol}")
            continue
        if record.clock_alignment_verified is not True:
            unresolved.append(symbol)
            reasons.append(f"clock_alignment_not_verified:{symbol}")
            continue
        if record.effective_availability_offset_seconds > 1e-9:
            failed.append(symbol)
            reasons.append(
                f"feature_arrives_after_decision:{symbol}:{record.effective_availability_offset_seconds:.6g}s"
            )
            continue
        role = symbol_map[symbol].role
        if role in {SymbolRole.LATENT_STATE, SymbolRole.REGIME}:
            if record.causal_estimator is not True:
                failed.append(symbol)
                reasons.append(f"latent_or_regime_state_not_causally_estimated:{symbol}")
                continue
            if record.estimator_frozen_before_evaluation is not True:
                unresolved.append(symbol)
                reasons.append(f"latent_or_regime_estimator_not_frozen:{symbol}")
                continue
        if not record.evidence_ids:
            unresolved.append(symbol)
            reasons.append(f"availability_evidence_missing:{symbol}")

    if failed:
        return AvailabilityReport(
            AvailabilityVerdict.FAIL,
            tuple(reasons),
            tuple(sorted(used)),
            tuple(failed),
            tuple(unresolved),
        )
    if unresolved:
        return AvailabilityReport(
            AvailabilityVerdict.CANNOT_CHECK,
            tuple(reasons),
            tuple(sorted(used)),
            (),
            tuple(unresolved),
        )
    return AvailabilityReport(
        AvailabilityVerdict.PASS,
        ("all_predictive_inputs_available_under_registered_decision_filtration",),
        tuple(sorted(used)),
        (),
        (),
    )
