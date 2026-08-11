#!/usr/bin/env python3
"""Freeze Paper III #326 successor-validation terminal packet."""

from __future__ import annotations

import json
from pathlib import Path

from rakl.paper3_successor_validation import write_successor_packet

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    packet = write_successor_packet(ROOT, created_at_utc="2026-08-11T23:50:00Z")
    terminal = packet["terminal_receipt"]
    print("terminal_status", terminal["terminal_status"])
    print("json", json.dumps({"issue": 326, "terminal": terminal["terminal_status"]}))


if __name__ == "__main__":
    main()
