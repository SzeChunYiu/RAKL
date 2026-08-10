from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "structural_amortization"


def test_paper3_v2_input_graph_is_explicit_and_complete() -> None:
    main_v2 = (SOURCE / "main_v2.tex").read_text(encoding="utf-8")
    inputs = re.findall(r"\\input\{([^}]+)\}", main_v2)
    assert "sections/03_benchmark_v2" in inputs
    assert "sections/05_evaluation_plan_v2" in inputs
    assert "sections/03_benchmark" not in inputs
    assert "sections/05_evaluation_plan" not in inputs
    assert inputs
    for relative in inputs:
        assert (SOURCE / f"{relative}.tex").is_file(), relative


def test_paper3_v2_workflow_builds_and_uploads_exact_versioned_manuscript() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "paper3-confirmatory-gate-v2.yml"
    ).read_text(encoding="utf-8")
    assert "main_v2.tex" in workflow
    assert "main_v2.pdf" in workflow
    assert "main_v2.log" in workflow
    assert r"Overfull \\[hv]box" in workflow
    assert "Float too large" in workflow
    assert "There were undefined references" in workflow
    assert "Blocking Paper 3 v2 LaTeX/PDF warning detected" in workflow
    assert "schemas/paper3-*.schema.json" in workflow


def test_paper3_v2_internal_review_is_not_independent_and_keeps_gate_closed() -> None:
    review = json.loads(
        (
            ROOT
            / "research"
            / "receipts"
            / "PAPER3_V2_GATE_INTERNAL_REVIEW_20260810.json"
        ).read_text(encoding="utf-8")
    )
    assert review["review_class"] == "same_context_internal_review_not_independent_peer_review"
    assert review["blocking_code_findings_remaining"] == []
    assert review["external_evidence_gate"]["passed"] is False
    assert review["training_inference_authorized"] is False
    for relative, digest in review["subject_artifact_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
