from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research" / "MINI_RESEARCH_DEMO_043_RECEIPT.json"
FIGURES = ROOT / "paper" / "figures"


def _load() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def growth_tex(data: dict) -> str:
    novelty = [int(row[1]) for row in data["semantic_novelty_by_round"]]
    labels = [str(row[0]) for row in data["semantic_novelty_by_round"]]
    cumulative = []
    total = 0
    for value in novelty:
        total += value
        cumulative.append(total)
    paths = [
        0,
        data["target_support_paths_after_new_evidence"],
        data["target_support_paths_after_new_evidence"],
        data["target_support_paths_after_new_evidence"],
    ]

    bars = []
    annotations = []
    for i, (label, value, new, path) in enumerate(zip(labels, cumulative, novelty, paths)):
        x = 1.35 * i
        h = 0.42 * value
        bars.append(f"\\fill[black!15] ({x:.2f},0) rectangle ({x + 0.72:.2f},{h:.2f});")
        bars.append(f"\\draw ({x:.2f},0) rectangle ({x + 0.72:.2f},{h:.2f});")
        bars.append(f"\\node[font=\\sffamily\\scriptsize] at ({x + 0.36:.2f},{h + 0.22:.2f}) {{{value}}};")
        annotations.append(f"\\node[font=\\sffamily\\scriptsize] at ({x + 0.36:.2f},-0.28) {{{label}}};")
        annotations.append(f"\\node[font=\\sffamily\\tiny] at ({x + 0.36:.2f},-0.58) {{novelty +{new}}};")
        state = "open" if path else "blocked"
        annotations.append(f"\\node[font=\\sffamily\\tiny] at ({x + 0.36:.2f},-0.82) {{target {state}}};")

    return "\n".join([
        "% GENERATED FROM research/MINI_RESEARCH_DEMO_043_RECEIPT.json. DO NOT HAND EDIT.",
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\draw[->] (-0.25,0) -- (5.35,0) node[right,font=\\sffamily\\scriptsize]{research round};",
        "\\draw[->] (0,-0.05) -- (0,3.35) node[above,font=\\sffamily\\scriptsize,align=center]{cumulative semantic objects};",
        *bars,
        *annotations,
        "\\draw[dashed] (1.71,0) -- (1.71,3.05);",
        "\\node[font=\\sffamily\\scriptsize,align=left,anchor=west] at (2.00,3.0) {new finite-amplitude evidence; target cut closes};",
        "\\end{tikzpicture}",
        "",
    ])


def context_tex(data: dict) -> str:
    archive = int(data["archive_token_estimate"])
    active = int(data["active_context_tokens"])
    ratio = float(data["active_to_archive_token_ratio"])
    max_width = 8.0
    active_width = max_width * active / archive
    roots = ", ".join(data["source_rehydration_roots"])
    return "\n".join([
        "% GENERATED FROM research/MINI_RESEARCH_DEMO_043_RECEIPT.json. DO NOT HAND EDIT.",
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\node[font=\\sffamily\\scriptsize,anchor=east] at (0,1.0) {archive};",
        f"\\fill[black!15] (0.2,0.72) rectangle ({0.2 + max_width:.2f},1.28);",
        f"\\draw (0.2,0.72) rectangle ({0.2 + max_width:.2f},1.28);",
        f"\\node[font=\\sffamily\\scriptsize,anchor=west] at ({0.35 + max_width:.2f},1.0) {{{archive} token estimate}};",
        "\\node[font=\\sffamily\\scriptsize,anchor=east] at (0,0.0) {active};",
        f"\\fill[black!35] (0.2,-0.28) rectangle ({0.2 + active_width:.2f},0.28);",
        f"\\draw (0.2,-0.28) rectangle ({0.2 + active_width:.2f},0.28);",
        f"\\node[font=\\sffamily\\scriptsize,anchor=west] at ({0.35 + active_width:.2f},0.0) {{{active} tokens ({100.0 * ratio:.1f}\\%)}};",
        f"\\node[font=\\sffamily\\scriptsize,anchor=west,align=left] at (0.2,-0.85) {{lossy working view remains pinned to canonical roots: {roots}}};",
        f"\\node[font=\\sffamily\\scriptsize,anchor=west,align=left] at (0.2,-1.25) {{{data['canonical_memory_views']} canonical + {data['lossless_memory_views']} lossless + {data['lossy_memory_views']} lossy memory views}};",
        "\\end{tikzpicture}",
        "",
    ])


def generate() -> dict[str, str]:
    data = _load()
    return {
        "fig5_demo_growth.tex": growth_tex(data),
        "fig6_demo_context.tex": context_tex(data),
    }


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for filename, content in generate().items():
        (FIGURES / filename).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
