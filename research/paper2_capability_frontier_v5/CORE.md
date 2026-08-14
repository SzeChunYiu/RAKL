# ARN v5 multi-family epoch — the learned-extractor successor does not discharge the residual

Read-first. Protocol: `../paper2_external_corpus_v1/PROTOCOL_V5_REDUCER.json`
(frozen at `a5fc1709`, amended pre-outcome by `AMENDMENT_02.json`).
Receipt: `../paper2_external_corpus_v1/results_v5_multifamily/RESULT.json`.
Proposal-only. Grants no scientific authority.

## Terminal

`NEGATIVE__CAPABILITY_ABSENT`, scope `MULTI_FAMILY`.
Admission `ADMITTED` at `EXTERNAL_LABEL`. Full battery enforced and passing
(B3′ governing, B1, B2, B4, B5). n = 1542 CONFIRM pairs, split by proverb.

Paper II names "a capable learned extractor" as the successor to the
deterministic reducer. That successor was built — spaCy `en_core_web_sm`
dependency parsing for predicate-argument structure, `all-MiniLM-L6-v2` for
vocabulary-independent correspondence — and read in one CONFIRM execution
alongside a vocabulary-masked variant and the strongest calibrated semantic
control. **It does not discharge the residual.** The negative now bounds the
family, not one reducer.

## Threshold-free discrimination (AUC; enters no terminal)

AUC 0.5 = none; < 0.5 = anti-predictive.

| arm | overall | near analogies (n=760) | far analogies (n=782) |
|---|---|---|---|
| `witness_structural_v5` | 0.4295 | 0.4469 | 0.4146 |
| `witness_masked_v5` | 0.4634 | 0.5034 | 0.4251 |
| `control_semantic` (strongest control) | 0.4103 | 0.4412 | 0.3804 |

Every arm is at or below chance, and the far-analogy slice is worse than the
near for all three. Destroying the surface vocabulary by construction
(`witness_masked_v5`) does not recover structure — it reaches chance on the near
slice and stays anti-predictive on the far one. The residual is not "the reducer
was too weak".

## The finding that matters most: G1 is confounded, G2 is load-bearing

| arm | G1 advantage | G1 CI | G1 | valid_accept | false_accept | G2 | AUC |
|---|---|---|---|---|---|---|---|
| `witness_structural_v5` | **+0.0274** | [0.0044, 0.0504] | fail | 0.0013 | 0.0078 | fail | 0.4295 |
| `witness_masked_v5` | **+0.0330** | [-0.0087, 0.0753] | fail | 0.9948 | 0.9896 | fail | 0.4634 |

Both witnesses show a **positive** paired-Brier advantage over the strongest
control, one of them with a CI excluding zero and reaching to 0.0504 against an
MDE of 0.05 — and both are **anti-predictive**. The advantage is not the witness
being good; it is the control being worse. `control_semantic` was selected as
strongest on DEV at 0.5571 exact and falls to 0.4682 on CONFIRM, an 0.089 drop:
its DEV threshold overfits.

**G1 alone would have reported a near-significant win for an arm with AUC 0.43.**
What caught it was G2's two-sided joint property: `witness_structural_v5` sits at
the all-reject corner (accepts 0.13% of valid transfers) and `witness_masked_v5`
at the all-accept corner (false-accepts 99% of invalid ones). Neither is a gate;
both are constants wearing a threshold.

This is a live vindication of Paper II's own probe-C rule — that a false-accept
figure is uninterpretable without its paired valid-transfer retention. Here the
paired form is what stands between the programme and a false positive, and it is
worth reporting as such rather than as a gate that merely failed.

## A second instrument lesson: B2 must compare the pair, not the decision

The registered B2 compares `(decision, structure-signature)` under
character-scrambling. Measured here:

| arm | changed_fraction (registered) | decision-only | verdict |
|---|---|---|---|
| `witness_structural_v5` | 1.000 | 0.0045 | pass |
| `witness_masked_v5` | 1.000 | 0.0097 | pass |

A decision-only text-destruction probe would have reported ~99.5%
scramble-**invariance** for an extractor that demonstrably reads the text —
because a degenerate operating point holds the decision constant under any
perturbation. The parent's tuple definition is doing real work. Recorded because
the first v5 runner implemented the decision-only form; see the deviation note
below.

## Preserved deviation

`results_v5_multifamily_r1_deviation/` holds a first execution whose runner
computed B2 in the decision-only form and did not *enforce* B2, B4 or B5. It
reached the same terminal, but it had not verified a registered probe, so it is
retained as a deviation receipt rather than as the epoch's result. The governing
receipt is `results_v5_multifamily/`, whose battery is enforced throughout.
`results_v5_admission_rejected/` holds the earlier admission rejection that
`AMENDMENT_02` repaired, pre-outcome.

## Scope — what this does and does not establish

- **Does**: bound the residual across a family — lexical, typed-structural,
  predicate-argument, sentence-encoder, and vocabulary-masked correspondence all
  measure at or below chance on third-party labels at n=1542, with no power
  excuse and a battery that passes. The objection "you only tried a weak
  reducer" is discharged.
- **Does not**: establish that no reducer can recover the contract's coordinates
  from natural artifacts; that frontier-scale extraction fails; or anything about
  the contract's soundness, which this epoch does not measure.
- The named successor now owed is a reducer whose correspondence is **not
  monotone in similarity**. Every functional executed to date is, and ARN builds
  its distractors to be surface-similar to the query while far analogies share
  only abstract structure, so similarity-monotone functionals are driven the
  wrong way exactly where transfer is hardest.
- A per-slice sign flip would exceed chance on this corpus. It exploits the
  corpus construction rather than measuring analogical structure and was
  forbidden in the protocol before outcome access. It was not run.

## Contamination

Both trained components may have seen ARN (public since 2023-10). The
declaration applies symmetrically to the witnesses and to `control_semantic`,
which uses the same encoder — contamination inflates them together and cannot
manufacture the witness-over-control advantage that is the registered statistic.
