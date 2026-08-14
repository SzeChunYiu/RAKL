#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from rakl.authority_chokepoint import audit_source_tree, format_findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = audit_source_tree(root)
    payload = {
        "schema_version": "paper1-production-authority-chokepoint-audit-v1",
        "files_checked": report.files_checked,
        "passed": report.passed,
        "findings": [
            {
                "path": item.path,
                "line": item.line,
                "surface": item.surface,
                "detail": item.detail,
            }
            for item in report.findings
        ],
        "grants_scientific_authority": False,
    }
    print(json.dumps(payload, sort_keys=True))
    if not report.passed:
        print(format_findings(report.findings))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
