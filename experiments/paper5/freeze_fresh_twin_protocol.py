#!/usr/bin/env python3
"""Freeze Paper 5 fresh replay twin design stub (#446 lane 7).

Rebuilds FREEZE_STUB.json and optional dev task manifest. Does not execute
models or access confirmatory outcomes.

Example::

    python experiments/paper5/freeze_fresh_twin_protocol.py \\
        --out-dir research/paper5_fresh_twin_v1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rakl.paper5_fresh_twin_generator import (
    build_freeze_stub,
    canonical_json_bytes,
    generate_dev_universe,
    load_failure_family_registry,
    sweep_leakage,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("research/paper5_fresh_twin_v1"),
        help="Output directory for freeze stub and dev manifest",
    )
    parser.add_argument(
        "--seeds-per-family",
        type=int,
        default=2,
        help="Development seeds per family (valid+invalid twins each)",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    registry = load_failure_family_registry()
    tasks = generate_dev_universe(seeds_per_family=args.seeds_per_family, registry=registry)
    leakage = sweep_leakage(tasks, registry=registry)
    if not leakage["passed"]:
        raise SystemExit(f"Leakage sweep failed: {leakage['findings'][:3]}")

    stub = build_freeze_stub(seeds_per_family=args.seeds_per_family)
    (out_dir / "FREEZE_STUB.json").write_text(
        json.dumps(stub, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest_path = out_dir / "DEV_TASK_MANIFEST.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for task in tasks:
            handle.write(json.dumps(task, sort_keys=True) + "\n")

    summary = {
        "task_count": len(tasks),
        "freeze_stub_sha256": stub["task_manifest_sha256"],
        "leakage_passed": leakage["passed"],
        "outcome_access_status": "NO_OUTCOME_ACCESSED",
    }
    print(json.dumps(summary, indent=2))
    print(f"wrote {out_dir / 'FREEZE_STUB.json'}")
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
