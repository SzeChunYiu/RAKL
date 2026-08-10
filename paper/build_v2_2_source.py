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

\paragraph{Persistent epistemic state is not active computational access.}
A bounded research process cannot expose every archived object to every proposer at every step. We therefore introduce a transient workspace above, rather than inside, canonical epistemic state. For candidate set \(C_t\), a gate selects
\[
W_t=G_{\kappa,\Pi_t^x}(C_t),\qquad |W_t|\leq\kappa .
\]
The frame records selected content, a typed broadcast map, a selection ledger and lifetime/intervention metadata. Downstream operators receive workspace projections and return proposals; canonical state still changes only through the existing verification and promotion path. This separation is motivated by prior blackboard control architectures and global-workspace accounts, where specialized processes coordinate through a shared, capacity-limited structure \cite{hayesroth1985,nii1986,dehaene2001,mashour2020}. Neural variants likewise select a small subset for broader reuse: the Consciousness Prior emphasizes attention-mediated selection and broadcast \cite{bengio2017}, while Shared Global Workspace architectures make specialist modules compete for a bandwidth-limited communication channel \cite{goyal2021}. RAKL therefore claims no novelty for shared workspaces, competition or broadcast in isolation.

\paragraph{Access, coherence and authority are different globalities.}
Let \(A_t(a)\) denote global computational accessibility, \(C_t(a)\) atlas coherence under the registered context/gluing obligations, and \(\alpha_t(a)\) scientific authority. The architecture enforces the non-implications
\[
A_t(a)\not\Rightarrow C_t(a),\qquad
A_t(a)\not\Rightarrow \operatorname{True}(a),\qquad
C_t(a)\not\Rightarrow \alpha_t(a)\text{ increases}.
\]
The workspace module has no canonical write capability: it can select, reweight, substitute, evict and broadcast items, but its direct output type is a proposal. Coactivation similarly produces no compatibility or gluing witness. We reserve workspace capacity for challenge, novelty and negative-history material so that a pure relevance or current-authority ranking cannot be the only gate policy. Controlled interventions on workspace contents can establish computational load-bearing influence on later proposals, but such cognitive provenance is stored separately from evidential provenance and cannot itself support a scientific claim.

\paragraph{J-space is motivation for causal tests, not a RAKL identity claim.}
Gurnee et al. report language-model representations with functional properties associated with a global workspace, including reportability, directed modulation, internal reasoning, flexible generalization and selectivity \cite{gurnee2026}. Their framing concerns functional access and explicitly takes no position on phenomenal consciousness. The formal J-space is defined from sparse non-negative combinations of J-lens vectors; for fixed sparsity \(k\), its geometry is a union of \(k\)-dimensional cones. This does not make it an order-theoretic lattice, and RAKL does not identify J-space with its epistemic substrate. The study also leaves the mechanism that causes representations to enter J-space uncharacterized. We use the result narrowly: it motivates intervention-based tests of which active representations are computationally load-bearing and reinforces the need to separate prominence from epistemic authority.

\subsection{Open-World Mechanism Discovery}

The failure that motivated this addition was not insufficient recursive depth but \emph{ontology-conditioned closure}: search could recursively refine concepts while inheriting the same vocabulary and disciplinary neighborhood. For each high-impact subsystem \(M\), RAKL now registers required functions
\[
\mathcal F_{\mathrm{req}}(M)=\{f_1,\ldots,f_n\},
\]
and an owner is valid only when it records a mechanism, scope, preconditions, postconditions, evidence, executable tests and failure semantics. Missing owners open blocking research fibers.

For each gap \(f\), the system inverts the capability into a functional signature
\[
\sigma(f)=(I,O,C,R,D,X),
\]
covering inputs, outputs, resource constraints, characteristic relations, dynamics/control behavior and intervention/failure signatures. Search routes are then generated independently across exact terminology, lexical variants, function-only descriptions, historical precursors, mathematical equivalents, implementation analogues, methodological inspiration, citation neighborhoods, literature bridges, adversarial alternatives, cross-language variants where applicable and a final freshness scan. At least one route must be lexically independent of the current core vocabulary. This requirement operationalizes the classic vocabulary problem in information retrieval \cite{furnas1987} and complements recent methodology-inspiration retrieval, which explicitly targets transferable methods beyond superficial topical similarity \cite{garikaparthi2025}.

Retrieved mechanisms retain source and route provenance and are assimilated as equivalent, subsumed, complementary, conflicting, novel residual or unresolved. A bounded Discovery Workspace reserves capacity for remote, challenging, historical and fresh candidates before ordinary relevance fill. Its function is to prevent local-fiber myopia, not to decide truth.

\paragraph{Bounded discovery closure, never absolute completeness.}
A function can receive a bounded discovery-closure certificate only after the required expansion routes are complete or explicitly inapplicable, a vocabulary-independent route has run, citation-neighborhood stability and freshness are recorded, an omission review and nearest-work equivalence audit are complete, and every unresolved candidate remains an explicit fiber. The terminal condition is therefore scoped to a route set, source universe, budget and time cutoff. RAKL makes no claim that finite search proves the non-existence of an unknown concept in an unrestricted open world.

\paragraph{GWT-OMISSION-01.}
The regression withholds the strings ``global workspace'', ``consciousness'', ``J-space'', ``blackboard'' and author names. The input describes only many parallel processes, bounded competitive selection of a small active set, broad downstream reuse, persistence/eviction, causal sensitivity to interventions and the rule that computational prominence does not establish truth. A scored retrieval run must recover blackboard architectures, Global Workspace/Global Neuronal Workspace, the Consciousness Prior, shared neural workspaces and the J-space work through at least one ontology-independent route. The software test included in this release validates the scoring and leakage contract; prospective recall on fresh hidden concepts remains an empirical coordinate rather than being inferred from this retrospective case.
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
        "J-space = RAKL lattice",
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
