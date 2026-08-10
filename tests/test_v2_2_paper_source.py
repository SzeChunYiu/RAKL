from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def _module():
    sys.path.insert(0, str(ROOT / "paper"))
    spec = importlib.util.spec_from_file_location(
        "build_v2_2_source",
        ROOT / "paper" / "build_v2_2_source.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_2_source_adds_workspace_and_open_world_discovery_section():
    module = _module()
    text = module.build_v2_2_source(
        subject_sha="a" * 40,
        software_tests=700,
    )
    assert r"\section{Workspace-gated research cognition and open-world discovery}" in text
    assert "computational access" in text
    assert "bounded discovery-closure certificate" in text
    assert "GWT-OMISSION-01" in text
    assert "J-space" in text
    assert "order-theoretic lattice" in text
    assert "phenomenal consciousness" in text
    assert r"\bibitem{gurnee2026}" in text
    assert r"\bibitem{garikaparthi2025}" in text


def test_v2_2_source_remains_exact_subject_bound():
    module = _module()
    sha = "b" * 40
    text = module.build_v2_2_source(subject_sha=sha, software_tests=701)
    assert rf"\newcommand{{\SoftwareTests}}{{701}}" in text
    assert rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{sha}}}}}" in text
