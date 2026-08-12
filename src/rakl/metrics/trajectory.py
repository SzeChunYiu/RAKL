"""In-memory learning-trajectory model built from ``exposure_outcomes.jsonl``.

This module parses the Phase-1 exposure sweep into the object the Orion
trajectory figure (``orion.metrics.viz.render_trajectory``) renders: per-
coordinate mastery-vs-exposure and marginal-gain-vs-exposure curves for one
structural family. It computes nothing that grants authority -- it only
reshapes recorded probe outcomes into aligned series.

JSONL schema (``exposure_outcomes.jsonl``)
------------------------------------------
One JSON object per line. Each line is one measured cell, keyed by the triple
``(family, exposure_count, probe_kind)``::

    {
      "family":         str,    # structural family / structure_id under exposure
      "exposure_count": int,    # number of same-structure examples seen (>= 0)
      "probe_kind":     str,    # probe instrument that produced this accuracy
      "coordinate":     str,    # one of the 6 MasteryCoordinate names
                                #   (principle|composition|boundary|
                                #    representation|transfer|retention),
                                #   case-insensitive
      "accuracy":       float,  # probe accuracy in [0, 1]
      "n":              int     # number of probe items behind this accuracy (>= 0)
    }

Notes
-----
* Several ``probe_kind`` rows may map to the same ``(coordinate, exposure)``
  cell; they are combined into an ``n``-weighted mean accuracy.
* A coordinate with **no** row at a given exposure is preserved as ``None`` (an
  unmeasured coordinate), never coerced to ``0.0``.
* Marginal gain at exposure ``e`` is ``mastery(e) - mastery(prev)``; it is
  ``None`` at the first exposure and wherever either endpoint is unmeasured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Iterable, Mapping

from ..training_projection import MasteryCoordinate

__all__ = [
    "CoordinateSample",
    "Trajectory",
    "load_trajectories",
    "load_trajectory",
    "parse_exposure_rows",
]

# Case-insensitive name -> canonical coordinate.
_COORD_BY_NAME: dict[str, MasteryCoordinate] = {c.value.lower(): c for c in MasteryCoordinate}
_COORDINATE_ORDER: tuple[MasteryCoordinate, ...] = tuple(MasteryCoordinate)


def _coordinate(name: str) -> MasteryCoordinate:
    try:
        return _COORD_BY_NAME[str(name).strip().lower()]
    except KeyError as exc:
        raise ValueError(
            f"unknown mastery coordinate {name!r}; expected one of "
            + ", ".join(c.value for c in _COORDINATE_ORDER)
        ) from exc


@dataclass(frozen=True)
class CoordinateSample:
    """Combined ``n``-weighted probe result for one (coordinate, exposure) cell."""

    accuracy: float
    n: int


@dataclass(frozen=True)
class Trajectory:
    """Per-coordinate mastery/marginal-gain series for one structural family.

    ``exposures`` is the sorted unique exposure grid. ``mastery`` maps each of
    the 6 coordinates to a tuple aligned with ``exposures`` whose entries are the
    measured accuracy or ``None`` (unmeasured). ``sample_n`` maps coordinate to
    the aligned per-exposure item counts (0 where unmeasured). This object is a
    measurement view; it grants no authority.
    """

    family: str
    exposures: tuple[int, ...]
    mastery: Mapping[MasteryCoordinate, tuple[float | None, ...]]
    sample_n: Mapping[MasteryCoordinate, tuple[int, ...]]

    @property
    def coordinates(self) -> tuple[MasteryCoordinate, ...]:
        return _COORDINATE_ORDER

    @property
    def is_empty(self) -> bool:
        """True when there is no usable measurement to render."""

        if not self.exposures:
            return True
        return all(
            value is None
            for series in self.mastery.values()
            for value in series
        )

    @property
    def total_n(self) -> int:
        """Total probe items behind this trajectory across all cells."""

        return sum(count for series in self.sample_n.values() for count in series)

    def mastery_series(self, coordinate: MasteryCoordinate) -> tuple[float | None, ...]:
        return self.mastery[coordinate]

    def marginal_gain_series(
        self, coordinate: MasteryCoordinate
    ) -> tuple[float | None, ...]:
        """Marginal gain vs exposure for one coordinate.

        Entry ``i`` is ``mastery[i] - mastery[i-1]``; ``None`` at the first
        exposure and wherever either endpoint is unmeasured. Robust to gaps: the
        "previous" reference is the most recent *measured* exposure, so a single
        missing cell does not silently produce a spurious jump -- it yields
        ``None`` for the gap and resumes against the last real value.
        """

        series = self.mastery[coordinate]
        gains: list[float | None] = []
        prev: float | None = None
        for value in series:
            if value is None:
                gains.append(None)
                continue
            gains.append(None if prev is None else value - prev)
            prev = value
        return tuple(gains)


def _validate_row(row: Mapping[str, object], line_no: int) -> tuple[str, int, MasteryCoordinate, float, int]:
    required = ("family", "exposure_count", "probe_kind", "coordinate", "accuracy", "n")
    missing = [key for key in required if key not in row]
    if missing:
        raise ValueError(f"line {line_no}: missing field(s) {missing}")
    family = str(row["family"]).strip()
    if not family:
        raise ValueError(f"line {line_no}: 'family' must be non-empty")
    try:
        exposure = int(row["exposure_count"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line_no}: 'exposure_count' must be an int") from exc
    if exposure < 0:
        raise ValueError(f"line {line_no}: 'exposure_count' must be >= 0")
    coordinate = _coordinate(row["coordinate"])
    accuracy = float(row["accuracy"])
    if not isfinite(accuracy) or not 0.0 <= accuracy <= 1.0:
        raise ValueError(f"line {line_no}: 'accuracy' must be finite and in [0,1]")
    n = int(row["n"])
    if n < 0:
        raise ValueError(f"line {line_no}: 'n' must be >= 0")
    return family, exposure, coordinate, accuracy, n


def parse_exposure_rows(rows: Iterable[Mapping[str, object]]) -> dict[str, Trajectory]:
    """Build one :class:`Trajectory` per family from already-parsed row dicts.

    Rows sharing a ``(family, coordinate, exposure_count)`` cell are combined
    with an ``n``-weighted mean accuracy (rows with ``n == 0`` contribute no
    weight; if every contributing row has ``n == 0`` the plain mean is used).
    """

    # family -> coordinate -> exposure -> (weighted_sum, weight, plain_sum, count, n_total)
    acc: dict[str, dict[MasteryCoordinate, dict[int, list[float]]]] = {}
    exposures_by_family: dict[str, set[int]] = {}

    for line_no, row in enumerate(rows, start=1):
        family, exposure, coordinate, accuracy, n = _validate_row(row, line_no)
        fam = acc.setdefault(family, {})
        coord_map = fam.setdefault(coordinate, {})
        cell = coord_map.setdefault(exposure, [0.0, 0.0, 0.0, 0.0, 0.0])
        cell[0] += accuracy * n  # weighted sum
        cell[1] += n             # weight
        cell[2] += accuracy      # plain sum
        cell[3] += 1             # count
        cell[4] += n             # total n
        exposures_by_family.setdefault(family, set()).add(exposure)

    trajectories: dict[str, Trajectory] = {}
    for family, coord_cells in acc.items():
        exposures = tuple(sorted(exposures_by_family[family]))
        mastery: dict[MasteryCoordinate, tuple[float | None, ...]] = {}
        sample_n: dict[MasteryCoordinate, tuple[int, ...]] = {}
        for coordinate in _COORDINATE_ORDER:
            cells = coord_cells.get(coordinate, {})
            values: list[float | None] = []
            counts: list[int] = []
            for exposure in exposures:
                cell = cells.get(exposure)
                if cell is None:
                    values.append(None)   # unmeasured coordinate -> None, not 0.0
                    counts.append(0)
                    continue
                weighted_sum, weight, plain_sum, count, n_total = cell
                if weight > 0:
                    values.append(weighted_sum / weight)
                else:
                    values.append(plain_sum / count)
                counts.append(int(n_total))
            mastery[coordinate] = tuple(values)
            sample_n[coordinate] = tuple(counts)
        trajectories[family] = Trajectory(
            family=family,
            exposures=exposures,
            mastery=mastery,
            sample_n=sample_n,
        )
    return trajectories


def load_trajectories(path: str | Path) -> dict[str, Trajectory]:
    """Parse an ``exposure_outcomes.jsonl`` file into one Trajectory per family.

    Blank lines are skipped. Malformed JSON or schema-invalid rows raise
    ``ValueError`` with the offending line number.
    """

    rows: list[Mapping[str, object]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid JSON ({exc.msg})") from exc
            if not isinstance(obj, Mapping):
                raise ValueError(f"line {line_no}: each JSONL row must be a JSON object")
            rows.append(obj)
    return parse_exposure_rows(rows)


def load_trajectory(path: str | Path, family: str | None = None) -> Trajectory:
    """Load a single trajectory.

    If ``family`` is given, return that family's trajectory. Otherwise the file
    must contain exactly one family (else raise), and that trajectory is
    returned.
    """

    trajectories = load_trajectories(path)
    if not trajectories:
        raise ValueError(f"{path}: no trajectory rows found")
    if family is not None:
        try:
            return trajectories[family]
        except KeyError as exc:
            raise ValueError(
                f"family {family!r} not in {sorted(trajectories)}"
            ) from exc
    if len(trajectories) != 1:
        raise ValueError(
            f"{path} holds {len(trajectories)} families {sorted(trajectories)}; "
            "pass family=..."
        )
    return next(iter(trajectories.values()))
