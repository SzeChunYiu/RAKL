from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple


class SaturationAxis(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    OPERATOR = "OPERATOR"
    EXPERIENCE_PATTERN = "EXPERIENCE_PATTERN"
    OBSTRUCTION = "OBSTRUCTION"
    RELATION = "RELATION"
    PATH = "PATH"
    META_METHOD = "META_METHOD"


@dataclass(frozen=True)
class NoveltyRound:
    round_id: str
    route_family: str
    independent_route: bool
    retained_novelty: Tuple[Tuple[SaturationAxis, int], ...]
    residual_axes: Tuple[SaturationAxis, ...] = ()
    residual_signature: Tuple[str, ...] = ()
    blocked: bool = False

    def __post_init__(self) -> None:
        if not self.round_id or not self.route_family:
            raise ValueError("novelty round requires round_id and route_family")
        axes = [axis for axis, _ in self.retained_novelty]
        if len(set(axes)) != len(axes):
            raise ValueError("retained_novelty may contain each axis at most once")
        if any(value < 0 for _, value in self.retained_novelty):
            raise ValueError("retained novelty counts cannot be negative")

    def novelty_for(self, axis: SaturationAxis) -> int:
        return dict(self.retained_novelty).get(axis, 0)


@dataclass(frozen=True)
class SaturationVectorState:
    rounds: Tuple[NoveltyRound, ...] = ()


@dataclass(frozen=True)
class SaturationAxisReport:
    axis: SaturationAxis
    flat: bool
    independent_flat_route_families: Tuple[str, ...]
    recent_retained_novelty: int
    reopen_residuals: Tuple[str, ...]


@dataclass(frozen=True)
class SaturationVectorReport:
    axis_reports: Tuple[SaturationAxisReport, ...]
    required_axes: Tuple[SaturationAxis, ...]
    bounded_saturated: bool
    reasons: Tuple[str, ...]

    @property
    def grants_absolute_completeness(self) -> bool:
        return False

    def flat(self, axis: SaturationAxis) -> bool:
        return next(report.flat for report in self.axis_reports if report.axis is axis)


def add_novelty_round(state: SaturationVectorState, round_: NoveltyRound) -> SaturationVectorState:
    if any(existing.round_id == round_.round_id for existing in state.rounds):
        raise ValueError(f"duplicate novelty round id: {round_.round_id}")
    return SaturationVectorState(state.rounds + (round_,))


def assess_saturation_vector(
    rounds: Iterable[NoveltyRound],
    *,
    required_axes: Tuple[SaturationAxis, ...] = tuple(SaturationAxis),
    min_independent_flat_routes: int = 2,
    window: int = 6,
) -> SaturationVectorReport:
    """Assess bounded semantic flatness separately for each RAKL view.

    Paper count, token count, or repeated same-route searches do not establish
    saturation.  An axis is flat only after independent route families add zero
    retained novelty and no recent native residual explicitly reopens that axis.
    """

    if min_independent_flat_routes < 1 or window < 1:
        raise ValueError("saturation route and window parameters must be positive")
    round_tuple = tuple(rounds)
    recent = round_tuple[-window:]
    reports: list[SaturationAxisReport] = []

    for axis in SaturationAxis:
        flat_routes: list[str] = []
        recent_novelty = 0
        reopen_residuals: list[str] = []
        for round_ in recent:
            value = round_.novelty_for(axis)
            recent_novelty += value
            if round_.independent_route and value == 0 and round_.route_family not in flat_routes:
                flat_routes.append(round_.route_family)
            if axis in round_.residual_axes:
                reopen_residuals.extend(round_.residual_signature or (f"residual:{round_.round_id}",))
        flat = len(flat_routes) >= min_independent_flat_routes and not reopen_residuals
        reports.append(
            SaturationAxisReport(
                axis=axis,
                flat=flat,
                independent_flat_route_families=tuple(flat_routes),
                recent_retained_novelty=recent_novelty,
                reopen_residuals=tuple(dict.fromkeys(reopen_residuals)),
            )
        )

    by_axis = {report.axis: report for report in reports}
    reasons: list[str] = []
    for axis in required_axes:
        report = by_axis[axis]
        if not report.flat:
            if report.reopen_residuals:
                reasons.append(f"{axis.value}:reopened_by_native_residual")
            elif len(report.independent_flat_route_families) < min_independent_flat_routes:
                reasons.append(f"{axis.value}:insufficient_independent_flat_routes")
    return SaturationVectorReport(
        axis_reports=tuple(reports),
        required_axes=required_axes,
        bounded_saturated=not reasons,
        reasons=tuple(reasons),
    )
