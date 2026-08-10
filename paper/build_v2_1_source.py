from __future__ import annotations

import argparse
import base64
import bz2
import hashlib
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V2_RELEASE = ROOT / "paper" / "arxiv_release_v2_2026-08-10"
FIGURES = ROOT / "paper" / "figures"
GENERATED_FIGURES = FIGURES / "generated"
V2_EXPECTED_SHA256 = "4adec2bb256775823dde3b5f520a9ef599c4fe95078121a513ce71e301ac5302"
PARTS = (
    "main.tex.bz2.b64.part01",
    "main.tex.bz2.b64.part02a",
    "main.tex.bz2.b64.part02b",
    "main.tex.bz2.b64.part03",
    "main.tex.bz2.b64.part04",
)


class PatchError(RuntimeError):
    pass


def decode_v2_source() -> str:
    encoded = "".join((V2_RELEASE / name).read_text(encoding="utf-8").strip() for name in PARTS)
    raw = bz2.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != V2_EXPECTED_SHA256:
        raise RuntimeError(f"reviewed V2 source digest mismatch: {digest}")
    return raw.decode("utf-8")


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise PatchError(f"{label}: expected one exact anchor, observed {count}")
    return text.replace(old, new, 1)


def _insert_before_once(text: str, anchor: str, insertion: str, label: str) -> str:
    return _replace_once(text, anchor, insertion.rstrip() + "\n\n" + anchor, label)


def _validate_subject(subject_sha: str, software_tests: int) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", subject_sha):
        raise ValueError("subject_sha must be a 40-character lowercase git SHA")
    if software_tests < 1:
        raise ValueError("software_tests must be positive")


