# Paper IV — Structural Learning Mechanics (design/protocol preprint + executed Phase-0/1)

`main.tex` is a preregistered design-and-protocol preprint that now also reports **one executed
step**: the Phase-0/1 exposure instrument (#461) run on the frozen Qwen2.5 0.5B–7B ladder, which
returned a **supported negative** (no state-dependent structural residual). No positive
adaptive-allocation claim is made; the Phase-2 scheduler is deliberately not built.

```
main.tex             # entry point (single-file)
figures/phase1_result.pdf     # cross-model Phase-0/1 result figure
figures/scripts/make_phase1_result.py   # generator (reads figures/data/)
figures/data/<model>_outcomes.jsonl     # vendored real A100 exposure outcomes (packet-bound)
```
Full result set + per-model trajectory figures: `research/paper4_phase1_results/`. A standalone
*positive* empirical Paper IV still requires the Phase-2–4 programme + a capable in-ladder model
+ gate #462.
