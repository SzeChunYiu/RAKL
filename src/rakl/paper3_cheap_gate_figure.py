from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def generate_cheap_gate_figure(
    *, receipt: dict[str, Any], output_prefix: Path
) -> tuple[Path, Path, Path]:
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    arm_order = [
        "semantic_calibrated",
        "skill_aware",
        "dependency_aware",
        "witnessed_structure",
    ]
    labels = ["Semantic", "Skill-aware", "Dependency-aware", "Witnessed structure"]
    metrics = receipt["arm_metrics"]
    positions = np.arange(len(arm_order))
    width = 0.36
    colors = ("#4C78A8", "#F58518")
    figure, axes = plt.subplots(1, 3, figsize=(7.2, 2.45), constrained_layout=True)

    axes[0].bar(
        positions - width / 2,
        [metrics[arm]["roc_auc"] for arm in arm_order],
        width,
        color=colors[0],
        label="ROC-AUC",
    )
    axes[0].bar(
        positions + width / 2,
        [metrics[arm]["average_precision"] for arm in arm_order],
        width,
        color=colors[1],
        label="Average precision",
    )
    axes[0].set_title("a   Held-out discrimination", loc="left", pad=8, fontweight="bold")
    axes[0].set_ylabel("Score")
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(frameon=False, loc="lower right")

    axes[1].bar(
        positions - width / 2,
        [metrics[arm]["brier"] for arm in arm_order],
        width,
        color=colors[0],
        label="Brier",
    )
    axes[1].bar(
        positions + width / 2,
        [metrics[arm]["log_loss"] for arm in arm_order],
        width,
        color=colors[1],
        label="Log loss",
    )
    axes[1].set_title("b   Probabilistic error", loc="left", pad=8, fontweight="bold")
    axes[1].set_ylabel("Loss (lower is better)")
    axes[1].legend(frameon=False, loc="upper right")

    axes[2].bar(
        positions - width / 2,
        [metrics[arm]["q2_true_accept"] for arm in arm_order],
        width,
        color=colors[0],
        label="Q2 true accept",
    )
    axes[2].bar(
        positions + width / 2,
        [metrics[arm]["q3_false_accept"] for arm in arm_order],
        width,
        color=colors[1],
        label="Q3 false accept",
    )
    axes[2].set_title("c   Transfer safety", loc="left", pad=8, fontweight="bold")
    axes[2].set_ylabel("Rate")
    axes[2].set_ylim(0, 1.05)
    axes[2].legend(frameon=False, loc="center right")

    for axis in axes:
        axis.set_xticks(positions, labels, rotation=35, ha="right")
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(axis="x", length=0)

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    outputs = tuple(output_prefix.with_suffix(suffix) for suffix in (".pdf", ".svg", ".png"))
    figure.savefig(outputs[0], bbox_inches="tight")
    figure.savefig(outputs[1], bbox_inches="tight")
    figure.savefig(outputs[2], dpi=220, bbox_inches="tight")
    plt.close(figure)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    for output in generate_cheap_gate_figure(receipt=receipt, output_prefix=args.output_prefix):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
