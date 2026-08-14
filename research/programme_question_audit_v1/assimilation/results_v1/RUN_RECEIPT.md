# CONGRUENCE-CONTEST-V1 — run receipt

Executed 2026-08-14 on laptop billy, fresh isolated shallow clone
`~/rakl-qaudit` at branch commit `2eb152a` (the freeze commit), python3.9,
`PYTHONPATH=src`, evaluator sha256 verified on the execution host before
running (`adf4ef9e...5078506`, matches the freeze). Exit code 0; self-tests
passed (planted false-merge case, witness-translation known case, fail-closed
bad-witness rejection). Clone removed after result copy.

## Typed outcome

`SURFACE_IMPORT_REFUTED / ADAPTED_TRANSFER_SUPPORTED_AT_INSTRUMENT_GRADE`
(faithful term-level e-graph import: `PRECONDITION_BLOCKED`, recorded in the
protocol, not run.)

## Results against frozen predictions

| endpoint | class | prediction | measured |
|---|---|---|---|
| substrate shape | descriptive | all-star | 31/31 star-shaped; **only 6 distinct shape classes** across the substrate |
| B1 false-merge rate | MEASURED | >= 0.5 | **0.833** (150/180) |
| B1 role-class recall | MEASURED | << 1 | **0.0** (ordering makes base reps first; construction-influenced, noted) |
| B2 role-class recall via witness translation | MEASURED | 1.0 | **1.0** (155/155 witnessed merges; 0 rejected; translation worked) |
| duplication exhibit (shipped code) | MEASURED | flat growth, doubled storage | second-pass new roles **0**, saturation `BOUNDED_SATURATED`, storage 31 -> **62** |
| storage A / B1 / B2 | MEASURED + CONF | B2 = N (closed form) | 186 / 6 / **31** — B2:A exactly 1:(R+1): **construction-dominated, not headlined** |
| JUMP-class recall (all arms) | CONF | 1.0 | 1.0 / 1.0 / 1.0 |
| B2 false merges | CONF | 0 | 0 |

## Honest reading

1. **The surface import is refuted on real substrate**: shape congruence
   without witnesses false-merges 83.3% of the time here, because the real
   Lean graph is massively shape-degenerate (31 structures, 6 shape classes).
   The compression it "wins" (186 -> 6) is exactly its corruption.
2. **The governed adaptation carries the transfer**: witnessed congruence
   compacts 6-fold while preserving BOTH declared query classes —
   signature-class directly, role-class through witness translation (the
   e-graph `find()` analogue, and the measured cell that could genuinely have
   failed).
3. **The knowledge-compilation lesson lands measurably**: recall is a
   per-query-class property. The same compaction that is lossless for
   signature queries is total loss for role queries without witnesses.
4. **The shipped-space duplication exposure is real**: `StructureSpace`
   reads `BOUNDED_SATURATED` while identical restatements double storage —
   measured on shipped code, motivating the witnessed-congruence absorption
   as a framework candidate (proposal-only; nothing here modifies the
   framework).

## Scope

One small kernel-checked star-shaped substrate under a synthetic variant load;
instrument grade; no e-graph fidelity claim; no natural-corpus claim; grants
no scientific or promotion authority. Storage ratio B2:A is construction-
dominated under this load and is not a finding.
