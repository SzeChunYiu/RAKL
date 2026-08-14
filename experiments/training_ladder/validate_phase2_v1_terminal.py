#!/usr/bin/env python3
"""Validate Paper-IV Phase-2 runner-code/scientific-terminal pairs.

The Phase-2 runner uses non-zero local process codes for some complete registered
scientific terminals.  A SLURM wrapper must validate the completed receipt first
and only then decide whether the scheduler execution itself succeeded.

This module changes no scientific threshold and grants no scientific authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


RC_TERMINALS = {
    0: {
        "ADAPTIVE_RESIDUAL_SUPPORTED",
        "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST",
        "PARENT_MATCHES_OR_BEATS",
        "STATIC_EQUALS_ADAPTIVE",
        "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION",
        "UNDERPOWERED",
    },
    1: {"ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION"},
    2: {"RESOURCE_BLOCKED"},
}


def validate_terminal_pair(receipt: object, runner_code: int) -> tuple[bool, str]:
    if not isinstance(receipt, dict):
        return False, "phase2_final_receipt_missing_or_invalid"
    if receipt.get("schema_version") != "rakl-paper4-phase2-result-v1":
        return False, "phase2_result_schema_mismatch"
    if receipt.get("grants_scientific_authority") is not False:
        return False, "phase2_scientific_authority_boundary_invalid"
    terminal = receipt.get("terminal")
    allowed = RC_TERMINALS.get(int(runner_code))
    if allowed is None:
        return False, f"phase2_unregistered_runner_code:{runner_code}"
    if terminal not in allowed:
        return False, f"phase2_runner_code_terminal_mismatch:{runner_code}:{terminal}"
    return True, str(terminal)


def _selftest() -> None:
    base = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "grants_scientific_authority": False,
    }
    for code, terminals in RC_TERMINALS.items():
        for terminal in terminals:
            ok, observed = validate_terminal_pair({**base, "terminal": terminal}, code)
            assert ok and observed == terminal
    ok, reason = validate_terminal_pair({**base, "terminal": "RESOURCE_BLOCKED"}, 0)
    assert not ok and "mismatch" in reason
    ok, reason = validate_terminal_pair({**base, "terminal": "ADAPTIVE_RESIDUAL_SUPPORTED"}, 1)
    assert not ok and "mismatch" in reason
    ok, reason = validate_terminal_pair({**base, "terminal": "UNDERPOWERED"}, 9)
    assert not ok and "unregistered_runner_code" in reason
    ok, reason = validate_terminal_pair(
        {"schema_version": "rakl-paper4-phase2-result-v1", "terminal": "UNDERPOWERED", "grants_scientific_authority": True},
        0,
    )
    assert not ok and "authority" in reason
    print("P4 Phase-2 terminal validator selftest: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--runner-code", type=int)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        _selftest()
        return
    if args.receipt is None or args.runner_code is None:
        parser.error("--receipt and --runner-code are required unless --selftest is used")
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"CANNOT_CHECK_EXECUTION_STATE: unreadable final receipt: {exc}") from exc
    ok, detail = validate_terminal_pair(receipt, args.runner_code)
    if not ok:
        raise SystemExit(f"CANNOT_CHECK_EXECUTION_STATE: {detail}")
    print(f"P4_PHASE2_SCIENTIFIC_TERMINAL_VALID terminal={detail} runner_code={args.runner_code}")


if __name__ == "__main__":
    main()
