from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "paper4_verified_discovery"
SRC = ROOT / "main.tex"


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:64] or "section"


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    # Once materialized, the normalized manuscript is canonical and this step
    # becomes a no-op. build.py has independent ownership and is never generated
    # here.
    if r"\input{sections/01_" in text:
        return

    abstract_end = text.index(r"\end{abstract}") + len(r"\end{abstract}")
    pre = text[:abstract_end]
    if r"\usepackage{tikz}" not in pre:
        pkg_anchor = r"\usepackage{enumitem}"
        packages = (
            pkg_anchor
            + "\n"
            + r"\usepackage{graphicx}"
            + "\n"
            + r"\usepackage{tikz}"
            + "\n"
            + r"\usetikzlibrary{arrows.meta,positioning,shapes.geometric}"
        )
        if pkg_anchor not in pre:
            raise SystemExit("Paper IV package anchor missing")
        pre = pre.replace(pkg_anchor, packages, 1)

    identity_anchor = r"\newcommand{\CC}{\texttt{CANNOT\_CHECK}}"
    if r"\IfFileExists{build_identity.tex}" not in pre:
        if identity_anchor not in pre:
            raise SystemExit("Paper IV build-identity anchor missing")
        pre = pre.replace(
            identity_anchor,
            identity_anchor
            + "\n"
            + r"\IfFileExists{build_identity.tex}{\input{build_identity.tex}}{\newcommand{\SoftwareTests}{UNBOUND}\newcommand{\ImplementationSHA}{\texttt{UNBOUND}}}",
            1,
        )

    tail = text[abstract_end:]
    bib_i = tail.index(r"\begin{thebibliography}")
    body = tail[:bib_i]
    bib = tail[bib_i : tail.rindex(r"\end{document}")]
    bib = bib.replace(
        "(2025). doi:10.1038/s41586-025-09833-y.",
        "651, 607--613 (2026). doi:10.1038/s41586-025-09833-y.",
    )

    matches = list(re.finditer(r"(?m)^\\section\{([^}]*)\}", body))
    if not matches:
        raise SystemExit("Paper IV has no top-level sections to normalize")
    secdir = ROOT / "sections"
    secdir.mkdir(exist_ok=True)
    inputs: list[str] = []

    for i, match in enumerate(matches, 1):
        end = matches[i].start() if i < len(matches) else len(body)
        title = match.group(1)
        filename = f"{i:02d}_{slug(title)}.tex"
        (secdir / filename).write_text(body[match.start() : end].strip() + "\n", encoding="utf-8")
        inputs.append(f"\\input{{sections/{filename[:-4]}}}")

        if title == "Proof assurance and verifier trust":
            addendum = ROOT / "ASSURANCE_BOUND_ADDENDUM.tex"
            if not addendum.exists():
                raise SystemExit("Paper IV assurance addendum missing before normalization")
            name = "06b_assurance_bound.tex"
            (secdir / name).write_text(addendum.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")
            inputs.append(f"\\input{{sections/{name[:-4]}}}")

        if title == "RAKL integration":
            appendix = ROOT / "RELEASE_APPENDIX.tex"
            if not appendix.exists():
                raise SystemExit("Paper IV release appendix missing before normalization")
            name = "11b_reference_implementation.tex"
            (secdir / name).write_text(appendix.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")
            inputs.append(f"\\input{{sections/{name[:-4]}}}")
            inputs.append(r"\input{figures/figure_appendix}")

    (secdir / "99_references.tex").write_text(bib.strip() + "\n", encoding="utf-8")
    SRC.write_text(
        pre
        + "\n\n"
        + "\n".join(inputs)
        + "\n"
        + r"\input{sections/99_references}"
        + "\n"
        + r"\end{document}"
        + "\n",
        encoding="utf-8",
    )
    (ROOT / "ASSURANCE_BOUND_ADDENDUM.tex").unlink(missing_ok=True)
    (ROOT / "RELEASE_APPENDIX.tex").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
