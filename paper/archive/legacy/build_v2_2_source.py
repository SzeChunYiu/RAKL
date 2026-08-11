from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from build_v2_1_source import (
    FIGURES,
    GENERATED_FIGURES,
    PatchError,
    _insert_before_once,
    build_v2_1_source,
)


def build_v2_2_source(*, subject_sha: str, software_tests: int) -> str:
    text = build_v2_1_source(subject_sha=subject_sha, software_tests=software_tests)

    owmd_section = r"""
\section{Workspace-gated research cognition and open-world discovery}

The persistent atlas is designed to remember what a research process has established, rejected or left unresolved. It is not intended to place the entire archive in active computational context. That distinction matters because salience is easy to create: a claim can become available to every downstream operator without becoming coherent with the rest of the evidence, let alone more trustworthy.

\subsection{A transient workspace without epistemic write authority}

For a current target and residual, let \(C_t\) denote candidate material retrieved from canonical state. A bounded gate selects
\[
W_t=G_{\kappa,\Pi_t^x}(C_t),\qquad |W_t|\leq\kappa .
\]
The frame stores selected content, a typed broadcast map, a selection ledger and intervention/lifetime metadata. Downstream operators consume projections of this frame and return proposals. Canonical state still changes only through verification and promotion.

This separation has substantial prior art. Blackboard architectures coordinated heterogeneous knowledge sources through a shared structure \cite{hayesroth1985,nii1986}; Global Workspace and Global Neuronal Workspace accounts emphasise broad availability under limited capacity \cite{dehaene2001,mashour2020}. Neural variants make the same computational idea explicit: the Consciousness Prior uses attention-mediated selection and broadcast \cite{bengio2017}, while Shared Global Workspace architectures make specialist modules compete for a bandwidth-limited communication channel \cite{goyal2021}. We therefore do not claim novelty for shared workspaces, competition or broadcast themselves. The RAKL-specific requirement is narrower: workspace access must not create a new route to scientific authority.

Let \(A_t(a)\) denote computational access, \(C_t(a)\) atlas coherence under registered context and gluing obligations, and \(\alpha_t(a)\) scientific authority. The intended non-implications are
\[
A_t(a)\not\Rightarrow C_t(a),\qquad
A_t(a)\not\Rightarrow \operatorname{True}(a),\qquad
C_t(a)\not\Rightarrow \alpha_t(a)\text{ increases}.
\]
The reference workspace enforces the first boundary at the software write surface: it can select, reweight, substitute, evict and broadcast, but its direct output is a proposal. Coactivation creates no compatibility or gluing witness. The default gate also reserves capacity for challenge, novelty and negative-history material, preventing a simple relevance ranking from filling every slot with material that already agrees with the current state.

Controlled workspace interventions can still be scientifically useful. Removing, replacing or reweighting an active item can show that the item was computationally load-bearing for a later proposal. That result belongs to cognitive provenance. It is stored separately from evidential provenance and cannot, by itself, support the scientific claim carried by the item.

\subsection{J-space as an empirical comparison, not an identity claim}

Gurnee et al. report language-model representations with functional properties associated with a global workspace, including reportability, directed modulation, internal reasoning, flexible generalisation and selectivity \cite{gurnee2026}. Their framing concerns functional access and explicitly takes no position on phenomenal consciousness. The formal J-space construction is also geometric rather than order-theoretic: for fixed sparsity \(k\), sparse non-negative combinations of J-lens vectors form a union of \(k\)-dimensional cones. That construction supplies neither a partial order nor meet/join laws, so `J-space = RAKL lattice' is not a licensed inference. The study further leaves open the mechanism that causes representations to enter J-space. We use the work as motivation for selective-access and intervention tests, not as a theorem about the epistemic substrate.

\subsection{Open-World Mechanism Discovery}

The search failure that motivated this addition was not a lack of recursion. Recursive search had repeatedly refined concepts while inheriting the same vocabulary and disciplinary neighbourhood. We call this \emph{ontology-conditioned closure}. The repair begins one level earlier, with functional ownership. For each high-impact subsystem \(M\), the system registers
\[
\mathcal F_{\mathrm{req}}(M)=\{f_1,\ldots,f_n\}.
\]
A function is considered owned only when the record names a mechanism, scope, preconditions, postconditions, evidence, executable tests and failure semantics. A subsystem label alone is not sufficient.

An unowned or contested function is then inverted into a signature
\[
\sigma(f)=(I,O,C,R,D,X),
\]
covering inputs, outputs, resource constraints, characteristic relations, dynamics/control behaviour and intervention or failure signatures. The discovery protocol branches from that description across exact terminology, lexical variants, function-only search, historical precursors, mathematical equivalents, implementation analogues, methodological inspiration, citation neighbourhoods, literature bridges, adversarial alternatives, cross-language variants when applicable, and a final freshness scan. At least one completed route must be lexically independent of the core vocabulary. The requirement follows a familiar retrieval lesson: different communities often use different words for the same function \cite{furnas1987}. It also complements methodology-inspiration retrieval, which explicitly searches for transferable methods rather than relying on topical similarity alone \cite{garikaparthi2025}.

Retrieved mechanisms keep both source and route provenance. They are classified as equivalent, subsumed, complementary, conflicting, novel residual or unresolved. Equivalent and subsuming prior work narrows the novelty boundary instead of being relabelled as a framework invention. A bounded Discovery Workspace then reserves attention for remote, challenging, historical and fresh candidates before ordinary relevance fill. Its role is comparison and search control, not truth assignment.

\paragraph{A bounded closure claim.}
A function can receive a bounded discovery-closure certificate only after the required routes are complete or explicitly inapplicable, a vocabulary-independent route has run, citation-neighbourhood stability and a freshness cutoff are recorded, omission and nearest-work equivalence audits are complete, and unresolved candidates remain explicit fibers. The certificate is therefore indexed by route set, source universe, budget and time. It does not claim that finite search proves the non-existence of a relevant concept in an unrestricted open world.

\paragraph{GWT-OMISSION-01.}
The regression test withholds the strings ``global workspace'', ``consciousness'', ``J-space'', ``blackboard'' and relevant author names. It exposes only function: many parallel processes, competitive admission of a small active set, bounded capacity, broad downstream reuse, persistence and eviction, causal sensitivity to interventions, and the rule that prominence does not establish truth. A scored retrieval run must reach blackboard architectures, Global Workspace/Global Neuronal Workspace, the Consciousness Prior, shared neural workspaces and the J-space study through at least one ontology-independent route. The current test validates the scoring, route-provenance and name-leakage contract. Prospective recall on genuinely fresh hidden concepts remains an empirical evaluation rather than a conclusion drawn from this retrospective case.
"""
    text = _insert_before_once(
        text,
        r"\section{Known-answer engineering trace}",
        owmd_section,
        "owmd-workspace-section",
    )

    bib_delta = r"""
\bibitem{hayesroth1985} B. Hayes-Roth. A blackboard architecture for control. \emph{Artificial Intelligence} 26:251--321, 1985. doi:10.1016/0004-3702(85)90063-3.
\bibitem{nii1986} H. P. Nii. The Blackboard Model of Problem Solving and the Evolution of Blackboard Architectures. \emph{AI Magazine} 7(2):38--53, 1986.
\bibitem{dehaene2001} S. Dehaene and L. Naccache. Towards a cognitive neuroscience of consciousness: basic evidence and a workspace framework. \emph{Cognition} 79:1--37, 2001. PMID:11164022.
\bibitem{mashour2020} G. A. Mashour, P. Roelfsema, J.-P. Changeux, and S. Dehaene. Conscious Processing and the Global Neuronal Workspace Hypothesis. \emph{Neuron} 105:776--798, 2020. doi:10.1016/j.neuron.2020.01.026.
\bibitem{bengio2017} Y. Bengio. The Consciousness Prior. arXiv:1709.08568, 2017.
\bibitem{goyal2021} A. Goyal et al. Coordination Among Neural Modules Through a Shared Global Workspace. arXiv:2103.01197, 2021.
\bibitem{gurnee2026} W. Gurnee et al. Verbalizable Representations Form a Global Workspace in Language Models. \emph{Transformer Circuits Thread}, published 6 July 2026; arXiv:2607.15495, posted 16 July 2026.
\bibitem{furnas1987} G. W. Furnas, T. K. Landauer, L. M. Gomez, and S. T. Dumais. The Vocabulary Problem in Human-System Communication. \emph{Communications of the ACM} 30:964--971, 1987. doi:10.1145/32206.32212.
\bibitem{garikaparthi2025} A. Garikaparthi et al. MIR: Methodology Inspiration Retrieval for Scientific Research Problems. In \emph{ACL 2025}, 28614--28659. doi:10.18653/v1/2025.acl-long.1390.
"""
    text = _insert_before_once(text, r"\end{thebibliography}", bib_delta, "owmd-bibliography")

    forbidden = (
        "phenomenal consciousness established",
        "absolute open-world completeness",
    )
    for phrase in forbidden:
        if phrase in text:
            raise PatchError(f"forbidden v2.2 release phrase present: {phrase}")
    return text


def stage_v2_2_release(
    destination: Path,
    *,
    subject_sha: str,
    software_tests: int,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    source = build_v2_2_source(subject_sha=subject_sha, software_tests=software_tests)
    main = destination / "main.tex"
    main.write_text(source, encoding="utf-8")
    for path in FIGURES.glob("*.tex"):
        shutil.copy2(path, destination / path.name)
    for stem in ("fig5_demo_growth", "fig6_demo_context"):
        source_pdf = GENERATED_FIGURES / f"{stem}.pdf"
        if not source_pdf.exists():
            raise FileNotFoundError(f"generate figures before staging: {source_pdf}")
        shutil.copy2(source_pdf, destination / source_pdf.name)
    return main


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--software-tests", required=True, type=int)
    args = parser.parse_args()
    source = build_v2_2_source(subject_sha=args.subject_sha, software_tests=args.software_tests)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(source, encoding="utf-8")
    if args.stage is not None:
        stage_v2_2_release(args.stage, subject_sha=args.subject_sha, software_tests=args.software_tests)
    if args.output is None and args.stage is None:
        print(hashlib.sha256(source.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
