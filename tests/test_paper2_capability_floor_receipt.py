from __future__ import annotations

import json
from pathlib import Path

from rakl.paper2_capability_floor_receipt import (
    CAPABILITY_RECEIPT_PATH,
    build_capability_floor_decision_receipt,
)
from rakl.v3_authority import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_capability_floor_receipt_exists_and_blocks_oracle_kill() -> None:
    receipt = _load(ROOT / CAPABILITY_RECEIPT_PATH)
    assert receipt["oracle_execution_status"] == "NOT_EXECUTED"
    assert receipt["oracle_blocked_status"] == "CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE"
    assert receipt["decision"]["blocks_confirmatory_without_oracle"] is True
    assert receipt["decision"]["kill_narrowing_available"] is False
    assert receipt["provisional_classification"] == "SUSPECTED_CAPABILITY_FLOOR_PENDING_ORACLE"


def test_capability_receipt_binds_existing_jobs_only() -> None:
    receipt = _load(ROOT / CAPABILITY_RECEIPT_PATH)
    v12 = receipt["experience_benchmark_v1_2"]
    assert v12["job_id"] == 3476548
    assert v12["reset_success_rate"] == 0.0
    assert v12["learning_success_rate"] == 0.0
    micro = receipt["adjacent_microtrial_capability_evidence"]
    assert micro["microtrial_v4_2"]["exact_conceptual_pass_arm_count"] == 0
    assert micro["microtrial_v4_3"]["exact_conceptual_pass_arm_count"] == 0
    assert micro["microtrial_v4_3_1"]["exact_conceptual_pass_arm_count"] == 0


def test_capability_receipt_matches_live_builder() -> None:
    live = build_capability_floor_decision_receipt(ROOT, created_at_utc="2026-08-11T22:00:00Z")
    frozen = _load(ROOT / CAPABILITY_RECEIPT_PATH)
    for key in (
        "oracle_execution_status",
        "oracle_blocked_status",
        "provisional_classification",
        "observed_facts",
        "decision",
    ):
        assert live[key] == frozen[key]
    assert live["artifact_sha256"] == canonical_sha256({k: v for k, v in live.items() if k != "artifact_sha256"})
