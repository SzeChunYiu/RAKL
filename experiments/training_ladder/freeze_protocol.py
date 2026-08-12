#!/usr/bin/env python3
"""Freeze or validate #461 training-ladder Phase 0/1 protocol (pre-outcome)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET_DIR = ROOT / "research" / "training_time_rakl_phase0_1"
sys.path.insert(0, str(ROOT / "src"))

from rakl.training_ladder.protocol import (  # noqa: E402
    build_protocol_freeze_packet,
    build_protocol_freeze_receipt,
    validate_protocol_freeze,
)


def _repo_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _rakl_version() -> str:
    version_path = ROOT / "RAKL_VERSION.json"
    if version_path.is_file():
        payload = json.loads(version_path.read_text(encoding="utf-8"))
        return str(payload.get("incumbent", {}).get("method_version", payload.get("version", "unknown")))
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--write", action="store_true", help="Write packet and receipt to packet-dir")
    args = parser.parse_args()

    if args.write:
        packet = build_protocol_freeze_packet(repo_sha=_repo_sha(), rakl_version=_rakl_version())
        receipt = build_protocol_freeze_receipt(packet)
        args.packet_dir.mkdir(parents=True, exist_ok=True)
        (args.packet_dir / "PROTOCOL_FREEZE_PACKET.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.packet_dir / "PROTOCOL_FREEZE_RECEIPT.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    validation = validate_protocol_freeze(args.packet_dir)
    payload = {
        "verdict": validation.verdict,
        "reasons": list(validation.reasons),
        "protocol_subject_hash": validation.protocol_subject_hash,
    }
    print(json.dumps(payload, indent=2))
    return 0 if validation.verdict == "PROTOCOL_FREEZE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
