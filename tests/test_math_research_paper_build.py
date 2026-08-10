from __future__ import annotations

from paper.build_math_research_assurance import build_math_research_assurance_source


def test_release_build_binds_exact_subject_and_includes_assurance_sections() -> None:
    sha = "a" * 40
    text = build_math_research_assurance_source(subject_sha=sha, software_tests=777)
    assert rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{sha}}}}}" in text
    assert r"\newcommand{\SoftwareTests}{777}" in text
    assert r"\begin{proposition}[Assurance decomposition for a verifier-gated proof DAG]" in text
    assert r"\section{Typed discovery search and reference implementation}" in text
    assert r"\emph{Nature} 651, 607--613 (2026)" in text
    assert "UNBOUND" not in text


def test_release_build_rejects_invalid_subject_identity() -> None:
    try:
        build_math_research_assurance_source(subject_sha="bad", software_tests=1)
    except ValueError as exc:
        assert "40-character" in str(exc)
    else:
        raise AssertionError("invalid subject SHA should fail closed")
