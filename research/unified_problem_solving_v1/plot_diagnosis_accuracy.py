"""Plot results/diagnosis_accuracy.json -> diagnosis_accuracy.pdf/.png.

Two panels:
  (a) per-cause containment + top-1 (first-listed) accuracy at noise 0.1,
      bootstrap 95% CIs;
  (b) forced-wrong vs honest-ambiguous (and correct unique identification)
      rates as noise increases.

Okabe-Ito palette; single axis per panel; recessive grid; thin marks.
Development known-world evidence only -- not an authority signal.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "research" / "unified_problem_solving_v1" / "results"
RESULT_FILE = RESULT_DIR / "diagnosis_accuracy.json"

# Okabe-Ito
BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
PINK = "#CC79A7"
ORANGE = "#E69F00"

INK = "#333333"
MUTED = "#666666"
GRID = "#d9d9d9"

PANEL_A_NOISE = "0.1"


def _style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(MUTED)
        ax.spines[spine].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8, width=0.8)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.7)


def _short(cause: str) -> str:
    return cause.replace("_GAP", "").replace("_", "\n").title()


def _err(entry: dict) -> tuple[float, float]:
    rate, (lo, hi) = entry["rate"], entry["ci95"]
    return rate - lo, hi - rate


def panel_causes(ax: plt.Axes, data: dict) -> None:
    per_cause = data["results_by_noise"][PANEL_A_NOISE]["per_cause"]
    identifiable = data["structural_identifiability"]
    causes = sorted(
        per_cause,
        key=lambda c: (-per_cause[c]["top1_first_listed"]["rate"], c),
    )
    x = np.arange(len(causes))
    width = 0.38
    for offset, metric, color, label in (
        (-width / 2, "containment", BLUE, "containment: true cause in candidates"),
        (+width / 2, "top1_first_listed", VERMILLION, "top-1 (first-listed candidate)"),
    ):
        rates = [per_cause[c][metric]["rate"] for c in causes]
        errs = np.array([_err(per_cause[c][metric]) for c in causes]).T
        ax.bar(
            x + offset,
            rates,
            width - 0.04,
            color=color,
            linewidth=0,
            label=label,
            zorder=3,
        )
        ax.errorbar(
            x + offset,
            rates,
            yerr=errs,
            fmt="none",
            ecolor=INK,
            elinewidth=0.8,
            capsize=2,
            capthick=0.8,
            zorder=4,
        )
    labels = [
        _short(c) + ("" if identifiable[c] else "\n(no unique\nsignal)") for c in causes
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6.5, color=INK)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("accuracy at noise 0.1 (95% bootstrap CI)", fontsize=8, color=INK)
    ax.set_title(
        "(a) per-cause diagnosis accuracy, noise = 0.1",
        fontsize=9,
        color=INK,
        loc="left",
    )
    legend = ax.legend(
        fontsize=7,
        loc="lower left",
        frameon=True,
        framealpha=0.92,
        edgecolor="none",
        facecolor="white",
    )
    legend.set_zorder(5)


def panel_noise_sweep(ax: plt.Axes, data: dict) -> None:
    noises = [f"{n:.1f}" for n in data["noise_levels"]]
    xs = [float(n) for n in noises]
    series = (
        ("honest_ambiguous", GREEN, "o", "-", "honest ambiguous / discriminator / cannot-check"),
        ("identified_correct", BLUE, "s", "--", "unique identification, correct"),
        ("forced_wrong", VERMILLION, "^", "-.", "forced wrong single diagnosis"),
    )
    for metric, color, marker, linestyle, label in series:
        rows = [data["results_by_noise"][n]["overall"][metric] for n in noises]
        rates = [r["rate"] for r in rows]
        errs = np.array([_err(r) for r in rows]).T
        ax.errorbar(
            xs,
            rates,
            yerr=errs,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.6,
            markersize=4.5,
            capsize=2,
            elinewidth=0.8,
            capthick=0.8,
            label=label,
            zorder=3,
        )
    ax.set_xticks(xs)
    ax.set_xlim(-0.02, 0.32)
    ax.set_ylim(-0.02, 1.0)
    ax.set_xlabel("signal corruption rate (drop / spurious / raw-unrecognised)", fontsize=8, color=INK)
    ax.set_ylabel("rate over scenarios (95% bootstrap CI)", fontsize=8, color=INK)
    ax.set_title(
        "(b) verdict honesty under signal corruption",
        fontsize=9,
        color=INK,
        loc="left",
    )
    ax.legend(fontsize=7, frameon=False, loc="upper left")


def main() -> int:
    data = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.0, 4.6))
    _style_axis(ax_a)
    _style_axis(ax_b)
    panel_causes(ax_a, data)
    panel_noise_sweep(ax_b, data)
    fig.suptitle(
        f"mechanic_diagnosis under injected deficiencies -- N={data['n_scenarios_per_noise_level']} "
        f"scenarios per noise level, seed {data['seed']}\n"
        "development known-world evidence -- not an authority signal; "
        "signal names are pre-classified, so accuracy reflects the signal->cause table, not inference",
        fontsize=9,
        color=INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    for suffix in ("pdf", "png"):
        out = RESULT_DIR / f"diagnosis_accuracy.{suffix}"
        fig.savefig(out, dpi=200)
        print(f"WROTE={out.relative_to(ROOT)}")
    print("AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
