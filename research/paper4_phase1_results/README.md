# Paper IV Phase-1 (#461) — exposure-sweep results (frozen Qwen ladder)

Real LUNARC A100 runs (jobs 3486377–80) of the frozen Phase-0/1 exposure-ladder instrument.
Every run is bound to protocol packet hash `fce2bb17…`, `grants_scientific_authority=false`,
`scientific_claim_status=NO_EMPIRICAL_RESULT`. Terminals are read straight from the data.

| Model | Terminal | What happened |
|---|---|---|
| Qwen2.5-0.5B | `NO_STATE_DEPENDENT_RESIDUAL` | max same-structure acc 0.667; no differential state-dependent gain |
| Qwen2.5-1.5B | `MODEL_FLOOR` | never cleared chance (0.5) on principle |
| Qwen2.5-3B | `REPETITION_REMAINS_VALUABLE` | learned `state_reachability` 0.5→1.0 (exp≥4, held); other 2 families at chance |
| Qwen2.5-7B | `NO_STATE_DEPENDENT_RESIDUAL` | learned `state_reachability` early (exp 1–4) then forgot it (0.5 by exp 8) |

## Honest synthesis
Across the frozen Qwen 0.5B–7B ladder, **no model exhibits the hypothesized state-dependent
structural residual** (`MECHANISM_SIGNAL_PRESENT` was never reached). Only the simplest family
(`state_reachability`, reachability from an edge list) was learnable at all, and only unstably
(3B held it, 7B forgot it); `balance_conservation` and `sequence_composition` stayed at chance
for every model and exposure.

Per the frozen protocol this is a **supported negative**: the central mechanism is unsupported
*at this capability level*, so the Phase-2 adaptive scheduler is **not** built. It does **not**
refute the mechanism for capable models — it shows the instrument's capability floor gates the
test, consistent with the series' `CAPABLE_MODEL_AVAILABLE=NO_REFUTED` blocker (Paper VI §13d).
Testing the residual properly requires a capable in-ladder model and gate #462.

Figures: `<model>/traj_<family>.pdf` (mastery + marginal-gain vs exposure), via `orion.metrics`.
