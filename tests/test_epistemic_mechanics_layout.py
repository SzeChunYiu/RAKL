from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _builder():
    spec = importlib.util.spec_from_file_location(
        "epistemic_mechanics_layout_builder",
        ROOT / "paper" / "build_epistemic_mechanics.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_epistemic_mechanics_source


def test_release_builder_breaks_long_formal_displays() -> None:
    text = _builder()(
        subject_sha="a" * 40,
        software_tests=1,
    )
    assert "K_t=(&\\mathcal A_t" in text
    assert "\\begin{array}{lll}" in text
    assert "A_t(a)&=\\text{computational accessibility}" in text


def test_release_layout_repairs_leave_formal_terms_present() -> None:
    text = _builder()(
        subject_sha="b" * 40,
        software_tests=1,
    )
    for token in (
        "\\mathcal H_t^{-}",
        "\\mathrm{PARTIALLY\\ IDENTIFIED}",
        "\\mathrm{CANNOT\\ CHECK}",
        "\\alpha_t(a)&=\\text{epistemic authority}",
    ):
        assert token in text
