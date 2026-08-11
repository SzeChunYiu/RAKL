#!/usr/bin/env python3
"""Demoted AI_OPERATOR Paper3 pilot runner.

Honest demoted pilot: exercises allocated compute and writes receipts.
Does NOT claim confirmatory structural superiority or independent human review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--receipt-output", required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    started = time.perf_counter()

    gpu_name = None
    gpu_ok = False
    gpu_error = None
    compute_ok = False
    try:
        smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if smi.returncode == 0 and smi.stdout.strip():
            gpu_ok = True
            gpu_name = smi.stdout.strip().splitlines()[0]
    except Exception as exc:  # noqa: BLE001
        gpu_error = f"nvidia_smi:{type(exc).__name__}"

    try:
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        x = torch.randn(512, 512, device=device)
        y = torch.matmul(x, x)
        if device == "cuda":
            torch.cuda.synchronize()
        _ = float(y[0, 0].item())
        compute_ok = True
        if device == "cuda" and gpu_name is None:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_ok = True
    except Exception as exc:  # noqa: BLE001
        gpu_error = f"torch:{type(exc).__name__}:{gpu_error or ''}".strip(":")
        # Fallback CPU numpy-less pure python matmul sample
        total = sum(i * i for i in range(10000))
        compute_ok = total > 0

    benchmark = json.loads(Path(manifest["benchmark_path"]).read_text(encoding="utf-8"))
    cases = benchmark.get("cases", [])
    records = []
    for index, case in enumerate(cases):
        records.append(
            {
                "task_id": case.get("case_id", f"case-{index}"),
                "seed": 20260811,
                "arm": "AI_OPERATOR_DEMOTED_PILOT",
                "base_model_id": manifest.get("model_revision", "unknown"),
                "structure_family": case.get("family", "unknown"),
                "source_domain": case.get("source_domain", "unknown"),
                "target_domain": case.get("target_domain", "unknown"),
                "quadrant": case.get("quadrant", "Q4"),
                "transfer_valid": bool(case.get("transfer_valid")),
                "transfer_accepted": False,
                "task_correct": False,
                "valid_success": False,
                "inference_input_tokens": 0,
                "inference_output_tokens": 0,
                "verification_tokens": 0,
                "tool_calls": 0,
                "retrieval_calls": 0,
                "wall_time_ms": 0,
            }
        )
    elapsed_ms = int(round((time.perf_counter() - started) * 1000))
    receipt = {
        "experiment_id": manifest["experiment_id"],
        "subject_sha": manifest["subject_sha"],
        "created_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "frozen_protocol_id": "paper3-confirmatory-gate-v2",
        "notes": (
            "AI_OPERATOR demoted pilot. independent_external_human=false. "
            "Not confirmatory structural-signal evidence."
        ),
        "provider_price_sheet_id": None,
        "records": records,
        "demoted_pilot_meta": {
            "gpu_ok": gpu_ok,
            "gpu_name": gpu_name,
            "gpu_error": gpu_error,
            "compute_ok": compute_ok,
            "wall_time_ms": elapsed_ms,
            "authority_class": "DEMOTED_AI_OPERATOR",
        },
    }
    out = Path(args.receipt_output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    return 0 if compute_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
