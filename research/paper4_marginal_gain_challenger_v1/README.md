# Paper IV marginal-gain challenger v1 (F_MARGINAL_GAIN_V4)

The queued allocation-policy lever from the attribution lane, executed **through** the
instrument-admissibility gate: argmin mastery *level* → argmax believed marginal *gain*,
guard rails demoted from budget-consuming targets to constraints, per-slot water-filling.

Nothing here grants scientific authority, activates training-policy authority, touches
the 7B Phase-2 evaluator, or reverses the preserved adaptive-v1 negative.

## Files

| File | Role |
|---|---|
| `PROTOCOL.json` | Frozen pre-outcome: instrument v2, arms, seeds, hard gates, predictions P1–P6, terminal branches. Includes the pre-declared secondary-gate ceiling rule and its binding record |
| `INSTRUMENT_V2_CEILING.json` | Licensing receipt: ADMISSIBLE (constructive +0.0800 ≥ κ·MDE = 0.06; upper bound +0.0974; tier spread 1.22×) |
| `INSTRUMENT_DESIGN_LOG.jsonl` | One entry — the first configuration licensed; no design iteration occurred |
| `DEVELOPMENT_RECEIPT.json` | Develop seed 202608141201 (challenger frozen before access) |
| `ASSURANCE_RECEIPT.json` | Assurance seed 202608141301, consumed once. Terminal read from data |

Runner: `../../experiments/orion_closure/run_p4_marginal_gain_challenger.py`
(world dynamics `apply_batch` and arms A–E imported byte-identical from the frozen
parent runner). Production-mechanic mirror: `src/rakl/training_scheduler_challenger.py`
(+ tests); `src/rakl/training_scheduler.py` is byte-untouched.

## Instrument v2 — why and what

The reference instrument is formally INADMISSIBLE
(`../paper4_instrument_admissibility_v1/REFERENCE_INSTRUMENT_ADMISSIBILITY.json`).
v2 repairs exactly the diagnosed blocking cause: round-0 learner state becomes
world-dependent (a world-specific deficient coordinate pair at 0.10, others at 0.94),
so state information is decision-relevant by construction. Dynamics, budget (48),
rounds and batch size are unchanged from the parent. PRINCIPLE and RETENTION each
appear among the deficient pairs so neither the v1 guard rails nor their demotion is
uniformly favoured.

## The admissibility mechanic did fresh pre-outcome work here

The pre-declared secondary-gate rule fired: the constructive ceiling over the expected
`C_SCALAR_LOSS_AWARE` rollout is only **+0.0046** (per-world 0.0036–0.0060), below
κ·0.02 = 0.024. The v1-style F−C ≥ 0.02 material-margin gate would have been a second
unreachable gate; it was bound **sign-only** (CI excluding zero) before any arm outcome,
and the material-margin question vs C is recorded as unresolvable by this instrument.

## Assurance result (seed 202608141301, run once)

| gate | frozen requirement | observed | verdict |
|---|---|---|---|
| P2 | F−D ≥ 0.05, CI>0 | **+0.0760** [0.0755, 0.0764] | **GREEN** |
| P3 | F−C > 0 sign-only, CI>0 | +0.000249 [0.00012, 0.00038] | GREEN (tiny; C-ceiling is 0.0046) |
| P3b | F−strongest parent (=C) > 0, CI>0 | +0.000249 | GREEN |
| P4 | safety harm vs D ≥ −0.01 | **+0.157** (F is the safest arm) | GREEN |
| P5 | all worlds F−D > 0 | 6/6 (+0.070…+0.081) | GREEN |

Terminal: **`DEVELOPMENT_POSITIVE_MARGINAL_GAIN_CHALLENGER_IN_LICENSED_INSTRUMENT`**.
F extracts ≈95% of the licensed constructive ceiling vs D (+0.0760 of +0.0800).
No algorithm change occurred between the freeze and assurance; develop and assurance
agree to ~4 decimal places on every contrast.

## P6 falsified — recorded, not smoothed over

Frozen diagnostic P6 predicted the v1 policy stays negative in a licensed instrument.
**It does not**: E(v1)−D = **+0.0747** here. Reading:

- the parent negative (E−D = −0.0166 in the reference instrument) was
  **policy×instrument-conditional**, not an intrinsic policy defect — consistent with
  the reference instrument's INADMISSIBLE verdict and preserved exactly as scoped
  ("this v1 policy in that instrument");
- in a state-divergent instrument, deficit-chasing of any kind (level- or
  gain-driven) beats static; the specific marginal-gain-vs-level contrast is small
  here (F−E ≈ +0.0014 balanced, +0.0009 safety, both in F's favour);
- therefore the strongest supported claim is **adaptive-vs-static in licensed
  instruments**, not marginal-gain-vs-level superiority. The mechanism-level
  claim about the derivative remains open.

## Honest scope

Model-free development stress. The positive licenses continued development of the
challenger lane; it is not evidence about real models, does not satisfy any #462
condition, and the 7B Phase-2 protocol remains the (unexecuted, frozen) confirmatory
path — now with an advisory that its own admissibility should be ceiling-probed first.
