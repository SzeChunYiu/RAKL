from __future__ import annotations

from pathlib import Path

from rakl.mini_research_metrology import receipt_json


def test_round044_frozen_metrology_receipt_exactly_reconstructs_from_code():
    frozen = Path("research/MINI_RESEARCH_METROLOGY_044_RECEIPT.json").read_text(encoding="utf-8")
    assert frozen == receipt_json()
