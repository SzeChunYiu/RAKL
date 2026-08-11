# Paper 5 longitudinal metrology v1 (#253)

**Status:** `ANALYSIS_ADVANCED_RESIDUAL_OPEN` — durable registry + honest tables landed; pooled longitudinal claim refused.

## What is frozen here

| Artifact | Role |
|---|---|
| `longitudinal_event_universe.jsonl` | verbatim harvest envelopes (56 events) |
| `COVERAGE_OBSERVATION_20260811.json` | coverage receipt; pooling refused |
| `MEASUREMENT_BASIS.json` | vocabulary + refuse-to-pool policy |
| `CYCLE_REGISTRY.jsonl` | durable cycle registry (completeness / chronology / durability) |
| `DURABLE_BLOB_INDEX.jsonl` | framework archive index for all blobs incl. 39 branch-only sources |
| `retained_growth_events.jsonl` | seven-axis events with lineage; `INTERNAL_METROLOGY` |
| `experience_conversion_events.jsonl` | funnel fields where present; absent stages stay `CANNOT_MEASURE` |
| `failure_events.jsonl` / `routing_events.jsonl` | partial observations; series mostly `CANNOT_MEASURE` |
| `process_telemetry_inventory.jsonl` | cycle surface inventory — **not** process-telemetry schema |
| `resource_metrics.jsonl` | per-row resource proxies; costs not pooled |
| `seven_axis_cohort_summary.json` | per-schema-version sums only |
| `figure_sources.json` + `figures/` | Fig 2 cohort curves; Fig 3/4/7 status panels |
| `DATASET_MANIFEST.json` / `ANALYSIS_RECEIPT.json` | binding receipt |

## Reproduce

```bash
python experiments/paper5/analyze_longitudinal_universe.py \
  --universe research/paper5_longitudinal_v1/longitudinal_event_universe.jsonl \
  --out-dir research/paper5_longitudinal_v1
```

## Integrity

- Missing historical fields are never zeroed.
- Cross-version pooling is refused (`cross_version_pooling_authorized: false`).
- Retrieval ≠ reuse; repo growth ≠ semantic growth.
- Novelty remains `INTERNAL_METROLOGY` until #255.
- Does **not** unblock #250/#251 or fabricate #255 annotators.

## Residual axes (issue stays open)

See `ANALYSIS_RECEIPT.json` → `residual_axes_keeping_issue_open`.
