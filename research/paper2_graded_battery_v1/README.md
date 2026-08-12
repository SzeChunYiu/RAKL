# Graded evidence-integration battery v1 — GLM-5.2

**Status:** `NON_SEALED_HOSTED_EVIDENCE`. Not the registered Paper II protocol, not
confirmatory, grants no scientific authority. A hosted endpoint is not
weight-attestable. Recorded because these are the first arm comparisons in this
project run on instruments *demonstrated* able to register a difference.

Total: **~540 model runs** across six configurations, every one gated by leak
controls that abort the run on failure.

## Why it exists

The single pendulum task is at floor for Qwen2.5 0.5B-7B and at ceiling for
GLM-5.2 (30/30 both arms — `paper2_hosted_capability_probe_v1`), so it cannot
register an effect of either sign. This battery builds a difficulty gradient
stressing the one coordinate that was never saturated: evidence-ID binding.

## Design

Procedurally generated evidence-integration tasks. Sources make claims under
context coordinates; only some dimensions are **load-bearing**. A source is
misaligned only if it differs from the target on a load-bearing dimension.
Ground truth comes from a verifier over generator structure — **never** from
recording which coordinate was perturbed.

- **DIRECT**: raw source prose + question.
- **RAKL**: same prose plus normalized context coordinates. No target
  comparison, no relevance filtering, no disposition.

## Leak controls — run before any delta, abort on failure

1. **Mechanical baseline** — tag-only all-dimension set comparison, no LLM.
   `exact_pass = 0.00` at every level.
2. **Disposition scan** — no per-source verdict in either prompt. Zero hits.

Both caught real defects **in this battery** before any comparison ran:
- v0 shipped a precomputed `differing_dimensions` field to the RAKL arm; the
  mechanical baseline scored **1.00 exact**. The arm was being handed the label.
- The prompt stated the naive rule while the verifier applied the relevance rule,
  penalising the model for following instructions.

A third arm — **selective retrieval** — was built and then **withheld**: its
structural-proximity prefilter discards ~100% of misaligned sources
(recall 0.00–0.11), so it would post a large negative as an artifact of the
retriever rather than of RAKL. A construct that can only fail is as invalid as
one that can only pass.

## Result A — relevance stated (n=30/cell)

```
lvl  src dim nm | DIRECT f1 | RAKL f1 | delta_f1   p     | mech_f1
L1     8  2   2 |   0.906   |  0.881  | -0.0248  0.391   | 0.82
L2    14  4   4 |   0.870   |  0.867  | -0.0031  0.910   | 0.81
L3    20  4   7 |   0.856   |  0.847  | -0.0091  0.737   | 0.83
L4    26  5  10 |   0.811   |  0.829  | +0.0184  0.508   | 0.79
```

Difficulty axis works: DIRECT declines monotonically 0.906 → 0.811
(slope −0.030/level), misaligned-F1 0.911 → 0.734. Both arms sit **above** the
mechanical baseline (+0.082/+0.060/+0.031/+0.024) — the model is reasoning, not
tag-matching. This is the sensitivity demonstration the pendulum never had.

## Scale is not a difficulty lever

Extending to 26/34/40 sources with multi-dimensional near-misses gives DIRECT
mean F1 **0.834 / 0.840 / 0.822** — a flat asymptote. Adding more of the same
does not make the task harder; the residual error is not reasoning difficulty.

## Result B — relevance hidden (n=30/cell)

Load-bearing dimensions no longer enumerated; the model must classify each
dimension as physical setup vs recording procedure from a stated rule.

```
lvl  src nm | DIRECT f1  misF1 | RAKL f1  misF1 | delta_f1   p     | mech_f1
R0    10  5 |   0.792    0.752 |  0.770   0.705 | -0.0214  0.422   | 0.78
R1    14  6 |   0.789    0.702 |  0.770   0.639 | -0.0188  0.465   | 0.77
R1b   16  8 |   0.777    0.668 |  0.795   0.739 | +0.0181  0.483   | 0.80
```

**Both arms collapse onto the mechanical baseline** (deltas vs mech: +0.009,
+0.014, −0.026 for DIRECT; −0.012, −0.004, −0.007 for RAKL). With relevance
hidden, GLM-5.2 does not perform the relevance step — it falls back to naive
all-dimension matching. That is a genuine capability finding, and it means this
configuration also cannot discriminate: both arms are executing the same
heuristic.

## What this licenses

**Normalization-only RAKL shows no measurable benefit in any of six
configurations** (~540 runs). Deltas: −0.025, −0.003, −0.009, +0.018, −0.021,
−0.019, +0.018. All p > 0.39, no trend with difficulty, direction inconsistent.

**Not** licensed:
- No claim about RAKL as a whole. The treatment is *normalization only* — a
  deliberately narrow operationalization. Selective retrieval, experience
  conditioning and typed authority remain untested.
- Not a proof of no effect. n=30/cell leaves deltas below ~0.05 mean F1
  undetectable.
- Result B's null is weaker than Result A's, because both arms sat at the
  mechanical baseline — an instrument at its floor is uninformative in the same
  way one at ceiling is.

## The pointer this gives Paper II

When relevance is stated, the model reasons and normalization adds nothing —
the extraction was never the bottleneck. When relevance is hidden, the model
stops reasoning and normalization still adds nothing — because normalized
coordinates do not say *which* coordinates matter.

Both halves point the same way: if RAKL has value on this task family, it is in
**relevance determination**, not representation. That is a different treatment
and it is the one worth building next.

## Pooled estimate — a precise null, not merely a non-significant one

Seven configurations, inverse-variance pooled (SE recovered from each config's
delta and two-sided p):

| config | delta | p | SE |
|---|---:|---:|---:|
| L1 stated, 8 src | −0.0248 | 0.391 | 0.0289 |
| L2 stated, 14 src | −0.0031 | 0.910 | 0.0274 |
| L3 stated, 20 src | −0.0091 | 0.737 | 0.0271 |
| L4 stated, 26 src | +0.0184 | 0.508 | 0.0278 |
| R0 hidden, 10 src | −0.0214 | 0.422 | 0.0267 |
| R1 hidden, 14 src | −0.0188 | 0.465 | 0.0257 |
| R1b hidden, 16 src | +0.0181 | 0.483 | 0.0258 |

```
POOLED delta (RAKL - DIRECT, mean F1) = -0.0056
  SE 0.0102   95% CI [-0.0256, +0.0144]   p = 0.584
```

**Any true benefit larger than +0.014 mean F1 is excluded at 95% confidence.**
Normalization-only RAKL cannot be helping by more than ~1.4 F1 points on this
task family at this operating point.

This is the difference between "we did not detect an effect" and "an effect of
practically meaningful size is ruled out". Every prior arm comparison in this
repository ran at n=1 (one task, one seed) and could only ever produce the
former; the latter is a result.

Caveat preserved: this bounds the *normalization* treatment only. It says nothing
about selective retrieval, experience conditioning or typed authority, and the
bound applies to this synthetic evidence-integration family, not to the
registered pendulum protocol.
