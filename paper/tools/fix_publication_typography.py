from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCHES = {
    ROOT / "paper1_epistemic_mechanics" / "sections" / "01_introduction_foundations_state.tex": (
        r"""\[
V(p,e,\gamma)\in\{\mathrm{SUPPORTED},\mathrm{REFUTED},\mathrm{PARTIALLY\ IDENTIFIED},\mathrm{BLOCKED},\mathrm{CANNOT\ CHECK}\}.
\]""",
        r"""\[
\begin{aligned}
V(p,e,\gamma)\in\{&\mathrm{SUPPORTED},\mathrm{REFUTED},\mathrm{PARTIALLY\ IDENTIFIED},\\
&\mathrm{BLOCKED},\mathrm{CANNOT\ CHECK}\}.
\end{aligned}
\]""",
    ),
    ROOT / "paper1_epistemic_mechanics" / "sections" / "03_workspace.tex": (
        r"""\[
A_j(a)=\|J_j(a)\|,\qquad
C_j(a)=\|J_j(a)\|_{2\to 2},\qquad
\bar A_j(a)=\frac{1}{n_j}A_j(a).
\]""",
        r"""\[
\begin{aligned}
A_j(a)&=\|J_j(a)\|,\\
C_j(a)&=\|J_j(a)\|_{2\to 2},\\
\bar A_j(a)&=\frac{1}{n_j}A_j(a).
\end{aligned}
\]""",
    ),
}


def main() -> None:
    changed = 0
    for path, (old, new) in PATCHES.items():
        text = path.read_text(encoding="utf-8")
        if new in text:
            continue
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"expected exactly one typography anchor in {path}, found {count}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        changed += 1
    print(f"publication typography patches applied: {changed}")


if __name__ == "__main__":
    main()
