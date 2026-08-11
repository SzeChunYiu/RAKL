from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "math_research_assurance" / "main.tex"
ASSURANCE_ADDENDUM = (
    ROOT / "paper" / "math_research_assurance" / "ASSURANCE_BOUND_ADDENDUM.tex"
)
RELEASE_APPENDIX = (
    ROOT / "paper" / "math_research_assurance" / "RELEASE_APPENDIX.tex"
)


def _validate_sha(subject_sha: str) -> None:
    if len(subject_sha) != 40 or any(ch not in "0123456789abcdef" for ch in subject_sha):
        raise ValueError("subject_sha must be a 40-character lowercase git SHA")


def build_math_research_assurance_source(*, subject_sha: str, software_tests: int) -> str:
    _validate_sha(subject_sha)
    if software_tests < 1:
        raise ValueError("software_tests must be positive")

    text = SOURCE.read_text(encoding="utf-8")
    addendum = ASSURANCE_ADDENDUM.read_text(encoding="utf-8").strip()
    release = RELEASE_APPENDIX.read_text(encoding="utf-8").strip()

    macro_anchor = r"\newcommand{\CC}{\texttt{CANNOT\_CHECK}}"
    if text.count(macro_anchor) != 1:
        raise RuntimeError("Paper IV macro binding anchor changed")
    bound_macros = (
        macro_anchor
        + "\n"
        + rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{subject_sha}}}}}"
        + "\n"
        + rf"\newcommand{{\SoftwareTests}}{{{software_tests}}}"
    )
    text = text.replace(macro_anchor, bound_macros, 1)

    novelty_anchor = r"\section{Novelty is bounded and defeasible}"
    if text.count(novelty_anchor) != 1:
        raise RuntimeError("Paper IV assurance-addendum anchor changed")
    text = text.replace(
        novelty_anchor,
        addendum + "\n\n" + novelty_anchor,
        1,
    )

    # Freshness hardening: two 2026 primary-source neighbors make the
    # solver-versus-research and formalization/evaluation boundary explicit.
    research_gap_anchor = (
        "Mathematical research adds obligations absent from a benchmark with a known target answer."
    )
    if text.count(research_gap_anchor) != 1:
        raise RuntimeError("Paper IV research-gap anchor changed")
    research_gap_delta = r"""
Recent work makes the same frontier distinction from complementary directions. Jiang et al. argue that formal-mathematics systems must move from predefined problem solving toward open-ended research agents with explicit support for exploration, abstraction and human--AI collaboration \cite{jiang2026frontier}. MA-ProofBench, meanwhile, evaluates 200 formalized mathematical-analysis theorems produced through a human-led, LLM-assisted formalization pipeline with independent expert review and reports substantial difficulty even for current models \cite{pu2026maproof}. These results strengthen the need to separate proof search, specification fidelity and research-level assurance rather than treating benchmark proof success as an end-to-end research certificate.
""".strip()
    text = text.replace(
        research_gap_anchor,
        research_gap_anchor + "\n\n" + research_gap_delta,
        1,
    )

    evaluation_anchor = r"\section{Preregistered evaluation}"
    if text.count(evaluation_anchor) != 1:
        raise RuntimeError("Paper IV release-section anchor changed")
    text = text.replace(
        evaluation_anchor,
        release + "\n\n" + evaluation_anchor,
        1,
    )

    # The semantic promotion chain is intentionally long. Render it as a
    # two-row aligned relation rather than a single unbreakable display on A4.
    promotion_old = """\\[
\\texttt{CONJECTURE}
\\rightarrow
\\texttt{FORMALIZED\\_UNPROVEN}
\\rightarrow
\\texttt{MACHINE\\_PROVEN}
\\rightarrow
\\texttt{BOUNDED\\_NOVEL\\_RESULT}
\\rightarrow
\\texttt{NEW\\_MATHEMATICS\\_CANDIDATE}.
\\]"""
    promotion_new = """\\[
\\begin{aligned}
\\texttt{CONJECTURE}
&\\rightarrow \\texttt{FORMALIZED\\_UNPROVEN}
\\rightarrow \\texttt{MACHINE\\_PROVEN}\\\\
&\\rightarrow \\texttt{BOUNDED\\_NOVEL\\_RESULT}
\\rightarrow \\texttt{NEW\\_MATHEMATICS\\_CANDIDATE}.
\\end{aligned}
\\]"""
    if text.count(promotion_old) != 1:
        raise RuntimeError("Paper IV promotion-chain anchor changed")
    text = text.replace(promotion_old, promotion_new, 1)

    # Normalize AlphaProof to the Nature version-of-record metadata while using
    # the DOI as the stable anchor, rather than relying on TeX line formatting.
    alpha_old = "(2025). doi:10.1038/s41586-025-09833-y."
    alpha_new = "651, 607--613 (2026). doi:10.1038/s41586-025-09833-y."
    if text.count(alpha_old) != 1:
        raise RuntimeError("AlphaProof DOI/year anchor changed")
    text = text.replace(alpha_old, alpha_new, 1)

    bibliography_anchor = r"\begin{thebibliography}{9}"
    if text.count(bibliography_anchor) != 1:
        raise RuntimeError("Paper IV bibliography anchor changed")
    text = text.replace(bibliography_anchor, r"\begin{thebibliography}{11}", 1)

    bibliography_end = r"\end{thebibliography}"
    if text.count(bibliography_end) != 1:
        raise RuntimeError("Paper IV bibliography end anchor changed")
    freshness_bib = r"""
\bibitem{jiang2026frontier}
E. Jiang et al., ``From Solvers to Research: Large Language Model-Driven Formal Mathematics at the Research Frontier,'' arXiv:2607.07779 (2026).

\bibitem{pu2026maproof}
L. Pu et al., ``MA-ProofBench: A Two-Tiered Evaluation of LLMs for Theorem Proving in Mathematical Analysis,'' arXiv:2606.13782 (2026).
""".strip()
    text = text.replace(
        bibliography_end,
        freshness_bib + "\n\n" + bibliography_end,
        1,
    )

    release_disclosure = r"""
\section*{Code, materials and AI-use disclosure}
The public research artifact is maintained at \url{https://github.com/SzeChunYiu/RAKL}. The release package binds the manuscript to an exact Git subject, passing-test count, hostile assurance benchmark receipt and publication-artifact manifest. The repository contains the typed mathematical-research assurance runtime, benchmark task packet, workflow specification and release builder used by this paper. Language models were used as research, coding and drafting tools; they are not authors and their generated proposals receive no mathematical authority without the verification and governance steps described in the paper. Personal author metadata, funding and competing-interest declarations are supplied separately at submission and are not inferred by the build system.
""".strip()
    text = text.replace(
        r"\begin{thebibliography}{11}",
        release_disclosure + "\n\n" + r"\begin{thebibliography}{11}",
        1,
    )

    required_fragments = (
        subject_sha,
        rf"\newcommand{{\SoftwareTests}}{{{software_tests}}}",
        r"\begin{proposition}[Assurance decomposition for a verifier-gated proof DAG]",
        r"\section{Typed discovery search and reference implementation}",
        r"\section{Preregistered evaluation}",
        r"\section{Limitations}",
        r"\section*{Code, materials and AI-use disclosure}",
        r"\begin{thebibliography}{11}",
        r"\begin{aligned}",
        "Nature} 651, 607--613 (2026). doi:10.1038/s41586-025-09833-y.",
        r"\cite{jiang2026frontier}",
        r"\cite{pu2026maproof}",
    )
    for fragment in required_fragments:
        if fragment not in text:
            raise RuntimeError(f"required release fragment missing: {fragment}")

    # Lint only affirmative overclaims. Negative statements explaining why such
    # claims are not licensed are intentionally allowed.
    forbidden_affirmative_claims = (
        "we prove global novelty",
        "global novelty is established",
        "guarantees global novelty",
        "autonomous mathematical discovery superiority has been established",
        "we establish autonomous mathematical discovery superiority",
    )
    if "UNBOUND" in text:
        raise RuntimeError("unbound release identity present")
    lower_text = text.lower()
    for phrase in forbidden_affirmative_claims:
        if phrase.lower() in lower_text:
            raise RuntimeError(f"forbidden affirmative release claim present: {phrase}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--software-tests", type=int, required=True)
    args = parser.parse_args()
    text = build_math_research_assurance_source(
        subject_sha=args.subject_sha,
        software_tests=args.software_tests,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
