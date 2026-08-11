#!/usr/bin/env python3
"""Build the frozen task/arm/repetition execution order for Paper 5.

This script does not execute a model and does not inspect outcomes.  It only
turns an already frozen task list into a deterministic block-randomized schedule
for the four preregistered attribution arms.

Input JSON shape::

    {
      "packet_id": "...",
      "tasks": [
        {"task_id": "T001", "stratum": "REPEATED_FAMILY"},
        ...
      ]
    }

The task payload may contain additional fields; they are preserved only through
its content hash and are not copied into the schedule.  The final confirmatory
packet must separately bind the task/evaluator/model/resource/sham/state hashes
before any evaluated output is opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

ARMS = (
    "MODEL_ONLY",
    "RAKL_RESET",
    "RAKL_SHAM_MEMORY",
    "RAKL_LEARNING",
)
STRATA = (
    "REPEATED_FAMILY",
    "CROSS_DOMAIN_TRANSFER",
    "HOSTILE_NEAR_MISS",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_tasks(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
        raise SystemExit("task file must be a JSON object with a tasks list")
    return payload


def validate_tasks(tasks: list[dict[str, Any]], expected_tasks: int | None) -> None:
    ids = [str(item.get("task_id", "")) for item in tasks]
    if any(not task_id for task_id in ids):
        raise SystemExit("every task needs a non-empty task_id")
    if len(ids) != len(set(ids)):
        raise SystemExit("task_id values must be unique")
    if expected_tasks is not None and len(tasks) != expected_tasks:
        raise SystemExit(f"expected {expected_tasks} tasks, found {len(tasks)}")

    invalid = sorted({str(item.get("stratum", "")) for item in tasks} - set(STRATA))
    if invalid:
        raise SystemExit(f"invalid/missing task strata: {invalid}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--expected-tasks", type=int, default=120)
    parser.add_argument(
        "--allow-nonstandard-task-count",
        action="store_true",
        help="permit a development/dry-run packet smaller than the preregistered 120-task target",
    )
    args = parser.parse_args()

    if args.repetitions < 1:
        raise SystemExit("repetitions must be >= 1")

    payload = load_tasks(args.tasks)
    tasks = payload["tasks"]
    expected = None if args.allow_nonstandard_task_count else args.expected_tasks
    validate_tasks(tasks, expected)

    rng = random.Random(args.seed)
    blocks: list[dict[str, Any]] = []
    sequence = 0
    for task in tasks:
        for repetition in range(1, args.repetitions + 1):
            order = list(ARMS)
            rng.shuffle(order)
            for position, arm in enumerate(order, start=1):
                sequence += 1
                blocks.append(
                    {
                        "sequence": sequence,
                        "task_id": task["task_id"],
                        "stratum": task["stratum"],
                        "repetition": repetition,
                        "arm_order_position": position,
                        "arm": arm,
                        "run_id": f"{task['task_id']}-r{repetition}-{arm}",
                    }
                )

    stratum_counts = {
        stratum: sum(1 for item in tasks if item["stratum"] == stratum)
        for stratum in STRATA
    }
    schedule_core = {
        "schema_version": "paper5-attribution-schedule-v1",
        "packet_id": payload.get("packet_id", ""),
        "task_file_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
        "task_payload_canonical_sha256": sha256_json(payload),
        "randomization_seed": args.seed,
        "repetitions": args.repetitions,
        "arms": list(ARMS),
        "task_count": len(tasks),
        "stratum_counts": stratum_counts,
        "run_count": len(blocks),
        "runs": blocks,
    }
    schedule = {
        **schedule_core,
        "schedule_core_sha256": sha256_json(schedule_core),
        "claim_boundary": (
            "Execution-order artifact only. It contains no outcomes and grants no empirical or promotion claim."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(schedule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)
    print(schedule["schedule_core_sha256"])


if __name__ == "__main__":
    main()
