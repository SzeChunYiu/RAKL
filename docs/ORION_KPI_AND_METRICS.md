# Orion KPIs & Metrics — turning framework concepts into measurable, visualizable, algorithm-driving quantities

**Status:** design catalog (proposal). Defines the measurable quantities already latent in
the framework, turns each into a named KPI, states the algorithm each KPI enables, and
specifies how it is visualized for readers. No KPI grants scientific authority; a KPI is a
measurement, never a promotion signal. Real values are produced by the experiments named
per row — this document does not report results.

## Why
Orion talks about *saturation*, *mastery*, *authority*, *coverage*, *transfer safety* — all
of which are quantities, not adjectives. If we name them as KPIs we get three things at once:
1. **Readers** see, per epoch/exposure, how an LLM's problem-solving state evolves (not a
   single accuracy number).
2. **The framework** gets first-class control signals — an allocator/router can *act* on a
   KPI (e.g. stop exposing a saturated structure; escalate an unsaturated one).
3. **The papers** get honest process-level figures instead of only end-point scores.

## The KPI catalog

| KPI | Definition (measured object) | Range / direction | Algorithm it enables | Visualization | Owning paper / experiment |
|---|---|---|---|---|---|
| **Structural mastery vector** `M_t(s)` | 6 probe-based coordinates (principle, composition, boundary, representation, transfer, retention) at checkpoint `θ_t` | each ∈ [0,1], no scalarization | Allocation: expose the *lowest* unsaturated coordinate next | Radar (per checkpoint) + 6 small-multiple lines vs epoch | Paper IV / #461 Phase 1 |
| **Saturation level** `sat(s,c)` | marginal accuracy gain of the next equal-cost same-structure example on coordinate `c` | [0,1]↓, saturated ≈ 0 | Stop-rule: cut same-structure exposure when `sat < ε` **and** retention floor holds | Marginal-gain curve vs exposure, ε line | Paper IV / #461 |
| **Saturation epoch** `E*(s,c)` | first exposure count where `sat < ε` | integer epoch | Schedules total budget per structure | Vertical marker on the trajectory | Paper IV / #461 |
| **Retention / forgetting** | coordinate value on an earlier structure after training moved on | [0,1]↑ | Hard *constraint* (not objective term): any schedule that violates the floor is infeasible | Retention band with floor line | Paper IV §Prop. retention |
| **Authority coverage** | fraction of a claim's authority poset axes (G,R,M,I,D) that are LICENSED | [0,1]↑, non-compensatory | Gate: block promotion until load-bearing axes covered | Stacked axis-status bar per claim | Paper I |
| **Gate safety (false-accept)** | P(model=ACCEPT \| gold=REJECT) under the applicability gate vs plain/CoT | [0,1]↓ | Fail-closed obligation gate (already shipped) | Bar + bootstrap CI (the comparator figure) | Paper II §comparator |
| **Method-saturation** | rate of *new* method discovery per research round (novelty of GROW⇄CLOSE output) | ↓ toward 0 = saturated | Loop-until-dry stopping; trigger "one-dimension-higher" meta-method | New-method-per-round curve | Paper III / generative programme |
| **Coverage / atlas fill** | fraction of the typed compatibility complex with ≥1 licensed chart | [0,1]↑ | Router target: JUMP toward lowest-coverage fibre | Heatmap over the atlas | Paper VI |
| **Cost-to-target vector** | tokens / examples / FLOPs / GPU-h / wall-clock to a frozen capability target, *incl.* extraction+probe overhead | ≥0↓ | Adaptive-vs-static allocation decision `E−D` | Parallel-coordinates per arm | Paper IV §Phase 2 |

## The reader-facing figure: an LLM's problem-solving trajectory

A single "process" figure per solved problem, populated by the Phase-1 run:

```
  mastery                                        saturation (marginal gain)
  1.0 ┤        ╭───principle───────────           0.5 ┤╲  principle saturates at E*=8
      │      ╭─╯    ╭──composition──                   │ ╲___
      │    ╭─╯    ╭─╯   ╭─boundary─                     │     ╲___  composition still climbing
      │  ╭─╯   ╭──╯  ╭──╯                               │         ╲____
  0.0 ┼──┴─────┴─────┴──────────  exposure→        0.0 ┼──────────────────  exposure→
        1  2   4   8  16  32  64                        1  2  4  8 16 32 64
```

The left panel shows *what the learner has mastered* per coordinate as it sees more of a
structure; the right shows *where the next example still buys something*. Together they say,
concretely and per epoch, "principle learned early, composition/boundary lag" — the exact
"how does the LLM attempt the problem over time" picture, with the saturation KPI overlaid.

## From KPI to algorithm (the point of naming them)
Once these are computed, allocation/routing becomes a policy over KPIs, e.g.:
```
next_structure, next_probe = argmin over (s,c) of  mastery[s][c]
                             subject to  retention_floor(s') for all s'  (hard)
                             and         sat[s][c] > ε        (still learnable)
```
This is the `TrainingAllocationPolicy` Paper IV Phase 2 tests — but the *same* KPI signals
also drive the inference-time SEARCH→JUMP→GLUE→LIFT router (coverage KPI) and the
Paper III method loop (method-saturation KPI). One metric layer, three consumers.

## Implementation plan
1. `orion.metrics` — pure functions computing each KPI from the existing typed objects
   (`StructuralMasteryEstimate`, saturation receipt, authority poset, comparator results).
   No new authority; KPIs are read-only measurements.
2. `orion.metrics.viz` — the trajectory + saturation figure (matplotlib, Okabe–Ito, the
   dataviz palette rules), fed by real Phase-1 `exposure_outcomes.jsonl`.
3. Wire the real trajectory figure into Paper IV (process evidence) and reference the KPI
   layer from Papers I/II/III/VI where each KPI lives.

Honesty guardrail: every KPI figure states its N, seed, and that it is a system/process
measurement, not a scientific-authority or promotion signal.
