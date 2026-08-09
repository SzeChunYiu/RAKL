---
name: rakl
description: Apply the RAKL evidence-governed scientific research method to hard research, modelling, engineering, mechanism-discovery, literature-assimilation, or Self-RAKL tasks in this repository or a user project.
---

# RAKL Claude Code adapter

This is a thin adapter. Do not duplicate the full method here.

1. Read `skills/rakl-core/SKILL.md`.
2. Read `skills/rakl-core/manifest.yaml`.
3. Load the two always-loaded core files declared by the manifest.
4. Detect only the workflow(s) required by the current task and load only those workflow fragments.
5. For a formal-definition question, read `docs/FORMAL_SYSTEM_SPECIFICATION.md` only as needed. Do not preload it for ordinary project operations.
6. For persistent projects, prefer `python -m rakl` project state/task packets over keeping the scientific archive in conversation context.
7. For Self-RAKL, follow `skills/rakl-core/workflows/self-rakl.md` and the frozen bootstrap benchmark. Do not count this same coding session as independent review.

## Context discipline

Keep the active context to:

```text
current object + QoI
active fiber/residual
relevant invariants/falsifiers
minimum evidence/negative-history packet
candidate method/formalism state
next discriminator
```

Historical ledgers, raw paper corpora and unrelated method fibers stay external until a targeted read is justified.

## Write discipline

Before implementation changes that are meant to improve a research method or scientific claim:

```text
freeze benchmark/evaluator
-> smallest scoped change
-> hostile/known-answer tests
-> exact candidate execution
-> receipt
-> fresh assurance when self-evolution is claimed
```

Do not convert proposal fluency, local tests, or a high model score into scientific authority.
