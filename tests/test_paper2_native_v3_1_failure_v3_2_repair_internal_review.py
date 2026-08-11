from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REVIEW = (
    ROOT
    / "research/paper2_microtrial_v3/"
    "PAPER2_NATIVE_V3_1_FAILURE_V3_2_REPAIR_INTERNAL_REVIEW_20260811.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v3_2_internal_review_binds_closed_recursive_hostile_passes() -> None:
    review = _load(REVIEW)
    assert _sha(ROOT / review["schema_binding"]["path"]) == review["schema_binding"]["sha256"]
    for artifact in review["reviewed_artifacts"]:
        assert _sha(ROOT / artifact["path"]) == artifact["sha256"]
    assert review["passes"] == [
        {
            "concerns": ["P2-V32-HR-B01", "P2-V32-HR-B02", "P2-V32-HR-B03"],
            "pass_id": "initial_hostile_review",
            "verdict": "BLOCKED",
        },
        {
            "concerns": ["P2-V32-HR-B04", "P2-V32-HR-B05"],
            "pass_id": "post_repair_hostile_review_1",
            "verdict": "BLOCKED",
        },
        {
            "concerns": ["P2-V32-HR-B06", "P2-V32-HR-B07"],
            "pass_id": "post_repair_hostile_review_2",
            "verdict": "BLOCKED",
        },
        {
            "concerns": [],
            "pass_id": "post_repair_hostile_review_3",
            "verdict": "PASS",
        },
    ]
    assert {item["concern_id"] for item in review["concern_ledger"]} == {
        f"P2-V32-HR-B0{index}" for index in range(1, 8)
    }
    assert all(item["state"] == "closed" for item in review["concern_ledger"])
    assert review["blocking_concerns"] == []
    assert review["checks"]["reviewer_final_focused_tests"] == {"failed": 0, "passed": 46}
    assert review["checks"]["post_review_receipt_focused_tests"] == {
        "failed": 0,
        "passed": 47,
    }
    assert review["checks"]["native_v3_2_jobs_submitted"] == 0
    assert review["checks"]["native_v3_2_model_executions"] == 0
    assert review["checks"]["native_v3_2_evaluated_result_records"] == 0
    assert review["verdict"] == (
        "PASS__V3_1_FAILURE_PRESERVED__V3_2_REPAIR_READY_NOT_SUBMITTED"
    )
    assert "not independent review" in review["claim_boundary"].lower()

    jsonschema = pytest.importorskip("jsonschema")
    schema = _load(ROOT / review["schema_binding"]["path"])
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(review)
