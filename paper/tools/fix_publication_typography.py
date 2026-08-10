from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCHES = {
    ROOT / "paper1_epistemic_mechanics" / "sections" / "01_introduction_foundations_state.tex": (
        r"""\[
V(p,e,\gamma)\in
\{\mathrm{SUPPORTED},\mathrm{REFUTED},\mathrm{PARTIALLY\ IDENTIFIED},
\mathrm{BLOCKED},\mathrm{CANNOT\ CHECK}\}.
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
A_t(a)=\text{computational accessibility},\qquad
C_t(a)=\text{atlas coherence},\qquad
\alpha_t(a)=\text{epistemic authority}.
\]""",
        r"""\[
\begin{aligned}
A_t(a)&=\text{computational accessibility},\\
C_t(a)&=\text{atlas coherence},\\
\alpha_t(a)&=\text{epistemic authority}.
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
