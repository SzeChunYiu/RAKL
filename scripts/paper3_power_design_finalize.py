#!/usr/bin/env python3
"""Finalize Paper III pre-label power design receipts (#248).

Runs zero-label verification, reads frozen simulation output, and writes:

  research/paper3/power_design/ZERO_LABELS_AT_POWER_DESIGN.json
  research/paper3/power_design/DECISION_RECEIPT.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.paper3_annotation import canonical_sha256  # noqa: E402
from rakl.paper3_power_design import (  # noqa: E402
    CONFIG_PATH,
    DECISION_PATH,
    RESULTS_PATH,
    ZERO_LABELS_PATH,
    build_decision_receipt,
    build_zero_labels_at_power_design,
)

OUT_DIR = ROOT / "research" / "paper3" / "power_design"


def main() -> int:
    if not RESULTS_PATH.is_file():
        raise SystemExit(
            "missing POWER_RESULTS.json; run scripts/paper3_power_design_simulate.py first"
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    zero_labels = build_zero_labels_at_power_design(ROOT, created_at_utc=created)
    decision = build_decision_receipt(
        ROOT,
        config=config,
        results=results,
        zero_labels=zero_labels,
        created_at_utc=created,
    )

    ZERO_LABELS_PATH.write_text(
        json.dumps(zero_labels, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(ZERO_LABELS_PATH)
    print(DECISION_PATH)
    print("decision_path", decision["decision_path"], decision["decision"])
    print("zero_labels_sha256", canonical_sha256(zero_labels))
    print("decision_sha256", canonical_sha256(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
