#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from rakl.framework_closure import ClosureDisposition, ClosureIssue, ClosureLedger


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "research" / "unified_problem_solving_v1" / "VTG_CLOSURE_LEDGER.json"
RESULT_PATH = ROOT / "research" / "unified_problem_solving_v1" / "results" / "vtg_closure_audit.json"


def exact_subject_sha() -> str:
    configured = os.environ.get("RAKL_SUBJECT_SHA", "").strip()
    if configured:
        return configured
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _file_evidence_problems(evidence_ids: tuple[str, ...]) -> list[str]:
    problems: list[str] = []
    for evidence_id in evidence_ids:
        if evidence_id.startswith("file:"):
            path = ROOT / evidence_id[5:]
            if not path.exists():
                problems.append(f"missing_evidence_file:{path.relative_to(ROOT)}")
    return problems


def load_ledger(subject_sha: str) -> tuple[ClosureLedger, dict]:
    data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    if data.get("subject_binding") != "RUNTIME_EXACT_GIT_HEAD":
        raise ValueError("closure ledger must bind to runtime exact git head")
    issues = []
    for row in data["issues"]:
        issue = ClosureIssue(
            issue_id=row["issue_id"],
            title=row["title"],
            owner_surface=row["owner_surface"],
            severity=row["severity"],
            subject_hash=subject_sha,
            disposition=ClosureDisposition(row["disposition"]),
            evidence_ids=tuple(row.get("evidence_ids", ())),
            test_paths=tuple(row.get("test_paths", ())),
            falsifier=row.get("falsifier"),
            next_epistemic_cut=row.get("next_epistemic_cut"),
            reviewer_context_ids=tuple(row.get("reviewer_context_ids", ())),
        )
        issues.append(issue)
    ledger = ClosureLedger(
        ledger_id=data["ledger_id"],
        frozen_subject_hash=subject_sha,
        issues=tuple(issues),
        audit_context_ids=tuple(data.get("audit_context_ids", ())),
    )
    return ledger, data


def main() -> int:
    subject_sha = exact_subject_sha()
    ledger, raw = load_ledger(subject_sha)
    problems: list[dict] = []
    for issue_id, issue_problems in ledger.problems:
        problems.append({"issue_id": issue_id, "problems": list(issue_problems)})
    for issue in ledger.issues:
        file_problems = _file_evidence_problems(issue.evidence_ids)
        file_problems.extend(
            f"missing_test_file:{test_path}"
            for test_path in issue.test_paths
            if not (ROOT / test_path).exists()
        )
        if file_problems:
            problems.append({"issue_id": issue.issue_id, "problems": file_problems})

    disposition_counts: dict[str, int] = {}
    for issue in ledger.issues:
        disposition_counts[issue.disposition.value] = disposition_counts.get(issue.disposition.value, 0) + 1

    result = {
        "schema": "orion.vtg.closure-audit-result.v1",
        "subject_sha": subject_sha,
        "ledger_id": ledger.ledger_id,
        "registered_issue_count": len(ledger.issues),
        "registered_issues_all_owned": not problems,
        "problem_count": len(problems),
        "problems": problems,
        "disposition_counts": disposition_counts,
        "open_empirical_issue_ids": [
            issue.issue_id for issue in ledger.issues if issue.disposition is ClosureDisposition.OPEN_EMPIRICAL
        ],
        "open_external_assurance_issue_ids": [
            issue.issue_id for issue in ledger.issues if issue.disposition is ClosureDisposition.OPEN_EXTERNAL_ASSURANCE
        ],
        "nature_skills_frozen_rubric": raw.get("nature_skills_frozen_rubric"),
        "global_hidden_issue_absence_claimed": False,
        "scientific_authority_granted": False,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"VTG_CLOSURE_SUBJECT={subject_sha}")
    print(f"REGISTERED_ISSUES={len(ledger.issues)}")
    print(f"REGISTERED_ISSUES_ALL_OWNED={'true' if not problems else 'false'}")
    print("GLOBAL_HIDDEN_ISSUE_ABSENCE_CLAIMED=false")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    if problems:
        for problem in problems:
            print(json.dumps(problem, sort_keys=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
