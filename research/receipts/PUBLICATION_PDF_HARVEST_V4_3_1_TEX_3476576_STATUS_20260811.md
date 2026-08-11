# Publication PDF harvest status — V4.3.1 TeX as-of-3476576

Date: 2026-08-11

## Requested action

After TeX PR noting V4.3.1 job **3476576** (both-parse; exact still 0), dispatch `publication-pdfs` and harvest canonical PDFs.

## Outcome: BLOCKED (pre-existing main CI)

- TeX PR: https://github.com/SzeChunYiu/RAKL/pull/278 (merged).
- Ingest PR: https://github.com/SzeChunYiu/RAKL/pull/277 (merged).
- `publication-pdfs` on #278 tip `462f1f8…` failed at exact-head pytest before compile:
  - run: https://github.com/SzeChunYiu/RAKL/actions/runs/31532990763
  - failures: frozen `BATCH_CONTRACT_V4.json` / readiness / V4.1 internal-review subject-hash drift
  - expected frozen sha `07eda3b715…`; tip bytes `8fdfbe09c2…` (mutated in #270 while binding shared runner bytes).

No green canonical PDF artifact exists for this TeX tip, so no PDF harvest package is admitted.

## Exact scores (confirmed; gate unchanged)

| Job | Arm | parse_valid | conceptual | exact_conceptual_pass |
|-----|-----|-------------|------------|------------------------|
| 3476576 | DIRECT_CORPUS | true | 1/5 | false |
| 3476576 | RAKL_CONTEXT | true | 3/5 | false |

`exact_conceptual_pass_arm_count=0`. Serialization-only repair. Not a 1.5B improvement claim. Parent **3476566** remains DIRECT parse-null residual.

## Next discriminator (outside this fiber)

Restore or separately rebind frozen V4/V4.1 contract/readiness hashes without softening the exact conceptual gate; then re-dispatch `publication-pdfs` and harvest.
