from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "paper" / "generate_demo_figures.py"


def _module():
    spec = importlib.util.spec_from_file_location("rakl_demo_figure_generator", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_demo_figures_equal_generator_output():
    generated = _module().generate()
    for filename, expected in generated.items():
        committed = (ROOT / "paper" / "figures" / filename).read_text(encoding="utf-8")
        assert committed == expected


def test_demo_figures_declare_machine_generation_source():
    generated = _module().generate()
    for content in generated.values():
        assert content.startswith("% GENERATED FROM research/MINI_RESEARCH_DEMO_043_RECEIPT.json")
