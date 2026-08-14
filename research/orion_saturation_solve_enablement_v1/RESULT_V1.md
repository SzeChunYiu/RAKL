# Result v1 — MECH-BOUNDED-SATURATION, solve-enablement ablation

**Verdict: NULL. The benefit column does not gain an entry from this run.**

Frozen protocol: `PROTOCOL.json`. Receipts: `receipts/results_v1.json`, `receipts/gate_audit.json`.

## Feasibility verdict on the external anchor (reported first)

AutoResearchBench (arXiv:2604.25256) was verified to primary depth and upgraded from
`SEARCH_SNIPPET`. Title, authors, submission date (2026-04-28) and the 9.39% / 9.31% ceiling
were confirmed against the arXiv record; the dataset was downloaded, decrypted and
characterised (1000 records = 600 deep + 400 wide; wide gold sets mean 9.24, range 2–34,
3695 papers total).

**Execution is nevertheless `BLOCKED`**, for two independent reasons:

1. The DeepXiv retrieval endpoint is unpublished — `PAPER_SEARCH_API_URL` is empty in
   `example.env` and defaults to `""` in `tool_deepxivsearch.py`. The paper's standard
   retrieval environment cannot be reproduced.
2. No LLM is available on the sanctioned compute host (no ollama, no vllm, no llama.cpp,
   6 GiB GPU, no OpenAI-compatible endpoint), so no LLM-in-the-loop arm can run at all.

One discrepancy is preserved rather than smoothed: the released bundle contains **3695**
wide-research gold papers against **3692** reported in the paper. Recorded `FLAGGED`.

Per the dataset card, no decrypted question or answer text appears in this repository.

The substituted anchor is Lean-adjudicated theorem proving over held-out Mathlib theorems.
**This is Mathlib-level lemma proving, not frontier mathematics.** The operator's stated
target was frontier mathematics; that target is not met and is not claimed. miniF2F was
assessed and recorded `CANNOT_CHECK` at the installed toolchain (its main branch pins
`leanprover/lean4:v4.24.0` against an installed `v4.14.0`).

## Gate falsifiability

`audit_gate` on the scoring path, control asserted first:

| | |
|---|---|
| `baseline_pass` | **true** (the gate passes on real evidence, so the probe is not vacuous) |
| verdict | **FALSIFIABLE** |
| SENSITIVE probes | `corrupt_premises`, `drop_premises`, `false_goal` (2/2 flips each) |
| INSENSITIVE | `shuffle_premises` — expected; `simp` is order-tolerant here, so this is a control on the probe, not a defect |

A FALSIFIABLE verdict means only that the gate could have failed. It does not make any PASS correct.

## What was frozen before outcome access

Population rule, arms, budget accounting, premise budget, evaluator identity, decision rule,
falsifier, and `k = 20`. `k` derives from Arm A's round counts, which depend only on
retrieval and never on solve outcomes.

Two defects were caught **before** any outcome was accessed, and both are preserved:

- **Refuted solve interface.** `simp only [proof-term constants]` passed the gold-solvability
  control on 4 of 1406 candidates. A theorem's proof-term constants are not a simp set that
  reproduces its proof. Replaced by `simp [·]` with a two-sided population gate: `simp` alone
  must fail (a real gap exists) and `simp [gold]` must succeed (the gap is closeable).
- **Degenerate design.** The first round schedule gave each route context exactly one
  non-independent round, so the tracker's same-context flat requirement was structurally
  unreachable, saturation never fired, and both arms collapsed onto an identical 14-round
  schedule (`rounds_A_distribution = {14: 112}`). Repaired with three deepening sweeps per
  context. No outcome was visible when this change was made.

A third defect was caught by inspection: the task's own theorem sits in the retrieval corpus
and every route ranks it first, so `simp [self]` would have closed every task in both arms and
manufactured a 100% tie. The self-retrieval guard excludes it and its near-name variants,
symmetrically across arms.

## Result

n = 112 paired tasks. Floor `simp` = 0% and ceiling `simp [gold]` = 100%, both by construction.

| | Arm A (saturating) | Arm B (uniform, k=20) |
|---|---|---|
| solve rate | **0.357** (40/112) | **0.313** (35/112) |
| total retrieval rounds | 2256 | 2240 |
| mean gold-premise coverage | 0.342 | 0.349 |

Discordant pairs: A-only **8**, B-only **3**. **Exact McNemar two-sided p = 0.227.**

The pre-declared rule requires `p <= 0.05` for a demonstrated benefit. It is not met.
The direction favours saturation (+4.5 pp) but is not distinguishable from noise at this n.

The 0.7% residual in total rounds favours Arm A, so it cannot explain a null — but it would
have to be acknowledged had the result gone the other way.

## Single-stage attribution

The arms genuinely differ: selections differ on **99 of 112** tasks, mean Jaccard 0.68. The
design is not degenerate and the mechanism does move what reaches the tactic. The direction is
consistent in both subgroups (A ≥ B whether A stopped earlier or later than B).

The binding constraint is that only **11 tasks are discordant at all**. The failure is
attributed to the **population stage**: n = 112 cannot resolve a ~4–5 pp effect. The funnel
shows where it was lost — 2046 raw → 1581 → 1406 well-posed → 934 with a real gap → **112**
gap-closeable, a 12% yield on the ceiling filter.

The matching lever is therefore more tasks, not a different mechanism, and a revival run on a
widened module basis is under way (`DESIGN-ITERATION-2`). The decision rule, arms, routes and
premise budget are unchanged; only the population grows.

## Mediating coordinate

Gold-premise coverage is **essentially equal** across arms (0.342 vs 0.349, marginally lower
for A). Whatever small solve-rate difference exists is therefore **not** attributable to
coverage. This matters: coverage is the construct bounded saturation is defined in terms of,
so a coverage-driven win would have been the weakest possible evidence. Its flatness here is
consistent with the null and is reported for that reason.

## What must not be promoted from this run

- No benefit entry. `MECH-BOUNDED-SATURATION` remains without a demonstrated benefit.
- The +4.5 pp direction is **not** a positive result and must not be quoted as a trend.
- The FALSIFIABLE gate verdict is not evidence that any PASS is correct.
- Nothing here speaks to frontier mathematics.
- This is same-context analysis, not independent review.
