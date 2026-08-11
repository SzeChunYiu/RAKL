from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "paper4_verified_discovery"
KEYS = (
    "jiang2026frontier",
    "tsoukalas2026open",
    "ota2026discovery",
    "zhang2026leanmarathon",
    "gui2026robust",
)
PARAGRAPHS = (
    "\n\nA 2026 position paper focused explicitly on the transition from formal solvers to "
    "frontier mathematical research reaches a closely aligned diagnosis: open research adds "
    "under-specification, exploration, relational structure, tool integration and human--AI "
    "coordination obligations that are absent from fixed-target theorem-proving benchmarks "
    "\\cite{jiang2026frontier}. That roadmap therefore owns the broad claim that AI4Math must "
    "move from solver benchmarks toward research-agent systems.\n\n"
    "Formal proof search has also crossed from fixed olympiad-style targets into open-problem "
    "research. Tsoukalas et al. report a large-scale formal-proof-search study in which an agent "
    "resolved a subset of open Erd\\H{o}s problems and OEIS conjectures under machine verification "
    "\\cite{tsoukalas2026open}. Separately, Ota, Osa and Harada study self-supervised theorem discovery "
    "inside a formal axiomatic system, growing a reusable theorem library from axioms and inference "
    "rules alone \\cite{ota2026discovery}. These systems therefore own important territory around "
    "AI-assisted open-problem proof search and formal theorem-library growth.\n\n"
    "Long-horizon formalization itself now has a closer systems parent. LeanMarathon uses an evolving "
    "blueprint, adversarial target-fidelity review, a proof DAG and CI-gated local repair to formalize "
    "research mathematics over long developments \\cite{zhang2026leanmarathon}. A separate robustness "
    "study shows why target fidelity remains a distinct obligation: current autoformalizers can be "
    "unstable under global paraphrase and often fail to faithfully reflect local perturbations of the "
    "informal proof \\cite{gui2026robust}. The present paper therefore does not claim novelty for proof "
    "DAGs, long-horizon blueprint orchestration or the observation that autoformalization can drift. "
    "Its residual is assurance-specific: which artifacts may acquire specification, truth, novelty, "
    "research-value and verifier-trust authority; which exact receipts bind those promotions; and how "
    "those coordinates fail closed under long-horizon machine search."
)
BIB = (
    "\n\n\\bibitem{jiang2026frontier}\n"
    "E. Jiang et al. From Solvers to Research: Large Language Model-Driven Formal Mathematics "
    "at the Research Frontier. \\emph{arXiv:2607.07779}, 2026.\n\n"
    "\\bibitem{tsoukalas2026open}\n"
    "G. Tsoukalas et al. Advancing Mathematics Research with AI-Driven Formal Proof Search. "
    "\\emph{arXiv:2605.22763}, 2026.\n\n"
    "\\bibitem{ota2026discovery}\n"
    "K. Ota, T. Osa, and T. Harada. Self-Supervised Theorem Discovery in a Formal Axiomatic "
    "System. \\emph{arXiv:2606.28747}, 2026.\n\n"
    "\\bibitem{zhang2026leanmarathon}\n"
    "Y. Zhang, Y. Sun, T. Suzuki, J. D. Lee, and F. Liu. LeanMarathon: Toward Reliable AI "
    "Co-Mathematicians through Long-Horizon Lean Autoformalization. \\emph{arXiv:2606.05400}, 2026.\n\n"
    "\\bibitem{gui2026robust}\n"
    "Z. Gui, S. Yang, and Z. Shi. Evaluating the Robustness of Proof Autoformalization in Lean 4. "
    "\\emph{arXiv:2606.14867}, 2026.\n"
)
ANCHOR = (
    "Other systems use LLM generation together with executable evaluation or evolutionary "
    "search to discover new constructions and algorithms \\cite{romera2024,novikov2025,georgiev2025}."
)


def _key_state(text: str) -> tuple[bool, ...]:
    return tuple(key in text for key in KEYS)


def patch_body(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    state = _key_state(text)
    if all(state):
        return
    if any(state):
        raise SystemExit(f"Paper IV has a partial nearest-work refresh in {path}: {state}")
    count = text.count(ANCHOR)
    if count != 1:
        raise SystemExit(f"Paper IV nearest-work anchor count in {path}: {count}")
    path.write_text(text.replace(ANCHOR, ANCHOR + PARAGRAPHS, 1), encoding="utf-8")


def patch_bib(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    state = tuple((f"\\bibitem{{{key}}}" in text) for key in KEYS)
    if all(state):
        return
    if any(state):
        raise SystemExit(f"Paper IV has a partial nearest-work bibliography refresh in {path}: {state}")
    marker = r"\end{thebibliography}"
    count = text.count(marker)
    if count != 1:
        raise SystemExit(f"Paper IV bibliography marker count in {path}: {count}")
    path.write_text(text.replace(marker, BIB + "\n" + marker, 1), encoding="utf-8")


def main() -> None:
    normalized_body = ROOT / "sections" / "01_the_gap_between_solving_and_research.tex"
    normalized_bib = ROOT / "sections" / "99_references.tex"
    if normalized_body.exists() and normalized_bib.exists():
        patch_body(normalized_body)
        patch_bib(normalized_bib)
        return

    main = ROOT / "main.tex"
    text = main.read_text(encoding="utf-8")
    state = _key_state(text)
    if not all(state):
        if any(state):
            raise SystemExit(f"Paper IV monolithic source has partial nearest-work refresh: {state}")
        count = text.count(ANCHOR)
        if count != 1:
            raise SystemExit(f"Paper IV monolithic nearest-work anchor count: {count}")
        text = text.replace(ANCHOR, ANCHOR + PARAGRAPHS, 1)
    bib_state = tuple((f"\\bibitem{{{key}}}" in text) for key in KEYS)
    if not all(bib_state):
        if any(bib_state):
            raise SystemExit(f"Paper IV monolithic bibliography has partial refresh: {bib_state}")
        marker = r"\end{thebibliography}"
        count = text.count(marker)
        if count != 1:
            raise SystemExit(f"Paper IV monolithic bibliography marker count: {count}")
        text = text.replace(marker, BIB + "\n" + marker, 1)
    main.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
