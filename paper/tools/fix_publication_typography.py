from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATCHES = [
    (
        ROOT / "paper1_epistemic_mechanics" / "sections" / "01_introduction_foundations_state.tex",
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
    (
        ROOT / "paper1_epistemic_mechanics" / "sections" / "03_workspace.tex",
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
    (
        ROOT / "paper1_epistemic_mechanics" / "sections" / "03_workspace.tex",
        r"\subsection{Selection as a constrained top-$k$ problem}",
        r"\subsection{Selection as a constrained \texorpdfstring{top-$k$}{top-k} problem}",
    ),
    (
        ROOT / "paper2_rakl_framework" / "sections" / "99_round050_latest_refs.tex",
        r"""\bibitem{riosgarcia2026}
M. R\'ios-Garc\'ia, N. Alampara, C. Gupta, I. Mandal, S. Mannan, A. A. Aghajani, N. M. A. Krishnan, and K. M. Jablonka. AI scientists produce results without reasoning scientifically. \emph{arXiv:2604.18805}, 2026.

""",
        "",
    ),
    (
        ROOT / "paper4_verified_discovery" / "sections" / "10_rakl_integration.tex",
        r"""\[
\texttt{CONJECTURE}
\rightarrow
\texttt{FORMALIZED\_UNPROVEN}
\rightarrow
\texttt{MACHINE\_PROVEN}
\rightarrow
\texttt{BOUNDED\_NOVEL\_RESULT}
\rightarrow
\texttt{NEW\_MATHEMATICS\_CANDIDATE}.
\]""",
        r"""\[
\begin{aligned}
\texttt{CONJECTURE}
&\rightarrow \texttt{FORMALIZED\_UNPROVEN}
\rightarrow \texttt{MACHINE\_PROVEN}\\
&\rightarrow \texttt{BOUNDED\_NOVEL\_RESULT}
\rightarrow \texttt{NEW\_MATHEMATICS\_CANDIDATE}.
\end{aligned}
\]""",
    ),
]


def main() -> None:
    changed = 0
    for path, old, new in PATCHES:
        if not path.exists():
            raise SystemExit(f"publication typography target missing: {path}")
        text = path.read_text(encoding="utf-8")
        if old not in text:
            if new and new in text:
                continue
            if not new:
                continue
            raise SystemExit(f"publication typography anchor missing in {path}")
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"expected exactly one typography anchor in {path}, found {count}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        changed += 1
    print(f"publication typography patches applied: {changed}")


if __name__ == "__main__":
    main()
