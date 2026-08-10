from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "epistemic_mechanics" / "main.tex"
_INPUT_RE = re.compile(r"\\input\{([^}]+)\}")


def _expand_inputs(text: str, *, source_root: Path, stack: tuple[Path, ...] = ()) -> str:
    """Inline local TeX inputs so the staged publication source is self-contained."""

    def replacement(match: re.Match[str]) -> str:
        rel = Path(match.group(1))
        if rel.suffix != ".tex":
            rel = rel.with_suffix(".tex")
        path = (source_root / rel).resolve()
        root = source_root.resolve()
        if root not in path.parents:
            raise RuntimeError(f"epistemic-mechanics input escapes source root: {rel}")
        if path in stack:
            chain = " -> ".join(str(item.relative_to(root)) for item in stack + (path,))
            raise RuntimeError(f"recursive epistemic-mechanics input: {chain}")
        if not path.is_file():
            raise RuntimeError(f"missing epistemic-mechanics input: {rel}")
        content = path.read_text(encoding="utf-8")
        return _expand_inputs(content, source_root=source_root, stack=stack + (path,))

    while _INPUT_RE.search(text):
        text = _INPUT_RE.sub(replacement, text)
    return text


def _replace_exact_once(text: str, old: str, new: str, *, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"epistemic-mechanics layout anchor changed: {label}")
    return text.replace(old, new, 1)


def _apply_release_layout_repairs(text: str) -> str:
    """Break three long formal displays without changing their mathematical content.

    The modular source stays readable, while the exact release builder guarantees that
    formally important tuples/enumerations fit the publication width.  Every rewrite is
    exact-anchor guarded so a future semantic edit reopens the build contract instead of
    silently receiving a stale formatting patch.
    """

    text = _replace_exact_once(
        text,
        """\\[
K_t=(\\mathcal A_t,\\mathcal T_t,\\mathcal V_t,\\mathcal E_t,\\mathcal U_t,
\\mathcal O_t,\\mathcal F_t,\\mathcal H_t^{-},\\mathcal S_t,\\mathcal G_t^K).
\\]""",
        """\\[
\\begin{aligned}
K_t=(&\\mathcal A_t,\\mathcal T_t,\\mathcal V_t,\\mathcal E_t,\\mathcal U_t,\\\\
     &\\mathcal O_t,\\mathcal F_t,\\mathcal H_t^{-},\\mathcal S_t,\\mathcal G_t^K).
\\end{aligned}
\\]""",
        label="canonical-state-vector",
    )
    text = _replace_exact_once(
        text,
        """\\[
V(p,e,\\gamma)\\in
\\{\\mathrm{SUPPORTED},\\mathrm{REFUTED},\\mathrm{PARTIALLY\\ IDENTIFIED},
\\mathrm{BLOCKED},\\mathrm{CANNOT\\ CHECK}\\}.
\\]""",
        """\\[
V(p,e,\\gamma)\\in
\\left\\{
\\begin{array}{lll}
\\mathrm{SUPPORTED}, & \\mathrm{REFUTED}, & \\mathrm{PARTIALLY\\ IDENTIFIED},\\\\
\\mathrm{BLOCKED}, & \\mathrm{CANNOT\\ CHECK}
\\end{array}
\\right\\}.
\\]""",
        label="verification-outcomes",
    )
    text = _replace_exact_once(
        text,
        """\\[
A_t(a)=\\text{computational accessibility},\\qquad
C_t(a)=\\text{atlas coherence},\\qquad
\\alpha_t(a)=\\text{epistemic authority}.
\\]""",
        """\\[
\\begin{aligned}
A_t(a)&=\\text{computational accessibility},\\\\
C_t(a)&=\\text{atlas coherence},\\\\
\\alpha_t(a)&=\\text{epistemic authority}.
\\end{aligned}
\\]""",
        label="access-coherence-authority",
    )
    return text


def build_epistemic_mechanics_source(*, subject_sha: str, software_tests: int) -> str:
    if len(subject_sha) != 40 or any(ch not in "0123456789abcdef" for ch in subject_sha):
        raise ValueError("subject_sha must be a 40-character lowercase git SHA")
    if software_tests < 1:
        raise ValueError("software_tests must be positive")
    text = SOURCE.read_text(encoding="utf-8")
    text = _expand_inputs(text, source_root=SOURCE.parent)
    text = _apply_release_layout_repairs(text)
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
    if r"\input{" in text:
        raise RuntimeError("staged epistemic-mechanics source still contains unresolved input")
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
