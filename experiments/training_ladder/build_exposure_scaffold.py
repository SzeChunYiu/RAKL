#!/usr/bin/env python3
"""Emit frozen #461 exposure-curve harness scaffold (pre-outcome, no learner runs)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET_DIR = ROOT / "research" / "training_time_rakl_phase0_1"
sys.path.insert(0, str(ROOT / "src"))

from rakl.training_ladder import (  # noqa: E402
    ExposureProbeKind,
    build_known_structure_catalog,
    build_exposure_curve_harness,
    verify_case,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--harness-id", default="training-ladder-phase0-1-exposure-scaffold")
    args = parser.parse_args()

    cases = [verify_case(c) for c in build_known_structure_catalog(seed_offsets=(0, 1))]
    if len(cases) < 2:
        raise SystemExit("catalog too small for exposure scaffold")

    harness = build_exposure_curve_harness(
        harness_id=args.harness_id,
        case_ids_by_probe={
            ExposureProbeKind.SAME_STRUCTURE: [cases[0].case_id],
            ExposureProbeKind.HOSTILE_NEAR_MISS: [cases[1].case_id],
            ExposureProbeKind.NEW_COMPOSITION: [cases[2].case_id if len(cases) > 2 else cases[0].case_id],
        },
    )
    payload = {
        "schema_version": "training-ladder-exposure-scaffold-v1",
        "harness_id": harness.harness_id,
        "harness_hash": harness.harness_hash,
        "exposure_counts": list(harness.exposure_counts),
        "mastery_coordinates": [coord.value for coord in harness.mastery_coordinates],
        "comparator_proxies": list(harness.comparator_proxies),
        "schedule_entry_count": len(harness.schedule),
        "frozen_before_outcomes": harness.frozen_before_outcomes,
        "learner_outcomes_accessed": harness.learner_outcomes_accessed,
        "grants_efficacy_claim": harness.grants_efficacy_claim,
        "grants_scientific_authority": False,
        "scientific_claim_status": "NO_EMPIRICAL_RESULT",
        "claim_boundary": (
            "Phase 1 exposure-curve harness scaffold only. Schedules registered probe kinds "
            "and exposure counts without executing a learner or accessing outcomes."
        ),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "EXPOSURE_CURVE_HARNESS_SCAFFOLD.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path)
    print(f"  schedule_entries {payload['schedule_entry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
