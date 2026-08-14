#!/usr/bin/env python3
"""Fail-closed preflight for post-contract mechanic promotion candidates.

The ordinary promotion gate scores evidence.  This preflight answers whether a
new candidate is still authorized to *enter* that scorer under the current
knowledge/supersession registry.  CI runs this contract through tests so a new
candidate cannot land while bound to a stale-but-structurally-valid packet.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from promotion_gate import CANDIDATES, PRE_PACKET_LEGACY_CANDIDATES  # noqa: E402
from rakl.mechanic_research_packet_registry import (  # noqa: E402
    load_active_packet_registry,
    resolve_packet_eligibility,
)

REGISTRY_PATH = ROOT / "research/mechanic_research_packets_v1/ACTIVE_PACKET_REGISTRY.json"


def active_registration_problems(*, candidates=None, registry=None) -> tuple[str, ...]:
    candidates = CANDIDATES if candidates is None else candidates
    registry = load_active_packet_registry(REGISTRY_PATH) if registry is None else registry
    problems: list[str] = []
    for candidate_id, spec in candidates.items():
        if candidate_id in PRE_PACKET_LEGACY_CANDIDATES:
            continue
        variant_id = spec.get("research_packet_variant_id")
        if not variant_id:
            problems.append(f"{candidate_id}:research_packet_variant_id_missing")
            continue
        report = resolve_packet_eligibility(variant_id, registry, repo_root=ROOT)
        if not report.eligible_for_existing_promotion_gate:
            detail = ",".join(report.reasons)
            problems.append(f"{candidate_id}:{variant_id}:{report.status.value}:{detail}")
    return tuple(problems)


def main() -> int:
    problems = active_registration_problems()
    for problem in problems:
        print(problem)
    print(f"ACTIVE_PACKET_PREFLIGHT_PROBLEMS={len(problems)}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
