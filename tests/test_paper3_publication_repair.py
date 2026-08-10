from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "structural_amortization"


def _manuscript() -> str:
    paths = [SOURCE / "main.tex", *sorted((SOURCE / "sections").glob("*.tex"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_paper3_repair_uses_width_safe_layouts_and_precise_missing_evidence_language() -> None:
    manuscript = _manuscript()
    assert r"\begin{tabularx}{\linewidth}" in manuscript
    assert r"\begin{aligned}" in manuscript
    assert r"\path{src/rakl/structural_transfer.py}" not in manuscript
    assert "retrieval/adaptation/verification costs" not in manuscript
    assert "remains unlicensed until" in manuscript
    assert "remains falsified unless" not in manuscript


def test_paper3_workflow_fails_on_blocking_pdf_warnings() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "paper3-structural-amortization.yml"
    ).read_text(encoding="utf-8")
    assert r"Overfull \\[hv]box" in workflow
    assert "Float too large" in workflow
    assert "There were undefined references" in workflow
    assert "Blocking Paper 3 LaTeX/PDF warning detected" in workflow


def test_paper3_internal_review_binds_post_audit_sources() -> None:
    review = json.loads(
        (
            ROOT
            / "research"
            / "receipts"
            / "PAPER3_CHEAP_GATE_INTERNAL_REVIEW_20260810.json"
        ).read_text(encoding="utf-8")
    )
    resolved = set(review["resolved_this_iteration"])
    assert "P3-GATE-R4-TYPOGRAPHY" in resolved
    assert "P3-GATE-R4-MISSING-EVIDENCE" in resolved
    subjects = review["subjects"]
    for path, key in (
        (SOURCE / "main.tex", "manuscript_source_sha256"),
        (SOURCE / "sections" / "03_benchmark.tex", "benchmark_section_sha256"),
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == subjects[key]
