#!/usr/bin/env python3
"""Validate Paper-5 freeze stubs and refuse confirmatory/audit handoff.

This module exists so a later packet builder cannot accidentally emit
``CONFIRMATORY_PACKET_FROZEN_AND_EXECUTABLE`` or invent annotator responses.
It validates the committed stubs against their schemas and exits non-zero if
authority or handoff invariants are violated.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]

STUBS = (
    (
        ROOT / "research/paper5_confirmatory_packet_v1/PACKET_FREEZE_STUB.json",
        ROOT / "schemas/paper5-confirmatory-packet-freeze-stub-v1.schema.json",
        "NOT_CONFIRMATORY_PACKET_FROZEN_AND_EXECUTABLE",
    ),
    (
        ROOT / "research/paper5_novelty_audit_v1/AUDIT_FREEZE_STUB.json",
        ROOT / "schemas/paper5-novelty-audit-freeze-stub-v1.schema.json",
        None,
    ),
    (
        ROOT / "research/paper5_novelty_audit_v1/AUDIT_UNIVERSE_MANIFEST.json",
        ROOT / "schemas/paper5-audit-universe-manifest-v1.schema.json",
        None,
    ),
    (
        ROOT / "research/paper5_novelty_audit_v1/ZERO_EXTERNAL_NOVELTY_LABELS.json",
        ROOT / "schemas/paper5-zero-external-novelty-labels-v1.schema.json",
        None,
    ),
    (
        ROOT / "research/paper5_longitudinal_v1/COVERAGE_OBSERVATION_20260811.json",
        ROOT / "schemas/paper5-longitudinal-coverage-observation-v1.schema.json",
        None,
    ),
)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-confirmatory-handoff",
        action="store_true",
        help="forbidden flag; present only so misuse is an explicit hard fail",
    )
    args = parser.parse_args()
    if args.allow_confirmatory_handoff:
        raise SystemExit(
            "refusing --allow-confirmatory-handoff: confirmatory handoff is not "
            "available from freeze stubs"
        )

    for stub_path, schema_path, expected_handoff in STUBS:
        stub = load(stub_path)
        schema = load(schema_path)
        Draft202012Validator(schema).validate(stub)
        if stub.get("grants_scientific_authority") is not False:
            raise SystemExit(f"{stub_path}: grants_scientific_authority must be false")
        if expected_handoff is not None and stub.get("handoff_status") != expected_handoff:
            raise SystemExit(
                f"{stub_path}: handoff_status must be {expected_handoff!r}, "
                f"got {stub.get('handoff_status')!r}"
            )
        if stub.get("handoff_status") == "CONFIRMATORY_PACKET_FROZEN_AND_EXECUTABLE":
            raise SystemExit(
                f"{stub_path}: confirmatory handoff is forbidden on a stub artifact"
            )
        if stub_path.name == "AUDIT_FREEZE_STUB.json":
            if stub.get("annotator_responses_present") or stub.get("adjudication_present"):
                raise SystemExit(f"{stub_path}: fabricated human responses are forbidden")
        print(f"OK {stub_path.relative_to(ROOT)} status={stub.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
