#!/usr/bin/env python3
"""Pre-outcome claim-boundary wrapper for the frozen Paper-IV Phase-2 experiment.

The scientific experiment is still ``phase2_adaptive_v1.run`` byte-for-byte.
This wrapper changes no selection, training, assurance, inference, terminal or
resource value.  It runs the parent in a private temporary directory and only
then exposes an outcome receipt whose standalone-paper field cannot outrun
issue #462's later generalization gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from experiments.training_ladder import phase2_adaptive_v1 as PARENT

POSITIVE_PHASE2_TERMINALS = {
    "ADAPTIVE_RESIDUAL_SUPPORTED",
    "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST",
}
ALLOWED_TERMINALS = POSITIVE_PHASE2_TERMINALS | {
    "PARENT_MATCHES_OR_BEATS",
    "STATIC_EQUALS_ADAPTIVE",
    "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION",
    "UNDERPOWERED",
    "RESOURCE_BLOCKED",
    "INVALID_CONTAMINATED",
}


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def harden_parent_receipt(parent: dict) -> dict:
    terminal = parent.get("terminal")
    if terminal not in ALLOWED_TERMINALS:
        raise ValueError(f"unregistered Phase-2 terminal: {terminal!r}")
    original = dict(parent)
    safe = dict(parent)
    safe["phase2_policy_result_positive"] = terminal in POSITIVE_PHASE2_TERMINALS
    safe["paper4_standalone_authorized"] = False
    safe["paper4_standalone_gate_status"] = "PENDING_ISSUE_462_GENERALIZATION_AND_DISTINCT_CONTENT_GATES"
    safe["paper4_standalone_remaining_gates"] = [
        "fresh structural-family generalization",
        "more than one model/checkpoint regime",
        "anti-salami/distinct-content boundary under issue #462",
    ]
    safe["claim_boundary_hardening"] = "PHASE2_POSITIVE_IS_A_PREREQUISITE_NOT_STANDALONE_AUTHORIZATION"
    safe["parent_receipt_canonical_sha256"] = _canonical_sha256(original)
    safe["parent_standalone_field_was"] = bool(original.get("paper4_standalone_authorized", False))
    safe["grants_scientific_authority"] = False
    return safe


def run(outdir: Path, *, dry_run: bool = False) -> int:
    if dry_run:
        return PARENT.run(outdir, dry_run=True)

    outdir = outdir.resolve()
    outdir.parent.mkdir(parents=True, exist_ok=True)
    if outdir.exists() and any(outdir.iterdir()):
        raise SystemExit(f"CANNOT_CHECK_EXECUTION_STATE: refusing nonempty output directory: {outdir}")
    tmp = Path(tempfile.mkdtemp(prefix=".p4-phase2-parent-", dir=outdir.parent))
    try:
        parent_code = PARENT.run(tmp, dry_run=False)
        parent_receipt_path = tmp / "FINAL_RECEIPT.json"
        if not parent_receipt_path.is_file():
            return parent_code
        parent_bytes = parent_receipt_path.read_bytes()
        parent_receipt = json.loads(parent_bytes)
        safe_receipt = harden_parent_receipt(parent_receipt)

        outdir.mkdir(parents=True, exist_ok=True)
        for path in tmp.iterdir():
            if path.name == "FINAL_RECEIPT.json":
                continue
            os.replace(path, outdir / path.name)
        (outdir / "PARENT_RECEIPT_BINDING.json").write_text(
            json.dumps(
                {
                    "schema_version": "rakl-p4-phase2-parent-receipt-binding-v2",
                    "parent_receipt_byte_sha256": hashlib.sha256(parent_bytes).hexdigest(),
                    "parent_receipt_canonical_sha256": _canonical_sha256(parent_receipt),
                    "parent_terminal": parent_receipt.get("terminal"),
                    "parent_standalone_field_was": bool(parent_receipt.get("paper4_standalone_authorized", False)),
                    "parent_receipt_not_exposed_as_final": True,
                    "grants_scientific_authority": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(safe_receipt, indent=2, sort_keys=True) + "\n")
        return parent_code
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    raise SystemExit(run(args.outdir, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
