#!/usr/bin/env python3
"""Fail closed if the active packet registry's revalidated knowledge basis drifts.

The immutable registry subject records the knowledge state on which the first
eligibility classification was frozen.  A later revalidation may explicitly
review tracked basis changes and move the *freshness anchor* forward without
rewriting preregistration packets.  CI verifies both halves:

1. every tracked change between the original registry subject and the recorded
   revalidation anchor is enumerated in the revalidation receipt; and
2. no tracked change exists after that anchor on the exact subject being tested.

Thus a new saturation round cannot silently leave stale ACTIVE packets eligible,
while an explicit later revalidation can legitimately incorporate new knowledge.
"""
from __future__ import annotations

import json
import subprocess
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


def _changed_paths(base: str, head: str) -> tuple[str, ...]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..{head}", "--", *TRACKED_BASIS_PATHS],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return tuple(sorted(line.strip() for line in proc.stdout.splitlines() if line.strip()))


def _is_ancestor(base: str, head: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head],
        cwd=ROOT,
        check=False,
        capture_output=True,
    ).returncode == 0


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    revalidation = json.loads(REVALIDATION.read_text(encoding="utf-8"))

    original = str(registry["subject_main_sha"])
    receipt_original = str(revalidation["original_registry_subject_sha"])
    anchor = str(revalidation["observed_current_main_sha"])

    if original != receipt_original:
        print(
            "ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK "
            f"registry_subject={original} revalidation_subject={receipt_original}"
        )
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    if not _is_ancestor(original, anchor) or not _is_ancestor(anchor, "HEAD"):
        print(
            "ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK "
            f"non_ancestral_binding original={original} anchor={anchor}"
        )
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    reviewed = _changed_paths(original, anchor)
    declared = tuple(sorted(str(path) for path in revalidation.get("relevant_path_changes", ())))
    if reviewed != declared:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK revalidation_change_set_mismatch")
        for path in reviewed:
            print(f"ACTUAL_REVALIDATED_BASIS_CHANGE={path}")
        for path in declared:
            print(f"DECLARED_REVALIDATED_BASIS_CHANGE={path}")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    post_anchor = _changed_paths(anchor, "HEAD")
    if post_anchor:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=BLOCKED_KNOWLEDGE_BASIS_CHANGED_AFTER_REVALIDATION")
        for path in post_anchor:
            print(f"CHANGED_BASIS_PATH={path}")
        print("ACTION_REQUIRED=explicit_registry_revalidation")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    print("ACTIVE_PACKET_REGISTRY_DRIFT=NO_UNREVIEWED_TRACKED_BASIS_DRIFT")
    print(f"ORIGINAL_REGISTRY_SUBJECT={original}")
    print(f"REVALIDATION_ANCHOR={anchor}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
