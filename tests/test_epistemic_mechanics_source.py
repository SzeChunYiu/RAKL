from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "build_epistemic_mechanics",
        ROOT / "paper" / "build_epistemic_mechanics.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_epistemic_mechanics_contains_required_formal_results():
    text = (ROOT / "paper" / "epistemic_mechanics" / "main.tex").read_text(encoding="utf-8")
    for needle in (
        "Workspace non-authority",
        "Coactivation non-gluing",
        "Conservative workspace extension",
        "No finite certificate of unrestricted open-world completeness",
        "Finite-budget OWMD termination",
        "Scalar inadequacy",
        "GWT-OMISSION-01",
        "Typed compatibility complex",
    ):
        assert needle in text


def test_epistemic_mechanics_exact_subject_binding():
    module = _module()
    sha = "c" * 40
    text = module.build_epistemic_mechanics_source(subject_sha=sha, software_tests=702)
    assert rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{sha}}}}}" in text
    assert rf"\newcommand{{\SoftwareTests}}{{702}}" in text
    assert "UNBOUND" not in text
