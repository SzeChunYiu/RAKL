#!/usr/bin/env python3
"""Fail closed: do not reinterpret pendulum V4.1 harvests as v3 experience runs.

Issue #138 section B requires RESET_BASELINE vs LEARNING_ENABLED with disjoint
development/transfer tasks and state chronology. Paper II V4.1 microtrials are a
different matched-prompt protocol (RAKL_CONTEXT vs DIRECT) and must not be fed to
``analyze_v3_experience_benchmark.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_EXPERIENCE_PACKET_FIELDS = (
    "initial_state_hash",
    "learned_state_after_development_hash",
    "development_task_ids",
    "transfer_task_ids",
)


def inspect_candidate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = str(payload.get("schema_version", ""))
    reasons: list[str] = []
    if "pendulum" in schema or "v4_1" in schema or "V4_1" in schema:
        reasons.append(f"schema_version marks pendulum/V4.1 protocol: {schema}")
    if payload.get("experiment_id", "").startswith("PENDULUM_"):
        reasons.append("experiment_id is a pendulum microtrial, not experience benchmark")
    if "records" in payload and isinstance(payload["records"], list):
        conditions = {
            row.get("condition")
            for row in payload["records"]
            if isinstance(row, dict) and row.get("condition")
        }
        if conditions & {"RAKL_CONTEXT", "DIRECT"}:
            reasons.append(
                "arm labels are RAKL_CONTEXT/DIRECT (prompt materialization), "
                "not RESET_BASELINE/LEARNING_ENABLED"
            )
    missing = [field for field in REQUIRED_EXPERIENCE_PACKET_FIELDS if field not in payload]
    if missing:
        reasons.append("missing experience-benchmark packet fields: " + ", ".join(missing))
    return {
        "path": str(path),
        "schema_version": schema or None,
        "compatible_with_experience_benchmark_analyzer": False if reasons else True,
        "blockers": reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "candidates",
        nargs="+",
        type=Path,
        help="Harvest/result/packet JSON files to check for experience-benchmark compatibility",
    )
    parser.add_argument("--out", type=Path, help="Optional JSON receipt path")
    args = parser.parse_args()

    inspections = [inspect_candidate(path) for path in args.candidates]
    blockers = [item for item in inspections if item["blockers"]]
    receipt = {
        "schema_version": "paper2-v4-1-to-experience-compatibility-v1",
        "verdict": "CANNOT_CHECK" if blockers else "COMPATIBLE",
        "claim_boundary": (
            "Compatibility gate only. A CANNOT_CHECK verdict forbids feeding these "
            "artifacts to analyze_v3_experience_benchmark.py / plot_v3_experience_benchmark.py "
            "as issue #138 section B evidence."
        ),
        "inspections": inspections,
        "grants_experience_benchmark_authority": False,
    }
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    else:
        print(text, end="")
    if blockers:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
