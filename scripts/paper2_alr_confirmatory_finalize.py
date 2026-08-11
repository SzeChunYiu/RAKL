#!/usr/bin/env python3
"""Freeze Paper II #324 confirmatory ALR protocol packet."""

from __future__ import annotations

import json
from pathlib import Path

from rakl.paper2_alr_confirmatory import refuse_confirmatory_claim, write_confirmatory_packet

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    packet = write_confirmatory_packet(ROOT, created_at_utc="2026-08-11T23:50:00Z")
    terminal = packet["terminal_receipt"]
    try:
        refuse_confirmatory_claim(ROOT)
        refused = False
    except PermissionError as exc:
        refused = True
        print("refuse_confirmatory_claim", str(exc))
    print("terminal_status", terminal["terminal_status"])
    print("blockers", terminal["blockers"])
    print(
        "json",
        json.dumps(
            {
                "issue": 324,
                "terminal": terminal["terminal_status"],
                "claim_refused": refused,
            }
        ),
    )


if __name__ == "__main__":
    main()
