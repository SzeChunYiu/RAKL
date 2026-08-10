from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "epistemic_mechanics" / "main.tex"


def build_epistemic_mechanics_source(*, subject_sha: str, software_tests: int) -> str:
    if len(subject_sha) != 40 or any(ch not in "0123456789abcdef" for ch in subject_sha):
        raise ValueError("subject_sha must be a 40-character lowercase git SHA")
    if software_tests < 1:
        raise ValueError("software_tests must be positive")
    text = SOURCE.read_text(encoding="utf-8")
    old_sha = r"\newcommand{\ImplementationSHA}{\texttt{UNBOUND}}"
    old_tests = r"\newcommand{\SoftwareTests}{UNBOUND}"
    if text.count(old_sha) != 1 or text.count(old_tests) != 1:
        raise RuntimeError("epistemic-mechanics source binding anchors changed")
    text = text.replace(
        old_sha,
        rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{subject_sha}}}}}",
        1,
    )
    text = text.replace(
        old_tests,
        rf"\newcommand{{\SoftwareTests}}{{{software_tests}}}",
        1,
    )
    forbidden = ("[[RESULT:", "independent peer review completed", "phenomenal consciousness established")
    for phrase in forbidden:
        if phrase in text:
            raise RuntimeError(f"forbidden release phrase present: {phrase}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--software-tests", required=True, type=int)
    args = parser.parse_args()
    text = build_epistemic_mechanics_source(
        subject_sha=args.subject_sha,
        software_tests=args.software_tests,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
