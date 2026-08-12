"""Orion metric layer -- pure KPI functions + the trajectory figure.

Canonical import name: ``orion.metrics`` (an alias of the on-disk ``rakl``
implementation package; ``import orion.metrics`` and ``import rakl.metrics`` both
resolve here).

This layer turns the framework's already-typed objects into named, bounded,
read-only KPIs and the reader-facing trajectory/saturation figure. Nothing here
grants scientific or structural-transfer authority: **every KPI is a
measurement, never a promotion/authority signal**. See
``docs/ORION_KPI_AND_METRICS.md`` for the catalog these implement.

``viz`` is imported lazily via ``render_trajectory`` so that importing the KPI
functions does not require matplotlib.
"""

from __future__ import annotations

from .kpis import (
    LICENSED,
    AuthorityCoverage,
    GateRecord,
    authority_coverage,
    gate_false_accept,
    mastery_vector,
    retention_ok,
    saturation_epoch,
    saturation_level,
)
from .trajectory import (
    CoordinateSample,
    Trajectory,
    load_trajectories,
    load_trajectory,
    parse_exposure_rows,
)

__all__ = [
    # KPI functions
    "mastery_vector",
    "saturation_level",
    "saturation_epoch",
    "retention_ok",
    "authority_coverage",
    "gate_false_accept",
    # KPI value types / constants
    "AuthorityCoverage",
    "GateRecord",
    "LICENSED",
    # trajectory model
    "Trajectory",
    "CoordinateSample",
    "load_trajectory",
    "load_trajectories",
    "parse_exposure_rows",
    # figure (lazy matplotlib import)
    "render_trajectory",
]


def render_trajectory(*args, **kwargs):
    """Lazy proxy for :func:`rakl.metrics.viz.render_trajectory`.

    Imported on first call so that ``import orion.metrics`` (KPI use) does not
    hard-depend on matplotlib. This is a measurement renderer, never an authority
    signal.
    """

    from .viz import render_trajectory as _render_trajectory

    return _render_trajectory(*args, **kwargs)
