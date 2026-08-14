# External Research-Agent Registry — START HERE

**Issue:** [#588](https://github.com/SzeChunYiu/RAKL/issues/588) Phase 0 + Phase 1
**Registry version:** v1, frozen 2026-08-14
**Status:** `OPEN` — the landscape pass is **not** saturated. Do not cite this as a complete landscape.
**Authority:** proposal-only. Grants no scientific, method or promotion authority. No `ORION_SCORE` is derivable.

## What this is

A versioned record of external autonomous-research systems and their evaluation suites, treated
two ways at once, as #588 requires: as **baselines** that say whether ORION is competitive, and as
**knowledge projections** — evidence about how a research machine can be organized.

## What v1 actually establishes

| | |
|---|---|
| Systems registered | 9 |
| Benchmark suites registered | 8 |
| Registry entries at primary depth | 2 of 17 (3 sources fetched; 1 is evidence-only, not a registry row) |
| Rounds run / flat rounds | 3 / **0** |
| Saturation status | `OPEN` |
| Supports a completeness claim | **No** |

Three route-family rounds each produced substantive growth, so no flat round exists and bounded
saturation is not established. That is the honest v1 result, not a placeholder: **the landscape was
still producing new instruments on every route when the pass stopped.**

Most entries rest on search snippets rather than primary text, so most architecture fields read
`CANNOT_CHECK`. This is deliberate — issue #588 forbids equating marketing claims with measured
capability, and a guessed architecture field is worse than an absent one.

## Why this sits upstream of the RSHEA flow

RAKL problem-work runs through the RSHEA pipeline. This pass deliberately does not, because it is
**evidence acquisition**, not a candidate decision: there is no telemetry to turn into receipts, no
epoch to evaluate, and no candidate to gate. RSHEA engages at **Phase 7**, when a `MechanicCandidate`
from `mechanics/mechanics.json` becomes an actual ORION challenger — at which point it takes the
normal route through receipts → epoch + hard gates → `shadow_decide` → governed proposal.

Nothing in this directory may enter that flow as anything but an input.

## Deliverable status against issue #588

| # | Deliverable | State |
|---|---|---|
| 1 | Bounded 2026 landscape saturation record | **First draft** — recorded, status `OPEN`, not saturated |
| 2 | Versioned registry + schema | **First draft** — schema-validated, most fields `CANNOT_CHECK` |
| 3 | Mechanic records per competitor | **First draft** — 9 compiled, none with independent evidence |
| 4 | Exact baseline/version freeze | **Open** — every `commit` and almost every `evaluated_version` is `CANNOT_CHECK` |

Deliverable 4 is explicitly **not** met. What exists is a frozen record *that the versions are
unknown*, which is the opposite of a version freeze and cannot support a reproducibility claim.

## Files

| Path | What it holds |
|---|---|
| `registry.json` | The frozen v1 registry — systems, benchmarks, evidence grades, source anchors |
| `mechanics/mechanics.json` | 9 competitor mechanics compiled into RAKL vocabulary, each with a transfer obligation |
| `saturation/rounds.json` | The three route-family rounds, growth vectors, and 5 open residuals |
| `TAXONOMY.md` | Phase 0 comparison-class freeze (A–D) and the rules for using it |
| `ANCHOR_VERIFICATION.md` | Every #588 anchor checked against primary sources, including two corrections |
| `../../schemas/external-research-agent-registry-v1.schema.json` | Registry schema |
| `../../src/rakl/external_agent_registry.py` | Loader, derived-saturation audit, integrity checks |

## Derive the status — never hand-assert it

```bash
python -m rakl.external_agent_registry
```

`saturation_status` in `registry.json` is **checked against** the status derived from the recorded
rounds. Editing the registry to claim `BOUNDED_SATURATED` raises `RegistryError` rather than being
believed. Two independent guards enforce this:

1. growth must be flat for the required consecutive rounds, **and**
2. the operator-order perturbation audit must actually have been performed.

Guard 2 exists because guard 1 alone can be satisfied by simply running lazy rounds.

## The three rules that constrain every use of this registry

1. **No scalar ranking.** `permits_scalar_ranking` is pinned `false`. Report Pareto frontiers across
   quality/cost/robustness/auditability, never one weighted number.
2. **Architecture-causal claims need a matched contract.** Only systems marked
   `ARCHITECTURE_CAUSAL_ELIGIBLE` may enter a Phase 4 causal arm. Everything else — every proprietary
   system — is `SYSTEM_LEVEL_ONLY`, and "ORION architecture > X architecture" is never licensed for it.
3. **Same-substrate is not independent.** ResearchClawBench's strongest reported agent is Claude Code,
   which is the harness ORION itself runs on. Any ORION result there is a same-substrate comparison.

## What v1 found that #588 did not list

The issue's anchor list was incomplete, which is the pass's main yield:

- **ResearchClawBench** — end-to-end re-discovery with the **target paper hidden at evaluation**; the
  closest external instrument to RAKL's Tier 3 fresh-blind requirement.
- **Holistic Agent Leaderboard (HAL)** — a cost-controlled shared-scaffold harness. This is the
  methodological answer to Phase 4's matched-arm problem, which the issue specified but left unsourced.
- **AARRI-Bench** — scores nuanced scientific judgement rather than task completion; the natural probe
  for ORION's calibrated-abstention and `CANNOT_CHECK`-honesty QoIs.
- **The verification-gap survey** — 83% of surveyed systems release code, but only 38% release seeds or
  traces and 38% report any novelty verification; **no L4-autonomy system has an externally validated
  in-loop oracle.** This is the strongest available external argument for RAKL's assurance separation.
- **Open-ended-research case studies** — frontier agents given six days and thousands of dollars of
  compute on two unpublished NeurIPS 2026 papers completed all the engineering but made no substantial
  research progress; both were rejected by the original authors. Five named failure modes.

## Next actions, in order

1. Close `RES-EXT-003` — run the operator-order perturbation audit, without which no round can count.
2. Continue rounds until two consecutive flat rounds (`RES-EXT-002`).
3. Upgrade evidence grades by reading primary full text (`RES-EXT-001`); architecture fields may be
   filled **only** from primaries.
4. Resolve the flagged chronology anchors (`RES-EXT-004`).
5. Adopt `MEC-CONTROLLED_RETRIEVAL_ENVIRONMENT` before claiming any Tier 1 literature comparison — it
   is what makes a literature-route arm causal rather than confounded by corpus access.

`MEC-DOMAIN_GROUNDED_REFLECTION` is the strongest positive-transfer candidate for Phase 7: a cheap
domain-law checker is evidence-bearing in a way an LLM judge is not. `MEC-DARWINIAN_WORKFLOW_EVOLUTION`
is the most informative comparator, because it is Self-RAKL's mechanic evolution with an LLM-judge
fitness where RAKL requires an evidence gate — the faithful-versus-repaired challenger contrast is the
actual experiment.
