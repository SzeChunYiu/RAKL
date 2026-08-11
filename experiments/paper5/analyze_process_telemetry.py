#!/usr/bin/env python3
"""Aggregate Paper 5 process telemetry into the Figure-7 dashboard table.

Input: JSONL records conforming to ``schemas/process-telemetry.schema.json``.
The script performs lightweight structural checks in addition to any JSON-schema
validation performed by the execution harness. Heterogeneous cost-policy IDs are
reported and make ``costs_comparable`` false; costs are never silently pooled as
if they shared one unit definition.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

OUTCOMES = ("SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "BLOCKED", "CANNOT_CHECK")
AXES = (
    "KNOWLEDGE",
    "OPERATOR",
    "EXPERIENCE_PATTERN",
    "OBSTRUCTION",
    "RELATION",
    "PATH",
    "META_METHOD",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise SystemExit(f"{path}:{lineno}: expected JSON object")
        rows.append(value)
    if not rows:
        raise SystemExit("process telemetry is empty")
    return rows


def validate(rows: list[dict[str, Any]]) -> None:
    ids = [row.get("invocation_id") for row in rows]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise SystemExit("invocation_id values must be non-empty and unique")
    for row in rows:
        rid = row["invocation_id"]
        if not row.get("process_surface") or not row.get("task_id"):
            raise SystemExit(f"{rid}: process_surface/task_id required")
        if row.get("outcome") not in OUTCOMES:
            raise SystemExit(f"{rid}: invalid outcome")
        if row.get("authority_scope") != "MEASUREMENT_ONLY":
            raise SystemExit(f"{rid}: authority_scope must be MEASUREMENT_ONLY")
        if float(row.get("cost", -1)) < 0 or not row.get("cost_policy_id"):
            raise SystemExit(f"{rid}: invalid cost/cost_policy_id")
        novelty = row.get("retained_novelty")
        if not isinstance(novelty, dict):
            raise SystemExit(f"{rid}: retained_novelty mapping required")
        if any(int(novelty.get(axis, 0)) < 0 for axis in AXES):
            raise SystemExit(f"{rid}: retained novelty cannot be negative")
        for field in ("residual_before", "residual_after", "retrieved_ids", "selected_ids", "rejected_ids"):
            if not isinstance(row.get(field), list):
                raise SystemExit(f"{rid}: {field} must be a list")


def rate(num: int, den: int) -> float:
    return num / den if den else 0.0


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["process_surface"]].append(row)

    result: list[dict[str, Any]] = []
    for surface in sorted(grouped):
        items = grouped[surface]
        n = len(items)
        outcome_counts = {name: sum(row["outcome"] == name for row in items) for name in OUTCOMES}
        policy_ids = sorted({row["cost_policy_id"] for row in items})
        novelty = {axis: sum(int(row["retained_novelty"].get(axis, 0)) for row in items) for axis in AXES}
        retained_total = sum(novelty.values())
        contractions = [len(row["residual_before"]) - len(row["residual_after"]) for row in items]
        retrieved = sum(len(row["retrieved_ids"]) for row in items)
        selected = sum(len(row["selected_ids"]) for row in items)
        rejected = sum(len(row["rejected_ids"]) for row in items)
        row_out: dict[str, Any] = {
            "process_surface": surface,
            "invocation_count": n,
            "valid_completion_rate": rate(outcome_counts["SUCCESS"] + outcome_counts["PARTIAL_SUCCESS"], n),
            "failure_rate": rate(outcome_counts["FAILURE"], n),
            "blocked_rate": rate(outcome_counts["BLOCKED"], n),
            "cannot_check_rate": rate(outcome_counts["CANNOT_CHECK"], n),
            "mean_cost": statistics.fmean(float(row["cost"]) for row in items),
            "cost_policy_ids": ";".join(policy_ids),
            "costs_comparable": len(policy_ids) <= 1,
            "mean_raw_residual_contraction": statistics.fmean(contractions),
            "retained_novelty_total": retained_total,
            "retained_novelty_per_invocation": retained_total / n,
            "retrieved_object_count": retrieved,
            "selected_object_count": selected,
            "rejected_object_count": rejected,
            "selection_rate_given_retrieval": selected / retrieved if retrieved else 0.0,
        }
        for axis in AXES:
            row_out[f"novelty_{axis}"] = novelty[axis]
        result.append(row_out)
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telemetry", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    rows = load_jsonl(args.telemetry)
    validate(rows)
    aggregates = aggregate(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "process_dashboard.csv", aggregates)
    summary = {
        "schema_version": "paper5-process-telemetry-analysis-v1",
        "telemetry_sha256": hashlib.sha256(args.telemetry.read_bytes()).hexdigest(),
        "invocation_count": len(rows),
        "process_surface_count": len(aggregates),
        "all_costs_comparable_within_surface": all(row["costs_comparable"] for row in aggregates),
        "aggregates": aggregates,
        "claim_boundary": "Process measurement only; no process metric grants scientific or promotion authority.",
    }
    (args.out_dir / "process_dashboard_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.out_dir / "process_dashboard.csv")


if __name__ == "__main__":
    main()
