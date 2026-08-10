from __future__ import annotations

import json
from pathlib import Path

from rakl.mini_research_demo import receipt_json


def test_committed_mini_demo_receipt_equals_executable_result():
    root = Path(__file__).resolve().parents[1]
    committed = json.loads(
        (root / "research" / "MINI_RESEARCH_DEMO_043_RECEIPT.json").read_text(encoding="utf-8")
    )
    executable_json_shape = json.loads(receipt_json())
    assert committed == executable_json_shape
