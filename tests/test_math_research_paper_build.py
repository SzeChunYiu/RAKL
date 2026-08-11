from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "math_research_builder", ROOT / "paper" / "build_math_research_assurance.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_build_binds_exact_subject_and_includes_assurance_sections() -> None:
    sha = "a" * 40
    text = _module().build_math_research_assurance_source(
        subject_sha=sha,
        software_tests=777,
    )
    assert rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{sha}}}}}" in text
    assert r"\newcommand{\SoftwareTests}{777}" in text
    assert r"\begin{proposition}[Assurance decomposition for a verifier-gated proof DAG]" in text
    assert r"\section{Typed discovery search and reference implementation}" in text
    assert r"\emph{Nature} 651, 607--613 (2026)" in text
    assert r"\cite{jiang2026frontier}" in text
    assert r"\cite{pu2026maproof}" in text
    assert "arXiv:2607.07779 (2026)" in text
    assert "arXiv:2606.13782 (2026)" in text
    assert r"\section*{Code, materials and AI-use disclosure}" in text
    assert r"\begin{thebibliography}{11}" in text
    assert "UNBOUND" not in text


def test_release_build_rejects_invalid_subject_identity() -> None:
    try:
        _module().build_math_research_assurance_source(
            subject_sha="bad",
            software_tests=1,
        )
    except ValueError as exc:
        assert "40-character" in str(exc)
    else:
        raise AssertionError("invalid subject SHA should fail closed")
