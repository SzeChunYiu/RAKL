# Paper VI — smallest real scoped utility result (`SRSU-P6-GOVERNED-ACCEPTANCE`)

**Status:** executed. All five registered falsifiers survive.
**Authority:** proposal-only. Grants no scientific or promotion authority. No scalar ranking.
**Substrate:** laptop billy, `/home/billy/rakl-verify`, `.venv/bin/python` 3.11.14. No compute on the Mac.

## The object

The ORION governed-acceptance layer: a candidate may be promoted only when every frozen hard gate
is `PASS` with evidence bound to the exact candidate, and an unresolved gate blocks promotion.
The question is not "do the gates fire" but **what fail-closed acceptance costs and what it buys**.

## Read the claim-class split first

| Class | Coordinates | Why |
|---|---|---|
| `CONFORMANCE` — **not evidence** | arm A false-promotion rate; receipt completeness; A-vs-C | Determined by the gate definitions. A catching defects drawn from RAKL's own invariant list is a wiring check. It may not carry a headline. |
| `MEASURED` — the actual result | fail-closed tax; throughput; cost; **A-vs-D**; **D-vs-B at matched throughput** | Nothing in the gate definitions fixes these. |

`A_ORION_GOVERNED` false-promotion is `0.000` everywhere. That number is **conformance, not a finding.**

## What was actually measured

Evidence availability is anchored externally to the verification-gap survey (arXiv:2608.05179,
`PRIMARY_ABSTRACT`) via external-agent registry v1: 83% of surveyed systems release code, 38%
release seeds or traces. Per-gate availability is drawn at the rate of the gate's evidence class.
The **composition** of the 12-gate contract is not authored at one point — `n_repro` (how many
gates are reproducibility-class) is swept 0..12 and the whole curve is reported.

### Primary result, neutral scalar model, matched throughput

| `n_repro` | A: fail-closed tax | A: true-promotion | D: false-promotion | B: false-promotion |
|---|---|---|---|---|
| 0 | 0.897 | 0.051 | 0.089 | 0.294 |
| 4 | 0.994 | 0.003 | 0.166 | 0.345 |
| 12 | 1.000 | 0.000 | 0.321 | 0.397 |

Arm B is calibrated on a disjoint split so its acceptance rate matches arm D's
(0.5870 vs 0.5875 at `n_repro=0`), so these false-promotion rates are compared at equal throughput.

**Three findings, in order of strength:**

1. **Executing the gate contract cuts false promotion 3.31× at matched throughput** (0.089 vs 0.294,
   `n_repro=0`), *even when the gates fail open on unresolved evidence*. The benefit decays to 1.24×
   at `n_repro=12` as evidence availability falls.
2. **The fail-closed rule drives false promotion to zero at a throughput tax of 0.897 → 1.000.**
   Under the anchored rates, ORION's governed acceptance promotes almost nothing: true-promotion
   peaks at 0.051 and is 0.000 for `n_repro ≥ 7`. This is not a flattering number and is not
   presented as one.
3. **The binding parameter is evidence availability, not gate design.** With 12 gates, per-gate
   availability `p` must reach **0.9816** for a 20% tax and **0.9913** for a 10% tax. The anchored
   code-class rate of 0.83 gives a tax of 0.893; the repro-class rate of 0.38 gives 0.99999.

Finding 3 is the load-bearing one for the external-baseline programme: it converts
`MEC-CONTROLLED_RETRIEVAL_ENVIRONMENT` from a methodological preference into a **quantified
precondition**. A controlled-evidence environment is not a nicety for fair comparison; without one,
fail-closed governance has no operable regime at all.

Governance cost: 12 gate evaluations and ~6.0 µs per decision (arm A) versus 5 scalar evaluations
and ~0.3 µs (arm B) — roughly 20× wall time, which is negligible against any real evidence-acquisition cost.

## Falsifiers — all five survive

