"""Tests for ALR neighbouring-benchmark residual audit (#154)."""

from __future__ import annotations

from rakl.alr_neighbour_residual import load_audit, validate_audit


def test_neighbour_residual_demonstrated_novelty_unlicensed() -> None:
    audit = validate_audit(load_audit())
    assert audit.novelty_licensed is False
    assert audit.grants_scientific_authority is False
    assert audit.status == "RESIDUAL_DEMONSTRATED_NOVELTY_UNLICENSED"
    assert len(audit.rows) >= 4
    assert any(r.benchmark_id == "ALR_V2_THIS_PROTOCOL" for r in audit.rows)
