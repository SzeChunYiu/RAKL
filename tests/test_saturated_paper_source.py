from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "saturated_epistemic_mechanics" / "source"


def _v22_module():
    sys.path.insert(0, str(ROOT / "paper"))
    spec = importlib.util.spec_from_file_location(
        "round050_build_v2_2_source", ROOT / "paper" / "build_v2_2_source.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expand_tex(path: Path, seen: set[Path] | None = None) -> str:
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        raise AssertionError(f"recursive TeX input: {path}")
    seen.add(path)
    text = path.read_text(encoding="utf-8")

    def repl(match: re.Match[str]) -> str:
        rel = match.group(1)
        candidates = [SOURCE / rel, path.parent / rel]
        if not rel.endswith(".tex"):
            candidates = [candidate.with_suffix(".tex") for candidate in candidates]
        candidate = next((p for p in candidates if p.exists()), None)
        if candidate is None:
            # build_identity.tex is intentionally injected only for exact-subject release builds.
            if rel == "build_identity.tex":
                return ""
            raise AssertionError(f"missing TeX input: {rel}")
        return _expand_tex(candidate, seen.copy())

    return re.sub(r"\\input\{([^}]+)\}", repl, text)


def test_chaptered_source_manifest_is_complete():
    manifest = json.loads((SOURCE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["source_layout"] == "chaptered"
    assert manifest["entrypoint"] == "main.tex"
    assert len(manifest["sections"]) >= 18
    for rel in manifest["sections"] + manifest["assets"]:
        assert (SOURCE / rel).exists(), rel


def test_all_manuscript_citations_have_unique_bibliography_entries():
    expanded = _expand_tex(SOURCE / "main.tex")
    citations: set[str] = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", expanded):
        citations.update(part.strip() for part in group.split(",") if part.strip())
    bibitems = re.findall(r"\\bibitem\{([^}]+)\}", expanded)
    assert len(bibitems) == len(set(bibitems))
    missing = sorted(citations - set(bibitems))
    assert not missing, missing
    assert len(bibitems) >= 90


def test_saturated_manuscript_is_approximately_three_times_v22_depth():
    expanded = _expand_tex(SOURCE / "main.tex")
    baseline = _v22_module().build_v2_2_source(subject_sha="0" * 40, software_tests=1)
    ratio = len(expanded.split()) / len(baseline.split())
    assert ratio >= 2.95, ratio


def test_geometry_and_saturation_boundaries_are_explicit():
    expanded = _expand_tex(SOURCE / "main.tex")
    required = (
        "Three geometries of scientific memory: Obsidian, J-space and RAKL",
        "navigation graph",
        "representation geometry",
        "epistemic state",
        "Formal Concept Analysis",
        "compatibility complex",
        "Same-context manuscript review can support only",
        "independent peer review",
        "Section purpose is itself a proof obligation",
    )
    for phrase in required:
        assert phrase in expanded, phrase