def build_v2_1_source(*, subject_sha: str, software_tests: int) -> str:
    _validate_subject(subject_sha, software_tests)
    text = decode_v2_source()

    text = _replace_once(
        text,
        r"\newcommand{\SoftwareTests}{627}",
        rf"\newcommand{{\SoftwareTests}}{{{software_tests}}}",
        "software-test-count",
    )
    text = _replace_once(
        text,
        r"\newcommand{\ImplementationSHA}{\texttt{5995e99b0ef5e8d192a786c082ea880acadaab88}}",
        rf"\newcommand{{\ImplementationSHA}}{{\texttt{{{subject_sha}}}}}",
        "implementation-sha",
    )

    provenance_delta = r"""
\paragraph{Provenance standards and the novelty boundary.}
Provenance representation itself is established infrastructure. W3C PROV-O, for example, supplies a general ontology for interchanging provenance across heterogeneous systems \cite{w3cprov2013}. \RAKL{} therefore does not claim novelty for provenance graphs or source ancestry. Its narrower contribution is to couple source-rehydratable provenance to context-scoped scientific objects, typed relation witnesses, multi-axis authority and gated canonical updates; provenance visibility alone neither establishes truth nor licenses a mechanism or identification claim.
"""
    text = _insert_before_once(
        text,
        r"\subsection{Analogy and active inquiry}",
        provenance_delta,
        "provenance-delta",
    )

    memory_lineage_delta = r"""
\paragraph{Compression lineage and what is not claimed.}
Minimum-description-length reasoning formalizes an important pressure against representational complexity \cite{rissanen1978}, while the information-bottleneck principle studies compression that preserves information relevant to a target variable \cite{tishby2000}. These are intellectual-lineage analogies rather than algorithms silently implemented by the current reference profile. The present context compiler does not estimate mutual information or solve an information-bottleneck objective, and the Knowledge Atlas ``volume'' introduced below is not a description length. The retained engineering lesson is narrower: compactness, target-relevant retained function and scientific authority must be measured separately.
"""
    text = _insert_before_once(
        text,
        r"\section{Formal method}",
        memory_lineage_delta,
        "memory-lineage-delta",
    )

    learning_delta = r"""
\paragraph{What ordinary RAKL learning changes.}
Ordinary \RAKL{} operation is external-state learning, not implicit modification of the base LLM weights. Accepted scientific state, negative history, provenance, method experience and retrieval/materialized views live outside the replaceable model. A contextual scientific projection selects what a source asserts for a registered question and context; normalization aligns units, terminology or coordinates; an optional embedding projects a view into retrieval space; and compression changes a derivative storage/materialization representation. These operations are not interchangeable. Embedding proximity never defines canonical scientific identity, and a lossy summary can save tokens only while retaining source pins and an erasure ledger; it cannot replace the raw evidence required for a strong verification operation.
"""
    text = _insert_before_once(
        text,
        r"\section{Atomic LLM research lifecycle}",
        learning_delta,
        "external-state-learning-delta",
    )

    obsidian_delta = r"""
\paragraph{The Obsidian miss as an external-discovery failure mode.}
The analogy above also exposed a failure in the method-development search process: the earlier external-framework atlas already contained a ``knowledge map'' facet, yet it did not independently surface Obsidian or the broader personal-knowledge-graph neighborhood before an externally supplied candidate made the connection obvious. Personal knowledge graphs are themselves an established research area concerned with representation, management and use of structured personal knowledge \cite{skjaeveland2023}. Round~44 therefore records this incident as an \texttt{EXOGENOUS\_CONCEPT\_MISS}, not as evidence that the knowledge was unavailable. External-method and novelty searches now distinguish in-domain, function-first, adjacent-discipline, interaction-analogy and adversarial-prior-art routes. If a later candidate overlaps registered target functions but was missed after a route ensemble declared saturation, external-discovery saturation reopens. The retrospective Obsidian recovery validates the guard mechanism only; it is not prospective transfer evidence for a generally improved discovery skill.
"""
    text = _insert_before_once(
        text,
        r"\section{Known-answer engineering trace}",
        obsidian_delta,
        "obsidian-failure-delta",
    )

    old_growth_intro = (
        r"Figure~\ref{fig:demogrowth} shows semantic growth and target reachability. Round R0 contributes six semantic objects but leaves the target blocked; R1 adds the finite-amplitude object and opens the target; subsequent same-context and independent routes add no semantic object, yielding the configured scoped saturation state. The refuted mass-dependence claim is not deleted to make the graph cleaner; it remains negative history."
    )
    new_growth_intro = r"""Longitudinal atlas metrology requires a frozen measurement basis. In the V2.1 receipt, the basis \texttt{PENDULUM\_FIBER\_KIND\_METROLOGY\_V1} fingerprints the fiber partition, atom-kind schema, identity policy and context schema; a changed basis makes the comparison invalid rather than manufacturing apparent growth. Under that basis, the number of occupied $(\text{fiber},\text{atom kind})$ cells stays at seven from R0 through R3, while the atom count changes from eight to nine at R1. Geometry is reported separately from target-conditioned scientific progress: R0$\rightarrow$R1 closes one blocking cut and opens one support path, R1$\rightarrow$R2 is flat on the registered progress coordinates, and R2$\rightarrow$R3 adds an independent evidence root without opening another target path. Negative-history growth is likewise a separate coordinate rather than a penalty hidden inside one scalar score."""
    text = _replace_once(text, old_growth_intro, new_growth_intro, "growth-intro")

    text = _replace_once(
        text,
        r"\resizebox{0.78\textwidth}{!}{\input{fig5_demo_growth.tex}}",
        r"\input{fig5_demo_growth.tex}",
        "growth-figure-wrapper",
    )
    old_growth_caption = r"\caption{\textbf{Known-answer semantic growth and target reachability.} Cumulative semantic objects are counted after identity resolution, not by source count. The finite-amplitude evidence contributes one new object and closes the previously blocking target cut. Later routes are semantically flat.}"
    new_growth_caption = r"\caption{\textbf{Knowledge geometry and target-conditioned value are distinct.} \textbf{a}, Basis-bound atlas geometry: the occupied-cell count remains seven while the atom count increases from eight to nine at R1. \textbf{b}, Target access: the finite-amplitude evidence closes the blocking cut and opens the support path at R1; R2 is flat. \textbf{c}, Independent evidence roots increase again at R3 without another support-path opening. All values are deterministic known-answer engineering quantities, not evidence of scientific superiority.}"
    text = _replace_once(text, old_growth_caption, new_growth_caption, "growth-caption")

    old_context_intro = r"The demo also illustrates why storage growth and prompt growth are different quantities. The candidate archive used for the trace has a 270-token estimate, while the target-conditioned working set uses 52 tokens (19.3\%). The lossy target summary remains explicitly pinned to canonical roots `raw:S1', `raw:S3' and `raw:S7'; those sources can be rehydrated when stronger verification needs detail erased by the summary."
    new_context_intro = r"""The demo also separates three engineering capacity planes. The logical scientific archive has a 270-token estimate while the target-conditioned working set uses 52 tokens (19.3\%). The eight original raw source payloads contain 826 bytes; the reference content-addressed archive stores them in 739 bytes after using lossless compression only where it reduces size. A byte-identical refetch increases logical raw accounting from 826 to 892 bytes and the logical record count from eight to nine, but physical storage remains 739 bytes because the payload blob is deduplicated. Cold demotion then leaves three protected blobs using 273 hot bytes and moves five blobs cold; total stored bytes and all canonical records remain unchanged. The lossy target summary remains pinned to canonical roots `raw:S1', `raw:S3' and `raw:S7', and exact rehydration is verified."""
    text = _replace_once(text, old_context_intro, new_context_intro, "context-intro")
    text = _replace_once(
        text,
        r"\resizebox{0.88\textwidth}{!}{\input{fig6_demo_context.tex}}",
        r"\input{fig6_demo_context.tex}",
        "context-figure-wrapper",
    )
    old_context_caption = r"\caption{\textbf{Known-answer context materialization.} The active context is a target-conditioned view rather than a copy of the archive. The reported token counts are deterministic engineering counts in the mini-world; they do not establish real-world compression performance.}"
    new_context_caption = r"\caption{\textbf{Archive, active context and hot storage are controlled separately.} \textbf{a}, The target-conditioned prompt uses 52 of a 270-token archive estimate. \textbf{b}, The eight raw payloads occupy 826 bytes before physical compression, 739 bytes after lossless storage, and 273 bytes in the protected hot tier after cold demotion. \textbf{c}, an exact refetch grows logical history while physical storage stays at 739 bytes; canonical rehydration remains exact. These are reference-backend engineering measurements, not production-scale storage or scientific-performance claims.}"
    text = _replace_once(text, old_context_caption, new_context_caption, "context-caption")

    old_demo_boundary = r"The demo therefore supplies evidence for a limited claim: the reference implementation can preserve source lineage while collapsing exact semantic duplicates, retain context-distinct claims, avoid specified false contradictions, preserve a refutation, represent a missing prerequisite as an epistemic cut, open a target support path when that prerequisite arrives, and materialize a bounded rehydratable working context. It does not show that an LLM using RAKL discovers better science. That stronger claim belongs to the matched and Polymarket experiments."
    new_demo_boundary = r"The demo therefore supplies evidence for a limited claim: the reference implementation can preserve source lineage while collapsing exact semantic duplicates, retain context-distinct claims, avoid specified false contradictions, preserve a refutation, represent a missing prerequisite as an epistemic cut, open a target support path when that prerequisite arrives, measure geometry only under a frozen basis, distinguish target value from graph growth, deduplicate and losslessly compress canonical bytes, bound the hot and prompt working sets, and rehydrate required evidence. It does not show that an LLM using \RAKL{} discovers better science. That stronger claim belongs to the matched and real-science experiments."
    text = _replace_once(text, old_demo_boundary, new_demo_boundary, "demo-boundary")

    current_boundary_anchor = r"\section{First-sign Self-RAKL evidence}"
    current_boundary_delta = r"""
\paragraph{Round-44/45 hardening boundary.}
The V2.1 hardening pass adds basis-bound lattice metrology, a non-compensatory target-progress vector, a lossless content-addressed reference archive with hot/cold capacity control, an exogenous-discovery saturation guard, and a provider-neutral same-model pendulum microtrial harness. These additions have executable tests and deterministic receipts where applicable. The matched microtrial itself remains preregistered and unexecuted, and the Obsidian repair remains retrospective; neither addition licenses a general scientific-superiority or strong self-evolution claim.
"""
    text = _insert_before_once(text, current_boundary_anchor, current_boundary_delta, "current-boundary-delta")

    self_delta = r"""
The Obsidian incident is another preserved first-sign failure. A relevant adjacent knowledge-navigation system was available in the world but not surfaced by the framework's earlier search routes; a later external prompt exposed the miss. Rather than adding the product name to a permanent exception list, \RAKL{} records the miss as failure memory and expands the route contract prospectively. Because the repair was designed after seeing the missed case, rediscovering Obsidian carries no fresh-transfer credit.
"""
    text = _insert_before_once(
        text,
        r"\section{Preregistered empirical evaluation}",
        self_delta,
        "self-correction-delta",
    )

    old_matched = r"The same base LLM will be compared under matched evidence cutoff, tools, hidden outcomes and resource budget across direct strong prompting, retrieval-augmented research, a strong generic agentic workflow, fixed \RAKL{} and self-evolving \RAKL{}. Primary outcomes include hidden scientific-defect precision/recall, unsupported authority upgrades, counterevidence uptake, negative-history recovery, experiment discrimination per cost, final held-out scientific performance, context tokens, tool calls and wall time. The framework loses its empirical case if simpler conditions match its registered scientific-process and final-task outcomes at lower cost without more blocking failures."
    new_matched = r"The same base LLM will be compared under matched evidence cutoff, tools, hidden outcomes and a common preregistered resource ceiling across direct strong prompting, retrieval-augmented research, a strong generic agentic workflow, fixed \RAKL{} and self-evolving \RAKL{}. The ceiling constrains model input/output tokens, preprocessing model tokens, preprocessing tool calls, external retrieval and wall time; actual resource use may differ because preprocessing is part of the intervention, but every arm must report its usage and remain within the same envelope. Primary outcomes include hidden scientific-defect precision/recall, unsupported authority upgrades, counterevidence uptake, negative-history recovery, experiment discrimination per cost, final held-out scientific performance, context tokens, preprocessing cost, tool calls and wall time. The framework loses its empirical case if simpler conditions match its registered scientific-process and final-task outcomes at lower cost without more blocking failures. The pendulum same-model microtrial is only a diagnostic bridge to this broader programme and cannot establish general superiority."
    text = _replace_once(text, old_matched, new_matched, "matched-workflow-delta")

    discussion_delta = r"""
Two additional falsifiers follow from the hardening pass. First, longitudinal atlas-volume or density claims are invalid if their measurement-basis fingerprint changes; ontology refinement cannot count as knowledge growth by itself. Second, external-framework or novelty saturation is falsified for a scope when a later candidate materially overlaps registered functions yet was missed by a route ensemble that had declared saturation. In that case the missed candidate remains failure memory, the affected discovery scope reopens, and a repair earns method credit only prospectively on fresh hidden concepts.
"""
    text = _insert_before_once(
        text,
        r"\section*{Reproducibility and AI-use statement}",
        discussion_delta,
        "discussion-falsifier-delta",
    )

    old_repro = r"The public repository is \url{https://github.com/SzeChunYiu/RAKL}. It maintains frozen benchmarks, content-addressed execution receipts, exact-subject CI, negative-history records, release manifests and editable paper/figure sources. The v2 engineering demonstration is emitted by \path{src/rakl/mini_research_demo.py}; its committed machine receipt is \path{research/MINI_RESEARCH_DEMO_043_RECEIPT.json}; quantitative Figure~\ref{fig:demogrowth} and Figure~\ref{fig:democontext} are generated from that receipt and equality-checked in CI. Language models are research, coding and drafting tools rather than authors; their proposals do not possess canonical scientific authority. Same-context role simulations are not counted as independent peer review. The later journal-results manuscript will bind exact data/transformation identities, model-run receipts and all quantitative figure source data."
    new_repro = r"The public repository is \url{https://github.com/SzeChunYiu/RAKL}. It maintains frozen benchmarks, content-addressed execution receipts, exact-subject CI, negative-history records, release manifests and editable paper/figure sources. The V2.1 engineering figures are rendered with deterministic Matplotlib code from \path{research/MINI_RESEARCH_DEMO_043_RECEIPT.json}, \path{research/MINI_RESEARCH_METROLOGY_044_RECEIPT.json} and \path{research/MINI_ARCHIVE_STORAGE_044_RECEIPT.json}; CI checks the plotted source coordinates and exports PDF, editable SVG, PNG preview and machine-readable figure source data. Structural arrows are intentionally unlabelled in the paper schematics, and quantitative arrow callouts are forbidden by repository tests. Language models are research, coding and drafting tools rather than authors; their proposals do not possess canonical scientific authority. Same-context role simulations and the present internal Nature-style review rounds are not counted as independent peer review. The later journal-results manuscript will bind exact data/transformation identities, model-run receipts and all quantitative figure source data."
    text = _replace_once(text, old_repro, new_repro, "reproducibility-delta")

    bib_delta = r"""
\bibitem{rissanen1978} J. Rissanen. Modeling by shortest data description. \emph{Automatica}, 14(5):465--471, 1978. doi:10.1016/0005-1098(78)90005-5.
\bibitem{tishby2000} N. Tishby, F. C. Pereira, and W. Bialek. The information bottleneck method. arXiv:physics/0004057, 2000.
\bibitem{w3cprov2013} W3C. PROV-O: The PROV Ontology. W3C Recommendation, 30 April 2013. \url{https://www.w3.org/TR/prov-o/}.
\bibitem{skjaeveland2023} M. G. Skj\ae veland, K. Balog, N. Bernard, W. \L ajewska, and T. Linjordet. An Ecosystem for Personal Knowledge Graphs: A Survey and Research Roadmap. arXiv:2304.09572, 2023.
"""
    text = _insert_before_once(text, r"\end{thebibliography}", bib_delta, "bibliography-delta")

    # Public source must remain a scoped methods/preregistration manuscript.
    forbidden = ("[[RESULT:", "scientific superiority demonstrated", "independent peer review completed")
    for phrase in forbidden:
        if phrase in text:
            raise PatchError(f"forbidden release phrase present: {phrase}")
    return text


