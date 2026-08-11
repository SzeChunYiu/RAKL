from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/receipts/RAKL_V3_AUTHORITY_HARDENING_20260811.json"


def test_v3_authority_hardening_receipt_reconstructs_exact_payload_and_sources() -> None:
    payload = json.loads(RECEIPT.read_text())
    recorded = payload.pop("payload_sha256")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert sha256(canonical).hexdigest() == recorded
    assert payload["verdict"] == (
        "INTERNAL_CONFORMANCE_PASS_MERGE_ALLOWED_AFTER_REQUIRED_CI"
    )
    assert payload["paper_files_touched"] == []
    assert payload["final_exact_head_review"]["review_result"] == "CLEAN"
    assert payload["final_exact_head_review"]["merge_allowed_after_required_ci"] is True
    assert payload["current_main_refresh"] == {
        "main_commit": "337807625a60ba821e123f39d05f085fd9b0a5fa",
        "history_merge_commit": "815249dff0f8f38b9af5ce12b4b03038a9f66990",
        "merge_parents": [
            "4adcb8e79acb1a070db971e622d6e4ef79e4660d",
            "337807625a60ba821e123f39d05f085fd9b0a5fa",
        ],
        "authority_source_or_test_overlap": False,
        "conflicts": [],
        "paper_files_resolved_or_edited_by_this_round": [],
    }
    for path, expected in payload["source_sha256"].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == expected
