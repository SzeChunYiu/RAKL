#!/usr/bin/env python3
"""Finalize Paper II pre-execution power design receipts (#247).

Requires POWER_RESULTS.json from paper2_power_design_simulate.py. Writes:

  research/paper2/power_design/ZERO_OUTCOMES_AT_POWER_DESIGN.json
  research/paper2/power_design/DECISION_RECEIPT.json

Run from repository root:

  python3 scripts/paper2_power_design_finalize.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.paper2_power_design import (  # noqa: E402
    CONFIG_PATH,
    DECISION_PATH,
    RESULTS_PATH,
    ZERO_OUTCOMES_PATH,
    build_decision_receipt,
    build_zero_outcomes_at_power_design,
)

OUT_DIR = ROOT / "research" / "paper2" / "power_design"


def main() -> None:
    if not RESULTS_PATH.exists():
        raise SystemExit(
            "missing POWER_RESULTS.json; run scripts/paper2_power_design_simulate.py first"
        )
    config = json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))
    results = json.loads((ROOT / RESULTS_PATH).read_text(encoding="utf-8"))
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    zero_outcomes = build_zero_outcomes_at_power_design(ROOT, created_at_utc=created)
    decision = build_decision_receipt(
        ROOT,
        config=config,
        results=results,
        zero_outcomes=zero_outcomes,
        created_at_utc=created,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ZERO_OUTCOMES_PATH.write_text(
        json.dumps(zero_outcomes, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {ZERO_OUTCOMES_PATH}")
    print(f"wrote {DECISION_PATH}")
    print(f"decision_path={decision['decision_path']} decision={decision['decision']}")


if __name__ == "__main__":
    main()
