# Programme question audit v1 — Papers I, II, V, VI + the metric open problem

Date: 2026-08-14, base commit `08169241`. Same-context analysis throughout;
not independent review; grants no scientific or promotion authority.

Object: the QUESTIONS of the four papers, not their answers — "are we asking
the best questions?" Scored per candidate against (a) receipts on main,
(b) sign-robustness (frontier/tradeoff questions over victory questions, per
the Paper 3 audit precedent), (c) field need (in-repo-verified anchors only;
CANNOT_CHECK elsewhere), (d) consistency with the no-scalarization theorem and
`research/mechanism_benefit_ledger/ledger.json`. Question tables are
non-compensatory — no scalar ranking of candidates anywhere.

## Table

| Paper | Current question | Recommended question | Executable delta | Delta owner |
|---|---|---|---|---|
| I | What discipline must an evidence-governed agent obey? (soundness; answered, 87 mechanized theorems) | Where does the reasoning live, and which compiled obligations are load-bearing? (reasoning-location frame + hypothesis-necessity audit; operator addendum weighed in) | Per-hypothesis drop-probe + countermodel table over `formal/RaklFormal.lean` (CPU, Lean 4.14, feasible) | paper1 lanes |
| II | When may experience transfer? (spec + executed ARN negative) | What reducer capability makes structural transfer pay? (capability staircase = frontier, not victory) | Frozen staircase on the frozen ARN pairs; R1 rung CPU-feasible; learned rungs resource-gated | paper2 lanes |
| V | Can assurance make LLM math research auditable? (+ prospective performance) | What does kernel-verification buy per unit cost in the solving loop? (overhead / exposure / localization frontier) | Verified-vs-unverified derivation sweep on the real Lean hypergraph (CPU, minutes; endpoint classification frozen) | paper56-frontier |
| VI | Is Orion a working engine? (rests on benefit column) | What does each layer contribute, and at what cost? (non-compensatory per-layer table; amortization thesis tested layer by layer) | Frontier continuation: L3-AUTHORITY arm (scalar-ranked vs partial-order acceptance — the no-scalarization theorem's empirical companion) | benefit-saturation lane |

## Files

- `QUESTION_AUDIT_PAPER_I.json` … `QUESTION_AUDIT_PAPER_VI.json` — one table each
  (4–6 candidates, per-criterion cells, recommended question, delta,
  must-not-claim list, files used).
- `REPRESENTATION_TOURNAMENT_PROTOCOL_V1.json` — bounded representation
  tournaments (operator addendum): Contest 1 (OR-route vs AND-hypergraph on the
  Lean substrate, frozen, runnable now) and Contest 2 (exact signature vs
  graded metric, design-only, reducer-blocked); registered non-candidates
  (categorification, sheaf machinery with a flagged re-entry condition,
  embedding-only similarity).
- `metric_open_problem/PROTOCOL_METRIC_V1.json` — the open-problem study:
  requirements R1–R6 for a principled graded metric; Stage A instrument
  validation (frozen candidates, worlds, thresholds, predictions, MEASURED vs
  CONFORMANCE endpoint classification); Stage B external validation on ARN —
  frozen and BLOCKED (verdict: ARN works as the first external validation set
  only jointly with an admissible capable reducer).
- `metric_open_problem/EVALUATOR_STAGE_A.py` — deterministic stdlib evaluator
  (sha256 in the protocol), self-testing, exit codes 0/2/3.
- `metric_open_problem/results_stage_a/` — Stage A execution receipts (separate
  commit after the freeze; laptop billy, fresh clone). Typed outcome:
  `NEGATIVE_AT_FROZEN_GATE` — no candidate passes the frozen Spearman ≥ 0.80
  gate (exact GED lands 0.7975; no threshold rescue). Strongest measured
  positive: WL-3 separates 20/20 signature-equal non-isomorphic decoys that
  the incumbent exact signature cannot. Instrument-attributed residual and a
  versioned Stage A v2 revival are registered in the run receipt.
- `../../docs/REASONING_LOCATION.md` — where the reasoning lives (three sites,
  amortization-thesis falsifiability, honestly marked nearest work).

## Cross-cutting findings

1. **The empty benefit column is partially stale**: `benefit_L0/L1/L2` landed
   typed PROMOTE (mechanical arms, synthetic corpora, sign-offs pending). The
   capstone question should report that ladder, not wait for a hero result.
2. **One shared blocker, three unlocks**: an admissible capable reducer
   (through `admit_reducer` + contamination declaration) simultaneously unlocks
   the Paper II staircase, metric Stage B, and representation Contest 2. It is
   the programme's highest-leverage single capability.
3. **Endpoint classification is now a discipline**: every protocol here
   declares MEASURED vs CONFORMANCE cells before execution
   (SRSU-P6-CLASSIFICATION-CORRECTION-V1 precedent), so no gate can quietly be
   satisfied by construction again.
