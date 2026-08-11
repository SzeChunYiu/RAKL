#!/usr/bin/env python3
"""Plot Paper 5 retained-novelty audit metrics without fabricating missing values."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    raise SystemExit("matplotlib is required") from exc

AXIS_LABEL = {
    "KNOWLEDGE": "Knowledge",
    "OPERATOR": "Operator",
    "EXPERIENCE_PATTERN": "Experience pattern",
    "OBSTRUCTION": "Obstruction",
    "RELATION": "Relation",
    "PATH": "Path",
    "META_METHOD": "Meta-method",
    "POOLED": "Pooled",
}
LABEL_ORDER = (
    "SEMANTICALLY_NEW",
    "DUPLICATE_OR_EQUIVALENT",
    "SUPERSESSION_ONLY",
    "WRONG_AXIS",
    "INSUFFICIENT_EVIDENCE",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"no rows in {path}")
    return rows


def maybe_float(value: str) -> float | None:
    if value in ("", "None", "null"):
        return None
    result = float(value)
    return None if math.isnan(result) else result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    metrics = read_csv(args.analysis_dir / "novelty_audit_metrics.csv")
    confusion = read_csv(args.analysis_dir / "annotator_confusion.csv")

    axis_rows = [row for row in metrics if row["axis"] != "POOLED"]
    labels = [AXIS_LABEL[row["axis"]] for row in axis_rows]
    precision = [maybe_float(row["retained_novelty_precision"]) for row in axis_rows]
    false_collapse = [maybe_float(row["false_collapse_rate"]) for row in axis_rows]
    wrong_axis = [maybe_float(row["wrong_axis_rate"]) for row in axis_rows]

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4))
    x = list(range(len(axis_rows)))
    for ax, values, title in (
        (axes[0], precision, "Retained-novelty precision"),
        (axes[1], false_collapse, "False-collapse rate"),
        (axes[2], wrong_axis, "Wrong-axis rate"),
    ):
        heights = [0.0 if value is None else value for value in values]
        bars = ax.bar(x, heights)
        for bar, value in zip(bars, values):
            if value is None:
                ax.text(bar.get_x() + bar.get_width() / 2, 0.02, "NA", ha="center", va="bottom", rotation=90)
        ax.set_xticks(x, labels, rotation=35, ha="right")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Rate")
        ax.set_title(title)
    fig.suptitle("Paper 5 — independent audit of retained structured novelty")
    fig.tight_layout()
    fig.savefig(args.out_dir / "paper5_ext_novelty_audit_rates.pdf", bbox_inches="tight")
    plt.close(fig)

    matrix = {
        (row["annotator_a_label"], row["annotator_b_label"]): int(row["count"])
        for row in confusion
    }
    data = [[matrix.get((a, b), 0) for b in LABEL_ORDER] for a in LABEL_ORDER]
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    image = ax.imshow(data, aspect="auto")
    ax.set_xticks(range(len(LABEL_ORDER)), [item.replace("_", " ").title() for item in LABEL_ORDER], rotation=35, ha="right")
    ax.set_yticks(range(len(LABEL_ORDER)), [item.replace("_", " ").title() for item in LABEL_ORDER])
    ax.set_xlabel("Annotator B")
    ax.set_ylabel("Annotator A")
    ax.set_title("Pre-adjudication annotation agreement matrix")
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Item count")
    fig.tight_layout()
    fig.savefig(args.out_dir / "paper5_ext_novelty_audit_agreement.pdf", bbox_inches="tight")
    plt.close(fig)

    print(args.out_dir / "paper5_ext_novelty_audit_rates.pdf")
    print(args.out_dir / "paper5_ext_novelty_audit_agreement.pdf")


if __name__ == "__main__":
    main()
