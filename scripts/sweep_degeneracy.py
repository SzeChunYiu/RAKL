#!/usr/bin/env python3
"""Sweep repository measurement surfaces for the self-grading defect class.

Reports; repairs nothing. Surfaces owned by other lanes are inventoried with a
reproduction so the owning lane can fix them.

Exit code is the worst status found, using ``degeneracy_probe.EXIT_CODES``, so
``CANNOT_CHECK`` can never be mistaken for a pass by a caller.

    python scripts/sweep_degeneracy.py [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.degeneracy_probe import (  # noqa: E402
    EXIT_CODES,
    ArmPair,
    DegeneracyStatus,
    ProbeReport,
    probe_arm_answer_leak,
)

GOLD_FIELDS = ("misaligned_source_ids", "required_refuted_source_ids")


#: Task-level sealed known-answer evaluator shared by every pendulum microtrial
#: version. Individual version directories mostly do not restate it, so without
#: this fallback six of seven arm pairs would report CANNOT_CHECK and the live
#: instrument would go unassessed.
SHARED_GOLD = ROOT / "research/ROUND044_MATCHED_LLM_MICROTRIAL_PREREGISTRATION.json"


def _find_gold(directory: Path) -> tuple[dict[str, frozenset[str]], str]:
    """Recover evaluator gold for an arm pair, if it is recorded anywhere.

    Returns the gold plus the provenance of where it came from. Searched rather
    than hard-coded: a surface whose gold cannot be located is reported
    CANNOT_CHECK, never silently passed.
    """

    local = _scan_for_gold(sorted(directory.glob("*.json")) + sorted(directory.glob("*/*.json")))
    if local:
        return local, f"{directory.name} (local)"
    shared = _scan_for_gold([SHARED_GOLD]) if SHARED_GOLD.is_file() else {}
    if shared:
        return shared, SHARED_GOLD.relative_to(ROOT).as_posix()
    return {}, ""


def _scan_for_gold(candidates: list[Path]) -> dict[str, frozenset[str]]:
    for path in candidates:
        if "raw_outputs" in path.parts or path.name.startswith("result_receipt"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        found: dict[str, frozenset[str]] = {}

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in GOLD_FIELDS and isinstance(value, list):
                        found.setdefault(key, frozenset(str(v) for v in value))
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(payload)
        if found:
            return found
    return {}


def sweep_arm_pairs(root: Path) -> list[ProbeReport]:
    """Type B: does any treatment arm carry the graded answer?"""

    reports: list[ProbeReport] = []
    for directory in sorted((root / "research").glob("paper2_microtrial_*")):
        treatment = directory / "RAKL_CONTEXT_PROMPT.txt"
        control = directory / "DIRECT_CORPUS_PROMPT.txt"
        surface = f"{directory.name} RAKL_CONTEXT vs DIRECT_CORPUS"
        if not treatment.is_file() or not control.is_file():
            reports.append(
                ProbeReport(
                    surface,
                    DegeneracyStatus.CANNOT_CHECK,
                    reasons=("arm prompt pair not present in this directory",),
                )
            )
            continue
        gold, provenance = _find_gold(directory)
        if not gold:
            reports.append(
                ProbeReport(
                    surface,
                    DegeneracyStatus.CANNOT_CHECK,
                    reasons=(
                        "no evaluator gold found in this directory or in the "
                        "shared preregistration; the arm pair exists but its graded "
                        "answer could not be located, so leakage was NOT assessed",
                    ),
                )
            )
            continue
        report = probe_arm_answer_leak(
            ArmPair(
                surface,
                treatment.read_text(encoding="utf-8"),
                control.read_text(encoding="utf-8"),
                gold,
            )
        )
        reports.append(
            ProbeReport(
                report.surface,
                report.status,
                report.findings,
                report.reasons
                + (
                    f"gold provenance: {provenance}",
                    "graded fields CHECKED: " + ", ".join(sorted(gold)),
                    "graded fields NOT LOCATED (unassessed, not clean): "
                    + (
                        ", ".join(sorted(set(GOLD_FIELDS) - set(gold))) or "none"
                    ),
                ),
                report.records_probed,
            )
        )
    return reports


_RANK = {
    DegeneracyStatus.DEGENERATE: 0,
    DegeneracyStatus.SUSPECT: 1,
    DegeneracyStatus.CANNOT_CHECK: 2,
    DegeneracyStatus.CLEAN: 3,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    args = parser.parse_args()

    reports = sweep_arm_pairs(ROOT)
    reports.sort(key=lambda r: (_RANK[r.status], r.surface))

    print(f"{'STATUS':<14} {'FINDINGS':>8}  SURFACE")
    print("-" * 92)
    for report in reports:
        print(f"{report.status.value:<14} {len(report.findings):>8}  {report.surface}")
    for report in reports:
        for finding in report.findings:
            print(f"\n[{finding.status.value}] {report.surface}\n  {finding.detail}")
            for line in finding.evidence:
                print(f"    | {line}")

    worst = min((r.status for r in reports), key=lambda s: _RANK[s], default=DegeneracyStatus.CLEAN)
    summary = {
        "worst_status": worst.value,
        "counts": {
            status.value: sum(1 for r in reports if r.status is status)
            for status in DegeneracyStatus
        },
        "reports": [r.to_dict() for r in reports],
    }
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")
    print(f"\nworst status: {worst.value}  counts: {summary['counts']}")
    return EXIT_CODES[worst]


if __name__ == "__main__":
    raise SystemExit(main())
