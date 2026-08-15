# ARN local-vs-parent discriminator v1 — CORE

**Terminal: `DISCRIMINATOR_NOT_PROBATIVE__DISTRACTOR_DESIGN_ARTIFACT`.**
The ancestor challenge stays inadmissible. Ascent is still not licensed.

The frozen protocol (`PROTOCOL.json`, committed before execution) registered the discriminator the
ancestor challenge was missing. It executed cleanly and returned
`PARENT_RESPONSIBLE_SUPPORTED` — and that verdict is **retracted** by the probe-validity check the
protocol's own construct-independence declaration obliged. `RESULT.json` is preserved exactly as
executed; nothing in it is rewritten.

## What was asked

Three distinct repaired reducer families (v2 deterministic, v3 instance-paired, v4 relational) all
closed negative against one parent abstraction: *prose-level structural extraction by an admissible
reducer*. Three failed local repairs show the local level is not responsible. They do not separate
parent from child. The registered discriminator asked the prior question all three reducers
presuppose: under a source-grounded contract, does the licensed prose carry **any** label-blind
signal separating analogue from distractor?

## What was measured (`RESULT.json`, as executed)

DEV split only, 326 items, four frozen label-blind features, 1000-permutation null,
Bonferroni-corrected α = 0.0025.

| Feature | Accuracy | p |
|---|---|---|
| F1 content Jaccard | 0.4785 | 0.805 |
| F2 IDF overlap | 0.5230 | 0.210 |
| F3 bigram Jaccard | 0.4923 | 0.790 |
| F4 positional overlap | 0.4678 | 0.925 |

Nothing beats chance. Under the frozen rule that is `PARENT_RESPONSIBLE_SUPPORTED` — ascent
licensed.

## Why that verdict does not stand (`PROBE_VALIDITY.json`)

The corpus carries a `distractor_similarity` column. Splitting on it:

| Band | n | F1 | F2 | F3 | F4 |
|---|---|---|---|---|---|
| high | 134 | 0.355 | 0.396 | 0.455 | 0.340 |
| low | 192 | 0.565 | 0.612 | 0.518 | 0.557 |

The aggregate chance-level accuracy is **two opposite effects cancelling**. Where distractors were
selected for high surface similarity, the features score *below* chance — the surface signal points
at the distractor, by construction. Where they were not, the features score above it. Spread
reaches 0.217 on three of four features, well past the 0.10 threshold.

So the null was manufactured by the corpus's adversarial distractor design, not by absence of
recoverable information in the licensed prose. **The probe cannot separate parent from child**, and
a discriminator that cannot separate is not a discriminator.

This is the mirror image of a defect already on this programme's frontier: not a gate no seed can
fail, but a gate no signal can pass.

## What is deliberately not concluded

F2 reaches 0.612 on the low-similarity stratum, above the registered 0.60 accuracy floor. Applied
to that stratum alone the frozen rule would read `LOCAL_RESPONSIBLE_SUPPORTED`. **That reading is
refused.** The rule was registered over the whole DEV split, and re-cutting to a favourable stratum
after seeing outcomes is post-hoc responsibility selection — the thing the audit's `S06` invariant
and `P-RF3` exist to forbid. It is recorded as an observation for the successor's design, not as a
verdict.

Nothing here promotes or retracts any prior ARN terminal. The v2/v3/v4 negatives stand under their
own contracts.

## What the successor needs

A discriminator whose signal cannot be cancelled by distractor construction. Two candidate routes,
neither executed:

1. **Stratify before aggregating.** Register the distractor band as a blocking factor in the frozen
   rule rather than discovering it afterwards, so opposite-signed strata cannot average to a null.
2. **Move off the surface.** Every feature here is lexical, which is exactly the channel the corpus
   was built to poison. A representation the distractor design does not target — argument
   structure, event order, role correspondence — is the honest next probe, and is itself subject to
   the construct-independence obligations.

Until one of those runs, `AncestorChallenge.escalation_admissible` for the ARN lineage remains
`False`, and the frozen chain's `ASCEND` remains blocked by the stricter check.

## Reproduce

```bash
python research/arn_local_vs_parent_discriminator_v1/run_discriminator.py
python research/arn_local_vs_parent_discriminator_v1/run_probe_validity.py
```
