# Paper III fresh-task-lift gate — ceiling qualification attempt

**Terminal:** `CANNOT_CHECK__ORACLE_NOT_COMPUTABLE_NO_GENERATIVE_MODEL` · diagnostic only; promotes nothing, reverses no terminal, changes no frozen artifact. **Machine record:** [`CEILING_RECEIPT.json`](CEILING_RECEIPT.json) · **Script:** `compute_p3_lift_ceiling_v1.py` (seed `202608150001`, byte-identical across runs)

## Question

Paper III's four-arm fresh-task benefit obligation is `BLOCKED_ON_CAPABILITY_QUALIFICATION` pending an A100-class subject on a pinned
unquantized 7B. Its manuscript flags at `sections/07b_structural_learning_cautionary.tex:13` that the lift protocol's `0.05` gate "has no
recorded ceiling qualification" — **verified**: the sentence is at that line, and `DISCHARGE_PATHS.json:355-368` independently records
precondition T7/P7 `NOT_FOUND`. Attainable in principle?

## Verdict — the ceiling is not computable, not merely unrecorded

| | |
|---|---|
| ceiling upper / lower bound | **none — neither derivable pre-execution**; no CI, no interval to bracket |
| mechanic verdict | `CANNOT_CHECK`, fail-closed (`src/rakl/instrument_admissibility.py:20-21, 236-244`) |
| invariant across | MDE ∈ {0.01…0.30} × κ ∈ {1.0, 1.2, 2.0} — all 18 cells `CANNOT_CHECK` |
| explicitly not | `INSTRUMENT_INADMISSIBLE_CEILING_BELOW_GATE` (no upper bound ⇒ not shown unable to reach 0.05), not `ADMISSIBLE` (no lower bound ⇒ not shown able to), and not "checked and fine" |

**Missing inputs, and where each would have to come from:**

1. **Generative model of per-task, per-arm outcomes for the pinned subject.** The sibling lane had one in closed
   form (`P4_ADAPTIVE_PROTOCOL_FREEZE.json`: coordinates, rates, harm terms, integer budget 48) — precisely why its
   relaxation was solvable. Paper III's per-item outcome comes from Qwen2.5-7B-Instruct @ `a09a3545…` under a frozen
   evaluator, obtainable only from **executed pilot data on the staged A100** — the very measurement the gate is
   meant to license. It cannot exist beforehand.
2. **The frozen evaluator** — rubric, parser, success threshold, identity hash
   (`experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md:85`). Local, free, simply absent.
3. **The frozen task panel** with exact task IDs (`…:52`); 120 is a target, not a freeze (`…:46,54`). Also
   missing: any Paper-III-scoped protocol file — the nearest frozen document is the *Paper 5* preregistration,
   identified with Paper III's obligation via `DISCHARGE_PATHS.json:260` and `BLOCKED-residual-terminals.md:45`.

The two repo artifacts carrying four-arm-shaped outcome numbers were opened and **rejected as surrogate sources**:
`paper5_harness_selftest_v1/HARNESS_SELFTEST_RECEIPT_V1.md` (synthetic adapter, no model invoked, `NOT_A_PAPER5_RESULT`) and the
`NEGATIVE_NO_TRANSFER_SUCCESS_LIFT_UNDER_0_5B` receipt (sub-0.5B subject, 2 arms not 4, n=3/phase, `success_rate = 0.0` in every cell — a
degenerate floor; substitution is forbidden by the freeze).

**Structural reason (the deeper one):** the sibling's arms were *policies over a shared example budget*, so a monotone relaxation had
something to relax. Paper III's four arms — `MODEL_ONLY` / `RAKL_RESET` / `RAKL_SHAM_MEMORY` / `RAKL_LEARNING` (`…:10-30`) — are fixed
**conditions**, not policies. No allocation space exists, so the sibling construction has no analogue even if inputs 1–3 were supplied.

## Secondary, independent finding — `0.05` is not registered as a lift threshold

No material-effect threshold for any lift contrast was found. In the four-arm protocol `0.05` appears only as **alpha** (`…:54` two-sided α
beside a ~15pp planning effect; `…:144` Holm FWER). Paper III's registered `0.05` MDEs belong to the **objective** paired-Brier lane
(`paper3/power_design/POWER_SIMULATION_CONFIG.json :: registered_material_effects.primary_paired_brier_reduction_mde`) — a different,
already-executed instrument; the manuscript places lift thresholds in the future (`sections/07_evaluation_and_statistics.tex:137`).
Justifying searches: receipt field `registered_gate_provenance.searches_run_to_justify_the_absence_claim`. **Independent of the verdict** —
a threshold surfacing tomorrow would not change `CANNOT_CHECK`.

## Assumptions

Mirrored from the sibling (`paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json`): equal budget; oracle-policy (best attainable, not
candidate-attained); best achievable per-item outcome under the instrument's own dynamics; only an UPPER bound licenses `INADMISSIBLE`, only
a LOWER/EXACT bound licenses `ADMISSIBLE`; κ = 1.2. **Deviations:** (a) the Paper III declaration is *provisional and non-freezing* — no
lift MDE is registered, so nothing legitimate exists to freeze, and freezing one here would manufacture an obligation this lane never took
on; (b) no allocation space exists (above); (c) `equal_budget_verified` set **true** on the most favourable reading of `…:180`, so the
verdict is attributable to the oracle alone — the stricter reading also fails closed, independently. **Rejected as a non-bound:**
"saturation headroom = 1 − E[MODEL_ONLY]" would have given a convenient pro-staging `ADMISSIBLE`, but needs an unmeasured baseline and is an
achievability *claim*, not a constructive bound; not fed to the gate (`instrument_admissibility.py:15-17, 310`).

## Controls

| control | result |
|---|---|
| **Sibling reproduction** — recompute Paper IV's ceiling with its own runner, re-decide it | **PASS**; tier-3 upper bound recomputed `0.024570935346802103` vs published `0.024570935346802252` |
| verdict / licensing bound / declaration sha256 / κ-range | **bitwise identical** to published |
| numeric residual | max `1.5e-16` (1–3 ulp on 4 of 6 worlds; 2 bitwise exact) — last-bit float accumulation under a different CPython build/platform; bit-stable within this environment; runner and receipt entered the repo in one commit (`addd73eb`). **Chronology:** the criterion was bitwise, failed on that residual, and was then set to `1e-12` on the stated attribution with the decision-bearing fields required to stay bitwise — recorded in the receipt, not hidden |
| **No-alarm discrimination** (computable instrument, real headroom) | **PASS → `ADMISSIBLE`** — the run emits all three verdicts, so Paper III's `CANNOT_CHECK` is a measurement, not the mechanic's default |

## Decision consequence for staging the A100

**The qualification the manuscript asks for cannot gate this spend either way — staging is not de-risked, and the block is not "only
budget".** The honest repair is neither a bigger model nor a new instrument: freeze the missing artifacts that are local and free — the
**evaluator hash** (`…:85`) and a **material-effect threshold for the lift contrasts** — both already named as preconditions at
`ATTRIBUTION_PREREGISTRATION_V1.md:3`. Buying accelerator hours against an unfrozen evaluator and an unregistered effect threshold is a
strictly worse version of the risk 07b:13 warns about. A ceiling, if genuinely wanted first, needs a pilot-derived generative surrogate with
its own freeze — and such a surrogate could never license `ADMISSIBLE` on a policy score.
