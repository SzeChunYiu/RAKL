"""Plot path-quotient savings from results/path_quotient_savings.json.

Two panels: (a) mean reduction ratio (naive executions / equivalence
classes) vs k, one line per commute probability p, bootstrap 95% CI bands;
(b) mean NET saving after witness cost vs k per p, with a zero line showing
where quotienting pays and where it does not.

Okabe-Ito palette (validated), thin lines, direct end labels, recessive
grid. Development known-world evidence only -- not an authority signal.
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
RESULT_FILE = RESULT_DIR / "path_quotient_savings.json"

# Okabe-Ito subset, fixed order per p (validated: dataviz six-checks, light).
P_COLORS = {
    0.0: "#0072B2",
    0.3: "#E69F00",
    0.6: "#009E73",
    1.0: "#D55E00",
}

GRID_KW = {"color": "0.85", "linewidth": 0.5, "alpha": 0.6}
INK = "0.25"


def load_cells() -> dict:
    data = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    by_p: dict[float, list[dict]] = {}
    for cell in data["cells"]:
        by_p.setdefault(cell["commute_probability"], []).append(cell)
    for rows in by_p.values():
        rows.sort(key=lambda row: row["k"])
    return {"meta": data, "by_p": by_p}


def style_axis(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(INK)
    ax.tick_params(colors=INK, labelsize=8)
    ax.grid(True, which="major", **GRID_KW)
    ax.set_axisbelow(True)


def stagger_end_labels(ax, labels: list[tuple[float, str, str]]) -> None:
    """Place direct end labels, nudging apart in display space if needed."""
    transform = ax.transData
    inverse = transform.inverted()
    entries = sorted(
        (transform.transform((0.0, y))[1], y, text, color)
        for y, text, color in labels
    )
    min_gap = 11.0  # pixels
    placed: list[float] = []
    for display_y, _, _, _ in entries:
        if placed and display_y - placed[-1] < min_gap:
            display_y = placed[-1] + min_gap
        placed.append(display_y)
    x_right = ax.get_xlim()[1]
    for display_y, (_, _, text, color) in zip(placed, entries):
        data_y = inverse.transform((0.0, display_y))[1]
        ax.text(
            x_right + 0.08, data_y, text,
            color=color, fontsize=8,
            va="center", ha="left", clip_on=False,
        )


def main() -> int:
    loaded = load_cells()
    meta = loaded["meta"]
    by_p = loaded["by_p"]
    p_values = sorted(by_p)
    k_values = [row["k"] for row in by_p[p_values[0]]]

    fig, (ax_ratio, ax_net) = plt.subplots(1, 2, figsize=(9.2, 3.9))
    fig.subplots_adjust(left=0.075, right=0.93, top=0.80, bottom=0.14, wspace=0.42)

    # Panel (a): reduction ratio, log scale.
    end_labels_ratio = []
    for p in p_values:
        rows = by_p[p]
        color = P_COLORS[p]
        means = np.array([row["reduction_ratio_mean"] for row in rows])
        low = np.array([row["reduction_ratio_ci95"][0] for row in rows])
        high = np.array([row["reduction_ratio_ci95"][1] for row in rows])
        ax_ratio.fill_between(k_values, low, high, color=color, alpha=0.18, lw=0)
        ax_ratio.plot(k_values, means, color=color, lw=1.4,
                      marker="o", ms=3.5, label=f"p = {p}")
        end_labels_ratio.append((means[-1], f"p = {p}", color))
    ax_ratio.set_yscale("log")
    ax_ratio.set_xticks(k_values)
    ax_ratio.set_xlabel("k (transformations in solution set)", fontsize=9, color=INK)
    ax_ratio.set_ylabel("reduction ratio  naive / classes", fontsize=9, color=INK)
    ax_ratio.set_title("(a) explored orderings collapse under the quotient",
                       fontsize=9.5, color=INK, loc="left")
    style_axis(ax_ratio)
    ax_ratio.legend(fontsize=7, frameon=False, loc="upper left",
                    labelcolor=INK, handlelength=1.4)
    stagger_end_labels(ax_ratio, end_labels_ratio)

    # Panel (b): net saving after witness cost, symlog with zero line.
    end_labels_net = []
    for p in p_values:
        rows = by_p[p]
        color = P_COLORS[p]
        means = np.array([row["net_saving_mean"] for row in rows])
        low = np.array([row["net_saving_ci95"][0] for row in rows])
        high = np.array([row["net_saving_ci95"][1] for row in rows])
        ax_net.fill_between(k_values, low, high, color=color, alpha=0.18, lw=0)
        ax_net.plot(k_values, means, color=color, lw=1.4,
                    marker="o", ms=3.5, label=f"p = {p}")
        end_labels_net.append((means[-1], f"p = {p}", color))
    ax_net.axhline(0.0, color="0.45", lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax_net.text(k_values[-1] - 0.05, -1.5, "net saving = 0", fontsize=7,
                color="0.45", va="top", ha="right")
    ax_net.set_yscale("symlog", linthresh=20)
    ax_net.set_xticks(k_values)
    ax_net.set_xlabel("k (transformations in solution set)", fontsize=9, color=INK)
    ax_net.set_ylabel("net saving  naive − (classes + witness checks)",
                      fontsize=9, color=INK)
    ax_net.set_title("(b) quotienting pays only after the witness cost",
                     fontsize=9.5, color=INK, loc="left")
    style_axis(ax_net)
    ax_net.legend(fontsize=7, frameon=False, loc="upper left",
                  labelcolor=INK, handlelength=1.4)
    stagger_end_labels(ax_net, end_labels_net)

    fig.suptitle(
        "Path-quotient savings in random known worlds — "
        f"N = {meta['n_instances_per_cell']} instances/cell, "
        f"seed {meta['seed']}, bootstrap 95% CI\n"
        "development known-world evidence — not an authority signal",
        fontsize=10, color=INK, x=0.075, ha="left",
    )

    for suffix in ("pdf", "png"):
        out = RESULT_DIR / f"path_quotient_savings.{suffix}"
        fig.savefig(out, dpi=200)
        print(f"WROTE={out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
