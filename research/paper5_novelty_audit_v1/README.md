# Paper 5 retained-novelty audit v1 (#255)

**Status:** `AUDIT_UNIVERSE_FROZEN_PHASE0 / BLOCKED_ON_HUMAN / ZERO_EXTERNAL_NOVELTY_LABELS`

Phase 0 freeze binds the independent retained-novelty audit universe to the frozen #253 longitudinal dataset. Internal retained counts remain `INTERNAL_METROLOGY`. No external annotator labels, adjudication, or construct-validity claim is authorized.

## Frozen artifacts (Phase 0)

| Artifact | Role |
|---|---|
| `AUDIT_UNIVERSE_MANIFEST.json` | binds measurement basis, #253 manifest, retained/control universes, cutoff |
| `retained_event_universe.jsonl` | 104 internally retained axis events (`value > 0`) |
| `control_event_universe.jsonl` | 174 internally non-retained / zero-value controls |
| `BLINDED_AUDIT_CANDIDATE_FRAME.jsonl` | label-blind opaque item IDs + lineage (no internal retained boolean) |
| `INTERNAL_STRATIFICATION.jsonl` | internal retained/control flags for sample planning — **not for annotator release** |
| `ZERO_EXTERNAL_NOVELTY_LABELS.json` | zero external annotation/adjudication receipt |
| `AUDIT_FREEZE_STUB.json` | inventory + human blockers |

## Reproduce

```bash
python experiments/paper5/freeze_novelty_audit_universe.py \
  --longitudinal-dir research/paper5_longitudinal_v1 \
  --out-dir research/paper5_novelty_audit_v1
```

## Human blockers (issue stays OPEN)

Required before Phase 1 sampling / annotation:

- `annotator_A`
- `annotator_B`
- `adjudicator` (distinct from both annotators)
- `provenance_auditor`

Same-session AI roleplay is **not** independent review.

## Claim boundary

This freeze does **not** establish retained-novelty precision, false-collapse rate, axis validity, or semantic-growth authority. Those require frozen human labels and adjudication per `experiments/paper5/NOVELTY_AUDIT_PROTOCOL_V1.md`.
