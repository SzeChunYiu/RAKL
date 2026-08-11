# RAKL Methods Preprint v2 — 2026-08-10

This directory binds the exact reviewed v2 LaTeX source used to render the Round-043 methods preprint.

## Exact source reconstruction

The source is stored as deterministic bzip2+base64 chunks because one large GitHub contents payload was truncated during the release transaction. The truncation was detected by an exact-SHA CI test and is preserved in Git history as a failed release candidate.

Reconstruct `main.tex` with:

```bash
cat \
  main.tex.bz2.b64.part01 \
  main.tex.bz2.b64.part02a \
  main.tex.bz2.b64.part02b \
  main.tex.bz2.b64.part03 \
  main.tex.bz2.b64.part04 \
  | tr -d '\n\r' \
  | base64 -d \
  | bunzip2 \
  > main.tex
```

Expected SHA-256:

```text
main.tex  4adec2bb256775823dde3b5f520a9ef599c4fe95078121a513ce71e301ac5302
```

The repository test `tests/test_v2_paper_source_binding.py` performs the same reconstruction and refuses the release if a byte differs.

## Reviewed rendered artifact

The reviewed PDF was compiled locally from that exact `main.tex` and the editable figure sources in `paper/figures/`.

```text
PDF SHA-256: 1ec9d7eb3d1318292adf028f8b19a11886b17802022e901f4666ec4e01759b52
Pages:       23
References:  59
Figures:     6
Encrypted:   no
```

Visual QA rendered every page and inspected the complete contact sheet plus all figure-heavy pages. Blocking overfull boxes, unresolved citations/references, clipped content, and figure collisions were cleared in the reviewed artifact.

## V2 substantive additions

V2 is not a citation-only revision. It adds:

- cross-domain intellectual lineage and explicit novelty narrowing;
- a detailed explanation of how raw evidence becomes scientific memory;
- a machine-checkable 17-stage atomic LLM research lifecycle;
- explicit separation of scientific projection, semantic identity, storage compression, retrieval/index space, and active prompt materialization;
- a deterministic known-answer mini research project with machine-readable metrics;
- receipt-derived quantitative figures for atlas growth and context efficiency;
- a scoped comparison to Obsidian-style graph navigation;
- expanded discussion of belief revision, mechanism explanation, partial identification, provenance, active inquiry, metacognition, causal reasoning, reproducibility and long-context/RAG prior art.

## Known-answer engineering demo

Canonical receipt:

```text
research/MINI_RESEARCH_DEMO_043_RECEIPT.json
```

The mini pendulum world is intentionally deterministic and uses zero LLM calls. It verifies the software mechanics independently of stochastic model behavior. It **does not** authorize a claim that RAKL improves real scientific discovery.

Key code-emitted values include:

```text
raw sources                          8
projected claims                     9
canonical semantic claims            7
atlas atoms: before -> after          8 -> 9
support paths: before -> after        0 -> 1
epistemic cuts: before -> after       1 -> 0
negative-history objects              1
semantic novelty by round             6, 1, 0, 0
archive token estimate                270
active context tokens                 52
active/archive ratio                  19.3%
atomic lifecycle stages               17/17
terminal demo saturation              SATURATED_SCOPED
```

Those numbers are guarded by `tests/test_mini_research_receipt.py`; the two quantitative figure sources are guarded by `tests/test_demo_figure_generation.py`.

## Evidence boundary

The v2 methods preprint remains a formal/reference-implementation + preregistration paper. It does not yet authorize:

- empirical superiority over matched simpler research workflows;
- fresh-assurance strong Self-RAKL evolution;
- independent peer-review credit;
- positive real `polymarket_crypto` / spot-science results;
- universal framework completeness or global saturation.

The next major evidence stage is the matched Self-RAKL and real spot-science programme.
