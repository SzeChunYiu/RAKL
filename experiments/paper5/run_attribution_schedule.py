#!/usr/bin/env python3
"""Execute a frozen Paper 5 schedule through one frozen external adapter.

This orchestrator is provider-neutral. The execution session must implement and
freeze the environment-specific adapter before outcomes. The adapter interface is:

    <adapter_path> --envelope ENVELOPE.json --raw-output RAW.json \
                   --record-output RECORD.json

The adapter must write RAW.json before RECORD.json and RECORD.json must conform
to ``schemas/paper5-attribution-run-v1.schema.json``. This orchestrator verifies
frozen hashes, schedule identity, evaluation-state non-mutation, resource
ceilings and raw-output hash binding before appending the record to JSONL.

The orchestrator does not know how to call a model and therefore cannot silently
substitute a provider/model when the frozen adapter is unavailable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ARMS = ("MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING")
RESOURCE_FIELDS = (
    "model_input_tokens",
    "model_output_tokens",
    "preprocessing_model_tokens",
    "tool_calls",
    "retrieval_calls",
    "wall_time_ms",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_contract(contract: dict[str, Any], tasks_path: Path, schedule_path: Path, adapter: Path) -> None:
    if contract.get("schema_version") != "paper5-executor-contract-v1":
        raise SystemExit("executor contract schema_version mismatch")
    if sha256_file(tasks_path) != contract.get("tasks_sha256"):
        raise SystemExit("task file hash differs from frozen executor contract")
    if sha256_file(schedule_path) != contract.get("schedule_sha256"):
        raise SystemExit("schedule file hash differs from frozen executor contract")
    if not adapter.is_file():
        raise SystemExit(f"frozen adapter missing: {adapter}")
    if sha256_file(adapter) != contract.get("adapter_sha256"):
        raise SystemExit("adapter bytes differ from frozen executor contract")
    states = contract.get("arm_state_hashes", {})
    if set(states) != set(ARMS) or any(not states[arm] for arm in ARMS):
        raise SystemExit("executor contract must bind one non-empty state identity per arm")
    ceiling = contract.get("resource_ceiling", {})
    if set(RESOURCE_FIELDS) - set(ceiling):
        raise SystemExit("executor contract resource ceiling is incomplete")
    if any(int(ceiling[field]) < 0 for field in RESOURCE_FIELDS):
        raise SystemExit("negative resource ceiling")


def validate_schedule(tasks: dict[str, Any], schedule: dict[str, Any], contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    task_rows = tasks.get("tasks")
    run_rows = schedule.get("runs")
    if not isinstance(task_rows, list) or not isinstance(run_rows, list):
        raise SystemExit("task/schedule files have invalid structure")
    by_task = {row.get("task_id"): row for row in task_rows if isinstance(row, dict)}
    if len(by_task) != len(task_rows) or None in by_task:
        raise SystemExit("task IDs are missing or duplicated")
    if schedule.get("packet_id") != contract.get("packet_id") or tasks.get("packet_id") != contract.get("packet_id"):
        raise SystemExit("packet identity mismatch across tasks/schedule/contract")
    run_ids = [row.get("run_id") for row in run_rows]
    if any(not value for value in run_ids) or len(run_ids) != len(set(run_ids)):
        raise SystemExit("schedule run IDs are missing or duplicated")
    for row in run_rows:
        if row.get("task_id") not in by_task or row.get("arm") not in ARMS:
            raise SystemExit(f"invalid schedule row: {row.get('run_id')}")
    return by_task


def validate_record(record: dict[str, Any], schedule_row: dict[str, Any], contract: dict[str, Any], raw_path: Path) -> None:
    for field in ("run_id", "task_id", "repetition", "arm"):
        if record.get(field) != schedule_row.get(field):
            raise SystemExit(f"{schedule_row['run_id']}: adapter record changed frozen {field}")
    if record.get("arm") not in ARMS:
        raise SystemExit("record arm invalid")
    score = float(record.get("score", -1))
    if not 0.0 <= score <= 1.0 or not isinstance(record.get("success"), bool):
        raise SystemExit(f"{schedule_row['run_id']}: invalid score/success")
    expected_state = contract["arm_state_hashes"][record["arm"]]
    if record.get("state_before_hash") != expected_state or record.get("state_after_hash") != expected_state:
        raise SystemExit(f"{schedule_row['run_id']}: evaluation state mutated or wrong state used")
    if not raw_path.is_file() or raw_path.stat().st_size == 0:
        raise SystemExit(f"{schedule_row['run_id']}: raw output missing/empty")
    if record.get("output_hash") != sha256_file(raw_path):
        raise SystemExit(f"{schedule_row['run_id']}: output_hash does not bind raw output bytes")
    if not isinstance(record.get("validity_failures"), list) or not isinstance(record.get("failure_signature"), list):
        raise SystemExit(f"{schedule_row['run_id']}: validity/failure fields must be lists")
    if not record["success"] and not record["failure_signature"]:
        raise SystemExit(f"{schedule_row['run_id']}: failed run requires failure_signature")
    ceiling = contract["resource_ceiling"]
    for field in RESOURCE_FIELDS:
        value = int(record.get(field, -1))
        if value < 0:
            raise SystemExit(f"{schedule_row['run_id']}: missing/negative resource {field}")
        if value > int(ceiling[field]):
            raise SystemExit(f"{schedule_row['run_id']}: resource ceiling exceeded:{field}:{value}>{ceiling[field]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--results-jsonl", required=True, type=Path)
    parser.add_argument("--start-sequence", type=int, default=1)
    parser.add_argument("--stop-sequence", type=int)
    args = parser.parse_args()

    tasks = load(args.tasks)
    schedule = load(args.schedule)
    contract = load(args.contract)
    adapter = Path(contract["adapter_path"]).expanduser().resolve()
    validate_contract(contract, args.tasks, args.schedule, adapter)
    by_task = validate_schedule(tasks, schedule, contract)

    run_rows = sorted(schedule["runs"], key=lambda row: int(row["sequence"]))
    selected = [
        row for row in run_rows
        if int(row["sequence"]) >= args.start_sequence
        and (args.stop_sequence is None or int(row["sequence"]) <= args.stop_sequence)
    ]
    if not selected:
        raise SystemExit("no schedule rows selected")

    args.run_root.mkdir(parents=True, exist_ok=True)
    args.results_jsonl.parent.mkdir(parents=True, exist_ok=True)
    completed: set[str] = set()
    if args.results_jsonl.exists():
        for line in args.results_jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                completed.add(json.loads(line)["run_id"])

    for row in selected:
        run_id = row["run_id"]
        if run_id in completed:
            raise SystemExit(f"refusing to overwrite/re-execute already recorded run: {run_id}")
        run_dir = args.run_root / f"{int(row['sequence']):05d}-{run_id}"
        if run_dir.exists():
            raise SystemExit(f"run directory already exists: {run_dir}")
        run_dir.mkdir(parents=True)
        envelope = {
            "schema_version": "paper5-run-envelope-v1",
            "packet_id": contract["packet_id"],
            "schedule_row": row,
            "task": by_task[row["task_id"]],
            "expected_state_hash": contract["arm_state_hashes"][row["arm"]],
            "model_id": contract["model_id"],
            "model_revision": contract["model_revision"],
            "evaluator_protocol_hash": contract["evaluator_protocol_hash"],
            "tool_policy_id": contract["tool_policy_id"],
            "source_cutoff_id": contract["source_cutoff_id"],
            "resource_ceiling": contract["resource_ceiling"],
            "task_file_sha256": contract["tasks_sha256"],
            "schedule_file_sha256": contract["schedule_sha256"],
            "adapter_sha256": contract["adapter_sha256"],
        }
        envelope_path = run_dir / "envelope.json"
        raw_path = run_dir / "raw_output.json"
        record_path = run_dir / "record.json"
        atomic_json(envelope_path, envelope)

        command = [
            sys.executable,
            str(adapter),
            "--envelope",
            str(envelope_path),
            "--raw-output",
            str(raw_path),
            "--record-output",
            str(record_path),
        ]
        proc = subprocess.run(command, cwd=adapter.parent)
        if proc.returncode != 0:
            raise SystemExit(f"adapter failed for {run_id} with exit code {proc.returncode}")
        if not record_path.is_file():
            raise SystemExit(f"adapter did not write record: {record_path}")
        record = load(record_path)
        validate_record(record, row, contract, raw_path)
        with args.results_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        completed.add(run_id)
        print(f"RECORDED {row['sequence']} {run_id}")


if __name__ == "__main__":
    main()
