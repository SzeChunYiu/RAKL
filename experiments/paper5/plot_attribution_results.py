#!/usr/bin/env python3
"""Generate Paper 5 causal-attribution figures from analyzed CSV files.

Input directory must be produced by ``analyze_attribution_results.py``.
No synthetic fallback values are ever generated: missing columns or empty data
fail closed rather than drawing placeholder bars that could be mistaken for
results.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit("matplotlib is required for Paper 5 plotting") from exc

ARM_LABELS = {
    "MODEL_ONLY": "Model only",
    "RAKL_RESET": "RAKL reset",
    "RAKL_SHAM_MEMORY": "RAKL sham memory",
    "RAKL_LEARNING": "RAKL learning",
}
ARM_ORDER = tuple(ARM_LABELS)
STRATUM_LABELS = {
    "REPEATED_FAMILY": "Repeated family",
    "CROSS_DOMAIN_TRANSFER": "Cross-domain transfer",
    "HOSTILE_NEAR_MISS": "Hostile near-miss",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise SystemExit(f"missing analysis file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"analysis file has no rows: {path}")
    return rows


def f(row: dict[str, str], key: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, ValueError) as exc:
        raise SystemExit(f"missing/non-numeric {key}") from exc
    return value


def save(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(path)


def plot_four_arm(arm_rows: list[dict[str, str]], out: Path) -> None:
    lookup = {row["arm"]: row for row in arm_rows}
    if set(ARM_ORDER) - set(lookup):
        raise SystemExit("arm_metrics.csv is missing one or more preregistered arms")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    x = list(range(len(ARM_ORDER)))
    labels = [ARM_LABELS[arm] for arm in ARM_ORDER]

    scores = [f(lookup[arm], "mean_score") for arm in ARM_ORDER]
    score_err = [
        [scores[i] - f(lookup[arm], "score_ci_low") for i, arm in enumerate(ARM_ORDER)],
        [f(lookup[arm], "score_ci_high") - scores[i] for i, arm in enumerate(ARM_ORDER)],
    ]
    axes[0].bar(x, scores, yerr=score_err, capsize=3)
    axes[0].set_ylabel("Registered task score")
    axes[0].set_ylim(0, 1)
    axes[0].set_xticks(x, labels, rotation=20, ha="right")
    axes[0].set_title("Task-level mean score (95% bootstrap CI)")

    success = [f(lookup[arm], "success_rate") for arm in ARM_ORDER]
    success_err = [
        [success[i] - f(lookup[arm], "success_ci_low") for i, arm in enumerate(ARM_ORDER)],
        [f(lookup[arm], "success_ci_high") - success[i] for i, arm in enumerate(ARM_ORDER)],
    ]
    axes[1].bar(x, success, yerr=success_err, capsize=3)
    axes[1].set_ylabel("Task success rate")
    axes[1].set_ylim(0, 1)
    axes[1].set_xticks(x, labels, rotation=20, ha="right")
    axes[1].set_title("Task success (95% bootstrap CI)")

    fig.suptitle("Paper 5 — four-arm causal attribution")
    fig.tight_layout()
    save(fig, out / "paper5_fig5_four_arm_attribution.pdf")


def plot_contrasts(contrast_rows: list[dict[str, str]], out: Path) -> None:
    order = ["ARCHITECTURE", "EXPERIENCE", "CONTENT", "TOTAL"]
    lookup = {row["contrast"]: row for row in contrast_rows}
    if set(order) - set(lookup):
        raise SystemExit("contrasts.csv is missing registered contrasts")
    labels = [name.title() for name in order]
    x = list(range(len(order)))

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for axis, metric, lo_key, hi_key, ylabel, title in (
        (axes[0], "mean_score_delta", "score_delta_ci_low", "score_delta_ci_high", "Score difference", "Paired score contrasts"),
        (axes[1], "success_rate_delta", "success_delta_ci_low", "success_delta_ci_high", "Success-rate difference", "Paired success contrasts"),
    ):
        values = [f(lookup[name], metric) for name in order]
        errors = [
            [values[i] - f(lookup[name], lo_key) for i, name in enumerate(order)],
            [f(lookup[name], hi_key) - values[i] for i, name in enumerate(order)],
        ]
        axis.bar(x, values, yerr=errors, capsize=3)
        axis.axhline(0, linewidth=1)
        axis.set_xticks(x, labels, rotation=20, ha="right")
        axis.set_ylabel(ylabel)
        axis.set_title(title)
    fig.suptitle("Paper 5 — registered causal contrasts")
    fig.tight_layout()
    save(fig, out / "paper5_fig5_causal_contrasts.pdf")


def plot_paired_outcomes(rows: list[dict[str, str]], out: Path) -> None:
    order = ["TOTAL", "EXPERIENCE", "CONTENT", "ARCHITECTURE"]
    lookup = {row["contrast"]: row for row in rows}
    categories = ("both_success", "rakl_only_success", "baseline_only_success", "both_fail")
    labels = ("Both success", "RAKL/treatment only", "Baseline only", "Both fail")
    x = list(range(len(order)))

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    bottoms = [0.0] * len(order)
    for category, label in zip(categories, labels):
        vals = [f(lookup[name], category) for name in order]
        ax.bar(x, vals, bottom=bottoms, label=label)
        bottoms = [bottoms[i] + vals[i] for i in range(len(order))]
    ax.set_xticks(x, [name.title() for name in order])
    ax.set_ylabel("Task count")
    ax.set_title("Paired outcome categories — baseline-only harm shown symmetrically")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    save(fig, out / "paper5_fig5_paired_outcomes.pdf")


def plot_resources(arm_rows: list[dict[str, str]], out: Path) -> None:
    lookup = {row["arm"]: row for row in arm_rows}
    labels = [ARM_LABELS[arm] for arm in ARM_ORDER]
    x = list(range(len(ARM_ORDER)))
    metrics = (
        ("mean_model_input_tokens", "Input tokens"),
        ("mean_model_output_tokens", "Output tokens"),
        ("mean_tool_calls", "Tool calls"),
        ("mean_retrieval_calls", "Retrieval calls"),
        ("mean_wall_time_ms", "Wall time (ms)"),
    )
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2))
    axes_flat = list(axes.flat)
    for idx, (key, ylabel) in enumerate(metrics):
        vals = [f(lookup[arm], key) for arm in ARM_ORDER]
        axes_flat[idx].bar(x, vals)
        axes_flat[idx].set_xticks(x, labels, rotation=25, ha="right")
        axes_flat[idx].set_ylabel(ylabel)
    axes_flat[-1].axis("off")
    fig.suptitle("Paper 5 — actual resource use by arm")
    fig.tight_layout()
    save(fig, out / "paper5_fig5_resources.pdf")


def plot_strata(rows: list[dict[str, str]], out: Path) -> None:
    lookup = {(row["stratum"], row["arm"]): row for row in rows}
    strata = [name for name in STRATUM_LABELS if any(key[0] == name for key in lookup)]
    if not strata:
        raise SystemExit("stratum_metrics.csv contains no recognized strata")

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    width = 0.18
    centers = list(range(len(strata)))
    for arm_idx, arm in enumerate(ARM_ORDER):
        offsets = [c + (arm_idx - 1.5) * width for c in centers]
        success = [f(lookup[(stratum, arm)], "success_rate") for stratum in strata]
        axes[0].bar(offsets, success, width=width, label=ARM_LABELS[arm])
        validity = [f(lookup[(stratum, arm)], "validity_failure_rate") for stratum in strata]
        axes[1].bar(offsets, validity, width=width)
        false_transfer = []
        for stratum in strata:
            value = f(lookup[(stratum, arm)], "false_transfer_rate")
            false_transfer.append(0.0 if math.isnan(value) else value)
        axes[2].bar(offsets, false_transfer, width=width)

    labels = [STRATUM_LABELS[name] for name in strata]
    for axis, title, ylabel in (
        (axes[0], "Success", "Rate"),
        (axes[1], "Blocking validity failures", "Rate"),
        (axes[2], "False transfer", "Rate"),
    ):
        axis.set_xticks(centers, labels, rotation=20, ha="right")
        axis.set_ylim(0, 1)
        axis.set_title(title)
        axis.set_ylabel(ylabel)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Paper 5 — transfer value versus hostile near-miss safety")
    fig.tight_layout()
    save(fig, out / "paper5_fig6_transfer_safety.pdf")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    arm_rows = read_csv(args.analysis_dir / "arm_metrics.csv")
    contrast_rows = read_csv(args.analysis_dir / "contrasts.csv")
    paired_rows = read_csv(args.analysis_dir / "paired_outcomes.csv")
    stratum_rows = read_csv(args.analysis_dir / "stratum_metrics.csv")

    plot_four_arm(arm_rows, args.out_dir)
    plot_contrasts(contrast_rows, args.out_dir)
    plot_paired_outcomes(paired_rows, args.out_dir)
    plot_resources(arm_rows, args.out_dir)
    plot_strata(stratum_rows, args.out_dir)


if __name__ == "__main__":
    main()
