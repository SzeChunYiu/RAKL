from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


P4_PATHS = [
    "paper/papers/paper-04-verified-discovery/main.tex",
    "publication/papers/paper-04-verified-discovery/main.tex",
]
for path in P4_PATHS:
    replace_exact(
        path,
        "\\newcommand{\\ImplementationSHA}{\\texttt{0000000000000000000000000000000000000000}}\n"
        "\\newcommand{\\SoftwareTests}{1}\n",
        "",
    )
    replace_exact(
        path,
        "\\author{Sze Chun Yiu}\n\\date{10 August 2026}",
        "\\author{Sze Chun Yiu\\\\Stockholm University\\\\\\texttt{sze-chun.yiu@fysik.su.se}}\n"
        "\\date{11 August 2026}",
    )
    replace_exact(
        path,
        "The staged release source and machine receipt record the exact 40-character Git subject identifier used for evaluation; "
        "the manuscript also records \\SoftwareTests{} passing repository tests before PDF construction.",
        "Machine-readable receipts bind evaluated artifacts to exact release identities and their recorded test evidence; "
        "this stable manuscript source does not hard-code a Git subject or an aggregate repository test count.",
    )

INTRO_PATHS = [
    "paper/papers/paper-01-epistemic-mechanics/sections/01_introduction_foundations_state.tex",
    "publication/papers/paper-01-epistemic-mechanics/sections/01_introduction_foundations_state.tex",
]
old_verifier = r"""\[
V(p,e,\gamma)\in
\{\mathrm{SUPPORTED},\mathrm{REFUTED},\mathrm{PARTIALLY\ IDENTIFIED},
\mathrm{BLOCKED},\mathrm{CANNOT\ CHECK}\}.
\]"""
new_verifier = r"""\[
V(p,e,\gamma)\in
\left\{
\begin{aligned}
&\mathrm{SUPPORTED},\ \mathrm{REFUTED},\ \mathrm{PARTIALLY\ IDENTIFIED},\\
&\mathrm{BLOCKED},\ \mathrm{CANNOT\ CHECK}
\end{aligned}
\right\}.
\]"""
for path in INTRO_PATHS:
    replace_exact(path, old_verifier, new_verifier)

WORKSPACE_PATHS = [
    "paper/papers/paper-01-epistemic-mechanics/sections/03_workspace.tex",
    "publication/papers/paper-01-epistemic-mechanics/sections/03_workspace.tex",
]
old_access = r"""\[
A_t(a)=\text{computational accessibility},\qquad
C_t(a)=\text{atlas coherence},\qquad
\alpha_t(a)=\text{epistemic authority}.
\]"""
new_access = r"""\[
\begin{aligned}
A_t(a)&=\text{computational accessibility},\\
C_t(a)&=\text{atlas coherence},\\
\alpha_t(a)&=\text{epistemic authority}.
\end{aligned}
\]"""
for path in WORKSPACE_PATHS:
    replace_exact(
        path,
        r"\subsection{Selection as a constrained top-$k$ problem}",
        r"\subsection{Selection as a constrained top-k problem}",
    )
    replace_exact(path, old_access, new_access)

print("finalized v3 publication sources")
