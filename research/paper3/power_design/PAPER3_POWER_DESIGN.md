# Paper III confirmatory power design (#248)

Label-blind sample-size and minimum-detectable-effect study for the frozen
v2.1 sixteen-item confirmatory packet. Completed **before** the first external
human judgement on issue #217.

## Chronology

1. Verified issue #217 has zero imported external annotation payloads in the public repository.
2. Verified `research/paper3/annotation/` contains only frozen packets, rubrics, and source sets.
3. Recorded `ZERO_LABELS_AT_POWER_DESIGN.json` bound to the exact Git subject.
4. No first-label cutoff existed at decision time.

## Primary endpoint

**Paired per-item Brier reduction** (witnessed structure minus strongest frozen
semantic control) on adjudicated transfer validity. Secondary quantities —
ROC-AUC gain, average-precision gain, Q2 true-accept floor, Q3 false-accept
ceiling — are registered for descriptive/mechanistic readouts but do not
override the primary paired inference gate.

## Registered material effect (MDE)

| Quantity | MDE |
|----------|-----|
| Primary paired Brier reduction | 0.05 |
| ROC-AUC gain | 0.05 |
| Average-precision gain | 0.05 |
| Q2 true-accept improvement | 0.15 absolute |
| Q3 false-accept reduction | 0.15 absolute |

The primary MDE is the smallest paired Brier improvement that would materially
justify the structural-witness layer over the frozen BGE reranker control.

## Simulation

- Config: `POWER_SIMULATION_CONFIG.json` (seed `24820260811`, alpha `0.05`, power threshold `0.80`)
- Engine: `scripts/paper3_power_design_simulate.py` using `rakl.inference.paired_lift_verdict`
- Results: `POWER_RESULTS.json`

Plausible paired-difference sigmas `{0.08, 0.10, 0.12}` bracket expected item-level
Brier noise under leave-one-family-out evaluation.

## Decision

See `DECISION_RECEIPT.json`. Path selection rules:

- **Path A** — retain v2.1 only if n=16 reaches ≥80% power for the primary MDE across all decision sigmas.
- **Path B** — expand label-blind before labels if Path A fails but adequate n ≤ 48 is feasible.
- **Path C** — retain v2.1 as `CONFIRMATORY_PACKET_POWER_LIMITED` when n=16 is underpowered and no label-blind expansion packet is frozen in-repo (selected).

## Issue #217 instruction binding

After this decision, annotators follow `research/paper3/annotation/README_V2_1.md`
and the exact v2.1 packet hashes recorded in `DECISION_RECEIPT.json`. No packet
version change occurs on Path C.

## Reproduction

```bash
python3 scripts/paper3_power_design_simulate.py
python3 scripts/paper3_power_design_finalize.py
pytest tests/test_paper3_power_design.py -q
```
