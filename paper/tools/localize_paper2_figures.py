from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "paper2_rakl_framework"
SECTION = ROOT / "sections" / "08_known_answer_trace.tex"

REPLACEMENTS = {
    r"\input{fig5_demo_growth.tex}": r"\input{figures/fig5_demo_growth.tex}",
    r"\input{fig6_demo_context.tex}": r"\input{figures/fig6_demo_context.tex}",
}


def main() -> None:
    text = SECTION.read_text(encoding="utf-8")
    changed = 0
    for old, new in REPLACEMENTS.items():
        if new in text:
            continue
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"expected exactly one {old!r} in {SECTION}, found {count}")
        text = text.replace(old, new, 1)
        changed += 1
    SECTION.write_text(text, encoding="utf-8")
    print(f"Paper II figure-input localizations applied: {changed}")


if __name__ == "__main__":
    main()
