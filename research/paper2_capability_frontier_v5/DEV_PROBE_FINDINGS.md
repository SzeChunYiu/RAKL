# ARN v5 DEV probe — findings before protocol freeze

Status: DEV-split only (648 pairs). CONFIRM (1542 pairs) untouched.
Proposal-only. Grants no scientific authority. No terminal is filed by this file.

## F0. RETRACTED as stated — the receipts were present; the run reproduces exactly

**Retracted.** This section originally claimed the v3/v4 receipts were missing
from their branches. That check was run against stale local refs; against
`refs/pull/703/head` and `refs/pull/707/head` both receipts are present, and all
of `results_v2_reducer/`, `results_v3_reducer/` and `results_v4_reducer/` are on
`main`. See `../paper2_external_corpus_v1/RETRACTION_01.md`.

What stands is the reproduction: re-executing the committed v3 runner against the
committed corpus reproduces the PR's figures, and the resulting RESULT.json is
byte-identical to the one on `main`.

| quantity | PR #703 body | re-execution |
|---|---|---|
| B3 shuffled-gold advantage | 0.0044 | 0.004395 |
| B3 CI | [-0.029, 0.038] | [-0.028601, 0.038014] |
| witness confirm exact | 0.495 | 0.495460 |
| band control confirm exact | 0.506 | 0.506485 |
| terminal | NEGATIVE__CAPABILITY_ABSENT | NEGATIVE__CAPABILITY_ABSENT |

Reading: an independent reproduction of the v3 epoch, on a different host and
install from the one that produced the original.

## F1. The fitted operating point is the all-reject corner

DEV sweep of theta_w over the frozen grid 0.05..0.95 for the v3 instrument:

| theta_w | accept rate | CANNOT_CHECK | decidable exact | valid_accept | false_accept | G2 |
|---|---|---|---|---|---|---|
| 0.05 | 0.898 | 0.015 | 0.4796 | 0.877 | 0.920 | no |
| 0.10 | 0.395 | 0.015 | 0.4263 | 0.321 | 0.469 | no |
| 0.15 | 0.117 | 0.015 | 0.4953 | 0.111 | 0.123 | no |
| 0.45 (fitted) | 0.000 | 0.015 | 0.5016 | 0.000 | 0.000 | no |

**No theta_w on the frozen grid attains G2 on DEV.** The fitted theta_w = 0.45
yields accept rate exactly 0.000 in all four confirm quadrants.

This is *not* only an operating-point artifact: on DEV the v3 score is
**anti-correlated with gold** — mean score 0.0849 on gold-ACCEPT pairs versus
0.0992 on gold-REJECT pairs. Re-fitting the operating point cannot repair a
score whose discrimination is below chance. The operating-point rule is a real
protocol defect, but it is not the binding one.

## F2. Every similarity-typed correspondence functional is at or below chance

Threshold-free discrimination (AUC) on DEV, gold-ACCEPT vs gold-REJECT.
AUC 0.5 = no discrimination; < 0.5 = anti-predictive.

| # | correspondence family | AUC (all) | AUC near | AUC far |
|---|---|---|---|---|
| S0 | whole-narrative sentence-encoder cosine (strongest calibrated semantic control) | 0.4725 | 0.516 | 0.400 |
| S1 | frozen-anchor trajectory profile cosine | 0.4633 | — | — |
| S2 | predicate-argument triple, instance-paired greedy, embedding correspondence | 0.4733 | — | — |
| S3 | trajectory minus surface | 0.5045 | — | — |
| S5 | vocabulary-masked abstraction cosine (surface destroyed by construction) | 0.4551 | 0.486 | 0.404 |
| S6 | outcome-arc polarity delta match | 0.4537 | 0.436 | 0.480 |
| — | v3 typed structural coverage score | anti-correlated (0.0849 vs 0.0992) | — | — |

Encoder: `sentence-transformers/all-MiniLM-L6-v2`. Parser: spaCy `en_core_web_sm`
3.8.0. Contamination declaration owed: ARN public since 2023-10; the encoder's
pretraining corpus is not auditable here. The declaration applies symmetrically
to the witness families and to the S0 semantic control.

**Localization.** The signal is not merely absent, it is sign-controlled by the
corpus's own `analogy_level` axis: mildly predictive on near analogies (0.516)
and strongly anti-predictive on far analogies (0.400). ARN's distractors are
constructed to be surface-similar to the query while the far analogy shares
only abstract structure, so any monotone similarity functional is driven the
wrong way exactly where analogical transfer is hardest.

**Consequence for the named successor.** Paper II names "a capable learned
extractor" as the successor to the deterministic reducer. Six correspondence
families spanning lexical, typed-structural, predicate-argument, sentence-encoder,
vocabulary-masked and outcome-arc constructions are now measured at or below
chance on DEV. The residual is therefore *not* discharged by replacing the
reducer with a learned one of this class. This strengthens rather than repairs
the parent negative.

**What must NOT be done.** A per-slice sign flip (accept the *less* similar
candidate on far analogies) would exceed chance on this corpus. It would be
exploiting the corpus construction, not measuring analogical structure, and it is
forbidden as outcome tuning. It is recorded here so that its absence is
deliberate and auditable.

## F3. B3 shuffled-gold is confounded by differential abstention (derivation)

Under the frozen scoring map (ACCEPT 0.98, REJECT 0.02, CANNOT_CHECK 0.5) and a
shuffle preserving 50/50 balance — guaranteed here, since every ARN row yields
exactly one gold-ACCEPT and one gold-REJECT pair, so any permutation of the gold
column leaves the balance exact — the expectation must be taken over both gold
values *for each decision*:

    E[Brier | answered ACCEPT] = 0.5*(0.98-1)^2 + 0.5*(0.98-0)^2 = 0.4804
    E[Brier | answered REJECT] = 0.5*(0.02-1)^2 + 0.5*(0.02-0)^2 = 0.4804
    E[Brier | abstained]       = 0.5*(0.50-1)^2 + 0.5*(0.50-0)^2 = 0.25

The two decisive rows are equal, so a decisive arm scores 0.4804 **independently
of its accept rate and of its accuracy**. An arm abstaining at rate r scores
(1-r)*0.4804 + r*0.25 = 0.4804 - 0.2304*r. Hence the B3 statistic is

    E[advantage | shuffled gold] = 0.2304 * (r_witness - r_control)   (+ sampling noise)

B3 therefore measures *differential abstention*, not label leakage.

Checks against the executed lineage:
- v3: r = 0.01232 -> predicted 0.00284, observed 0.00440 (single-shuffle noise sd
  on n=1542 is ~0.012). Consistent.
- v4: observed 0.135 -> implied r ~ 0.586.

Consequences: an instrument with no leak at all fails B3 by abstaining, and a
genuine leak smaller than 0.2304*(r_w - r_c) is masked. B3 as registered is
neither sound nor complete for its stated purpose.

Status: **validated two-sided by known-answer test** and filed in
`research/paper2_battery_repair_v1/`. A synthetic arm whose decision is
`sha256(pair identity)` — gold is never one of its inputs — falsely fires B3 at
abstention rates 0.4 and 0.6, and clears the repaired probe at every swept rate;
a planted leak fires both probes at q >= 0.3, including when masked by abstention
at r = 0.6. Executed-lineage closure: v4's measured CANNOT_CHECK rate on CONFIRM
is 0.5629, predicting 0.1297 against a recorded 0.1347.
