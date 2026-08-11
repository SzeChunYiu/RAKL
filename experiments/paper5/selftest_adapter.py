#!/usr/bin/env python3
"""Non-model harness self-test adapter for the Paper 5 four-arm executor.

This adapter calls no model. It exists to answer one question that the Paper 5
pipeline had never been asked: **does the measuring instrument report the truth?**

An instrument that can only ever report "no lift" is as defective as one that can
only ever report success, and neither defect is visible from a single run. So the
adapter ships three frozen modes, and the harness is only trusted if it recovers
the correct answer in all three:

``NULL_CONSTANT``
    Score depends on ``task_id`` alone. Every arm sees the identical score on a
    given task, so every paired difference is **exactly 0.0**. Verifies plumbing:
    task/arm pairing, aggregation and contrast direction.

``NULL_NOISE``
    Score is drawn from one fixed distribution seeded per run. The distribution
    parameters are identical for every arm, so the true lift is 0 while the
    realized paired differences are non-zero. Verifies that the analyzer's
    intervals cover 0 rather than manufacturing an effect from noise.

``PLANTED_LIFT``
    ``NULL_NOISE`` plus a known ``+0.20`` offset applied to ``RAKL_LEARNING``
    only. Verifies that the analyzer can *recover a real effect*. Without this
    positive control, all-null output would be indistinguishable between a
    correct instrument and one wired to report nothing.

Arm-blindness is a property of the score *parameters*, not of the bytes the
adapter reads: the adapter must read ``arm`` because the orchestrator requires it
to echo the per-arm frozen state hash. In ``NULL_CONSTANT`` the score ignores arm
entirely; in ``NULL_NOISE`` arm selects the random draw but not the distribution;
in ``PLANTED_LIFT`` the arm-dependent offset is declared, auditable and asserted
by tests.

The mode is bound by ``packet_id`` rather than an environment variable, so it is
covered by the same identity the orchestrator already cross-checks across the
task file, the schedule and the executor contract. It cannot drift at run time.

Every record this adapter writes carries a ``harness_self_test`` block, and
``analyze_attribution_results.py`` refuses to present such results as a Paper 5
attribution result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

ADAPTER_ID = "paper5_selftest_adapter_v1"
PACKET_PREFIX = "paper5-harness-selftest-"
MODES = ("NULL_CONSTANT", "NULL_NOISE", "PLANTED_LIFT")

#: The known effect planted on RAKL_LEARNING in ``PLANTED_LIFT`` mode.
PLANTED_LIFT_DELTA = 0.20
PLANTED_ARM = "RAKL_LEARNING"

SUCCESS_THRESHOLD = 0.5

#: Deterministic, arm-independent resource usage. Held constant across arms so a
#: resource artefact cannot masquerade as a capability difference.
RESOURCE_USAGE = {
    "model_input_tokens": 1024,
    "model_output_tokens": 256,
    "preprocessing_model_tokens": 128,
    "tool_calls": 1,
    "retrieval_calls": 2,
    "wall_time_ms": 5,
}


def unit_interval(*parts: str) -> float:
    """Deterministic pseudo-uniform draw in [0, 1) from the given key parts."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def mode_from_packet_id(packet_id: str) -> str:
    if not packet_id.startswith(PACKET_PREFIX):
        raise SystemExit(
            f"selftest adapter refuses packet {packet_id!r}: it only runs packets named "
            f"{PACKET_PREFIX}<MODE>, which keeps synthetic output out of real packets"
        )
    mode = packet_id[len(PACKET_PREFIX) :]
    if mode not in MODES:
        raise SystemExit(f"unknown self-test mode {mode!r}; expected one of {list(MODES)}")
    return mode


def score_for(mode: str, task_id: str, repetition: int, arm: str) -> float:
    """Compute the synthetic score.

    ``NULL_CONSTANT`` deliberately ignores ``repetition`` and ``arm``.
    ``NULL_NOISE`` uses the same bounds for every arm.
    ``PLANTED_LIFT`` adds a declared offset to exactly one arm.
    """
    if mode == "NULL_CONSTANT":
        return 0.2 + 0.6 * unit_interval("NULL_CONSTANT", task_id)
    if mode == "NULL_NOISE":
        return 0.2 + 0.6 * unit_interval("NULL_NOISE", task_id, str(repetition), arm)
    if mode == "PLANTED_LIFT":
        base = 0.2 + 0.4 * unit_interval("PLANTED_LIFT", task_id, str(repetition), arm)
        if arm == PLANTED_ARM:
            base += PLANTED_LIFT_DELTA
        return base
    raise SystemExit(f"unknown self-test mode {mode!r}")


def build_record(envelope: dict[str, Any], raw_path: Path) -> dict[str, Any]:
    mode = mode_from_packet_id(str(envelope["packet_id"]))
    row = envelope["schedule_row"]
    task_id = str(row["task_id"])
    repetition = int(row["repetition"])
    arm = str(row["arm"])

    score = round(score_for(mode, task_id, repetition, arm), 12)
    if not 0.0 <= score <= 1.0:
        raise SystemExit(f"synthetic score escaped [0,1]: {score}")
    success = score >= SUCCESS_THRESHOLD

    record: dict[str, Any] = {
        "run_id": row["run_id"],
        "task_id": task_id,
        "repetition": repetition,
        "arm": arm,
        "state_before_hash": envelope["expected_state_hash"],
        "state_after_hash": envelope["expected_state_hash"],
        "success": success,
        "score": score,
        "failure_signature": [] if success else ["HARNESS_SELFTEST_BELOW_THRESHOLD"],
        "validity_failures": [],
        "output_hash": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "harness_self_test": {
            "adapter_id": ADAPTER_ID,
            "mode": mode,
            "grants_scientific_authority": False,
        },
    }
    record.update(RESOURCE_USAGE)
    return record


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", required=True, type=Path)
    parser.add_argument("--raw-output", required=True, type=Path)
    parser.add_argument("--record-output", required=True, type=Path)
    args = parser.parse_args()

    envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
    mode = mode_from_packet_id(str(envelope["packet_id"]))
    row = envelope["schedule_row"]

    # RAW must be written before RECORD so output_hash binds bytes already on disk.
    atomic_json(
        args.raw_output,
        {
            "adapter_id": ADAPTER_ID,
            "mode": mode,
            "run_id": row["run_id"],
            "model_invoked": False,
            "note": "Synthetic harness self-test output. No model was called. Not a Paper 5 result.",
        },
    )
    atomic_json(args.record_output, build_record(envelope, args.raw_output))


if __name__ == "__main__":
    main()
