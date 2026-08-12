"""Pure KPI functions for the Orion metric layer (``orion.metrics.kpis``).

These functions turn the framework's already-typed objects
(``StructuralMasteryEstimate``, saturation receipts, authority-poset axis
status, applicability-gate comparator records) into named, [0,1]-bounded
Key Performance Indicators.

Design contract for this whole module:

* Every function is **pure**: it performs no I/O, mutates no argument, and is
  fully determined by its inputs.
* Every KPI is a **measurement, never a promotion/authority signal**. Computing
  a good number here never licenses a claim, promotes a candidate, or grants
  scientific / structural-transfer authority. Authority is decided elsewhere by
  the governance gates; these values are read-only diagnostics.
* All returned magnitudes that are defined on the unit interval are validated to
  lie in ``[0, 1]``.

The KPIs implemented here are the "computable-now" rows of
``docs/ORION_KPI_AND_METRICS.md``: structural mastery vector, saturation level /
epoch, retention floor, authority coverage (non-compensatory), and gate
false-accept rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping, Sequence

from ..training_projection import MasteryCoordinate, StructuralMasteryEstimate

__all__ = [
    "LICENSED",
    "AuthorityCoverage",
    "GateRecord",
    "authority_coverage",
    "gate_false_accept",
    "mastery_vector",
    "retention_ok",
    "saturation_epoch",
    "saturation_level",
]

# Canonical "covered" status token for an authority-poset axis.
LICENSED = "LICENSED"


def _require_unit(value: float, name: str) -> float:
    """Return ``value`` if it is a finite number in ``[0, 1]``, else raise."""

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number, got {type(value).__name__}")
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0,1], got {value!r}")
    return value


def mastery_vector(
    estimate: StructuralMasteryEstimate,
) -> dict[MasteryCoordinate, float | None]:
    """Return the 6-coordinate structural mastery vector ``M_t(s)``.

    This is a measurement, never a promotion/authority signal.

    The vector is read straight off a checkpoint-/probe-bound
    :class:`StructuralMasteryEstimate`. It is deliberately **not** scalarized:
    each coordinate is an independent probe result in ``[0, 1]``, and an
    unmeasured coordinate stays ``None`` -- it is never coerced to ``0.0``.
    """

    vector: dict[MasteryCoordinate, float | None] = {}
    for coordinate, value in estimate.coordinate_values:
        if value is not None:
            _require_unit(value, f"mastery[{coordinate.value}]")
        vector[coordinate] = None if value is None else float(value)
    return vector


def saturation_level(marginal_gains: Sequence[float]) -> float:
    """Return the current saturation level ``sat(s,c)`` from a marginal-gain run.

    This is a measurement, never a promotion/authority signal.

    ``sat`` is defined in the catalog as the marginal accuracy gain the *next*
    equal-cost same-structure example buys on a coordinate. Given the observed
    marginal-gain sequence (oldest first), the current level is the most recent
    gain. It lives in ``[0, 1]`` with the direction "smaller = more saturated";
    an observed gain below zero (accuracy regressed) is clamped to ``0.0`` since
    a structure cannot be *less* than fully saturated.
    """

    if not marginal_gains:
        raise ValueError("saturation_level needs at least one observed marginal gain")
    latest = float(marginal_gains[-1])
    if not isfinite(latest):
        raise ValueError("marginal gains must be finite")
    return _require_unit(min(1.0, max(0.0, latest)), "saturation_level")


def saturation_epoch(
    marginal_gains: Sequence[float], epsilon: float
) -> int | None:
    """Return ``E*(s,c)``: the first exposure index where ``sat < epsilon``.

    This is a measurement, never a promotion/authority signal.

    ``marginal_gains`` is the per-exposure marginal-gain sequence (oldest
    first). The returned integer is the **0-based position** in that sequence of
    the first gain strictly below ``epsilon`` -- the point past which further
    same-structure exposure buys less than the stop threshold. ``None`` means
    the structure never saturated within the observed run (still learnable).
    The caller maps the returned index back to its ``exposure_count`` via the
    trajectory.
    """

    _require_unit(epsilon, "epsilon")
    for index, gain in enumerate(marginal_gains):
        gain = float(gain)
        if not isfinite(gain):
            raise ValueError("marginal gains must be finite")
        if gain < epsilon:
            return index
    return None


def retention_ok(value: float | None, floor: float) -> bool:
    """Return whether a retained coordinate value clears the retention floor.

    This is a measurement, never a promotion/authority signal.

    Retention is a **hard constraint**, not an objective term: any schedule
    whose earlier-structure coordinate has decayed below ``floor`` is
    *infeasible*. Fails closed -- an unmeasured value (``None``) cannot clear the
    floor and returns ``False``.
    """

    _require_unit(floor, "retention floor")
    if value is None:
        return False
    return _require_unit(value, "retention value") >= floor


@dataclass(frozen=True)
class AuthorityCoverage:
    """Non-compensatory authority-coverage KPI for one claim.

    ``coverage`` is the fraction of authority-poset axes that are ``LICENSED``.
    ``blocking_axes`` lists (sorted) every axis that is *not* licensed. Coverage
    is reported for readability only: because the gate is **non-compensatory**, a
    high fraction never compensates for a single blocking load-bearing axis --
    ``blocking_axes`` being non-empty is what blocks promotion, not the scalar.

    This is a measurement, never a promotion/authority signal.
    """

    coverage: float
    blocking_axes: tuple[str, ...]

    @property
    def fully_licensed(self) -> bool:
        return not self.blocking_axes


def authority_coverage(axis_status: Mapping[str, str]) -> AuthorityCoverage:
    """Return the non-compensatory authority coverage over a claim's poset axes.

    This is a measurement, never a promotion/authority signal.

    ``axis_status`` maps each authority axis (e.g. ``G, R, M, I, D``) to its
    status token; an axis counts as covered only when its status equals
    :data:`LICENSED`. Returns an :class:`AuthorityCoverage` carrying both the
    covered fraction and the sorted list of blocking (non-licensed) axes. Because
    the gate is non-compensatory, callers must consult ``blocking_axes`` -- not
    the scalar -- to decide feasibility.
    """

    if not axis_status:
        raise ValueError("authority_coverage requires at least one poset axis")
    blocking = tuple(
        sorted(axis for axis, status in axis_status.items() if status != LICENSED)
    )
    licensed = len(axis_status) - len(blocking)
    coverage = _require_unit(licensed / len(axis_status), "authority coverage")
    return AuthorityCoverage(coverage=coverage, blocking_axes=blocking)


@dataclass(frozen=True)
class GateRecord:
    """One applicability-gate comparison: model prediction vs gold decision.

    ``pred`` / ``gold`` are decision tokens, canonically ``"ACCEPT"`` /
    ``"REJECT"``.
    """

    pred: str
    gold: str


def _as_gate_record(item: GateRecord | Mapping[str, str]) -> GateRecord:
    if isinstance(item, GateRecord):
        return item
    if isinstance(item, Mapping):
        try:
            return GateRecord(pred=str(item["pred"]), gold=str(item["gold"]))
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError("gate record mapping needs 'pred' and 'gold' keys") from exc
    raise TypeError("gate records must be GateRecord instances or pred/gold mappings")


def gate_false_accept(
    records: Iterable[GateRecord | Mapping[str, str]],
    *,
    accept_token: str = "ACCEPT",
    reject_token: str = "REJECT",
) -> float:
    """Return the gate false-accept rate ``P(pred=ACCEPT | gold=REJECT)``.

    This is a measurement, never a promotion/authority signal.

    Computed over the sub-population the gate must fail closed on -- records
    whose gold decision is ``reject_token``. The value is the fraction of those
    that the model wrongly ``accept_token``ed, in ``[0, 1]`` (lower is safer).
    Raises if there are no gold-reject records, because a conditional rate is
    undefined over an empty condition (returning ``0.0`` would fabricate safety).
    """

    normalized = [_as_gate_record(item) for item in records]
    gold_rejects = [r for r in normalized if r.gold == reject_token]
    if not gold_rejects:
        raise ValueError(
            "gate_false_accept undefined: no gold=REJECT records to condition on"
        )
    false_accepts = sum(1 for r in gold_rejects if r.pred == accept_token)
    return _require_unit(false_accepts / len(gold_rejects), "gate false-accept rate")
