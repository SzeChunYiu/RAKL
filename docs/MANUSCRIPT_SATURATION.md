# Manuscript saturation

RAKL treats a paper as a **bounded publication projection** of canonical research state, not as the canonical state itself. Paper revision therefore reuses the existing saturation/stopping and review surfaces rather than adding a new high-impact method surface.

## Semantic growth

A manuscript pass counts as growth only when it retains a new canonical object of one of these kinds:

- claim distinction;
- citation or intellectual-lineage cluster;
- novelty-boundary change;
- proof obligation;
- explanatory bridge;
- falsifier;
- reviewer-relevant repair.

Paraphrase, repeated rediscovery and citation padding do not create growth. New growth resets the post-growth flatness tail.

## Local certificate

`ManuscriptSaturationProtocol` can return same-context local saturation only when:

1. every registered review lens has produced the required flat pass count **after the last material growth**;
2. every registered search route has also run flat after that growth;
3. freshness, nearest-work, proof-obligation and section-purpose audits are complete;
4. no `MATERIAL_OPEN` item remains.

Empirical questions may remain explicitly `EMPIRICAL_DEFERRED`; unavailable evidence may remain `BLOCKED_MISSING_EVIDENCE`; deliberately excluded neighbors may be `OUT_OF_SCOPE`. Those classifications stay visible in the receipt.

## What it does not certify

A local manuscript certificate does **not** mean:

- open-world literature completeness;
- scientific truth or empirical superiority;
- framework-wide scientific saturation;
- independent peer review;
- evidence-lineage-independent corroboration.

The receipt therefore hard-codes `independent_saturation=false` and `independent_peer_review=false`. Those coordinates can change only through genuinely independent external evidence, not by repeating same-context reviewer personas.

## Reopen rule

Any exogenous paper, reviewer counterexample, implementation result, proof obligation or artifact mismatch that materially changes the manuscript semantic state reopens the projection. The next local certificate must be earned again after the new object is assimilated.

## Section-purpose audit

Length itself gives no saturation credit. Every section and display must have a reader obligation that would become harder to discharge if it disappeared. Content that only repeats a definition or adds decorative citations is merged or removed; missing ancestry, assumptions, falsifiers, proof obligations or evidence boundaries open new manuscript fibers.
