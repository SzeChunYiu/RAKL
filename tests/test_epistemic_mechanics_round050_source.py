from __future__ import annotations

import importlib.util
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "build_epistemic_mechanics_round050",
        ROOT / "paper" / "build_epistemic_mechanics.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_round050_builder_promotes_versioned_longform_without_rewriting_legacy_source():
    legacy = (ROOT / "paper" / "epistemic_mechanics" / "main.tex").read_text(
        encoding="utf-8"
    )
    assert r"\title{Epistemic Mechanics: From Linguistic Claims to Evidence-Governed Scientific State}" in legacy

    text = _module().build_epistemic_mechanics_source(
        subject_sha="a" * 40,
        software_tests=700,
    )
    for needle in (
        "Foundations and the gap between them",
        "Three-context parity obstruction",
        "Closure-system lattice",
        "No faithful scalarization of incomparability",
        "Optimality of reservation-first greedy selection",
        "Unrestricted open-world completeness is not finitely certifiable",
        "Worked mechanics trace: the simple pendulum",
        "GWT-OMISSION-01",
        "typed compatibility complex",
    ):
        assert needle in text

    assert r"\title{Epistemic Mechanics for Evidence-Governed Scientific Research}" in text
    assert r"\section{Implementation correspondence and scope}" not in text
    assert r"\appendix" in text
    assert r"\section{Reproducibility and implementation correspondence}" in text
    assert r"\input{" not in text
    assert "paper/epistemic_mechanics_round050/sections/" in text
    assert "paper/epistemic_mechanics/sections/" not in text

    words = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", text.split(r"\begin{thebibliography}", 1)[0])
    assert len(words) >= 9000

    cited_keys: set[str] = set()
    for match in re.finditer(r"\\cite\{([^}]+)\}", text):
        cited_keys.update(key.strip() for key in match.group(1).split(","))
    bib_keys = set(re.findall(r"\\bibitem\{([^}]+)\}", text))
    assert len(cited_keys) >= 40
    assert len(bib_keys) >= 40
    assert cited_keys == bib_keys


def test_round050_builder_preserves_subject_binding_and_backslash_commands():
    module = _module()
    sha = "c" * 40
    text = module.build_epistemic_mechanics_source(subject_sha=sha, software_tests=702)
    assert rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{sha}}}}}" in text
    assert rf"\newcommand{{\SoftwareTests}}{{702}}" in text
    assert "UNBOUND" not in text
    assert "Git commit \\ImplementationSHA" not in text
    assert "\t" + "ext{aligned contradiction}" not in text
    assert "\\text{aligned contradiction}" in text


def test_round050_readme_identifies_promoted_and_legacy_sources():
    readme = (
        ROOT / "paper" / "epistemic_mechanics_round050" / "README.md"
    ).read_text(encoding="utf-8")
    assert "Epistemic Mechanics for Evidence-Governed Scientific Research" in readme
    assert "paper/epistemic_mechanics/main.tex" in readme
    assert "legacy frozen-parent source" in readme
