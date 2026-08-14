# L6-CAPABILITY-QUALIFICATION-V1 — frozen definition of "qualified"

Binding artifact: `PROTOCOL.json` (thresholds and justifications) +
`EVALUATOR.py` sha256
`7288a8eb4ab2fe921562ef32e40e974b68f410e626a6615800efc53c48da7422`.
This file is the human-readable index; on any divergence the protocol and
evaluator govern.

## The question qualification answers

L6-METHOD-EVOLUTION's benefit obligation ("fresh-task lift versus a
static-method parent") is `BLOCKED_ON_CAPABILITY_QUALIFICATION` — explicitly
not a null. A lift experiment is only interpretable if, in advance, the
static-method parent demonstrably (a) can do the tasks at all, (b) is not at
ceiling, (c) is measured by an instrument whose gold cannot echo predictions,
(d) has a connected routing surface for experience to act through, and (e) has
relevant experience available to be leveraged. Qualification checks exactly
those floor conditions and nothing else.

## Coordinates (all must PASS for QUALIFIED)

| # | Coordinate | Frozen gate | On failure |
|---|------------|-------------|------------|
| QC1 | INSTRUMENT_VALIDITY | Role-semantics audit on instruction text only; gold independence receipts clean (no candidate import/call; forbidden inputs absent; gold committed before parent run); blind human audit, disagreement < 0.05 | `CANNOT_CHECK(INSTRUMENT_DEFECT)` — parent metrics are never interpreted |
| QC2 | PARENT_COMPLETION_WINDOW | p̂ ∈ [0.20, 0.80], all-N denominator; exact 95% CI containing an edge → `CANNOT_CHECK(QC2_EDGE_INDETERMINATE)` + registered +120-task extension | FAIL(low): one-stage attribution → interface repair (#447 Stage-2 pattern) or battery re-stratification V2. FAIL(high): battery hardening V2 |
| QC3 | NON_DEGENERATE_VARIANCE | ≥ 8/12 families strictly mixed AND structured-readout validity ≥ 0.90 | FAIL: per-family attribution → family rebalance V2, or interface repair if readout is the failing part |
| QC4 | PER_FAMILY_HEADROOM | ≥ 8/12 families with rate ∈ [0.10, 0.90] (family 12 expected out-of-window by design) | FAIL: family rebalance V2 targeting only out-of-window families |
| QC5 | ROUTING_SURFACE_REACHABILITY | Store VALID at frozen head `7113f24b…`, 139 shadow episodes, zero admission upgrades; deterministic non-empty query battery; all ≥ 14 content-sensitivity flip pairs flip | FAIL: operational defect — localize first non-conforming boundary (open → query → derive → act), versioned repair, re-run. Integrity/snapshot/posture violations are `CANNOT_CHECK`, not FAIL |
| QC6 | EXPERIENCE_RELEVANCE_COVERAGE | ≥ 50% of families with ≥ 1 relevant episode (exact registered signature-token mapping) AND ≥ 1 family with a verified-outcome (SUCCESS) episode | FAIL: typed outcome backfill of the seed corpus (migration V2 per `MIGRATION_RECEIPT.md` residual 3) and/or mint new native episodes via the proposal-only shadow flow; never fabricated outcomes |
| QC7 | FRESHNESS | Zero contaminated instances (artifact-hash, exact problem-signature, id disjointness; checked against the frozen store head) | FAIL: regenerate exactly the contaminated instances under a fresh registered seed block; contaminated ids preserved |
| QC8 | COST_TELEMETRY | Per-task cost receipts present for 100% of runs, ≥ 2 distinct values, not all zero | FAIL: telemetry repair (operational), re-run |

Notes:

- **Evaluation order**: QC1 and the structural receipts (subject freeze, store
  integrity/snapshot, battery structure) are checked before any parent metric
  is read; their violations are `CANNOT_CHECK`, fail-closed.
- **Falsifiability**: every gate has a planted selftest world that flips it
  (`EVALUATOR.py --selftest`), and thresholds are strictly interior — the
  direct countermeasure to the L6 defect ("registered thresholds sit exactly
  at the ceilings"; four of six gate conditions NON_FALSIFIABLE). A run-level
  gate-falsifiability audit (paper3_gate_falsifiability_audit_v1 battery
  pattern) is a registered execution obligation.
- **NOT_QUALIFIED is informative, never a dead end**: each failed coordinate
  names its floor condition, measured value, and registered remediation lever
  (frozen in `EVALUATOR.py` `REMEDIATION`); per the global-recovery doctrine
  each gets one attributed revival iteration, re-frozen as V2 with the V1
  receipt preserved verbatim.
- **CANNOT_CHECK ≠ NOT_QUALIFIED ≠ "checked and fine"**: distinct verdicts,
  distinct exit codes (3 vs 0).

## Gold-label independence (the exact L6 defect this avoids)

`ladder.json` L6 readiness evidence: *"gold label is the prediction (same pure
function, same argument)"*. Here gold is minted only by (a) the hidden-world
generator at generation time (families 1–11, Stage-4 panel pattern) or (b) the
separate independent oracle module `experiments/paper3/independent_action_oracle_v1.py`
(family 12) under the PR #634 independence contract: the oracle never imports
or calls candidate code, candidate never receives oracle output, forbidden gold
inputs are enumerated, gold is sha256-committed before any parent execution,
and source hashes land in the final receipt.

## Task battery decision

CONSTRUCT (no reusable fresh battery exists): 240 tasks = 11 Stage-4 panel
families + 1 routing-liveness family × 20, seeded parametric generator, no
network, no LLM labeling, hardened Stage-5 scoring discipline, 10% blind human
audit. Freshness is instance-level against the episode store (procedure in
`PROTOCOL.json` `freshness_check`); family-level overlap with the experience
corpus is deliberate and required for the eventual lift to be expressible.

## Worked example — NON-EVIDENTIAL

Illustration of a NOT_QUALIFIED readout (3 rows, invented numbers, no run
occurred; this table is not evidence and must never be cited as a result):

| Coordinate | Measured | Gate | Status |
|---|---|---|---|
| QC2 | p̂ = 0.46, CI [0.40, 0.53] | [0.20, 0.80] | PASS |
| QC6 | coverage 0.58; verified-outcome families 0 | ≥ 0.50; ≥ 1 | FAIL → outcome-backfill lever |
| QC7 | 0 contaminated | 0 | PASS |

Verdict: `NOT_QUALIFIED(["QC6_EXPERIENCE_RELEVANCE_COVERAGE"])` — the lift
experiment would be uninterpretable because the treatment arm's primary
mechanism (verified-lesson application) has no material to act on; the
remediation is corpus outcome backfill, not threshold movement.

## Non-claims

Qualification ≠ lift. Passing gates ≠ benefit. Shadow episodes stay shadow.
`ladder.json` untouched. A QUALIFIED outcome authorizes exactly one thing: the
freezing of L6-LIFT-V1 as a separate protocol.
