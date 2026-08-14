# Phase 0 — comparison-class freeze

Frozen 2026-08-14 for issue #588. Registered systems carry one or more of these classes in
`registry.json`. **Systems in different classes may not be placed in one flat leaderboard.**

## Classes

| Class | Definition | Registered examples |
|---|---|---|
| **A** | Literature / deep-research agents — planning, retrieval, reading, citation, synthesis | Gemini Deep Research, DelveAgent, Asta v0 |
| **B** | Scientific-execution agents — generate/run code, analyse data, use scientific tools | Mini-SWE-Agent, DelveAgent, Asta v0, Claude Code |
| **C** | End-to-end / AI-scientist systems — hypothesis → literature → experiment → analysis → manuscript | AI Scientist-v2, InternAgent, Mimosa, Asta v0 |
| **D** | Self-improving / autonomous research systems — modify their own code, policies, prompts, search procedure or strategy from measured outcomes | Karpathy `autoresearch`, Mimosa |

Multi-class membership is normal and is recorded explicitly. Every entry also records the exact
evaluated configuration, version and date — or `CANNOT_CHECK` where the source did not state it.

## Comparator class — the rule that does the real work

Independently of A–D, each system carries a `comparator_class`:

- **`ARCHITECTURE_CAUSAL_ELIGIBLE`** — model, tools and budget can be matched, so the system may enter
  a Phase 4 causal arm.
- **`SYSTEM_LEVEL_ONLY`** — model, tool access, hidden retrieval corpus, evaluator or budget cannot be
  matched. Comparison is permitted but is a *system-level* observation.
- **`UNDETERMINED`** — not yet assessed; may not be used in any arm.

> Never write `ORION architecture > System X architecture` when the comparison confounds model, tool
> access, hidden retrieval corpus, evaluator or budget.

Every proprietary system is `SYSTEM_LEVEL_ONLY` by construction, and a test asserts this. In v1 only
four of nine systems are architecture-causal eligible.

## Same-substrate exclusion

A system running on the same harness or model as ORION is **not** an independent architecture arm,
regardless of its comparator class. `SYS-CLAUDE_CODE_AS_RESEARCH_AGENT` is registered precisely so
this confound is explicit rather than discovered later: it is the top-scoring agent in
ResearchClawBench's published cohort *and* ORION's own substrate.

## Class-to-benchmark map

| Class | Primary suites |
|---|---|
| A | AutoResearchBench, DeepResearch Bench, AstaBench |
| B | ScienceAgentBench, PhySciBench, AARRI-Bench, (HAL as infrastructure) |
| C | ResearchClawBench, AstaBench end-to-end category |
| D | *No public suite located.* |

**The class-D gap is a finding, not an omission.** Three route-family rounds found no public benchmark
that scores self-improvement quality — persistent learning, self-model calibration, self-evolution
trigger precision, meta-overfit rate. Every class-D system located (Karpathy `autoresearch`, Mimosa)
reports its own bespoke outcome instead.

Two consequences follow. First, ORION's self-improvement claims **cannot** be externally validated by
any Tier 1 suite currently in the registry; they need Tier 2 hostile mechanism benchmarks, and #588's
Phase 5 research-machine QoIs have no external comparator at all. Second, this is a defensible novelty
coordinate for Paper 6 — but only as "no public suite measures this", never as "ORION is best at it".
