#!/usr/bin/env python3
"""Plot Paper 5 longitudinal RAKL metrology from real cycle-metric records.

Input is JSONL, one chronological RAKL cycle per line. Required fields:

  cycle_id: string
  retained_novelty: mapping with all seven novelty-axis *delta* counts

Recommended fields used for additional figures when present in every record:
  method_version
  episode_count
  diagnosis_or_lesson_candidate_count
  validated_lesson_count
  reusable_tool_or_motif_count
  successful_fresh_reuse_count
  contradicted_or_failed_transfer_count
  repeated_failure_rate
  saturated_route_retry_rate
  route_switch_latency
  memory_changed_action_rate

The script refuses to invent missing values. Figure 2 is always available from the
seven-axis deltas; Figures 3/4 are emitted only when their registered fields are
complete.
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

AXES = (
    "KNOWLEDGE",
    "OPERATOR",
    "EXPERIENCE_PATTERN",
    "OBSTRUCTION",
    "RELATION",
    "PATH",
    "META_METHOD",
)
AXIS_LABELS = {
    "KNOWLEDGE": "Knowledge",
    "OPERATOR": "Operator",
    "EXPERIENCE_PATTERN": "Experience pattern",
    "OBSTRUCTION": "Obstruction",
    "RELATION": "Relation",
    "PATH": "Path",
    "META_METHOD": "Meta-method",
}
FUNNEL_FIELDS = (
    ("episode_count", "Task episodes"),
    ("diagnosis_or_lesson_candidate_count", "Diagnosis / lesson candidates"),
    ("validated_lesson_count", "Validated lessons"),
    ("reusable_tool_or_motif_count", "Reusable tools / motifs"),
    ("successful_fresh_reuse_count", "Successful fresh reuses"),
)
DYNAMICS_FIELDS = (
    ("repeated_failure_rate", "Repeated structural failure rate"),
    ("saturated_route_retry_rate", "Saturated-route retry rate"),
    ("route_switch_latency", "Route-switch latency"),
    ("memory_changed_action_rate", "Experience changed action rate"),
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{lineno}: expected object")
        rows.append(row)
    if not rows:
        raise SystemExit("cycle metrics file is empty")
    return rows


def validate(rows: list[dict[str, Any]]) -> None:
    ids = [row.get("cycle_id") for row in rows]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise SystemExit("cycle_id values must be non-empty and unique")
    for row in rows:
        novelty = row.get("retained_novelty")
        if not isinstance(novelty, dict):
            raise SystemExit(f"{row['cycle_id']}: retained_novelty mapping required")
        if set(novelty) != set(AXES):
            raise SystemExit(f"{row['cycle_id']}: retained_novelty must contain exactly the seven registered axes")
        if any(int(novelty[axis]) < 0 for axis in AXES):
            raise SystemExit(f"{row['cycle_id']}: retained novelty deltas cannot be negative")


def version_boundaries(rows: list[dict[str, Any]]) -> list[tuple[int, str]]:
    boundaries: list[tuple[int, str]] = []
    previous = None
    for index, row in enumerate(rows):
        version = row.get("method_version")
        if version and version != previous:
            boundaries.append((index, str(version)))
            previous = version
    return boundaries


def annotate_versions(ax: Any, rows: list[dict[str, Any]]) -> None:
    for index, version in version_boundaries(rows):
        ax.axvline(index, linewidth=0.8, linestyle="--")
        ax.text(index, 0.98, version, transform=ax.get_xaxis_transform(), rotation=90, va="top", ha="right", fontsize=7)


def plot_growth(rows: list[dict[str, Any]], out_dir: Path) -> None:
    cumulative = {axis: [] for axis in AXES}
    totals = {axis: 0 for axis in AXES}
    for row in rows:
        for axis in AXES:
            totals[axis] += int(row["retained_novelty"][axis])
            cumulative[axis].append(totals[axis])

    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    x = list(range(len(rows)))
    for axis in AXES:
        ax.plot(x, cumulative[axis], marker="o", markersize=2.5, linewidth=1.2, label=AXIS_LABELS[axis])
    annotate_versions(ax, rows)
    ax.set_xticks(x, [row["cycle_id"] for row in rows], rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("Cumulative retained novelty events")
    ax.set_xlabel("Chronological RAKL cycle")
    ax.set_title("Seven-axis retained structured-state growth — INTERNAL_METROLOGY until independent audit passes")
    ax.legend(frameon=False, ncol=2, fontsize=8)
    fig.tight_layout()
    path = out_dir / "paper5_fig2_retained_growth.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(path)


def complete(rows: list[dict[str, Any]], fields: tuple[tuple[str, str], ...]) -> bool:
    return all(all(field in row and row[field] is not None for field, _ in fields) for row in rows)


def plot_funnel(rows: list[dict[str, Any]], out_dir: Path) -> None:
    if not complete(rows, FUNNEL_FIELDS):
        print("SKIP paper5_fig3_experience_conversion.pdf: incomplete funnel fields")
        return
    latest = rows[-1]
    labels = [label for _, label in FUNNEL_FIELDS]
    values = [float(latest[field]) for field, _ in FUNNEL_FIELDS]
    contradicted = float(latest.get("contradicted_or_failed_transfer_count", 0))

    fig, ax = plt.subplots(figsize=(9.2, 4.7))
    x = list(range(len(values)))
    ax.bar(x, values)
    ax.set_xticks(x, labels, rotation=24, ha="right")
    ax.set_ylabel("Cumulative count")
    ax.set_title(f"Experience-to-method conversion at {latest['cycle_id']}")
    if "contradicted_or_failed_transfer_count" in latest:
        ax.text(0.99, 0.96, f"Contradicted/failed-transfer branch retained: {contradicted:g}", transform=ax.transAxes, ha="right", va="top")
    fig.tight_layout()
    path = out_dir / "paper5_fig3_experience_conversion.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(path)


def plot_dynamics(rows: list[dict[str, Any]], out_dir: Path) -> None:
    if not complete(rows, DYNAMICS_FIELDS):
        print("SKIP paper5_fig4_routing_failure_dynamics.pdf: incomplete dynamics fields")
        return
    x = list(range(len(rows)))
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2))
    for ax, (field, label) in zip(axes.flat, DYNAMICS_FIELDS):
        values = [float(row[field]) for row in rows]
        ax.plot(x, values, marker="o", markersize=3)
        annotate_versions(ax, rows)
        ax.set_xticks(x, [row["cycle_id"] for row in rows], rotation=60, ha="right", fontsize=6)
        ax.set_ylabel(label)
        ax.set_title(label)
    fig.suptitle("Repeated-failure and routing dynamics")
    fig.tight_layout()
    path = out_dir / "paper5_fig4_routing_failure_dynamics.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle-metrics", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    rows = load_jsonl(args.cycle_metrics)
    validate(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plot_growth(rows, args.out_dir)
    plot_funnel(rows, args.out_dir)
    plot_dynamics(rows, args.out_dir)


if __name__ == "__main__":
    main()
