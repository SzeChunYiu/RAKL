from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "saturated_builder", ROOT / "paper" / "build_saturated_epistemic_mechanics.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_saturated_paper_builder_binds_exact_subject(tmp_path: Path):
    sha = "a" * 40
    main_tex = _module().stage_saturated_paper(
        tmp_path / "paper", subject_sha=sha, software_tests=721
    )
    assert main_tex.exists()
    identity = (main_tex.parent / "build_identity.tex").read_text(encoding="utf-8")
    assert "\\newcommand{\\SoftwareTests}{721}" in identity
    assert f"\\newcommand{{\\ImplementationSHA}}{{\\texttt{{{sha}}}}}" in identity
    assert (main_tex.parent / "sections" / "06_three_geometries.tex").exists()
    assert (main_tex.parent / "fig5_demo_growth.pdf").exists()
