# Graded evidence-integration battery v1 — GLM-5.2, n=30 per cell

**Status:** `NON_SEALED_HOSTED_EVIDENCE`. Not the registered Paper II protocol, not
confirmatory, grants no scientific authority. A hosted endpoint is not
weight-attestable. Recorded because it is the first arm comparison in this
project run on an instrument that was *demonstrated* to be able to register a
difference.

## Why it exists

The single pendulum task is at floor for Qwen2.5 0.5B-7B and at ceiling for
GLM-5.2 (30/30 both arms, `paper2_hosted_capability_probe_v1`). It cannot
register an effect of either sign. This battery builds a difficulty gradient
that stresses the one coordinate that was never saturated: evidence-ID binding.

## Design

Procedurally generated evidence-integration tasks. Sources make claims under
context coordinates; only some dimensions are **load-bearing** for the target
question. A source is misaligned only if it differs from the target on a
load-bearing dimension. Ground truth is computed by a verifier over generator
structure — **never** by recording which coordinate was perturbed.

| Level | sources | dims | near-misses |
|---|---|---|---|
| L1 | 8 | 2 | 2 |
| L2 | 14 | 4 | 4 |
| L3 | 20 | 4 | 7 |
| L4 | 26 | 5 | 10 |

- **DIRECT** arm: raw source prose + question.
- **RAKL** arm: same prose plus normalized context coordinates. No target
  comparison, no relevance filtering, no disposition. The model must still
  decide which dimensions bind and apply them.

## Leak controls — run before any delta, run aborts if either fails

1. **Mechanical baseline** — a tag-only all-dimension set-comparison program, no
   LLM. Scores `exact_pass = 0.00` at every level (mean F1 0.79-0.83). The RAKL
   context map alone therefore does not hand over the answer.
2. **Disposition scan** — no per-source verdict appears in either prompt. Zero
   hits at every level.

Both controls caught a real defect in v0 of this battery: the RAKL arm shipped a
precomputed `differing_dimensions` relation, and the mechanical baseline scored
**1.00 exact** — the arm was being handed the label. Dimension relevance was
added so that naive all-dimension comparison fails. A second defect was caught by
inspection: the prompt stated the naive rule while the verifier applied the
relevance rule, so the model was penalised for following instructions. Both fixed
before any comparison was run.

## Result — no RAKL effect, on a validated instrument

```
lvl  src dim nm | DIRECT ex   f1    | RAKL   ex   f1    | delta_f1   p      | mech_f1
L1     8  2   2 | 0.03  0.906      | 0.07  0.881      | -0.0248  0.391    | 0.82
L2    14  4   4 | 0.10  0.870      | 0.17  0.867      | -0.0031  0.910    | 0.81
L3    20  4   7 | 0.03  0.856      | 0.00  0.847      | -0.0091  0.737    | 0.83
L4    26  5  10 | 0.03  0.811      | 0.03  0.829      | +0.0184  0.508    | 0.79
```

Mean delta across levels **-0.0046**; three of four negative; no trend with
difficulty. All p > 0.39.

## Instrument validity

**The difficulty axis works.** DIRECT mean F1 declines monotonically
0.906 → 0.870 → 0.856 → 0.811 (slope -0.030/level), and misaligned-F1 declines
0.911 → 0.834 → 0.801 → 0.734. Difficulty is doing what it was built to do.

**The arms are above the mechanical baseline** at every level (+0.082, +0.060,
+0.031, +0.024), so the model is performing relevance reasoning rather than the
naive rule. This is the sensitivity demonstration the pendulum instrument never
had.

**`exact_pass` remains near-floor (0.00-0.17)** and is the wrong primary
endpoint: it is an all-or-nothing conjunction that discards the graded signal.
Mean F1 is the informative endpoint, exactly as the Paper II power analysis
predicted.

## What this licenses, and what it does not

Licensed: on this synthetic evidence-integration family, at this operating point,
normalized context coordinates alone produce **no measurable benefit** over raw
prose, and the direction is if anything slightly negative.

**Not** licensed:
- No claim about RAKL as a whole. The treatment here is *normalization only* — a
  deliberately narrow operationalization. Selective retrieval, experience
  conditioning and typed authority are untested by this battery.
- No claim about the registered pendulum protocol; this is a different task family.
- Not a proof of no effect. At n=30/cell the observed spread leaves small effects
  (delta < ~0.05 in mean F1) undetectable. Pooling all levels (n≈120/arm) is the
  cheap next step, followed by testing the retrieval and experience arms that this
  battery does not touch.
