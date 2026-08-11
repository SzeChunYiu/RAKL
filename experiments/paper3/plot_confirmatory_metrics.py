#!/usr/bin/env python3
"""Plot Paper 3 confirmatory structural-vs-control metrics from a gate receipt.

This script consumes the machine-readable receipt emitted by
``src/rakl/paper3_confirmatory_gate.py`` after independent annotation has passed.
It never upgrades a failed/NOT_RUN receipt into a result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit("matplotlib is required") from exc


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("gate receipt must be a JSON object")
    return value


def metric(metrics: dict[str, Any], key: str) -> float:
    if key not in metrics:
        raise SystemExit(f"gate receipt arm metrics missing {key}")
    return float(metrics[key])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    receipt = load(args.receipt)
    gate = receipt.get("diagnostic_signal_gate", {})
    if gate.get("status") != "RUN":
        raise SystemExit(f"diagnostic signal gate was not run: verdict={receipt.get('gate_verdict')}")
    arm_metrics = receipt.get("arm_metrics", {})
    if "witnessed_structure" not in arm_metrics:
        raise SystemExit("receipt has no witnessed_structure arm")
    control_name = gate.get("strongest_control")
    if not control_name or control_name not in arm_metrics:
        raise SystemExit("receipt does not identify a valid strongest control")

    control = arm_metrics[control_name]
    structural = arm_metrics["witnessed_structure"]
    labels = [control_name.replace("_", " ").title(), "Witnessed structure"]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.2))
    axes[0].bar([0, 1], [metric(control, "roc_auc"), metric(structural, "roc_auc")])
    axes[0].set_xticks([0, 1], labels, rotation=20, ha="right")
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("ROC-AUC")
    axes[0].set_title("Discrimination")

    axes[1].bar([0, 1], [metric(control, "average_precision"), metric(structural, "average_precision")])
    axes[1].set_xticks([0, 1], labels, rotation=20, ha="right")
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel("Average precision")
    axes[1].set_title("Precision–recall")

    q2 = metric(structural, "q2_true_accept")
    q3 = metric(structural, "q3_false_accept")
    axes[2].bar([0, 1], [q2, q3])
    axes[2].set_xticks([0, 1], ["Q2 true accept", "Q3 false accept"], rotation=20, ha="right")
    axes[2].set_ylim(0, 1)
    axes[2].set_ylabel("Rate")
    axes[2].set_title("Load-bearing transfer cells")

    fig.suptitle("Paper 3 — independently annotated confirmatory gate")
    fig.tight_layout()
    primary = args.out_dir / "paper3_confirmatory_signal.pdf"
    fig.savefig(primary, bbox_inches="tight")
    plt.close(fig)

    if "brier" in control and "brier" in structural:
        fig, ax = plt.subplots(figsize=(6.4, 4.2))
        names = ["Brier"]
        control_values = [float(control["brier"])]
        structural_values = [float(structural["brier"])]
        if "log_loss" in control and "log_loss" in structural:
            names.append("Log loss")
            control_values.append(float(control["log_loss"]))
            structural_values.append(float(structural["log_loss"]))
        x = list(range(len(names)))
        width = 0.36
        ax.bar([v - width / 2 for v in x], control_values, width=width, label=labels[0])
        ax.bar([v + width / 2 for v in x], structural_values, width=width, label=labels[1])
        ax.set_xticks(x, names)
        ax.set_ylabel("Loss (lower is better)")
        ax.set_title("Paper 3 — calibration / probabilistic loss")
        ax.legend(frameon=False)
        fig.tight_layout()
        secondary = args.out_dir / "paper3_confirmatory_calibration.pdf"
        fig.savefig(secondary, bbox_inches="tight")
        plt.close(fig)
        print(secondary)

    print(primary)


if __name__ == "__main__":
    main()
