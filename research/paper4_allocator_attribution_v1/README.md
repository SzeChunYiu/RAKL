# Paper IV allocator failure attribution v1

Decomposition of the preserved adaptive-v1 development negative
(`../orion_p1_p4_closure_v2/P4_ADAPTIVE_DEVELOPMENT_NEGATIVE.json`).

Nothing here promotes, revives or reverses any terminal. `grants_scientific_authority=false`
on every artifact. The parent negative and every existing freeze are byte-unchanged.

## Files

| File | Role |
|---|---|
| `ATTRIBUTION_DIAGNOSTIC_PROTOCOL.json` | Frozen before outcome access, with 4 numbered predictions and their falsifiers |
| `ATTRIBUTION_RECEIPT.json` | Executed result, terminals read from data |
| `ATTRIBUTION_WORLD_RESULTS.jsonl` | 2,304 per-world/rep/arm records incl. realized budget counts |
| `CEILING_BOUNDS.json` | Three-tier bound on what *any* equal-budget policy can achieve here |
| `PACKET_oracle_ceiling_calibration_gate_v1.json` | Proposal-only revival packet (schema `mechanic-research-packet-v1`) |

Runners: `../../experiments/orion_closure/run_p4_allocator_attribution.py` and
`../../experiments/orion_closure/run_p4_instrument_ceiling_bounds.py`. The first **imports**
`world_rates` / `apply_batch` / `mean_ci` / `select_batch` unchanged from the frozen parent runner,
so no world dynamics were modified and arms D/E consume the identical RNG streams.

## Gate state for #466

**SATISFIED.** `../paper4_phase1_results_v2/7b/run_manifest_v2.json` freezes
`state_reachability → MECHANISM_SIGNAL_PRESENT` (Qwen2.5-7B-Instruct rev `a09a3545…`,
protocol subject `fce2bb17…`), and `../paper4_phase2_v1/PROTOCOL_V3.json` names that exact
artifact as `authorizing_phase1`. The #461 gate condition is met literally.

Execution of the 7B five-arm Phase-2 is nonetheless **BLOCKED (session compute scope)**: the
frozen envelope requires an A100-class accelerator running the exact pinned unquantized 7B
loading semantics; the authorized host for this session has a 6 GB RTX A3000. This is *not*
`RESOURCE_BLOCKED` — that frozen terminal means the envelope itself cannot be met, and an A100
plus `run_phase2_v1_lunarc.sbatch` meets it. The terminal is deliberately left unconsumed.

## Reproduction of the parent negative

Re-ran the frozen runner against `P4_ADAPTIVE_PROTOCOL_FREEZE.json`
(sha256 `46cc8ca5…`, matching its freeze manifest) on the authorized host.

- Every reported statistic reproduces **to all printed digits**, e.g.
  `E−D balanced_mastery = −0.016608417018047765`. → `PASS_EXACT_NUMERIC`.
- `RUNNER_REPRODUCTION_PROVENANCE.json`'s `original_receipt_sha256`
  (`c5c84ba1…`) is **`CANNOT_CHECK`**: the raw `FINAL_DEVELOPMENT_RECEIPT.json` was never
  harvested, only a curated subset, so byte-level receipt equality cannot be checked from
  repository bytes. Numeric equality is verified; the byte claim is not.

## Result

Equal budget (48 examples) in all arms. `D` = static structural parent.

| arm | balanced_mastery | −D mean [95% CI] | L1 of budget from uniform-8 | realized counts (P,C,B,Rep,T,Ret) |
|---|---|---|---|---|
| `D_STATIC_STRUCTURAL` | 0.79624 | reference | 0.00 | 8, 8, 8, 8, 8, 8 |
| `E_VECTOR_ADAPTIVE` (v1) | 0.77963 | **−0.01661** [−0.01740, −0.01583] | 10.33 | **13**, 7, 5.98, 6.85, 7, 8.17 |
| `X1_GUARDRAIL_AS_CONSTRAINT` | 0.78543 | −0.01080 [−0.01149, −0.01013] | 1.31 | 8, 8, 7.84, 7.51, 8.49, 8.17 |
| `X2_DECONCENTRATE` | 0.77574 | −0.02050 [−0.02067, −0.02034] | 16.00 | 13, 6, 5.37, 5.63, 7, 11 |
| `X3_BOTH_LEVERS` | 0.77372 | −0.02252 [−0.02300, −0.02202] | 7.50 | 8, 5.72, 7.70, 6.83, 9.44, 10.31 |
| `ORACLE_GREEDY_CEILING` | 0.79772 | **+0.00148** [+0.00135, +0.00160] | 5.65 | 10.19, 8.43, 7.83, 7.78, 8.20, 5.57 |

