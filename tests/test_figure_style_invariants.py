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


def test_quantitative_figure_generator_has_no_data_callouts_or_text_boxes():
    """Quantitative panels must read from axes/legends rather than callout annotations."""

    source = GENERATOR.read_text(encoding="utf-8")
    forbidden = [
        "arrowprops",
        "FancyArrow",
        "ConnectionPatch",
        ".annotate(",
        "bbox=dict",
        "bbox = dict",
        "ax.text(",
    ]
    violations = [token for token in forbidden if token in source]
    assert violations == [], f"forbidden quantitative callout primitives: {violations}"


def test_quantitative_figure_generator_uses_collision_aware_layout_and_editable_text():
    source = GENERATOR.read_text(encoding="utf-8")
    assert "constrained_layout=True" in source
    assert '"pdf.fonttype": 42' in source
    assert '"svg.fonttype": "none"' in source
    assert '"font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]' in source
