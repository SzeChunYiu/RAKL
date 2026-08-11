#!/usr/bin/env python3
"""Plot Paper 2 v3 experience benchmark metrics from analyzed CSV output."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit("matplotlib is required") from exc

PHASES = ("DEVELOPMENT_SEQUENCE", "FRESH_TRANSFER")
ARMS = ("RESET_BASELINE", "LEARNING_ENABLED")
LABELS = {"RESET_BASELINE": "Reset baseline", "LEARNING_ENABLED": "Learning enabled"}


def load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("metrics CSV is empty")
    return rows


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    rows = load(args.metrics)
    lookup = {(row["phase"], row["arm"]): row for row in rows}
    for key in ((phase, arm) for phase in PHASES for arm in ARMS):
        if key not in lookup:
            raise SystemExit(f"missing phase/arm row: {key}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.2))
    x = [0, 1]
    width = 0.36
    for phase_idx, phase in enumerate(PHASES):
        offset = -width / 2 if phase_idx == 0 else width / 2
        phase_label = "Development" if phase == "DEVELOPMENT_SEQUENCE" else "Fresh transfer"
        axes[0].bar(
            [value + offset for value in x],
            [f(lookup[(phase, arm)], "success_rate") for arm in ARMS],
            width=width,
            label=phase_label,
        )
        axes[1].bar(
            [value + offset for value in x],
            [f(lookup[(phase, arm)], "mean_score") for arm in ARMS],
            width=width,
        )
        axes[2].bar(
            [value + offset for value in x],
            [f(lookup[(phase, arm)], "repeated_failure_rate") for arm in ARMS],
            width=width,
        )
    for ax, title, ylabel in (
        (axes[0], "Success rate", "Rate"),
        (axes[1], "Registered score", "Mean score"),
        (axes[2], "Repeated structural failure", "Rate"),
    ):
        ax.set_xticks(x, [LABELS[arm] for arm in ARMS], rotation=15, ha="right")
        ax.set_ylim(0, 1)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
    axes[0].legend(frameon=False)
    fig.suptitle("Paper 2 — matched reset versus persistent-experience benchmark")
    fig.tight_layout()
    path = args.out_dir / "paper2_v3_experience_benchmark.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(path)

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.0))
    phase = "FRESH_TRANSFER"
    resource_specs = (
        ("total_model_input_tokens", "Model input tokens"),
        ("total_tool_calls", "Tool calls"),
        ("total_wall_time_ms", "Wall time (ms)"),
    )
    for ax, (field, label) in zip(axes, resource_specs):
        values = [f(lookup[(phase, arm)], field) for arm in ARMS]
        ax.bar(x, values)
        ax.set_xticks(x, [LABELS[arm] for arm in ARMS], rotation=15, ha="right")
        ax.set_ylabel(label)
        ax.set_title(f"Fresh transfer: {label}")
    fig.tight_layout()
    path2 = args.out_dir / "paper2_v3_fresh_transfer_resources.pdf"
    fig.savefig(path2, bbox_inches="tight")
    plt.close(fig)
    print(path2)


if __name__ == "__main__":
    main()
