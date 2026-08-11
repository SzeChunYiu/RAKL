#!/usr/bin/env python3
"""Analyze the RAKL v3 RESET_BASELINE vs LEARNING_ENABLED benchmark.

This is a lightweight result-side companion to ``src/rakl/experience_benchmark.py``.
The execution packet should still be validated by the canonical library before
this script is used for publication figures.

Packet JSON required fields:
  initial_state_hash
  learned_state_after_development_hash
  development_task_ids: list[str]
  transfer_task_ids: list[str]

Run JSONL required fields:
  run_id, task_id, arm, phase, state_before_hash, state_after_hash,
  success, score, failure_signature,
  model_input_tokens, model_output_tokens, preprocessing_model_tokens,
  tool_calls, retrieval_calls, wall_time_ms
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

ARMS = ("RESET_BASELINE", "LEARNING_ENABLED")
PHASES = ("DEVELOPMENT_SEQUENCE", "FRESH_TRANSFER")
RESOURCE_FIELDS = (
    "model_input_tokens",
    "model_output_tokens",
    "preprocessing_model_tokens",
    "tool_calls",
    "retrieval_calls",
    "wall_time_ms",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise SystemExit(f"{path}:{lineno}: expected JSON object")
        rows.append(value)
    return rows


def m(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def validate(packet: dict[str, Any], runs: list[dict[str, Any]]) -> None:
    development = tuple(packet.get("development_task_ids", []))
    transfer = tuple(packet.get("transfer_task_ids", []))
    if not development or not transfer or set(development) & set(transfer):
        raise SystemExit("packet must bind disjoint non-empty development and transfer task IDs")
    initial = packet.get("initial_state_hash")
    learned = packet.get("learned_state_after_development_hash")
    if not initial or not learned:
        raise SystemExit("packet missing initial/learned state hashes")
    if len({row.get("run_id") for row in runs}) != len(runs):
        raise SystemExit("run_id values must be unique")

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in runs:
        arm = row.get("arm")
        phase = row.get("phase")
        task = row.get("task_id")
        if arm not in ARMS or phase not in PHASES:
            raise SystemExit(f"{row.get('run_id')}: invalid arm/phase")
        expected_tasks = development if phase == "DEVELOPMENT_SEQUENCE" else transfer
        if task not in expected_tasks:
            raise SystemExit(f"{row.get('run_id')}: task is not registered for phase")
        score = float(row.get("score", -1))
        if not 0 <= score <= 1:
            raise SystemExit(f"{row.get('run_id')}: score outside [0,1]")
        for field in RESOURCE_FIELDS:
            if float(row.get(field, -1)) < 0:
                raise SystemExit(f"{row.get('run_id')}: missing/negative {field}")
        if not row.get("success") and not row.get("failure_signature"):
            raise SystemExit(f"{row.get('run_id')}: failed run lacks failure signature")

        before = row.get("state_before_hash")
        after = row.get("state_after_hash")
        if arm == "RESET_BASELINE":
            if before != initial or after != initial:
                raise SystemExit(f"{row.get('run_id')}: reset baseline state mutation/leakage")
        elif phase == "FRESH_TRANSFER":
            if before != learned:
                raise SystemExit(f"{row.get('run_id')}: fresh transfer did not start from frozen learned state")
        grouped[(task, arm)].append(row)

    for task in development + transfer:
        for arm in ARMS:
            if len(grouped[(task, arm)]) != 1:
                raise SystemExit(f"{task}/{arm}: expected exactly one run")

    # Learning development chronology must be one uninterrupted chain.
    previous = initial
    by_task_arm = {(row["task_id"], row["arm"]): row for row in runs}
    for task in development:
        row = by_task_arm[(task, "LEARNING_ENABLED")]
        if row["state_before_hash"] != previous:
            raise SystemExit(f"{task}: learning development chronology break")
        previous = row["state_after_hash"]
    if previous != learned:
        raise SystemExit("final development state does not equal registered learned state")


def repeated_failure_rate(rows: list[dict[str, Any]]) -> float:
    seen: set[tuple[str, ...]] = set()
    repeat = total_fail = 0
    for row in rows:
        if row["success"]:
            continue
        total_fail += 1
        signature = tuple(row.get("failure_signature", []))
        if signature in seen:
            repeat += 1
        seen.add(signature)
    return repeat / total_fail if total_fail else 0.0


def metrics(packet: dict[str, Any], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task_orders = {
        "DEVELOPMENT_SEQUENCE": packet["development_task_ids"],
        "FRESH_TRANSFER": packet["transfer_task_ids"],
    }
    lookup = {(row["task_id"], row["arm"]): row for row in runs}
    out = []
    for phase in PHASES:
        for arm in ARMS:
            rows = [lookup[(task, arm)] for task in task_orders[phase]]
            item = {
                "phase": phase,
                "arm": arm,
                "task_count": len(rows),
                "success_rate": m([float(row["success"]) for row in rows]),
                "mean_score": m([float(row["score"]) for row in rows]),
                "repeated_failure_rate": repeated_failure_rate(rows),
            }
            for field in RESOURCE_FIELDS:
                item[f"total_{field}"] = sum(float(row[field]) for row in rows)
            out.append(item)
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    runs = load_jsonl(args.runs)
    validate(packet, runs)
    result = metrics(packet, runs)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "paper2_v3_metrics.csv", result)

    by = {(row["phase"], row["arm"]): row for row in result}
    development_reset = by[("DEVELOPMENT_SEQUENCE", "RESET_BASELINE")]
    development_learning = by[("DEVELOPMENT_SEQUENCE", "LEARNING_ENABLED")]
    transfer_reset = by[("FRESH_TRANSFER", "RESET_BASELINE")]
    transfer_learning = by[("FRESH_TRANSFER", "LEARNING_ENABLED")]
    summary = {
        "schema_version": "paper2-v3-experience-analysis-v1",
        "packet_sha256": hashlib.sha256(args.packet.read_bytes()).hexdigest(),
        "runs_sha256": hashlib.sha256(args.runs.read_bytes()).hexdigest(),
        "metrics": result,
        "development_success_delta": development_learning["success_rate"] - development_reset["success_rate"],
        "development_score_delta": development_learning["mean_score"] - development_reset["mean_score"],
        "transfer_success_delta": transfer_learning["success_rate"] - transfer_reset["success_rate"],
        "transfer_score_delta": transfer_learning["mean_score"] - transfer_reset["mean_score"],
        "transfer_repeat_failure_delta": transfer_learning["repeated_failure_rate"] - transfer_reset["repeated_failure_rate"],
        "grants_global_capability_claim": False,
    }
    (args.out_dir / "paper2_v3_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out_dir / "paper2_v3_summary.json")


if __name__ == "__main__":
    main()
