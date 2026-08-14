# Paper II comparator requirements — 2026 audit

Date: 2026-08-14. Derived from `NOVELTY_THREAT_RANKING.md`.

The current confirmatory packet compares the full contract against lexical,
relational, mechanism-only and coordinate-ablated-twin arms. Given the threat
ranking, that arm set is insufficient: it only beats projections of itself.

## Mandatory arms before any novelty claim

1. **Transportability oracle (RED threat).** On any benchmark item expressible
   as a causal transport problem, run `sID` (or an equivalent complete transport
   decision) with the selection diagram supplied. If `sID` matches the contract's
   decisions wherever it is defined, the contract's residual is confined to the
   cases `sID` cannot express — which is exactly the claim that should then be
   made. This is the single most important missing comparator.

2. **Structure-mapping baseline (AMBER).** SME-style structural evaluation over
   the role/relation content, thresholded to a decision. Establishes whether
   the mapping conjunct carries any of the measured advantage.

3. **Selective-prediction baseline (AMBER).** A confidence-thresholded abstainer,
   and a conformal abstainer under covariate shift, both tuned to match the
   contract's abstention *rate*. This is the fair test of whether structural
   `CANNOT_CHECK` beats threshold-triggered abstention at equal coverage.

4. **Mechanism-alignment LLM judge under matched context.** Same information,
   same token budget, asked directly to judge transfer validity. The existing
   preliminary comparator is one model, one seed, one family-set.

5. **Trivial gates.** `always_reject`, `always_accept`, `always_cannot_check`.
   Established as necessary by the six-family audit: `always_reject` attains
   false-accept 0.000, so any false-accept figure reported without its paired
   valid-transfer retention figure is uninterpretable.

## Mandatory design constraints

Established by `research/paper2_six_family_audit_v1` (PR #593):

- **The `full` arm must be a predictor distinct from the gold function.** In the
  current packet `full = verify`, so its Brier loss is a constant 0.0004 and the
  primary "paired" statistic has zero variance in one arm.
- **The registered gate must be failable, demonstrated by exhibiting a failing
  seed.** 12/12 arbitrary seeds currently give 6/6 and p=0.03125.
- **Discriminating coordinates must be sampled, not assigned per stratum.**
  Two strata currently have mechanism exact3 of exactly 0.000 by construction and
  supply 66.7% of the headline gain.
- **The task surface must require recovery, not lookup.** Scrambling every
  `source_text`/`target_text` leaves gold and all six coordinates unchanged
  810/810; the coordinates are read from pre-parsed public fields.
- **Each coordinate must be the sole discriminator in some stratum**, or
  leave-one-out results describe the generator rather than the contract.

## Non-negotiable reporting rule

Report false-accept and valid-transfer retention **as a pair**, always. A gate
can attain zero false-accept by rejecting everything; selectivity is not edge.
