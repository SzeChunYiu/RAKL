from __future__ import annotations

import json

from rakl.failure_analysis import OracleVerdict, minimize_failure_conditions
from rakl.failure_analysis_io import RECEIPT_SCHEMA_VERSION, receipt_json_bytes, receipt_to_dict


def _receipt():
    report = minimize_failure_conditions(
        ("A", "B", "C"),
        lambda items: OracleVerdict.FAIL if {"A", "B"} <= set(items) else OracleVerdict.PASS,
        analysis_id="io-test",
        oracle_id="oracle-io",
        context_hash="ctx-io",
        revision_id="rev-io",
        failure_id="failure-io",
    )
    assert report.receipt is not None
    return report.receipt


def test_receipt_projection_matches_schema_contract_shape() -> None:
    payload = receipt_to_dict(_receipt())
    assert payload["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert payload["kind"] == "FAILURE_CONDITION_MINIMIZATION"
    assert payload["minimality_kind"] == "ONE_MINIMAL"
    assert payload["result_sets"] == [["A", "B"]]
    assert len(payload["content_hash"]) == 64
    assert payload["grants_causal_authority"] is False
    assert payload["grants_scientific_authority"] is False
    assert payload["grants_method_promotion_authority"] is False


def test_receipt_json_projection_is_deterministic_roundtrippable_json() -> None:
    receipt = _receipt()
    left = receipt_json_bytes(receipt)
    right = receipt_json_bytes(receipt)
    assert left == right
    parsed = json.loads(left)
    assert parsed == receipt_to_dict(receipt)
