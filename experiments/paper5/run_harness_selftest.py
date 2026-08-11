#!/usr/bin/env python3
"""Drive one end-to-end Paper 5 harness self-test and emit a receipt.

Chains the real production path -- schedule builder, executor contract builder,
orchestrator, analyzer -- against ``selftest_adapter.py`` instead of a model, so
the pipeline is exercised exactly as a confirmatory run would exercise it.

The point is to check the *instrument* before trusting it with a real packet:

* ``NULL_CONSTANT`` must yield paired deltas of exactly 0.0 on every contrast;
* ``NULL_NOISE`` must yield intervals covering 0 despite non-zero realized deltas;
* ``PLANTED_LIFT`` must recover the planted ``+0.20`` on the three contrasts that
  involve ``RAKL_LEARNING``, and must **not** produce it on ``ARCHITECTURE``
  (``RAKL_RESET`` vs ``MODEL_ONLY``), neither of which carries the offset.

The third mode is what makes the first two meaningful. A pipeline hard-wired to
report nothing would pass the two null modes perfectly.

Output is synthetic. Nothing produced here is a Paper 5 attribution result, and
the analyzer stamps every summary accordingly.

Example::

    python experiments/paper5/run_harness_selftest.py \
        --mode PLANTED_LIFT --out-root /tmp/paper5-selftest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

MODES = ("NULL_CONSTANT", "NULL_NOISE", "PLANTED_LIFT")
STRATA = ("REPEATED_FAMILY", "CROSS_DOMAIN_TRANSFER", "HOSTILE_NEAR_MISS")
ARMS = ("MODEL_ONLY", "RAKL_RESET", "RAKL_SHAM_MEMORY", "RAKL_LEARNING")

CEILING = {
    "model_input_tokens": 100000,
    "model_output_tokens": 100000,
    "preprocessing_model_tokens": 100000,
    "tool_calls": 100,
    "retrieval_calls": 100,
    "wall_time_ms": 600000,
}


def run(command: list[str]) -> None:
    proc = subprocess.run(command, cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit(f"step failed ({proc.returncode}): {' '.join(command)}")


def write_tasks(path: Path, packet_id: str, per_stratum: int) -> None:
    tasks: list[dict[str, Any]] = []
    index = 0
    for stratum in STRATA:
        for _ in range(per_stratum):
            index += 1
            tasks.append({"task_id": f"S{index:03d}", "stratum": stratum})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"packet_id": packet_id, "tasks": tasks}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def synthetic_state_hash(mode: str, arm: str) -> str:
    """A distinct frozen state identity per arm.

    There is no real RAKL state behind these: the adapter calls no model. They
    exist so the orchestrator's per-arm state-identity and non-mutation checks
    are genuinely exercised rather than bypassed.
    """
    return hashlib.sha256(f"paper5-selftest-state|{mode}|{arm}".encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--out-root", required=True, type=Path)
    parser.add_argument("--tasks-per-stratum", type=int, default=4)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260811)
    args = parser.parse_args()

    packet_id = f"paper5-harness-selftest-{args.mode}"
    out = args.out_root / args.mode
    if out.exists():
        raise SystemExit(f"refusing to overwrite an existing self-test run directory: {out}")
    out.mkdir(parents=True)

    tasks_path = out / "tasks.json"
    schedule_path = out / "schedule.json"
    contract_path = out / "contract.json"
    results_path = out / "results.jsonl"
    analysis_dir = out / "analysis"

    write_tasks(tasks_path, packet_id, args.tasks_per_stratum)

    run([
        sys.executable, str(HERE / "build_attribution_schedule.py"),
        "--tasks", str(tasks_path),
        "--out", str(schedule_path),
        "--seed", str(args.seed),
        "--repetitions", str(args.repetitions),
        "--allow-nonstandard-task-count",
    ])

    contract_command = [
        sys.executable, str(HERE / "build_executor_contract.py"),
        "--tasks", str(tasks_path),
        "--schedule", str(schedule_path),
        "--adapter", str(HERE / "selftest_adapter.py"),
        "--packet-id", packet_id,
        "--model-id", "NO_MODEL_INVOKED",
        "--model-revision", "NO_MODEL_INVOKED",
        "--evaluator-protocol-hash", hashlib.sha256(b"paper5-selftest-threshold-0.5").hexdigest(),
        "--tool-policy-id", "paper5-selftest-no-tools",
        "--source-cutoff-id", "paper5-selftest-no-sources",
        "--self-test-adapter-id", "paper5_selftest_adapter_v1",
        "--self-test-mode", args.mode,
        "--self-test-expected-outcome", EXPECTED[args.mode],
        "--out", str(contract_path),
    ]
    for arm in ARMS:
        contract_command += ["--arm-state-hash", f"{arm}={synthetic_state_hash(args.mode, arm)}"]
    for field, value in CEILING.items():
        contract_command += ["--ceiling", f"{field}={value}"]
    run(contract_command)

    run([
        sys.executable, str(HERE / "run_attribution_schedule.py"),
        "--tasks", str(tasks_path),
        "--schedule", str(schedule_path),
        "--contract", str(contract_path),
        "--run-root", str(out / "runs"),
        "--results-jsonl", str(results_path),
    ])

    run([
        sys.executable, str(HERE / "analyze_attribution_results.py"),
        "--tasks", str(tasks_path),
        "--schedule", str(schedule_path),
        "--results", str(results_path),
        "--out-dir", str(analysis_dir),
    ])

    summary = json.loads((analysis_dir / "summary.json").read_text(encoding="utf-8"))
    deltas = {row["contrast"]: row["mean_score_delta"] for row in summary["contrasts"]}
    receipt = {
        "schema_version": "paper5-harness-selftest-receipt-v1",
        "mode": args.mode,
        "packet_id": packet_id,
        "expected_outcome": EXPECTED[args.mode],
        "model_invoked": False,
        "task_count": summary["task_count"],
        "repetitions": summary["repetitions"],
        "run_count": summary["task_count"] * summary["repetitions"] * len(ARMS),
        "mean_score_delta": deltas,
        "analysis_core_sha256": summary["analysis_core_sha256"],
        "grants_scientific_authority": False,
        "claim_boundary": (
            "Instrument validation only. Synthetic adapter, no model invoked. Not a Paper 5 attribution result."
        ),
    }
    receipt_path = out / "selftest_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(receipt_path)
    for name in ("ARCHITECTURE", "EXPERIENCE", "CONTENT", "TOTAL"):
        print(f"  {name:<13} mean_score_delta = {deltas[name]:+.6f}")


EXPECTED = {
    "NULL_CONSTANT": "every contrast mean_score_delta exactly 0.0",
    "NULL_NOISE": "non-zero realized deltas with intervals covering 0",
    "PLANTED_LIFT": "+0.20 recovered on TOTAL/EXPERIENCE/CONTENT, ~0 on ARCHITECTURE",
}


if __name__ == "__main__":
    main()
