from __future__ import annotations

from pathlib import Path

from rakl.mini_archive_demo import receipt_json


def test_round044_frozen_archive_receipt_exactly_reconstructs_from_code():
    frozen = Path("research/MINI_ARCHIVE_STORAGE_044_RECEIPT.json").read_text(encoding="utf-8")
    assert frozen == receipt_json()
