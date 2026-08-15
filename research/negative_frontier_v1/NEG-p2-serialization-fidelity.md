# `AUXILIARY_DIAGNOSTIC_ONLY__NOT_PART_OF_FROZEN_REGISTRATION (probe-G refutation of the PROMOTE_CONDITIONALLY controlled-witness extraction terminal)`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/05_instrument_falsifiability.tex:41-46`

## Receipt

- **`receipt_path`:** `research/paper2_controlled_witness_extraction_audit_v1/results/PROBE_G_CONTROLLED_TEXT_INERTNESS.json` — **verified present**
- The refutation and the refuted terminal live in two different artifacts, by design. `research/paper2_controlled_witness_extraction_audit_v1/results/PROBE_G_CONTROLLED_TEXT_INERTNESS.json` carries `status: AUXILIARY_DIAGNOSTIC_ONLY__NOT_PART_OF_FROZEN_REGISTRATION` and the interpretation verbatim: "exact_decision=1.0 is entailed by parse success and is a measure of serialization fidelity, not of structural witness extraction from prose". The original `research/paper2_controlled_witness_extraction_v1/FINAL_RECEIPT.json` still carries `terminal: PROMOTE_CONDITIONALLY_CONTROLLED_TEXT_STRUCTURAL_WITNESS_EXTRACTION`, unedited -- that string is deliberately NOT present in the audit directory.
- supporting: `research/paper2_controlled_witness_extraction_v1/FINAL_RECEIPT.json`
- supporting: `research/paper2_controlled_witness_extraction_v1/PROTOCOL.json`
- supporting: `research/paper2_controlled_witness_extraction_audit_v1/README.md`

## What happened

n=1296 base tasks, 2592 text surfaces. The full controlled extractor scored exact decision 1.0, invalid false-accept 0.0, abstention recall 1.0; strongest non-extraction parent 0.889; a ten-mutation panel was caught in full. Probe G then showed the renderer emits 'Label :: serialized-value' lines carrying the structural records verbatim and the extractor parses them back: the render/extract composition is the IDENTITY on the structural record, recovered byte-identically on 2592/2592 surfaces. Scrambling the prose changes every rendered surface (1296/1296) and changes nothing else. The original FINAL_RECEIPT.json still carries terminal PROMOTE_CONDITIONALLY_...; the refutation lives in the separate audit directory, and the original is preserved unedited.

## One-stage attribution

instrument-construct. Exact decision 1.0 was 'entailed by parse success' (05:46) -- the instrument measured serialization fidelity, not witness extraction from prose.

## Lever

Narrowed survivor is retained explicitly: the mutation panel remains a valid test of fail-closed parser behaviour under field omission and tampering, 'an honest terminal of serialization-interface fail-closure'. The extraction question moved to the Case 3 prose-transfer successor.

## Class justification

The manuscript preserves the refuted conditional-promotion terminal verbatim and states what survives is 'deliberately narrower'. The successor epoch is Case 3.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
