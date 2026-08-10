# Paper IV integration map — Mathematical Research Assurance

Date: 2026-08-10

## Purpose

Paper IV is intentionally developed on its own branch rather than rewriting the three current paper branches during closeout. It supplies a mathematically sharp extension that can later be cherry-picked into Papers I–III without weakening their existing claim boundaries.

## Current paper interfaces

### Paper I — RAKL framework
Branch: `paper/closeout-rakl-framework-20260810`

Relevant existing claims:
- LLM is proposer, not authority.
- canonical state changes only through verification/governance;
- authority is multi-axis and partially ordered;
- residuals and epistemic cut sets reopen research fibers;
- constructive invention proposes new mechanisms/formalisms without automatic promotion.

Paper IV extension:
- instantiate these abstractions for mathematical research;
- add specification/truth/novelty/value/trust coordinates;
- add a proof-artifact trust chain and theorem-promotion state machine;
- add a dedicated `mathematical-research` workflow.

Recommended future patch to Paper I:
- one paragraph in the authority section distinguishing theorem truth from novelty;
- one paragraph in the constructive-invention section noting that mathematical inventions route through Paper IV assurance;
- add the new module/test count only after CI is green and release identity is rebound.

### Paper II — Epistemic Mechanics
Branch: `paper/closeout-epistemic-mechanics-20260810`

Relevant existing claims:
- proposal-generating models have no direct canonical write authority;
- scientific authority is a poset rather than a scalar;
- pairwise compatibility need not imply higher-order gluing;
- open-world completeness is bounded relative to an explicit research world.

Paper IV extension:
- gives a concrete theorem-level example of authority-coordinate incomparability;
- proves that novelty is non-monotone as the literature world expands;
- treats a novelty certificate as bounded open-world closure rather than universal novelty;
- separates stable proof authority from defeasible novelty authority.

Recommended future patch to Paper II:
- add truth-versus-novelty as a compact worked example in the authority-poset section;
- add novelty non-monotonicity to the discussion of bounded open-world closure.

### Paper III — Shared Structural Substrate / Structural Amortization
Branch: `paper/structural-amortization-v0`

Relevant existing claims:
- structural witnesses license cross-domain transfer while rejecting semantic decoys;
- structure induction, retrieval, adaptation and verification must be charged in total cost;
- current deterministic conformance results are implementation tests rather than proof of generalization.

Paper IV extension:
- use structural witnesses to canonicalize theorem statements for prior-art retrieval;
- use structure-aware retrieval to find stronger parent theorems and notation-changed rediscoveries;
- reuse verified proof motifs as search priors without granting authority to the transfer itself;
- measure whether structural reuse reduces proof-search cost under strict verification.

Recommended future patch to Paper III:
- add mathematical theorem retrieval as a held-out transfer domain;
- distinguish `structural transfer useful for search` from `formal proof authority`;
- include novelty-screen cost in total cost-to-capability when the downstream claim is discovery rather than exercise solving.

## Paper IV claims that should remain separate

Do not merge the following into Papers I–III until their own evidence matures:

1. end-to-end autonomous mathematical discovery superiority;
2. low false-positive novelty rate on real literature;
3. improved theorem-discovery productivity versus strong baselines;
4. robust informal-to-formal alignment without expert review;
5. global novelty or complete mathematical literature coverage.

## Implementation delta on Paper IV branch

- `src/rakl/math_research_assurance.py`
- `tests/test_math_research_assurance.py`
- `docs/MATHEMATICAL_RESEARCH_ASSURANCE.md`
- `skills/rakl-core/workflows/mathematical-research.md`
- `skills/rakl-core/workflows/problem-solving.md` updated with a mathematical-research handoff
- `skills/rakl-core/manifest.yaml` v0.5.0 routing and invariants
- `paper/math_research_assurance/main.tex`

## Next empirical program

1. run the full repository CI and new unit tests;
2. construct hostile proof-assurance fixtures (`sorryAx`, custom axiom, native trust, mismatched statement hash);
3. build a small theorem-rediscovery benchmark with notation-renamed equivalents and stronger-parent results;
4. build an autoformalization-trap benchmark;
5. evaluate a real Lean proof-search system through the state machine;
6. only then patch claims into Papers I–III.
