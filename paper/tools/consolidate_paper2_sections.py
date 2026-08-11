from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "paper2_rakl_framework" / "sections"


def consolidate(target: str, parts_dir: str) -> bool:
    target_path = ROOT / target
    parts_path = ROOT / parts_dir
    if not parts_path.exists():
        return False

    original = target_path.read_text(encoding="utf-8")
    marker = "\\input{sections/"
    prefix = original.split(marker, 1)[0].rstrip() + "\n\n"
    parts = sorted(parts_path.glob("part*.tex"))
    if not parts:
        raise SystemExit(f"no TeX parts found in {parts_path}")
    body = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in parts) + "\n"
    target_path.write_text(prefix + body, encoding="utf-8")
    for p in parts:
        p.unlink()
    parts_path.rmdir()
    return True


changed = 0
changed += consolidate("02_intellectual_lineage.tex", "02_lineage")
changed += consolidate("03_formal_method.tex", "03_formal")
print(f"Paper II section consolidations applied: {changed}")
