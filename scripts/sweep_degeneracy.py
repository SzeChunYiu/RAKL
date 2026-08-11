#!/usr/bin/env python3
"""Sweep repository measurement surfaces for the self-grading defect class.

Reports; repairs nothing. Surfaces owned by other lanes are inventoried with a
reproduction so the owning lane can fix them.

Exit code is the worst *actionable* status found, using
``degeneracy_probe.EXIT_CODES``. Sealed known Type B defects under issue #283
remain inventoried as DEGENERATE but do not drive the exit code when their
disposition hash still matches the frozen prompt bytes. ``CANNOT_CHECK`` can
never be mistaken for a pass by a caller.

    python scripts/sweep_degeneracy.py [--json OUT]
"""

from __future__ import annotations

import argparse
import hashlib
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
DISPOSITION_NAME = "TYPE_B_LEAK_DISPOSITION_283.json"


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
        if path.name == DISPOSITION_NAME:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        found: dict[str, frozenset[str]] = {}

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    # ROUND044 names the misalignment gold differently from the
                    # v1 evaluator; alias so v4.* arm pairs are assessed rather
                    # than left UNASSESSED (issue #283).
                    canonical = {
                        "misaligned_for_direct_target_contradiction_source_ids": "misaligned_source_ids",
                    }.get(key, key)
                    if canonical in GOLD_FIELDS and isinstance(value, list):
                        found.setdefault(canonical, frozenset(str(v) for v in value))
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(payload)
        if found:
            return found
    return {}


def _sealed_known_type_b(directory: Path, treatment: Path) -> tuple[bool, str]:
    """Return whether DEGENERATE is a hash-locked sealed known defect (#283)."""

    disposition_path = directory / DISPOSITION_NAME
    if not disposition_path.is_file():
        return False, ""
    try:
        payload = json.loads(disposition_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "disposition present but unreadable"
    if payload.get("status") != "SEALED_KNOWN_TYPE_B_DEGENERATE":
        return False, "disposition status is not SEALED_KNOWN_TYPE_B_DEGENERATE"
    expected = payload.get("sealed_rakl_context_prompt_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        return False, "disposition missing sealed prompt sha256"
    actual = hashlib.sha256(treatment.read_bytes()).hexdigest()
    if actual != expected:
        return (
            False,
            "disposition prompt hash mismatch: sealed bytes were mutated without "
            "a new instrument identity (refusing to treat as sealed-known)",
        )
    for receipt in payload.get("sealed_ingest_receipts") or []:
        if not isinstance(receipt, dict):
            continue
        rel = receipt.get("path")
        digest = receipt.get("sha256")
        if not isinstance(rel, str) or not isinstance(digest, str):
            continue
        path = ROOT / rel
        if not path.is_file():
            return False, f"sealed ingest receipt missing: {rel}"
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            return (
                False,
                f"sealed ingest receipt rewritten: {rel}",
            )
    return True, "sealed known Type B defect under issue #283; scores preserved as NOT_INFORMATIVE"


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
        extra_reasons = (
            f"gold provenance: {provenance}",
            "graded fields CHECKED: " + ", ".join(sorted(gold)),
            "graded fields NOT LOCATED (unassessed, not clean): "
            + (", ".join(sorted(set(GOLD_FIELDS) - set(gold))) or "none"),
        )
        if report.status is DegeneracyStatus.DEGENERATE:
            sealed, note = _sealed_known_type_b(directory, treatment)
            if sealed:
                extra_reasons = extra_reasons + (
                    note,
                    "exit_policy: sealed-known DEGENERATE does not drive sweep exit",
                )
            elif note:
                extra_reasons = extra_reasons + (note,)
        reports.append(
            ProbeReport(
                report.surface,
                report.status,
                report.findings,
                report.reasons + extra_reasons,
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


def _is_sealed_known(report: ProbeReport) -> bool:
    return any(
        reason.startswith("sealed known Type B defect") for reason in report.reasons
    )


def actionable_status(reports: list[ProbeReport]) -> DegeneracyStatus:
    """Worst status after excluding hash-locked sealed known Type B defects."""

    actionable = [
        report.status
        for report in reports
        if not (
            report.status is DegeneracyStatus.DEGENERATE and _is_sealed_known(report)
        )
    ]
    if not actionable:
        return DegeneracyStatus.CLEAN
    return min(actionable, key=lambda status: _RANK[status])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    args = parser.parse_args()

    reports = sweep_arm_pairs(ROOT)
    reports.sort(key=lambda r: (_RANK[r.status], r.surface))

    print(f"{'STATUS':<14} {'FINDINGS':>8}  SURFACE")
    print("-" * 92)
    for report in reports:
        marker = " [sealed-known]" if _is_sealed_known(report) else ""
        print(f"{report.status.value:<14} {len(report.findings):>8}  {report.surface}{marker}")
    for report in reports:
        for finding in report.findings:
            print(f"\n[{finding.status.value}] {report.surface}\n  {finding.detail}")
            for line in finding.evidence:
                print(f"    | {line}")

    worst_raw = min((r.status for r in reports), key=lambda s: _RANK[s], default=DegeneracyStatus.CLEAN)
    worst = actionable_status(reports)
    summary = {
        "worst_status": worst.value,
        "worst_status_including_sealed_known": worst_raw.value,
        "counts": {
            status.value: sum(1 for r in reports if r.status is status)
            for status in DegeneracyStatus
        },
        "sealed_known_degenerate": sum(
            1
            for r in reports
            if r.status is DegeneracyStatus.DEGENERATE and _is_sealed_known(r)
        ),
        "reports": [r.to_dict() for r in reports],
    }
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")
    print(
        f"\nworst actionable status: {worst.value}  "
        f"(including sealed-known: {worst_raw.value})  counts: {summary['counts']}"
    )
    return EXIT_CODES[worst]


if __name__ == "__main__":
    raise SystemExit(main())
