# Matched A3 vs A4 empirical ablation — preregistration v1

Status: `PACKET_FROZEN / EMPIRICS_UNRUN / NO_SCIENTIFIC_AUTHORITY`
Issue: #156
Date: 2026-08-11

Machine packet:
`research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json`

This freezes the **evaluation contract** for the A3↔A4 novelty-defense cell.
It does not invent ALR/recall/cost numbers.

## Research question

Under matched resources on the frozen scientific-transition authority V2 panel
(#154), does `A4_SCIENTIFIC_AUTHORITY_TYPING` improve Authority Leakage Rate
**without** collapsing valid-upgrade recall relative to
`A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED`?

## Arms

| Arm | Intervention |
|---|---|
| `A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED` | Provenance/schema-valid scalar governance (function-matched; **not** MemTX/PPMF) |
| `A4_SCIENTIFIC_AUTHORITY_TYPING` | Same information + G/R/M/I/D axis licensing |

## Frozen metrics (before result access)

```text
alr
valid_upgrade_recall
false_conservative_refusal_rate
wall_time_ms
peak_rss_bytes
state_growth_bytes
terminal_status_accuracy
```

ALR is never reportable alone. Benefit **and** cost must be reported together.

## CPU LUNARC cell (authorized)

A short FS9 CPU job may validate the freeze packet, re-run cheap A3↔A4
conformance, and emit an `EMPIRICS_UNRUN` status receipt. That job does **not**
mint A4>A3 novelty and does not invent model ALR numbers.

## Claim boundary

Allowed after this packet alone:

```text
matched A3 vs A4 evaluation contract is frozen; model empirics remain unrun
unless a later SCORED_ARM_RESPONSES receipt binds real responder payloads.
```

Not allowed:

```text
A4 > A3 novelty claim from freeze alone;
equivalence or superiority to MemTX/PPMF/AutoSci;
any invented ALR/recall/cost figure.
```
