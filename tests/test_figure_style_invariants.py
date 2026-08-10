from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "paper" / "figures"
GENERATOR = ROOT / "paper" / "generate_demo_figures.py"


def test_tikz_draw_paths_do_not_carry_inline_text_nodes():
    """Project style: structural paths are unlabeled; prose lives in separate nodes."""

    violations: list[str] = []
    for path in sorted(FIGURES.glob("*.tex")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("\\draw") and "node[" in stripped:
                violations.append(f"{path.name}:{line_no}:{stripped}")
            if stripped.startswith("\\draw") and " node{" in stripped:
                violations.append(f"{path.name}:{line_no}:{stripped}")
    assert violations == [], "inline text attached to drawn paths is forbidden:\n" + "\n".join(violations)


def test_quantitative_figure_generator_does_not_use_arrow_callouts():
    source = GENERATOR.read_text(encoding="utf-8")
    assert "arrowprops" not in source
    assert "FancyArrow" not in source
    assert "ConnectionPatch" not in source