Frozen predictions, read from data:

| | prediction | outcome |
|---|---|---|
| P1 | principle cap closes ≥60% of the gap (Δ ≥ 0.010) | **FALSIFIED** — Δ = +0.00580, 35% of the gap |
| P2 | deconcentration changes the gap by < 0.005 | **HELD numerically** (Δ = −0.00389) but the arm is confounded — see below; treat as uninformative |
| P3 | oracle ceiling < the frozen 0.05 hard gate | **HELD** — +0.00148, **33.8× below the gate** |
| P4 | E's allocation is world-invariant, PRINCIPLE = 13 | **HELD** — identical counts in 5 of 6 worlds |

Terminals: `ATTRIBUTION_MIXED` / **`INSTRUMENT_CANNOT_DISCRIMINATE`**.

P1 was my own pre-registered threshold and it failed. It is recorded as failed. No threshold
was moved after outcome access.

## Attribution

**Stage: allocation policy. Not single-lever — two sub-levers, both material, neither dominant.**

1. *Guard-rail budget capture.* v1 spends **13** examples on PRINCIPLE versus D's 8 — in every
   world — because `principle-until-0.90` and the per-round PRINCIPLE floor slot are budget-consuming
   **targets** rather than **constraints**, while `apply_batch` simultaneously erodes PRINCIPLE. The
   five extra examples go to the highest-mastery, highest-rate coordinate (rate 0.17) and are taken
   from coordinates at m≈0.55 (rate ≈0.09). Per-coordinate `E−D` mastery: PRINCIPLE **+0.0387**,
   every other coordinate negative (BOUNDARY −0.0515, REPRESENTATION −0.0251, COMPOSITION −0.0217,
   TRANSFER −0.0213, RETENTION −0.0188); sum = −0.0997 = exactly 6 × the balanced gap.
   Capping PRINCIPLE at D's 8 (`X1`) drives budget L1 from 10.33 to 1.31 and recovers 35% of the gap.
2. *Within-round temporal concentration.* `X1` reaches near-uniform budget yet still loses 0.0108,
   so the residual is the sequential `rate·(1−m)` saturation of committing 7 slots to one coordinate
   inside one round.

**The receipt's stated root cause is superseded as an interpretation.** It reads
"commits all non-repetition slots to one weakest coordinate … concentration-induced erosion".
The realized counts refute the budget-level reading: over 6 rounds v1's argmin walk visits each of
the 5 non-principle coordinates once and lands at ≈7 each — *near-uniform*. The receipt file itself
is immutable and unedited; only its interpretation is corrected.

**`X2` is uninformative and is not used as evidence.** It was designed to isolate concentration and
failed to: spreading the 7 slots via `(2,2,1,1,1)` over ascending-mastery order re-selects the argmin
every round, and RETENTION keeps re-entering that order as it decays — so `X2`'s budget deviation
*rose* from L1 10.33 to 16.00 (RETENTION 8.17→11, COMP/BOUN/REPR each stripped ~1–3). At the fitted
cross-arm slope of −0.001172 per unit L1, that ΔL1 = +5.67 alone predicts −0.00665, which is *larger*
than the observed `X2 − E = −0.00389`. The arm's deficit is therefore fully accounted for by budget
distortion, and it can speak to concentration in **neither** direction. An unconfounded concentration
lever — same budget vector, different within-round ordering — needs a fresh design.

The refutation of the receipt's concentration story rests solely on the realized-counts observation
above, which does not depend on `X2`. The evidence that within-round concentration costs *something*
rests solely on `X1` (near-uniform budget at L1 1.31, still −0.0108).

Transfer to production: `src/rakl/training_scheduler.py::choose_adaptive_training_batch` fills every
non-repetition slot from `target_ranked` — one coordinate — and `_target_coordinate` (lines 99–122)
selects `argmin` mastery **level**. Both v1 defects are present in the promoted mechanic, so the
diagnosis applies to it and not only to the simulator.

## The decisive finding — and a correction to it