| | Registered condition | Observed | Verdict |
|---|---|---|---|
| F1 | fail-closed tax ≈ 0 ⇒ claim vacuous | 0.897–1.000 | survives |
| F2 | A and D identical false promotion ⇒ fail-closed buys nothing | 0.000 vs 0.089–0.321 | survives |
| F3 | B not worse than A on integrity | 0.294 vs 0.000 | survives |
| F4 | A's cost not above B's | ~20× wall time | survives |
| F5 | D not below B at matched throughput | 0.089 vs 0.294 | survives |

## Negative history retained

`RESULTS_V1.json` is the **v1 run with a defective control arm** and is preserved unmodified.
In v1, arm B used a running-max incumbent over an i.i.d. stream — a monotone ratchet whose measured
acceptance rate collapsed to **0.014**, making its rates incomparable to any other arm. That is a
strawman control, not a result about the source mechanic, and it is retained as such.

v1.1 repairs **only** arm B, to the steelman the v1 freeze had already required.
**Chronology disclosure:** v1 results were seen before v1.1 was frozen. Arms A, C and D are
byte-identical to v1 and retain their pre-result freeze; arm B in v1.1 is a post-result repaired
control. Any claim resting on arm B is chronologically weaker than one resting on A/D alone.
Finding 2 and finding 3 rest on A and D only.

## Scope boundary — what this is not

- Not evidence about **any named external system**. Arm B is `REIMPLEMENTATION_CONTROL_ARM` for
  `MEC-GREEDY_ACCEPT_ON_HELD_OUT_SCALAR`; it is our implementation of a mechanic, **not** the
  Karpathy `autoresearch` system, and no result here compares against it.
- Not an architecture-superiority claim of any kind.
- Not generalizable beyond this synthetic population. Held-out defect-family generalization is
  **`CANNOT_CHECK`** — see below.
- Arm E (LLM-judge fitness, `MEC-DARWINIAN_WORKFLOW_EVOLUTION`) is **`BLOCKED`**: no LLM budget.
  A simulated judge with an assumed error model would be a sensitivity model, not a measurement,
  and was deliberately not run.

## `CANNOT_CHECK`: held-out defect families

Every defect family here is drawn from RAKL's own invariant list, so all of them are `CONFORMANCE`.
Externally-anchored held-out families could not be constructed: the registry asserts *"the five
failure modes named in the open-ended-research case studies"*
(`research/external_research_agents/README.md`; `mechanics/mechanics.json` names one of them,
instruction drift) but **does not record the list as data** — verified by exhaustive grep over all
six registry files. Authoring the families myself would make their freshness fictional. Blocked on
`RES-EXT-001`.

## Reproduce

```bash
ssh billy-laptop
cd ~/rakl-verify && .venv/bin/python experiments/paper6/run_governed_acceptance_v1_1.py
```

Deterministic and seeded (seeds 11–15, 400 episodes per cell, 400 disjoint calibration episodes).

## Files

| Path | What |
|---|---|
| `PREREGISTRATION_V1.json` | v1 freeze, committed before any result existed |
| `PREREGISTRATION_V1_1.json` | successor freeze; arm-B repair only, with chronology disclosure |
| `RESULTS_V1.json` | retained v1 run with the defective control arm |
| `RESULTS_V1_1.json` | primary result + leakage-inflated sensitivity variant |
| `../../experiments/paper6/run_governed_acceptance.py` | v1 runner |
| `../../experiments/paper6/run_governed_acceptance_v1_1.py` | v1.1 runner |

## Dependency

The evidence-availability anchor is read from the external-agent registry, which is **not on
`main`** — it is on branch `research/issue-588-external-agent-registry` (PR #591),
`basis_fingerprint` `a0565504e70eacf6e0b44bb4a7ff2c0d5eacfb88bc533a75e121c7b702c4a946`. The rates
are copied into `PREREGISTRATION_V1.json` rather than imported, so nothing here imports code or
data that `main` does not have.
