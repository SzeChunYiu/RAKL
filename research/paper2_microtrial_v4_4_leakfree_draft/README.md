# V4.4 leak-free prompt draft (NOT an execution packet)

Status: **DRAFT staging**. Executable successor after positive-control PASS: `research/paper2_microtrial_v4_4/`.

## Why this exists

Issue #283: live `RAKL_CONTEXT_PROMPT.txt` arms in `paper2_microtrial_v1`,
`v4_2`, and `v4_3_1` encode graded answers (`misaligned_source_ids={S4,S5}`,
`required_refuted_source_ids={S6}`) via treatment-only markers
(`CONTEXT_MISALIGNED_FOR_DIRECT_CONTRADICTION`, "retained as negative history",
and the S4/S5→target / S6→S2+S7 outcome edges). Historical runs using those
prompts are **NOT_INFORMATIVE** for RAKL-vs-DIRECT comparisons on the affected
fields. Their prompt bytes and sealed ingest receipts are hash-locked by
`TYPE_B_LEAK_DISPOSITION_283.json` in each generation directory — preserved as
negative history, not mutated and not silently re-scored.

## What this draft keeps / drops

Kept: per-source context and projection lines; non-outcome adjacency
(`CONDITIONAL` S1→S3, `INDEPENDENT_CORROBORATION` S3→S8).

Dropped: outcome-naming relation labels and edges that make the graded sets
recoverable from the treatment-only differential vocabulary.

Verified CLEAN by `rakl.degeneracy_probe.probe_arm_answer_leak` against the
ROUND044 gold (both graded fields). Live `v4_2` / `v4_3_1` remain DEGENERATE
under the same probe (locked by tests).

## Mandatory preconditions before any future execution

1. **Leakage probe**: this draft's arm pair must stay CLEAN under
   `probe_arm_answer_leak` / `scripts/sweep_degeneracy.py`.
2. **Positive control**: construct a condition where context must change the
   correct answer and show the instrument registers a non-zero difference. A
   null from a zero-sensitivity instrument is uninterpretable
   (session lead rule for #247).
3. Freeze a new batch contract / execution packet only after (1) and (2). Do not
   reuse V4.2 / V4.3.1 arm-comparison claims as RAKL capability evidence.

## Authority

This directory grants **no** model execution, harvest, or claim authority.
