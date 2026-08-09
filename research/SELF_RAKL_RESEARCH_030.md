# SELF-RAKL Research 030 — Scoped Self-Evolution Evidence

Date: 2026-08-09  
Starting `main`: `0299913aa4a786ea0a6762f14c53c9b26a670521`  
Frozen benchmark: `research/SELF_RAKL_RESEARCH_030_FROZEN_BENCHMARK.json`

## Transport/supersession history

A first self-evolution candidate was frozen and tested from earlier `main` `134aee702c48601d716b7de435dc30bd6c6938ba`. It reached exact candidate `1edeab7519e92dd3a7ab499d09c5fdcacfbe2088` and passed `337 passed in 8.65s`.

Before promotion, `main` advanced with an independent Round 029 evidence-lineage implementation and occupied the same Round-029 research filenames. The self-evolution candidate was therefore treated as stale and was **not force-promoted**. Round 030 re-registers the same self-evolution benchmark semantics on the new parent and preserves both histories.

## Core residual

RAKL's publication claim that the system can "evolve itself" needs a stricter evidence boundary:

```text
self-editing != benchmark gain != transfer != fresh evidence of evolution
```

The method should only claim scoped evolution when a child improves a frozen development packet and transfers positively to a fresh/blind assurance packet while exact identity, blocking invariants, history and evaluator separation remain clean.

## External novelty narrowing

Primary neighbors:

- ADAS / Meta Agent Search (`arXiv:2408.08435`): automatic invention/recombination of agentic systems.
- EvoAgentBench (`arXiv:2607.05202`): self-evolution via procedural ability transfer.
- SkillFoundry (`arXiv:2604.03964`): self-evolving validated scientific skill libraries from heterogeneous resources.
- Red Queen Gödel Machine (`arXiv:2606.26294`): co-evolution of agents and evaluators under controlled changing utilities.

Therefore RAKL must not claim novelty from self-modification, method recombination, skill accumulation, transfer evaluation or evaluator evolution alone.

## Two learning channels

RAKL's stronger architecture has two candidate sources:

```text
ENDOGENOUS
native residual -> RAKL-generated challenger

EXOGENOUS
external framework -> atomic operator extraction -> challenger
```

Both converge on the same evidence-governed assimilation/evaluation/promotion process. External reputation and internal authorship have no authority by themselves.

## Context-indexed capability frontier

The intended long-run method state is not one ever-larger super-agent. For each atomic fiber/context, RAKL should retain non-dominated validated methods. A new operator may replace an incumbent locally, add a complementary frontier point, deduplicate as equivalent, remain a parallel local view, or be blocked/rejected.

This realizes the user's desired "absorb strengths" behavior without violating the Knowledge Atlas principle.

The frontier remains theory-only in this round. Runtime implementation requires its own frozen benchmark.

## Scoped evolution verdicts

`src/rakl/evolution.py` provides a support-only classifier:

```text
SCOPED_EVOLUTION_EVIDENCE
TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED
LOCAL_IMPROVEMENT_ONLY
META_OVERFIT
NO_IMPROVEMENT
BLOCKED
CANNOT_CHECK
```

It does not modify `ConstitutionGuard`, promotion, workflow routing, protected evaluators or the Constitution.

## Assurance reserve

A blind assurance packet has a preregistered optimizer-visible exposure budget. Once exhausted, positive results may still demonstrate transfer but cannot repeatedly certify independent generations. This prevents recursive optimization from converting the publication holdout into an implicit development set.

## Native residual learned from concurrent main

The newly landed evidence-lineage implementation reveals another axis:

```text
process-blind assurance != evidence-lineage-independent assurance
```

A future benchmark must detect shared datasets, source corpora, generated-case ancestry or derivation chains between development and assurance tasks. This is registered as `META_N094_ASSURANCE_LINEAGE_INDEPENDENCE` and is **not retrofitted** into Round 030 acceptance because it was discovered after the original self-evolution benchmark freeze.

## Stale-branch executed evidence

The stale self-evolution candidate `1edeab7519e92dd3a7ab499d09c5fdcacfbe2088` passed the exact-subject CI suite with `337 passed in 8.65s`. This is preserved as process evidence but cannot authorize promotion onto the newer method state.

## Top-tier prospective experiment

Run repeated generations under matched resources with separate:

```text
DEVELOPMENT
TRANSFER
FRESH/ROTATED ASSURANCE
```

and compare fixed RAKL, unconstrained self-editing, development-only evolution, governed RAKL evolution, and governed RAKL evolution plus external method assimilation.

Report every positive/null/refuted/meta-overfit/blocked generation and track capability-frontier expansion rather than only the final best score.

## Saturation

```text
state = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The evidence-lineage residual, prospective multi-generation experiments, real-component assimilation and independent novelty review remain open.
