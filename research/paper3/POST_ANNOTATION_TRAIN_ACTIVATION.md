# Paper III — post-annotation train activation (fail-closed)

Status: `PROCESS / NO_GPU_SUBMIT / GATED_ON_REAL_#217_ARTIFACTS`

This is the exact activation order once real external annotations exist.
It does **not** authorize a GPU train by itself. Autopilot must not invent
labels and must not call `sbatch` / `paper3_lunarc_workload` until every gate
below passes.

## Preconditions (already true on main / FS9)

| Check | Evidence |
|---|---|
| Descriptor harvests READY | jobs `3476527`/`3476528`/`3476529` → `HARVEST_DESCRIPTOR_READY` |
| `training_authorized=false` on harvests | all three harvest + execution receipts |
| Subject-binding freeze process | PR `#190` / `SUBJECT_BINDING_FREEZE_WINDOW_144.md` + chain wrappers |
| Human annotation gate open | issue `#217` (successor of deleted `#43`) |
| Pre-label power decision | issue `#248` (merged) → Path C `CONFIRMATORY_PACKET_POWER_LIMITED` retain of v2.1 |
| Witness/label decoupling diagnostic frozen | `research/receipts/PAPER3_WITNESS_LABEL_DECOUPLING_FREEZE_20260811.json` |

## Activation chain (after real humans deliver)

```text
1. Import annotator A + B submissions (schemas/paper3-annotation-submission-v2-1)
2. Freeze both submissions before adjudication
3. Import distinct adjudicator packet
4. Import distinct provenance-audit packet
5. Build annotation-import receipt
   - training_authorized MUST remain false on the import receipt
   - passed=true only if role separation + chronology + schema hold
6. Run witness/label decoupling diagnostic FIRST
   - python -c "from rakl.paper3_witness_decoupling import decoupling_from_benchmark_cases; ..."
   - if witnessed_structure_authority == NOT_INFORMATIVE → stop structural-train claims
7. Run confirmatory gate (paper3_confirmatory_gate) on the exact subject SHA
   - expensive_training_authorized becomes true only if annotation + diagnostic gates pass
   - Path C power-limited interpretation: INDISTINGUISHABLE/UNDERPOWERED ≠ refutation
8. Only then: python -m rakl.paper3_lunarc_workload (never raw sbatch)
   - preflight requires gate expensive_training_authorized=true
   - partitions limited to gpua100/gpua100i/gpua40/gpua40i
9. Harvest train + frozen-inference receipts; keep nulls
```

## Hard stops

- Zero or synthetic `#217` payloads → remain blocked.
- Import receipt `training_authorized=true` → reject (`annotation_import_scope_violation`).
- Decoupling rate 0 → do not treat witnessed_structure as incremental signal.
- Subject freeze broken (`HEAD != origin/main != expected`) → fail closed; use chain wrappers.
- Same-session self-review is not independent provenance audit.

## FS9 note

Canonical descriptor subject `787c7e00…` remains harvested. Freeze-window
wrappers landed on `main` via `#190` but are **not** required on the old FS9
checkout until the next intentional subject rebind. Do not `git fetch` mid
stage→harvest window.

## Claim boundary

Shipping this checklist does not authorize training. Descriptor READY with
`training_authorized=false` is staging evidence only.
