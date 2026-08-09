from pathlib import Path

import pytest

from rakl.meta_history import compile_meta_fiber_history


def test_live_meta_history_diagnostic() -> None:
    research = Path(__file__).resolve().parents[1] / "research"
    report = compile_meta_fiber_history(research)
    if report.unresolved_issues:
        details = "; ".join(
            f"{issue.kind.value}|{issue.source_path}|{issue.fiber_id}|{issue.message}"
            for issue in report.unresolved_issues
        )
        escaped = details.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error file=tests/test_meta_history_diagnostic.py,line=1,title=meta-ledger::{escaped}")
        pytest.fail(f"live ledger unresolved: {len(report.unresolved_issues)}")
