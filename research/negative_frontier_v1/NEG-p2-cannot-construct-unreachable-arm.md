# `CANNOT_CONSTRUCT`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/04_typed_refusal.tex:32`
- `publication/papers/paper-02-structural-mechanics/sections/04_typed_refusal.tex:41`

## Receipt

- **`receipt_path`:** `research/paper2_causal_transport_absorption_v1/RECEIPT.json` — **verified present**
- Same receipt as p2-faithful-import-refuted. Verified verbatim at `arms[1]`: `"arm": "ARM-2_REPAIRABLE_EVIDENCE", "status": "CANNOT_CONSTRUCT"` with detail 'StructuralWitness.__post_init__ rejects empty evidence_ids, so an evidence-free witness is not an admissible presentation and the missing_witness_evidence branch of assess_transfer is unreachable through the public constructor.'
- supporting: `research/paper2_causal_transport_absorption_v1/PROTOCOL.json`
- supporting: `research/paper2_causal_transport_absorption_v1/AMENDMENT_01.json`
- supporting: `research/paper2_causal_transport_absorption_v1/MECHANIC_CANDIDATE.json`
- supporting: `research/paper2_causal_transport_absorption_v1/SOURCE_VERIFICATION.json`
- supporting: `src/rakl/transfer_impossibility.py`

## What happened

Arm 2 of the eight-arm typed-refusal design (ARM-2_REPAIRABLE_EVIDENCE) is preserved as CANNOT_CONSTRUCT. `StructuralWitness.__post_init__` rejects empty evidence_ids, so an evidence-free witness is not an admissible presentation and the `missing_witness_evidence` branch of `assess_transfer` is unreachable through the public constructor (constructor error: 'structural witness requires nonblank evidence identities'). The manuscript reports the arm as unreachable rather than counting it as a pass.

## One-stage attribution

instrument-construct. A registered arm turned out to be unconstructible under the shipped public API -- an honest coverage hole in the design, surfaced rather than silently scored.

## Lever

None proposed. The correct handling is exactly what was done: report the arm as unreachable, never as a pass. Inventoried because it is a place where the eight-arm design covers seven arms, and any future claim of eight-arm coverage would be false.

## Class justification

A structural property of the public constructor, preserved as an explicit non-pass. Reviving it would mean weakening the constructor's evidence requirement, which is the opposite of the design intent.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
