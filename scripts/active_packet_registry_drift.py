#!/usr/bin/env python3
"""Fail closed if the active packet registry's knowledge basis has drifted.

The registry is a later eligibility fact over immutable preregistration packets.
It is valid only for the knowledge basis it was revalidated against.  A newly
merged saturation round, packet amendment, packet validator change, or promotion
gate change must therefore force an explicit registry revalidation before any
ACTIVE packet can enter evidence scoring.

This is deliberately conservative: a tracked change may ultimately be irrelevant
to a given packet, but that conclusion must be recorded by a new revalidation
rather than inferred silently by the old registry.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research/mechanic_research_packets_v1/ACTIVE_PACKET_REGISTRY.json"
REVALIDATION = ROOT / "research/mechanic_research_packets_v1/ACTIVE_REGISTRY_REVALIDATION_20260814.json"

TRACKED_BASIS_PATHS = (
    "research/mechanic_research_packets_v1/PAPER5_PAPER6_SUCCESSORS.json",
    "research/p5_p6_saturation_v1/",
    "src/rakl/mechanic_research_packet.py",
    "src/rakl/mechanic_research_packet_io.py",
    "scripts/promotion_gate.py",
)


def _changed_paths(subject_sha: str, head: str = "HEAD") -> tuple[str, ...]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{subject_sha}..{head}", "--", *TRACKED_BASIS_PATHS],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return tuple(line.strip() for line in proc.stdout.splitlines() if line.strip())


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    revalidation = json.loads(REVALIDATION.read_text(encoding="utf-8"))
    registry_subject = str(registry["subject_main_sha"])
    original_subject = str(revalidation["original_registry_subject_sha"])
    if registry_subject != original_subject:
        print(
            "ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK "
            f"registry_subject={registry_subject} revalidation_subject={original_subject}"
        )
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    changed = _changed_paths(registry_subject)
    if changed:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=BLOCKED_KNOWLEDGE_BASIS_CHANGED")
        for path in changed:
            print(f"CHANGED_BASIS_PATH={path}")
        print("ACTION_REQUIRED=explicit_registry_revalidation")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    expected = tuple(revalidation.get("relevant_path_changes", ()))
    if expected:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK revalidation_claims_nonempty_drift")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    print("ACTIVE_PACKET_REGISTRY_DRIFT=NO_TRACKED_BASIS_DRIFT")
    print(f"REGISTRY_SUBJECT={registry_subject}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
