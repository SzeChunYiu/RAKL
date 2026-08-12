#!/usr/bin/env python3
"""Local label-blind Paper III semantic descriptor builder (non-LUNARC pre-run smoke).

Uses the frozen strong-control protocol and source set. Without model assets on disk
the builder fails closed with ``CANNOT_CHECK_MODEL_ASSET_MISSING`` — that is the
expected local smoke outcome until BGE weights are staged.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from rakl.paper3_strong_control import (  # noqa: E402
    build_semantic_descriptor_receipt,
    validate_semantic_descriptor_receipt,
)

DEFAULT_SOURCE_SET = ROOT / "research/paper3/annotation/SOURCE_ITEM_SET_V2_1_20260810.json"
DEFAULT_PROTOCOL = ROOT / "research/PAPER3_STRONG_CONTROL_PROTOCOL_V1_20260811.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-set", type=Path, default=DEFAULT_SOURCE_SET)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--model-dir", type=Path, required=True, help="directory with frozen BGE assets")
    parser.add_argument("--out", type=Path, help="write descriptor JSON (default stdout)")
    parser.add_argument(
        "--created-at",
        default=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    args = parser.parse_args()

    source_set = json.loads(args.source_set.read_text(encoding="utf-8"))
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    receipt = build_semantic_descriptor_receipt(
        source_set=source_set,
        protocol=protocol,
        model_dir=args.model_dir.expanduser().resolve(),
        created_at_utc=args.created_at,
    )
    failures = validate_semantic_descriptor_receipt(source_set, protocol, receipt)
    if failures:
        receipt.setdefault("validation_failures", []).extend(failures)

    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(args.out)
    else:
        print(payload, end="")

    if receipt.get("status") == "CANNOT_CHECK_CONTENT_BINDING_INVALID":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
