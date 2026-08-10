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

    evaluation_anchor = r"\section{Preregistered evaluation}"
    if text.count(evaluation_anchor) != 1:
        raise RuntimeError("Paper IV release-section anchor changed")
    text = text.replace(
        evaluation_anchor,
        release + "\n\n" + evaluation_anchor,
        1,
    )

    # Normalize AlphaProof to the Nature version-of-record metadata while using
    # the DOI as the stable anchor, rather than relying on TeX line formatting.
    alpha_old = "(2025). doi:10.1038/s41586-025-09833-y."
    alpha_new = "651, 607--613 (2026). doi:10.1038/s41586-025-09833-y."
    if text.count(alpha_old) != 1:
        raise RuntimeError("AlphaProof DOI/year anchor changed")
    text = text.replace(alpha_old, alpha_new, 1)

    required_fragments = (
        subject_sha,
        rf"\newcommand{{\SoftwareTests}}{{{software_tests}}}",
        r"\begin{proposition}[Assurance decomposition for a verifier-gated proof DAG]",
        r"\section{Typed discovery search and reference implementation}",
        r"\section{Preregistered evaluation}",
        r"\section{Limitations}",
        r"\begin{thebibliography}{9}",
        "Nature} 651, 607--613 (2026). doi:10.1038/s41586-025-09833-y.",
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
