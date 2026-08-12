#!/usr/bin/env python3
"""Re-instrument a frozen longitudinal harvest universe (#446).

Reads ``longitudinal_event_universe.jsonl`` and emits prospective
``RAKL_CYCLE_METRICS`` instrumentation without re-querying RAKL_math.

Example::

    python experiments/paper5/instrument_cycle_metrics_harvest.py \\
        --universe research/paper5_longitudinal_v1/longitudinal_event_universe.jsonl \\
        --out-dir /tmp/instrumentation
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from rakl.cycle_metrics_harvest import (
    INSTRUMENTATION_SCHEMA,
    build_instrumentation_row,
    instrumentation_coverage,
)


def load_universe(path: Path) -> list[dict]:
    rows: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{lineno}: expected object")
        rows.append(row)
    if not rows:
        raise SystemExit("universe is empty")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    instrumented_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    envelopes = load_universe(args.universe.expanduser().resolve())
    rows = [build_instrumentation_row(env, instrumented_at=instrumented_at) for env in envelopes]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "prospective_cycle_metrics_instrumentation.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    report = instrumentation_coverage(rows)
    report["instrumentation_version"] = INSTRUMENTATION_SCHEMA
    report["universe_sha256"] = hashlib.sha256(args.universe.read_bytes()).hexdigest()
    report["instrumentation_sha256"] = hashlib.sha256(out_path.read_bytes()).hexdigest()
    (args.out_dir / "cycle_metrics_instrumentation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(out_path)
    print(f"  rows                      {report['row_count']}")
    print(f"  payload schema classes    {report['payload_schema_classes']}")
    print(f"  rows with known denominators {report['rows_with_known_denominators']}")


if __name__ == "__main__":
    main()
