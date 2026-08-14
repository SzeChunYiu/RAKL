#!/usr/bin/env python3
"""Fail closed if the active packet registry's revalidated knowledge basis drifts.

The immutable registry subject records the knowledge state on which the first
eligibility classification was frozen. A later revalidation may explicitly
review tracked basis changes and move the *freshness anchor* forward without
rewriting preregistration packets. CI verifies three bindings:

1. every tracked change between the original registry subject and the recorded
   revalidation anchor is enumerated in the revalidation receipt;
2. the exact candidate subject contains no unreviewed tracked change after that
   anchor; and
3. the live target branch contains no unreviewed tracked change after that
   anchor, even when the PR head has not been rebased onto the latest target.

The third check is load-bearing: exact-head CI alone cannot see new commits on
main. A later saturation or packet-basis change on main must therefore block a
stale registry PR even when its own head is unchanged.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research/mechanic_research_packets_v1/ACTIVE_PACKET_REGISTRY.json"
REVALIDATION = ROOT / "research/mechanic_research_packets_v1/ACTIVE_REGISTRY_REVALIDATION_20260814.json"
TARGET_REF_ENV = "ACTIVE_PACKET_REGISTRY_TARGET_REF"

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


def _resolve_ref(ref: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def _fail(reason: str, **fields: str) -> int:
    suffix = " ".join(f"{key}={value}" for key, value in fields.items())
    print(f"ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK reason={reason}" + (f" {suffix}" if suffix else ""))
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 1


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    revalidation = json.loads(REVALIDATION.read_text(encoding="utf-8"))

    original = str(registry["subject_main_sha"])
    receipt_original = str(revalidation["original_registry_subject_sha"])
    anchor = str(revalidation["observed_current_main_sha"])
    target_ref = os.environ.get(TARGET_REF_ENV, "HEAD")

    if original != receipt_original:
        return _fail(
            "registry_revalidation_subject_mismatch",
            registry_subject=original,
            revalidation_subject=receipt_original,
        )

    try:
        target_sha = _resolve_ref(target_ref)
    except subprocess.CalledProcessError:
        return _fail("target_ref_unresolvable", target_ref=target_ref)

    if not _is_ancestor(original, anchor):
        return _fail("non_ancestral_revalidation_binding", original=original, anchor=anchor)
    if not _is_ancestor(anchor, "HEAD"):
        return _fail("candidate_head_predates_revalidation_anchor", anchor=anchor)
    if not _is_ancestor(anchor, target_ref):
        return _fail(
            "target_branch_predates_or_diverges_from_revalidation_anchor",
            anchor=anchor,
            target_ref=target_ref,
            target_sha=target_sha,
        )

    reviewed = _changed_paths(original, anchor)
    declared = tuple(sorted(str(path) for path in revalidation.get("relevant_path_changes", ())))
    if reviewed != declared:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK reason=revalidation_change_set_mismatch")
        for path in reviewed:
            print(f"ACTUAL_REVALIDATED_BASIS_CHANGE={path}")
        for path in declared:
            print(f"DECLARED_REVALIDATED_BASIS_CHANGE={path}")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    candidate_drift = _changed_paths(anchor, "HEAD")
    if candidate_drift:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=BLOCKED_KNOWLEDGE_BASIS_CHANGED_ON_CANDIDATE")
        for path in candidate_drift:
            print(f"CHANGED_BASIS_PATH={path}")
        print("ACTION_REQUIRED=explicit_registry_revalidation")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    target_drift = _changed_paths(anchor, target_ref)
    if target_drift:
        print("ACTIVE_PACKET_REGISTRY_DRIFT=BLOCKED_KNOWLEDGE_BASIS_CHANGED_ON_TARGET")
        print(f"TARGET_REF={target_ref}")
        print(f"TARGET_SHA={target_sha}")
        for path in target_drift:
            print(f"CHANGED_BASIS_PATH={path}")
        print("ACTION_REQUIRED=explicit_registry_revalidation")
        print("SCIENTIFIC_AUTHORITY_GRANTED=false")
        return 1

    print("ACTIVE_PACKET_REGISTRY_DRIFT=NO_UNREVIEWED_TRACKED_BASIS_DRIFT")
    print(f"ORIGINAL_REGISTRY_SUBJECT={original}")
    print(f"REVALIDATION_ANCHOR={anchor}")
    print(f"TARGET_REF={target_ref}")
    print(f"TARGET_SHA={target_sha}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
