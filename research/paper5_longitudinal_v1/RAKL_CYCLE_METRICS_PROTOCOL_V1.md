# RAKL_CYCLE_METRICS protocol v1 (#446)

**Status:** `SCHEMA_FROZEN_PROSPECTIVE_ONLY` — stable metrology contract for new RAKL_math cycles.

**Schema:** `schemas/rakl-cycle-metrics.schema.json` (`rakl-cycle-metrics-v1`)

**Validator:** `src/rakl/rakl_cycle_metrics.py`

## Purpose

Give Paper V (#446) a single prospective cycle-metrology object that records process evidence without minting theorem, tool, gluing, review-independence or scientific authority.

Historical heterogeneous blobs under `RAKL_CYCLE_METRICS-*-proposal-shadow` remain development data. They are **not** retroactively rewritten or confirmatory-rerun. New cycles should emit `rakl-cycle-metrics-v1`.

## Required sections

| Section | Role |
|---|---|
| `subjects` | Cycle identity: framework/application SHAs, atom/fibre, pre-action receipt |
| `opportunity_denominators` | Frozen before retrieval/action; unknown denominators → `CANNOT_MEASURE` + reason |
| `retrieval` | Retrieved/selected/rejected counts; recall rates only when denominators are integers |
| `action_change_attribution` | Pre/post memory and governance preferences; observational, not causal |
| `outcome` | Residuals, local result, false transfer / authority leak / chronology flags |
| `reuse_funnel` | Episode → lesson → reuse stages, including failed/out-of-scope branches |
| `cost` | Tokens, calls, wall time, provider cost where available |
| `longitudinal_performance_vector` | Five noncompensatory coordinate families; **no scalar RAKL score** |

## CANNOT_MEASURE policy

- Missing historical or runtime counters stay `{"status":"CANNOT_MEASURE","reason":"..."}`.
- Never substitute `0` for an unknown denominator or absent stage.
- Numeric recall/rate fields require a frozen non-negative integer denominator.
- `audit_rate_denominators()` rejects numeric rates when the paired denominator is `CANNOT_MEASURE`.

## Longitudinal performance vector (five dimensions)

1. **verified_progress** — residual contraction, obligation closure, local scoped result rate
2. **search_utility** — relevant-root recall, counterevidence recall, missed memory, route-change rate
3. **reuse_utility** — successful fresh reuse vs false/out-of-scope vs stale reuse
4. **governance** — prospective chronology, authority leakage, evidence-root binding, negative-history preservation
5. **efficiency** — progress per token / model call / retrieval call / wall time

Safety dimensions are noncompensatory. `aggregate_scalar_score_forbidden` must remain `true`.

## Claim boundary

- Process metrology ≠ mathematical proof ≠ scientific authority.
- Retrieval ≠ reuse; repository growth ≠ semantic growth.
- Seven-axis retained novelty, when present, stays `INTERNAL_METROLOGY` until independent audit (#255).
- Naturalistic repository history is descriptive development data, not a randomized efficacy study.

## Relation to Paper 5 v1 harvest (#253)

`research/paper5_longitudinal_v1/` remains the frozen retrospective harvest and refuses cross-version pooling. This schema governs **prospective** cycle emission going forward and unblocks longitudinal instrumentation in #446 without rerunning historical NS/Hodge/YM confirmatory cases.

## Minimal example

```python
from rakl.rakl_cycle_metrics import minimal_cycle_metrics_template, audit_cycle_metrics

doc = minimal_cycle_metrics_template(
    cycle_id="PROSPECTIVE-CYCLE-001",
    reason="eligible memory universe not frozen before retrieval",
)
assert audit_cycle_metrics(doc) == ()
```
