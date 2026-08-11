# Ablation ladder and intervention contracts

Issue #156 · 2026-08-11 · Detail file for
[`PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.md`](../PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.md)

**Nothing below has been run.** This freezes arm definitions and the
interventions between them so that a later execution cannot quietly redefine
what an arm was.

## Naming rule

An arm may approximate a parent's *function*. It is never that system. Arm names
carry no external system name, and every arm that approximates a parent states
what the real system does that the arm does not. This is enforced by
`rakl.closest_parent_matrix` (rules `arm_not_named_after_system` and
`arm_states_the_gap`).

## Ladder

| Arm | Adds | Approximated parent function | Explicitly **not** |
|---|---|---|---|
| `A0_MODEL_ONLY` | strong prompt, no persistent state | none | — |
| `A1_STATEFUL_MEMORY` | persistent store + retrieval | generic persistent agent memory | any named system: flat store, no schema governance, no two-tier split, no staged write, no provenance |
| `A2_EXPERIENCE_SUBSTRATE` | + TaskEpisodes, versioned Lessons, experience routing | the AutoSci-family experience/evolution function | not AutoSci — no five-stage lifecycle harness, no DAG multi-agent operators |
| `A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED` | + staged proposal/commit, validated writes, provenance, source/use permission | the MemTX/PPMF transactional-governance and provenance-authority function | not MemTX and not PPMF — see below |
| `A4_SCIENTIFIC_AUTHORITY_TYPING` | + G/R/M/I/D authority coordinates, non-escalating transitions | **none located** | — |
| `A5_SCIENTIFIC_HISTORY_AND_CONTEXT` | + context alignment, contradiction preservation, negative history | partially the MemTX conflict/rollback function, at different granularity | not MemTX — alignment before adjudication has no counterpart; MemTX's conflict slot is entity+attribute |
| `A6_SATURATION_AND_OPEN_WORLD` | + registered discovery routes, bounded freshness-expiring saturation | unresolved — see the `CANNOT_CHECK` rows | — |
| `A7_FULL_RAKL` | + protected method evolution gated on fresh assurance | the AutoSci SciEvolve function | not AutoSci — whether SciEvolve gates on a post-hoc check is unread, so the contrast is not yet established |

### What A3 is not

A3 reproduces the *function*, not the guarantees. MemTX additionally provides
five isolation levels, an eight-state lifecycle, type-dispatched cascade repair
verified over 5.5M states, and an action gate whose risk tier is trusted harness
configuration rather than agent output. PPMF additionally binds authority to
specific tool-call arguments at execution time using platform-maintained
metadata the writer cannot touch.

A3 is weaker than both. Any Paper-II sentence implying A3 stands in for either
system is false.

## Intervention contracts

One variable per step. "Turn off half the framework" ablations are excluded
because they move many causal variables at once and attribute nothing.

### A2 → A3 — staged commit, provenance, permission

| | |
|---|---|
| Code path changed | writes route through the staged proposal/commit path in `src/rakl/execution.py` and `src/rakl/hard_gates.py` instead of writing directly to the substrate |
| Information still available | identical retrieval surface; the same records are readable |
| Update permissions changed | a write becomes a proposal requiring validation before other readers see it; provenance and source permission recorded and enforced |
| State fields retained | all A2 fields, plus lineage edges and a source/permission block |
| Evaluator sees | unchanged — only committed state and the response contract |
| Expected mechanism | unvalidated or laundered writes stop reaching downstream reasoning |
| **Falsifier** | no reduction in unsupported downstream use when staging is enabled, indicating the losses were never write-path losses |

### A3 → A4 — typed authority coordinates

| | |
|---|---|
| Code path changed | the single authority scalar is replaced by the G/R/M/I/D vector in `src/rakl/authority_ledger.py`; the commit check consults per-axis licensing |
| Information still available | identical — the same evidence and provenance, re-typed |
| Update permissions changed | an update may raise some axes and not others; a source-trusted record no longer licenses every axis |
| State fields retained | all A3 fields, plus per-axis authority |
| Evaluator sees | unchanged |
| Expected mechanism | prediction→mechanism and mechanism→identification escalations refused while the same evidence still licenses its own axis |
| **Falsifier** | A4 refuses no more escalations than A3 — or refuses them only by refusing more overall, i.e. valid-upgrade recall falls in step with ALR, which would make the gain conservatism rather than typing |

That second clause is the one that matters. A4 can look good purely by being
more reluctant, so the paired metric is mandatory: an ALR improvement is only
attributable to typing if valid-upgrade recall holds.

### A4 → A5 — alignment, contradiction, negative history

| | |
|---|---|
| Code path changed | context alignment via `src/rakl/context_compiler.py` becomes a precondition of contradiction adjudication; refuted and null results persist in `src/rakl/failure_lattice.py` |
| Information still available | strictly more — negative history becomes readable |
| Update permissions changed | a contradiction claim requires an alignment; a later positive result may not delete a prior negative one |
| State fields retained | all A4 fields, plus alignment records and negative history |
| Evaluator sees | unchanged |
| Expected mechanism | premature refutation across mismatched regimes is replaced by an alignment request; negative results survive |
| **Falsifier** | alignment preconditions produce no change in premature-refutation rate, or block genuine refutations at the same rate they block premature ones |

### Contracts not yet written

`A0→A1`, `A1→A2`, `A5→A6` and `A6→A7` are deliberately absent. A5→A6 and A6→A7
depend on `CANNOT_CHECK` matrix rows — writing an intervention contract against
a parent function nobody has read would fix the wrong variable. Read AutoSci's
SciFlow and SciEvolve sections first.

## Cheap conformance (landed; not empirical)

Deterministic A3 vs A4 conformance fixtures live in
`src/rakl/ablation_a3_a4_conformance.py` with receipt
`research/paper2_closest_parent/A3_A4_CONFORMANCE_RECEIPT.json`.

They prove the intended mechanism difference on hostile prediction→mechanism and
mechanism→identification escalations, plus a legal upgrade control and a shared
provenance reject. **No model ablation has been run.** Arms are still not named
after external systems.

## Matched empirical packet (frozen; model empirics unrun)

Evaluation contract for A3 vs A4:

* packet: `research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json`
* runner: `src/rakl/ablation_a3_a4_matched_empirical.py`
* status (default): `EMPIRICS_UNRUN` — inventing ALR/recall/cost is forbidden
* evaluator binding: ALR V2 freeze receipt (`FREEZE_RECEIPT_V2.json`)
* LUNARC CPU cell: `experiments/paper2/lunarc/submit_a3_a4_matched_empirical_156.sh`
  validates the freeze and re-emits `EMPIRICS_UNRUN`; it does **not** mint A4>A3

## Before any arm is run

1. Resolve the six `CANNOT_CHECK` rows, or run without them and report them as
   unadjudicated. Do not let an unread row become a novelty sentence.
2. Adopt cascade repair. RAKL is behind MemTX here; running an ablation that
   ignores it measures the wrong thing.
3. Freeze the evaluator before arm results are visible. The authority-leakage
   panel is the natural evaluator; it must pass its own degeneracy audit first
   (issue #154).
4. Report ALR and valid-upgrade recall together for every arm. Any arm can win
   on ALR alone by refusing everything.
