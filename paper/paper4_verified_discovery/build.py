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

    # Paper IV is normalized into one section file per top-level section before
    # this builder runs. Bind the exact evaluated source and software-test count
    # without mutating the scientific manuscript.
    (ROOT / "build_identity.tex").write_text(
        f"\\newcommand{{\\SoftwareTests}}{{{software_tests}}}\n"
        f"\\newcommand{{\\ImplementationSHA}}{{\\texttt{{{subject_sha}}}}}\n",
        encoding="utf-8",
    )

    main = ROOT / "main.tex"
    text = main.read_text(encoding="utf-8")
    if r"\input{sections/01_" not in text:
        raise RuntimeError(
            "Paper IV must be normalized into section files before build.py; "
            "run paper/tools/normalize_paper4_sections.py first."
        )

    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "main.tex",
        ],
        cwd=ROOT,
        check=True,
    )
    out = ROOT / "final.pdf"
    shutil.copy2(ROOT / "main.pdf", out)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--subject-sha", required=True)
    p.add_argument("--software-tests", type=int, required=True)
    a = p.parse_args()
    print(build(a.subject_sha, a.software_tests))
