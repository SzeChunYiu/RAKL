"""Trajectory + saturation figure for the Orion metric layer (``orion.metrics.viz``).

``render_trajectory`` draws the reader-facing "problem-solving trajectory"
figure from ``docs/ORION_KPI_AND_METRICS.md``: a 2-panel figure whose left panel
shows the 6 mastery coordinates climbing vs exposure, and whose right panel
shows their marginal gain (what the next example still buys) vs exposure with an
``epsilon`` stop line.

Honesty guardrails baked into this module:

* It **renders only what it is given**. It never fabricates, interpolates, or
  invents data points; called with an empty trajectory it raises rather than
  drawing an empty or fake figure.
* The caller must supply ``title``, ``seed`` and ``n`` so the figure is honestly
  labeled. Every suptitle/caption states ``N`` and that the figure is a
  "system/process measurement -- not an authority signal".
* Uses the Okabe-Ito colorblind-safe palette, thin recessive lines, a recessive
  grid, and direct end-of-line labels (no legend-only encoding, no dual axis).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic raster/vector backend

import matplotlib.pyplot as plt  # noqa: E402  (must follow use("Agg"))

from ..training_projection import MasteryCoordinate
from .trajectory import Trajectory

__all__ = ["OKABE_ITO", "render_trajectory"]

# Okabe-Ito colorblind-safe palette, one per coordinate, plus ink.
OKABE_ITO: tuple[str, ...] = (
    "#0072B2",  # PRINCIPLE     - blue
    "#D55E00",  # COMPOSITION   - vermillion
    "#009E73",  # BOUNDARY      - bluish green
    "#CC79A7",  # REPRESENTATION- reddish purple
    "#E69F00",  # TRANSFER      - orange
    "#56B4E9",  # RETENTION     - sky blue
)
_INK = "#222222"
_GRID = "#DDDDDD"

_COORDINATE_ORDER: tuple[MasteryCoordinate, ...] = tuple(MasteryCoordinate)
_COLOR_BY_COORDINATE = dict(zip(_COORDINATE_ORDER, OKABE_ITO))


def _plot_measured(ax, exposures, series, color, label, *, marker):
    """Plot only the measured (non-None) points; return the last (x, y) drawn."""

    xs = [x for x, y in zip(exposures, series) if y is not None]
    ys = [y for y in series if y is not None]
    if not xs:
        return None
    ax.plot(xs, ys, color=color, linewidth=2.0, marker=marker, markersize=3.5,
            solid_capstyle="round", clip_on=False)
    # Direct end-of-line label instead of a legend.
    ax.annotate(
        label,
        xy=(xs[-1], ys[-1]),
        xytext=(4, 0),
        textcoords="offset points",
        va="center",
        ha="left",
        fontsize=7,
        color=color,
    )
    return xs[-1], ys[-1]


def _style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(_INK)
    ax.spines["bottom"].set_color(_INK)
    ax.tick_params(colors=_INK, labelsize=8)
    ax.grid(True, color=_GRID, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)


def render_trajectory(
    trajectory: Trajectory,
    out_path_stem: str | Path,
    *,
    title: str,
    seed: int | str,
    n: int,
    epsilon: float = 0.05,
) -> list[Path]:
    """Render ``trajectory`` to ``<out_path_stem>.pdf`` and ``.png``.

    Parameters
    ----------
    trajectory:
        The :class:`~rakl.metrics.trajectory.Trajectory` to draw. It is rendered
        verbatim; no points are invented. Raises ``ValueError`` if it is empty.
    out_path_stem:
        Path stem (no extension). ``.pdf`` and ``.png`` siblings are written.
    title, seed, n:
        Honest-labeling inputs. ``title`` names the run, ``seed`` and ``n``
        (probe-item count) are stamped into the caption. ``n`` must be > 0.
    epsilon:
        Saturation stop threshold; drawn as a horizontal reference line on the
        right (marginal-gain) panel.

    Returns the list of written file paths.

    This renders a system/process measurement, never a promotion/authority
    signal.
    """

    if n <= 0:
        raise ValueError("render_trajectory requires n > 0 for honest labeling")
    if trajectory.is_empty:
        raise ValueError(
            "render_trajectory refuses to draw an empty trajectory "
            "(no measured coordinates) -- it renders data, it does not invent it"
        )

    stem = Path(out_path_stem)
    exposures = trajectory.exposures

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    # Left: mastery vs exposure (6 small-multiple lines, direct-labeled).
    for coordinate in _COORDINATE_ORDER:
        _plot_measured(
            ax_left,
            exposures,
            trajectory.mastery_series(coordinate),
            _COLOR_BY_COORDINATE[coordinate],
            coordinate.value.lower(),
            marker="o",
        )
    ax_left.set_title("mastery vs exposure", color=_INK, fontsize=10)
    ax_left.set_xlabel("exposure count", color=_INK, fontsize=9)
    ax_left.set_ylabel("coordinate mastery (probe accuracy)", color=_INK, fontsize=9)
    ax_left.set_ylim(-0.02, 1.02)
    _style_axis(ax_left)

    # Right: marginal gain / saturation vs exposure, with the epsilon stop line.
    for coordinate in _COORDINATE_ORDER:
        _plot_measured(
            ax_right,
            exposures,
            trajectory.marginal_gain_series(coordinate),
            _COLOR_BY_COORDINATE[coordinate],
            coordinate.value.lower(),
            marker="o",
        )
    ax_right.axhline(epsilon, color=_INK, linewidth=1.0, linestyle="--", alpha=0.8)
    ax_right.annotate(
        f"epsilon = {epsilon:g} (saturation stop)",
        xy=(exposures[0], epsilon),
        xytext=(0, 3),
        textcoords="offset points",
        fontsize=7,
        color=_INK,
    )
    ax_right.axhline(0.0, color=_GRID, linewidth=0.8)
    ax_right.set_title("marginal gain (saturation) vs exposure", color=_INK, fontsize=10)
    ax_right.set_xlabel("exposure count", color=_INK, fontsize=9)
    ax_right.set_ylabel("marginal gain of next example", color=_INK, fontsize=9)
    _style_axis(ax_right)

    # Honest labeling: state N and the not-an-authority-signal disclaimer.
    fig.suptitle(
        f"{title}\nfamily={trajectory.family}  N={n}  seed={seed}  "
        "-- system/process measurement, not an authority signal",
        color=_INK,
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))

    written: list[Path] = []
    for suffix in (".pdf", ".png"):
        out = stem.with_suffix(suffix)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        written.append(out)
    plt.close(fig)
    return written
