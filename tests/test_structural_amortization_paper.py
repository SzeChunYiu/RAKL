from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "structural_amortization"
INPUT_RE = re.compile(r"\\input\{([^}]+)\}")
CITE_RE = re.compile(r"\\cite\{([^}]+)\}")
BIB_RE = re.compile(r"\\bibitem\{([^}]+)\}")


def _expand(path: Path, stack: tuple[Path, ...] = ()) -> str:
    path = path.resolve()
    if path in stack:
        raise AssertionError(f"recursive TeX input: {path}")
    text = path.read_text(encoding="utf-8")

    def repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        child = (path.parent / raw).resolve()
        if child.suffix != ".tex":
            child = child.with_suffix(".tex")
        assert SOURCE.resolve() in (child, *child.parents), f"path escape: {raw}"
        assert child.exists(), f"missing TeX input: {raw}"
        return _expand(child, stack + (path,))

    return INPUT_RE.sub(repl, text)


def _manuscript() -> str:
    return _expand(SOURCE / "main.tex")


def test_structural_amortization_source_is_modular_and_complete() -> None:
    main = (SOURCE / "main.tex").read_text(encoding="utf-8")
    required = {
        "sections/01_problem_and_parents",
        "sections/01b_shared_experience_nearest_work",
        "sections/02_structural_formalism",
        "sections/02b_directionality_evidence",
        "sections/03_benchmark",
        "sections/04_cost_and_hypotheses",
        "sections/05_evaluation_plan",
        "sections/99_references",
    }
    assert required.issubset(set(INPUT_RE.findall(main)))
    assert len(_manuscript()) > 14000


def test_all_paper3_citations_have_unique_bibliography_entries() -> None:
    manuscript = _manuscript()
    keys = [key for block in CITE_RE.findall(manuscript) for key in block.split(",")]
    bibs = BIB_RE.findall(manuscript)
    assert len(bibs) == len(set(bibs))
    missing = sorted(set(keys) - set(bibs))
    assert missing == []


def test_paper3_claim_boundary_remains_preregistered_not_result_claim() -> None:
    manuscript = _manuscript()
    assert "not yet an efficiency result" in manuscript
    assert "remains unlicensed until" in manuscript
    assert "remains falsified unless" not in manuscript
    assert "total cost-to-capability" in manuscript
    assert "Q3" in manuscript


def test_paper3_has_directional_and_boundary_aware_transfer_language() -> None:
    manuscript = _manuscript()
    lower = manuscript.lower()
    assert "directional structural witness" in lower
    assert "non-preserved" in lower
    assert "boundary" in lower
    assert "need not be transitive" in lower


def test_paper3_reports_fail_closed_cheap_gate_without_upgrading_authority() -> None:
    manuscript = _manuscript()
    assert "FAIL\\_CLOSED\\_MISSING\\_INDEPENDENT\\_ANNOTATION" in manuscript
    assert "44 constructed proposal pairs" in manuscript
    assert "11 proposed mechanism families" in manuscript
    assert "no foundation-model judgement" in manuscript
    assert "no training or inference run was launched" in manuscript
    assert "figures/paper3_cheap_gate_internal.pdf" in manuscript


def test_paper3_source_uses_width_safe_layouts_for_known_overflow_sites() -> None:
    manuscript = _manuscript()
    assert r"\begin{tabularx}{\linewidth}" in manuscript
    assert r"\begin{aligned}" in manuscript
    assert r"\path{src/rakl/structural_transfer.py}" not in manuscript
    assert "retrieval/adaptation/verification costs" not in manuscript


def test_paper3_dedicated_workflow_fails_on_blocking_pdf_warnings() -> None:
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
