from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_1_HARVEST_PASS_RECEIPT_20260811.json"
PRE_DISCREPANCY = ROOT / "research/paper2_microtrial_v3/PAPER2_V3_2_1_PRE_REHARVEST_CHRONOLOGY_DISCREPANCY_20260811.json"
POST_DISCREPANCY = ROOT / "research/paper2_microtrial_v3/PAPER2_V3_2_1_POST_HARVEST_SYNTHESIS_CHRONOLOGY_DISCREPANCY_20260811.json"
SUCCESSOR = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_1_HARVEST_PASS_CHRONOLOGY_CORRECTED_RECEIPT_20260811.json"
REVIEW = ROOT / "research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_1_HARVEST_PASS_CHRONOLOGY_CORRECTED_INTERNAL_REVIEW_20260811.json"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate(path: Path, schema_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(
        _load(schema_path), format_checker=jsonschema.FormatChecker()
    ).validate(_load(path))


def test_post_harvest_chronology_discrepancy_preserves_invalid_v1() -> None:
    receipt = _load(POST_DISCREPANCY)
    affected = receipt["affected_artifact"]
    dependency = receipt["prior_chronology_discrepancy"]
    assert affected["path"] == str(V1.relative_to(ROOT))
    assert affected["sha256"] == _sha(V1)
    assert affected["recorded_created_at_utc"] == _load(V1)["created_at_utc"]
    assert dependency["path"] == str(PRE_DISCREPANCY.relative_to(ROOT))
    assert dependency["sha256"] == _sha(PRE_DISCREPANCY)
    assert _time(affected["recorded_created_at_utc"]) < _time(dependency["created_at_utc"])
    assert _time(dependency["created_at_utc"]) < _time(affected["first_git_commit_created_at_utc"])
    assert receipt["negative_history_preserved"] is True
    assert receipt["jobs_submitted"] == 0
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
    schema_path = ROOT / receipt["schema_binding"]["path"]
    assert receipt["schema_binding"]["sha256"] == _sha(schema_path)
    _validate(POST_DISCREPANCY, schema_path)


def test_chronology_corrected_synthesis_is_after_every_bound_chronology_artifact() -> None:
    receipt = _load(SUCCESSOR)
    history = receipt["invalid_synthesis_history"]
    discrepancy = receipt["post_harvest_chronology_discrepancy"]
    assert history["path"] == str(V1.relative_to(ROOT))
    assert history["sha256"] == _sha(V1)
    assert history["created_at_utc_valid"] is False
    assert history["preserved"] is True
    assert discrepancy["path"] == str(POST_DISCREPANCY.relative_to(ROOT))
    assert discrepancy["sha256"] == _sha(POST_DISCREPANCY)
    assert _time(receipt["created_at_utc"]) > _time(discrepancy["created_at_utc"])
    assert _time(receipt["created_at_utc"]) > _time("2026-08-11T02:47:21Z")
    assert receipt["verdict"] == (
        "NATIVE_V3_2_1_HARVEST_STAGING_PASS__CHRONOLOGY_CORRECTED__"
        "EXECUTION_PACKET_NOT_YET_FROZEN"
    )
    schema_path = ROOT / receipt["schema_binding"]["path"]
    assert receipt["schema_binding"]["sha256"] == _sha(schema_path)
    _validate(SUCCESSOR, schema_path)


def test_chronology_successor_does_not_widen_native_claim() -> None:
    receipt = _load(SUCCESSOR)
    native = ROOT / receipt["native_harvest"]["path"]
    bootstrap = ROOT / receipt["repair_checkout_bootstrap"]["path"]
    assert receipt["native_harvest"]["sha256"] == _sha(native)
    assert receipt["repair_checkout_bootstrap"]["sha256"] == _sha(bootstrap)
    assert receipt["native_harvest"]["jobs_submitted_by_repair"] == 0
    assert receipt["native_harvest"]["model_execution_performed"] is False
    assert receipt["native_harvest"]["evaluated_result_record_count"] == 0
    assert receipt["cumulative_native_staging_counts"] == {
        "jobs_submitted": 6,
        "model_executions": 0,
        "evaluated_result_records": 0,
    }
    assert receipt["quantitative_figure_generated"] is False
    assert receipt["current_authority"] == (
        "HARVEST_STAGING_PASS__NO_MODEL_EXECUTION__NO_EVALUATED_RESULT"
    )


def test_chronology_corrected_internal_review_is_bound_and_not_independent() -> None:
    review = _load(REVIEW)
    assert review["blocking_concerns"] == []
    assert review["review_class"] == (
        "same_context_internal_recursive_hostile_review_not_independent_not_peer_review"
    )
    assert review["verdict"] == (
        "PASS__NATIVE_HARVEST_STAGING_PASS__CHRONOLOGY_CORRECTED__"
        "EXECUTION_PACKET_NOT_YET_FROZEN"
    )
    b08 = next(item for item in review["concern_ledger"] if item["concern_id"] == "P2-V321-NH-B08")
    assert b08["severity"] == "blocking"
    assert b08["state"] == "closed"
    for item in review["reviewed_artifacts"]:
        assert _sha(ROOT / item["path"]) == item["sha256"]
    schema_path = ROOT / review["schema_binding"]["path"]
    assert review["schema_binding"]["sha256"] == _sha(schema_path)
    _validate(REVIEW, schema_path)
