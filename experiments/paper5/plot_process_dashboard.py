#!/usr/bin/env python3
"""Render Paper 5 Figure 7 from ``process_dashboard.csv``.

The plot deliberately keeps outcome, cost, novelty and residual movement as
separate panels rather than inventing one heterogeneous process score.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit("matplotlib is required") from exc


def load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("process dashboard CSV is empty")
    return rows


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def label(surface: str) -> str:
    return surface.replace("_", " ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    rows = load(args.dashboard)
    rows = sorted(rows, key=lambda row: row["process_surface"])
    args.out_dir.mkdir(parents=True, exist_ok=True)

    y = list(range(len(rows)))
    labels = [label(row["process_surface"]) for row in rows]
    fig, axes = plt.subplots(1, 4, figsize=(15.5, max(6.0, 0.34 * len(rows) + 2.4)), sharey=True)

    axes[0].barh(y, [f(row, "invocation_count") for row in rows])
    axes[0].set_title("Invocations")
    axes[0].set_xlabel("Count")

    axes[1].barh(y, [f(row, "valid_completion_rate") for row in rows], label="Valid completion")
    axes[1].barh(y, [f(row, "blocked_rate") for row in rows], left=[f(row, "valid_completion_rate") for row in rows], label="Blocked")
    left2 = [f(row, "valid_completion_rate") + f(row, "blocked_rate") for row in rows]
    axes[1].barh(y, [f(row, "cannot_check_rate") for row in rows], left=left2, label="Cannot check")
    axes[1].set_xlim(0, 1)
    axes[1].set_title("Selected outcome rates")
    axes[1].set_xlabel("Rate")
    axes[1].legend(frameon=False, fontsize=7)

    axes[2].barh(y, [f(row, "retained_novelty_per_invocation") for row in rows])
    axes[2].set_title("Retained novelty yield")
    axes[2].set_xlabel("Events / invocation")

    axes[3].barh(y, [f(row, "mean_raw_residual_contraction") for row in rows])
    axes[3].axvline(0, linewidth=0.8)
    axes[3].set_title("Residual movement")
    axes[3].set_xlabel("Mean raw contraction")

    axes[0].set_yticks(y, labels, fontsize=7)
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)
    fig.suptitle("Paper 5 — RAKL process dashboard (heterogeneous metrics kept separate)")
    fig.tight_layout()
    path = args.out_dir / "paper5_fig7_process_dashboard.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(path)

    # Cost panel is separate because surfaces with different cost policies are not
    # numerically comparable. Draw only surfaces whose within-surface policy is
    # internally stable, and label the plot as descriptive.
    comparable = [row for row in rows if row.get("costs_comparable", "").lower() == "true"]
    if comparable:
        fig, ax = plt.subplots(figsize=(8.5, max(4.0, 0.30 * len(comparable) + 1.8)))
        yy = list(range(len(comparable)))
        ax.barh(yy, [f(row, "mean_cost") for row in comparable])
        ax.set_yticks(yy, [label(row["process_surface"]) for row in comparable], fontsize=7)
        ax.set_xlabel("Registered cost units (within-surface only)")
        ax.set_title("Paper 5 — process cost descriptions; do not rank across incompatible policies")
        fig.tight_layout()
        path2 = args.out_dir / "paper5_ext_process_costs.pdf"
        fig.savefig(path2, bbox_inches="tight")
        plt.close(fig)
        print(path2)


if __name__ == "__main__":
    main()