**Self-correction, made before merge.** My first pass read the greedy oracle's `+0.00148` as *the*
ceiling and reported it as "34× below the gate". That inference was **invalid**: a greedy oracle is
a *policy*, so its score is only a **lower** bound on what the instrument can produce. Concluding
"no policy can pass" from a policy score is a category error. `CEILING_BOUNDS.json` replaces it with
three tiers, and the conclusion is now carried by a genuine **upper** bound:

| tier | bound on mean advantage over static | vs. frozen 0.05 gate |
|---|---|---|
| 1 — greedy oracle *policy* (lower bound) | +0.00148 | 33.8× below |
| 2 — best constructive allocation found (lower bound, local search) | **+0.00446** | 11.2× below |
| 3 — **rigorous upper bound** (harm-free relaxation, exact water-filling) | **+0.02457** | **2.03× below** |

Tier 3 is rigorous: every harm term in `apply_batch` is non-negative and subtracted, and the gain
step `m → m(1−r)+r` is monotone increasing in `m`, so pointwise dominance is preserved and the
harm-free trajectory upper-bounds every with-harm trajectory. Maximizing it over integer count
vectors is a concave separable allocation, exact by greedy water-filling.

So the honest statement is: **no equal-budget allocation policy, however optimal, can reach this
instrument's own registered 0.05 gate — with a factor-2 margin, not a factor-34 one.** The
qualitative conclusion survives on a stronger footing; the headline magnitude was wrong and is
retracted. The greedy oracle also *harms* safety (`hard_safety_min −D = −0.00966` against a frozen
ceiling of −0.01).

**Tightness caveat.** Tier 3 is loose by construction — the relaxation drops *every* harm term,
including the ones that make `RETENTION_SENSITIVE` hard. Tier 2 and tier 3 differ by ≈5.5×, so the
true optimum is only localized to a wide interval whose upper end sits 2.03× under the gate. The
verdict is supported; it is not airtight, and a tighter relaxation would strengthen it. Given that
this document also records a previous "proof" that was off by 3.6×, the margin is stated rather
than rounded away.

Bootstrap CIs on the primary contrast are ≈0.0016 wide — by conventional power analysis amply
powered — which is precisely why the defect was invisible. Three structural causes, all verifiable
in `run_p4_adaptive_development_stress.py`:

- `initial_mastery` is one protocol-level vector; `world_rates()` varies **rates only**; `irng`
  noise is ±0.01. Round-0 learner state is therefore effectively **world-independent**, so learner
  state carries almost no information the static arm is not already exploiting.
- Gains are concave *per coordinate* (`rate·(1−m)`) with no cross-coordinate synergy, while harms
  are **linear in example count and coordinate-independent**. The equal-budget optimum of a sum of
  concave separable terms is near-equal spread — i.e. arm `D` is already near-optimal by construction.
- 6 rounds × 1 target coordinate ≈ the 5 non-principle coordinates, so argmin-level cycling
  degenerates to round-robin and the adaptive target functional barely expresses itself at all.

Consequence: the parent negative is valid **only** as "this v1 policy in this instrument". It does
not support any conclusion about learner-conditioned allocation in either direction. This is the
same defect class as the Phase-1 v1 generator (`../paper4_phase1_results/ROOT_CAUSE.md`) — an
instrument that cannot produce the signal it was built to test — and the repository's precedent
there was to retract the instrument and rebuild it.

The conservative operational consequence of the parent negative is unaffected: STATIC_STRUCTURAL
correctly remains the active default, now for a stronger reason — the evidence that would be needed
to displace it has never been obtainable from this instrument.

## Reconciliation with the parallel P4 lane on main

While this diagnostic was running, main advanced from `60654878` to `321f3f72`, adding
`../paper4_parent_assimilation_v1/PROTOCOL.json` — a parallel lane off the *same* base sha that
took the policy-tuning route this diagnostic says is unavailable. Its recorded lineage:

| candidate | −static | −strongest scalar parent | terminal |
|---|---|---|---|
| `ADAPTIVE_V2_DIVERSIFIED_DEFICIT_WITH_HARD_RESERVES` | +0.004958 | −0.002002 | `DEVELOPMENT_SUCCESSOR_REQUIRED` |
| `ADAPTIVE_V3_SPARSE_RESERVE` | −0.00133 | −0.00829 | `DEVELOPMENT_ONLY_REJECTED` |

Its RSHEA decision is `STOP_SIMULATOR_POLICY_TUNING_AND_ASSIMILATE_STRONGEST_PARENT`.

