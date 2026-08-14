"""Deterministic serialization helpers for proposal-only failure-analysis receipts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .failure_analysis import FailureAnalysisReceipt


RECEIPT_SCHEMA_VERSION = "orion.failure-analysis-receipt.v1"


def receipt_to_dict(receipt: FailureAnalysisReceipt) -> dict[str, Any]:
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "analysis_id": receipt.analysis_id,
        "kind": receipt.kind.value,
        "oracle_id": receipt.oracle_id,
        "context_hash": receipt.context_hash,
        "revision_id": receipt.revision_id,
        "target_id": receipt.target_id,
        "source_condition_ids": list(receipt.source_condition_ids),
        "result_sets": [list(result) for result in receipt.result_sets],
        "minimality_kind": receipt.minimality_kind.value,
        "oracle_calls": receipt.oracle_calls,
        "cannot_check_calls": receipt.cannot_check_calls,
        "notes": list(receipt.notes),
        "content_hash": receipt.content_hash,
        "grants_causal_authority": False,
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
    }


def receipt_json_bytes(receipt: FailureAnalysisReceipt) -> bytes:
    return json.dumps(
        receipt_to_dict(receipt),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def write_receipt(receipt: FailureAnalysisReceipt, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(receipt_json_bytes(receipt) + b"\n")
    return destination
