from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_STAGING_FAILURE_REPAIR_INTERNAL_REVIEW_20260811.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_internal_review_binds_exact_post_repair_subject_and_closed_blocker() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    for artifact in review["reviewed_artifacts"]:
        assert _sha(ROOT / artifact["path"]) == artifact["sha256"]
    assert review["passes"] == [
        {"concerns": ["P2-V31-HR-B01"], "pass_id": "initial_hostile_review", "verdict": "BLOCKED"},
        {"concerns": [], "pass_id": "post_repair_hostile_review", "verdict": "PASS"},
    ]
    assert review["concern_ledger"][0]["state"] == "closed"
    assert review["concern_ledger"][0]["planted_former_exploit_verdict"] == "HARVEST_CANNOT_CHECK"
    assert review["concern_ledger"][0]["planted_former_exploit_negative_history_preserved"] is False
    assert review["blocking_concerns"] == []
    assert review["verdict"] == "PASS__V3_FAILURE_PRESERVED__V3_1_REPAIR_READY_NOT_SUBMITTED"
    assert "not independent" in review["claim_boundary"].lower()