**The two lanes agree, and quantitatively.** Adaptive-v2's `+0.004958` sits essentially *at* the
tier-2 constructive ceiling computed here (mean `+0.00446`, best world `+0.00529`). That lane had
already found a near-optimal allocation for this instrument class and still missed its material-effect
gate — which is exactly what tier 3 says must happen. This diagnostic supplies the **mechanism** that
the `STOP_SIMULATOR_POLICY_TUNING` decision reached empirically: further policy tuning is not merely
unproductive, it is **bounded above** by roughly 0.025 against a 0.05 gate.

Honest caveats. The v2/v3 numbers come from an instrument that includes at least one world
(`NEAR_UNIFORM_HIGH_MASTERY_CONTROL`) **not** among the frozen six, and only that lane's
`PROTOCOL.json` is on main — no runner or receipt. So the numeric alignment is **cross-instrument
and approximate**, and their exact instrument is **`CANNOT_CHECK`** from repository bytes. The
agreement is corroborative, not a verified identity.

## Revival proposal (proposal-only)

`PACKET_oracle_ceiling_calibration_gate_v1.json`. One lever, placed at the stage the diagnosis
identifies as blocking — **evaluation/instrument**, not allocation policy, because no policy lever
is testable in an inadmissible instrument.

Mechanic: before executing an equal-budget allocation comparison, compute the instrument's oracle
ceiling and require `ceiling ≥ κ · MDE` with κ frozen in advance; otherwise emit
`INSTRUMENT_INADMISSIBLE_CEILING_BELOW_GATE` and do not spend the comparison. Fail closed to
`CANNOT_CHECK` when the oracle is not computable.

Novelty residual: power analysis bounds *sampling noise* for an assumed effect; it is silent on
whether the instrument can generate that effect at all. Prior art (skyline/oracle baselines,
regret-vs-oracle, ceiling analysis, assay positive controls) computes the same object but reports it
descriptively rather than binding it to a frozen pre-execution admissibility decision.

The allocation-policy lever — replace `argmin` mastery **level** with `argmax` measured **marginal
gain**, and demote PRINCIPLE/RETENTION from targets to constraints — is queued **behind** the
packet. It is a genuine mechanism-level criticism (Paper IV's thesis is about a derivative; the
allocator uses a level, and the two anti-correlate whenever harder coordinates learn slower —
TRANSFER is both lowest-mastery at 0.50 and lowest-rate at 0.08 in the base world). It is not
testable until an admissible instrument exists, and it must not be tuned inside this one.

## Pre-execution risk flagged against PROTOCOL_V3 (advisory only, no modification)

`../paper4_phase2_v1/PROTOCOL_V3.json` registers `mde_primary: 0.05` on `E−D` with no
oracle-ceiling calibration. Whether the 7B instrument has ≥0.05 of state-conditioning headroom is
**`CANNOT_CHECK`** without executing it. If it does not, 12 A100-hours buy an `UNDERPOWERED`
terminal. Recommendation for the operator: run a cheap ceiling probe before the confirmatory run.
This is advice; `PROTOCOL_V3.json` is untouched.

## #462 routing

Face-value branch on current evidence: **`CONCEPTUAL_CROSS_PAPER_ONLY`**, neighbour
`REJECT_NEW_PAPER`. Not `ABSORB_INTO_PAPER_III`, whose precondition is that adaptive structural
allocation *works* — on the record it lost. Zero of #462's five `PAPER_VI_JUSTIFIED` conditions
hold: the exposure signal is 1 of 12 model×family cells, Phase 2 is unexecuted, #468 is unexecuted.
**Not promotion-grade.**

Strongest currently-defensible Paper IV claim, and it is negative/structural:

> On a corrected known-structure instrument, learner-conditioned structural saturation is
> **capability-gated** — a differential state-dependent residual appears in exactly 1 of 12
> model×family cells (7B, `state_reachability`), at the top of the ladder, with
> `scientific_claim_status: NO_EMPIRICAL_RESULT`. The vector allocator that signal motivates loses
> to a static equal-coverage parent under equal budget, attributable to guard-rail budget capture
> plus within-round concentration. And the model-free instrument used to test it is provably unable
> to adjudicate the estimand: a rigorous upper bound on *any* equal-budget policy's advantage over
> the static parent is ≈0.025, below the instrument's own registered 0.05 gate.

No Structural Learning Mechanics law is established. The defensible objects are the fail-closed
allocator mechanic (engineering scope only), the preserved negatives, and the instrument-admissibility
finding.
