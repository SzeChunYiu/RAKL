"""Step 2 — execute arm A and arm B as separate processes over the byte-identical
gold-stripped corpus, record arm_run_started_at, and append RSHEA receipts
(sequence 3-8) to the chain started at corpus freeze.

Refuses to run if the corpus freeze manifest is missing (chronology guard), if
the frozen corpus hash changed since freeze, or if the module pin drifted.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    RESULTS_DIR, build_run_epoch, receipt_to_dict, sha256_file, utc_now_iso,
    verify_module_pins, write_json,
)

from rakl.observability_adapters import (  # noqa: E402
    process_telemetry_to_receipts, rakl_canonical_metrics,
)
from rakl.v3_metrology import ProcessOutcome, ProcessTelemetry  # noqa: E402


def main() -> int:
    verify_module_pins()
    manifest_path = os.path.join(RESULTS_DIR, "freeze_manifest.json")
    if not os.path.exists(manifest_path):
        print("CANNOT_CHECK: corpus freeze manifest missing; arms may not run first",
              file=sys.stderr)
        return 3
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    corpus_path = os.path.join(RESULTS_DIR, "corpus_v1.json")
    stripped_path = os.path.join(RESULTS_DIR, "corpus_v1_stripped.json")
    if sha256_file(corpus_path) != manifest["artifacts"]["corpus_v1.json"]:
        print("CANNOT_CHECK: corpus hash drifted since freeze", file=sys.stderr)
        return 3
    if sha256_file(stripped_path) != manifest["artifacts"]["corpus_v1_stripped.json"]:
        print("CANNOT_CHECK: stripped corpus hash drifted since freeze", file=sys.stderr)
        return 3

    epoch = build_run_epoch()
    if epoch.epoch_id != manifest["epoch_id"]:
        print("CANNOT_CHECK: epoch identity drifted since freeze", file=sys.stderr)
        return 3

    arm_run_started_at = utc_now_iso()
    while str(manifest["label_minted_at"]) >= arm_run_started_at:
        time.sleep(1)
        arm_run_started_at = utc_now_iso()

    receipts_all = []
    telemetry_all = []
    seq = 3
    harness = os.path.join(RESULTS_DIR, "harness", "arm_harness.py")
    for arm in ("A", "B"):
        out_path = os.path.join(RESULTS_DIR, f"arm_{arm.lower()}_output.json")
        proc = subprocess.run(
            [sys.executable, harness, "--arm", arm, "--corpus", stripped_path,
             "--out", out_path],
            capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"CANNOT_CHECK: arm {arm} failed: {proc.stderr}", file=sys.stderr)
            return 3
        with open(out_path, "r", encoding="utf-8") as handle:
            arm_out = json.load(handle)
        telemetry = ProcessTelemetry(
            invocation_id=f"benefit-l2-gluing-v1:arm-{arm}",
            process_surface="contextual_theory_gluing",
            task_id="BENEFIT-L2-GLUING-V1",
            input_state_hash=manifest["artifacts"]["corpus_v1_stripped.json"],
            output_state_hash=sha256_file(out_path),
            outcome=ProcessOutcome.SUCCESS,
            cost=float(arm_out["wall_clock_seconds"]),
            cost_policy_id="wall-clock-seconds",
            residual_before=("L2-benefit-unmeasured",),
            residual_after=("L2-benefit-unmeasured",),
            retained_novelty=(),
            evidence_pointers=(out_path,),
            timestamp=utc_now_iso(),
        )
        receipts = process_telemetry_to_receipts(
            telemetry, epoch, rakl_canonical_metrics, sequence_base=seq)
        seq += 3
        receipts_all.extend(receipt_to_dict(r) for r in receipts)
        telemetry_all.append({**asdict(telemetry), "outcome": telemetry.outcome.value})
        print(f"arm {arm}: glued={arm_out['n_declared_glue']} "
              f"time={arm_out['wall_clock_seconds']:.5f}s rss={arm_out['peak_rss_bytes']}")

    write_json(os.path.join(RESULTS_DIR, "rshea", "receipts_step2.json"), {
        "arm_run_started_at": arm_run_started_at,
        "telemetry": telemetry_all,
        "receipts": receipts_all,
    })
    print(f"step2 OK: arm_run_started_at={arm_run_started_at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
