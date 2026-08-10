from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from rakl.mini_research_demo import run_mini_research_demo


def test_committed_mini_demo_receipt_equals_executable_result():
    root = Path(__file__).resolve().parents[1]
    committed = json.loads(
        (root / "research" / "MINI_RESEARCH_DEMO_043_RECEIPT.json").read_text(encoding="utf-8")
    )
    executable_json_shape = json.loads(json.dumps(asdict(run_mini_research_demo())))
    assert committed == executable_json_shape
