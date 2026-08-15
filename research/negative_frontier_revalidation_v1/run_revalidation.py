"""Revalidate the twelve locally-revivable negatives against current main.

Two records have already turned out to carry levers that main has since executed
or refuted. This checks the rest of the workable set the same way, so that
effort is not spent reviving negatives that are already discharged.

Every hit is reported with the evidence needed to verify it by hand; nothing is
reclassified automatically.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

INVENTORY = Path("research/negative_frontier_v1/INVENTORY.json")
OUT = Path("research/negative_frontier_revalidation_v1/RESULT.json")

# Successor artifacts observed on main that plausibly discharge a lever. Each is
# checked for existence; the mapping is asserted only where the artifact names
# the record's own question.
CANDIDATES = {
    "p3-instrument-inadmissible-ceiling": [
        "research/paper3_lift_ceiling_qualification_v1/CEILING_RECEIPT.json",
    ],
    "p2-arn-v4-battery-failed": [
        "research/arn_v4r_role_boost_repair_v1/RESULT.json",
    ],
    "p2-arn-v3-capability-absent": [
        "research/paper2_external_corpus_v1/results_v5_multifamily/RESULT.json",
    ],
    "p2-arn-capability-absent": [
        "research/paper2_external_corpus_v1/results_v5_multifamily/RESULT.json",
    ],
    "p1-source-monitoring-repetition-attack": [
        "research/p1_source_identity_repair_v1",
    ],
}


def sh(*args: str) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    local = [r for r in inventory["records"] if r["class"] == "REVIVABLE_LOCAL"]

    rows = []
    for record in local:
        slug = record["slug"]
        receipt = record.get("receipt_path") or ""
        receipt_exists = bool(receipt) and Path(receipt).exists()

        # Commits touching the record's own receipt directory since the frontier
        # was authored. A record whose evidence moved after it was inventoried is
        # a staleness candidate on its own.
        receipt_dir = str(Path(receipt).parent) if receipt else ""
        recent = (
            sh("git", "log", "--oneline", "--since=2026-08-15", "--", receipt_dir)
            if receipt_dir
            else ""
        )

        successors = []
        for candidate in CANDIDATES.get(slug, []):
            path = Path(candidate)
            if not path.exists():
                continue
            referenced = candidate in json.dumps(record)
            successors.append(
                {
                    "artifact": candidate,
                    "exists_on_main": True,
                    "referenced_by_the_record": referenced,
                    "commit": sh("git", "log", "-1", "--format=%h %s", "--", candidate)[:110],
                }
            )

        undisclosed = [s for s in successors if not s["referenced_by_the_record"]]
        rows.append(
            {
                "slug": slug,
                "terminal": record["terminal"][:80],
                "lever": (record.get("core_lever") or "")[:110],
                "receipt_path": receipt,
                "receipt_exists_on_main": receipt_exists,
                "commits_touching_receipt_dir_since_inventory": recent.splitlines()[:3],
                "successor_artifacts_found": successors,
                "staleness": (
                    "LEVER_ALREADY_EXERCISED__NOT_REFERENCED"
                    if undisclosed
                    else "NO_SUCCESSOR_FOUND"
                ),
            }
        )

    stale = [r for r in rows if r["staleness"] != "NO_SUCCESSOR_FOUND"]
    missing_receipts = [r for r in rows if not r["receipt_exists_on_main"]]

    result = {
        "schema_version": "rakl-negative-frontier-revalidation-v1",
        "status": "PROPOSAL_ONLY__NO_RECORD_RECLASSIFIED_AUTOMATICALLY",
        "grants_scientific_authority": False,
        "question": "Which of the twelve locally-revivable negatives carry levers that main has already exercised?",
        "why": (
            "Two records already turned out to be stale — p2-arn-v4's lever was refuted by "
            "execution, and p3-instrument-inadmissible-ceiling's lever was executed on main "
            "without the record referencing the receipt. Spending revival effort on a discharged "
            "lever is the cheapest avoidable waste in the workable set."
        ),
        "records_checked": len(rows),
        "stale_records": len(stale),
        "records_whose_receipt_is_absent_from_main": [r["slug"] for r in missing_receipts],
        "caveat": (
            "Successor candidates are asserted by path and verified only for existence and "
            "non-reference. Each must be read before any record is reclassified; this run "
            "reclassifies nothing."
        ),
        "per_record": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for row in rows:
        mark = "STALE" if row["staleness"] != "NO_SUCCESSOR_FOUND" else "     "
        recv = "" if row["receipt_exists_on_main"] else "  [receipt absent from main]"
        print(f"{mark} {row['slug']:<40s}{recv}")
        for s in row["successor_artifacts_found"]:
            flag = "not referenced" if not s["referenced_by_the_record"] else "referenced"
            print(f"        -> {s['artifact']}  ({flag})")
    print(f"\nstale: {len(stale)}/{len(rows)}   receipts absent from main: {len(missing_receipts)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
