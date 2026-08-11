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
    assert payload["verdict"] == "INTERNAL_ASSURANCE_PASS_PENDING_INDEPENDENT_REVIEW"
    assert payload["paper_files_touched"] == []
    for path, expected in payload["source_sha256"].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == expected
