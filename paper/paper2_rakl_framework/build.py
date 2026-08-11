from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build(subject_sha: str, software_tests: int) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", subject_sha):
        raise ValueError("subject_sha must be a 40-character lowercase SHA")
    if software_tests < 1:
        raise ValueError("software_tests must be positive")

    (ROOT / "build_identity.tex").write_text(
        f"\\newcommand{{\\SoftwareTests}}{{{software_tests}}}\n"
        f"\\newcommand{{\\ImplementationSHA}}{{\\texttt{{{subject_sha}}}}}\n",
        encoding="utf-8",
    )

    # Rebuild every quantitative figure from the local frozen receipts.  This
    # prevents stale or damaged binary figures from acquiring publication
    # authority and makes the paper package self-contained.
    subprocess.run(
        ["python", str(ROOT / "figures" / "generate_demo_figures.py")],
        cwd=ROOT,
        check=True,
    )

    text = (ROOT / "main.tex").read_text(encoding="utf-8")
    text = text.replace(
        r"\input{fig5_demo_growth.tex}",
        r"\input{figures/fig5_demo_growth.tex}",
    ).replace(
        r"\input{fig6_demo_context.tex}",
        r"\input{figures/fig6_demo_context.tex}",
    )
    figure_input = r"\input{figures/figure_appendix}"
    reference_input = r"\input{sections/99_references.tex}"
    if figure_input not in text:
        text = text.replace(reference_input, figure_input + "\n" + reference_input, 1)

    temp = ROOT / "release_main.tex"
    temp.write_text(text, encoding="utf-8")
    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            temp.name,
        ],
        cwd=ROOT,
        check=True,
    )
    out = ROOT / "final.pdf"
    shutil.copy2(ROOT / "release_main.pdf", out)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--subject-sha", required=True)
    p.add_argument("--software-tests", type=int, required=True)
    a = p.parse_args()
    print(build(a.subject_sha, a.software_tests))
