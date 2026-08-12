# Paper IV Phase-1 (#461) — exposure-sweep results

Real LUNARC A100 runs of the frozen Phase-0/1 exposure-ladder instrument (one dir per model).
Each run is bound to the frozen protocol packet hash `fce2bb17…`, `grants_scientific_authority=false`,
`scientific_claim_status=NO_EMPIRICAL_RESULT`. Terminals are read straight from the data — no fabrication.

| Model | Terminal | Note |
|---|---|---|
| Qwen2.5-0.5B | `NO_STATE_DEPENDENT_RESIDUAL` | barely clears floor (max 0.667); no differential state-dependent gain |
| Qwen2.5-1.5B | (running) | |
| Qwen2.5-3B | (running) | |
| Qwen2.5-7B | (running) | |

Figures: `traj_<family>.pdf` (mastery + marginal-gain vs exposure), rendered via `orion.metrics`.
A `NO_STATE_DEPENDENT_RESIDUAL` terminal means: for that model the paper's structural-residual
mechanism is **unsupported** — a real, reportable negative, not a disappointment to engineer away.