def stage_v2_1_release(
    destination: Path,
    *,
    subject_sha: str,
    software_tests: int,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    source = build_v2_1_source(subject_sha=subject_sha, software_tests=software_tests)
    main = destination / "main.tex"
    main.write_text(source, encoding="utf-8")

    # Stage all editable schematic/wrapper TeX files next to the exact manuscript.
    for path in FIGURES.glob("*.tex"):
        shutil.copy2(path, destination / path.name)
    # Quantitative wrappers use same-directory PDF paths for hermetic release builds.
    for stem in ("fig5_demo_growth", "fig6_demo_context"):
        source_pdf = GENERATED_FIGURES / f"{stem}.pdf"
        if not source_pdf.exists():
            raise FileNotFoundError(f"generate figures before staging: {source_pdf}")
        shutil.copy2(source_pdf, destination / source_pdf.name)
    return main


def inspection_report(text: str) -> str:
    needles = (
        "SoftwareTests",
        "ImplementationSHA",
        "Known-answer engineering trace",
        "Obsidian analogy",
        "fig5_demo_growth",
        "fig6_demo_context",
        "Current evidence boundary",
        "Discussion and falsifiers",
        "Reproducibility",
        "\\begin{thebibliography}",
        "\\end{thebibliography}",
    )
    lines = text.splitlines()
    output: list[str] = ["=== SECTION HEADINGS ==="]
    output.extend(
        f"{index + 1:04d}: {line}"
        for index, line in enumerate(lines)
        if line.lstrip().startswith(("\\section", "\\subsection", "\\paragraph"))
    )
    for needle in needles:
        matches = [index for index, line in enumerate(lines) if needle in line]
        output.append(f"=== {needle} ===")
        if not matches:
            output.append("NOT FOUND")
            continue
        for index in matches[:3]:
            start = max(0, index - 3)
            stop = min(len(lines), index + 5)
            output.extend(f"{line_no + 1:04d}: {lines[line_no]}" for line_no in range(start, stop))
    return "\n".join(output) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--subject-sha")
    parser.add_argument("--software-tests", type=int)
    args = parser.parse_args()

    if args.subject_sha is None or args.software_tests is None:
        source = decode_v2_source()
    else:
        source = build_v2_1_source(
            subject_sha=args.subject_sha,
            software_tests=args.software_tests,
        )
    if args.inspect:
        print(inspection_report(source), end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(source, encoding="utf-8")
    if args.stage is not None:
        if args.subject_sha is None or args.software_tests is None:
            raise ValueError("--stage requires --subject-sha and --software-tests")
        stage_v2_1_release(
            args.stage,
            subject_sha=args.subject_sha,
            software_tests=args.software_tests,
        )
    if not args.inspect and args.output is None and args.stage is None:
        print(hashlib.sha256(source.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
