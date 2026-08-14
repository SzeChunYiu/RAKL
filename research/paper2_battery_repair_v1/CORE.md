# Battery repair v1 — B3 shuffled-gold measures abstention, not leakage

Read-first. Detail in this directory; raw receipt in `KNOWN_ANSWER_RECEIPT.json`.
Proposal-only. Grants no scientific authority.

> **Correction.** An earlier version of this package claimed the v3/v4 receipts
> were missing from their branches. That was a false positive from reading stale
> local refs; the receipts were present on the pull-request heads and are on
> `main`. See `../paper2_external_corpus_v1/RETRACTION_01.md`. The re-executions
> stand as an independent reproduction — byte-identical to the committed receipts.

## The finding

The registered B3 probe shuffles gold and re-runs the primary paired statistic;
an instrument is declared `BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE` if the
statistic still clears the MDE. Under the frozen scoring map the statistic it
uses cannot measure that.

With `p(ACCEPT)=0.98`, `p(REJECT)=0.02`, `p(CANNOT_CHECK)=0.5`, and a shuffle
that preserves 50/50 balance (guaranteed here: every ARN row contributes exactly
one gold-ACCEPT and one gold-REJECT pair, so any permutation of the gold column
leaves the balance exact):

| the arm answers | expected Brier under shuffled gold |
|---|---|
| ACCEPT | `0.5*(0.98-1)^2 + 0.5*(0.98-0)^2 = 0.4804` |
| REJECT | `0.5*(0.02-1)^2 + 0.5*(0.02-0)^2 = 0.4804` |
| CANNOT_CHECK | `0.5*(0.5-1)^2 + 0.5*(0.5-0)^2 = 0.25` |

The two decisive rows are equal, so expected Brier is independent of the arm's
accept rate *and* of its accuracy. An arm abstaining at rate `r` therefore scores
`0.4804 - 0.2304*r`, and

    E[B3 advantage] = 0.2304 * (r_witness - r_control)  + single-shuffle noise.

B3 is a measurement of **differential abstention**. It is neither sound (an arm
that cannot read gold fails it by abstaining) nor complete (a leak smaller than
the abstention term is masked).

## The repair

`src/rakl/battery_probes.py::b3_prime` scores only pairs on which *both* arms are
decisive. The abstention term vanishes identically; a leaking arm keeps leaking
on every pair it answers, so the leak signal is untouched. The probe narrows its
population, it does not lower its threshold, and it is fail-closed: no jointly
decisive pair means `CANNOT_CHECK` and `fires=True`, never a pass by absence.

## Known-answer validation (two-sided, 14 tests, all passing)

`tests/test_b3_abstention_confound.py`. No-alarm case asserted first and at every
swept rate.

| arm | condition | B3 original | B3 fires | B3' | B3' fires |
|---|---|---|---|---|---|
| zero label dependence | r=0.0 | -0.0087 | no | -0.0087 | no |
| zero label dependence | r=0.2 | 0.0293 | no | -0.0070 | no |
| zero label dependence | **r=0.4** | **0.0725** | **YES (false alarm)** | -0.0095 | no |
| zero label dependence | **r=0.6** | **0.1214** | **YES (false alarm)** | 0.0047 | no |
| planted leak | q=0.3, r=0 | 0.1177 | yes | 0.1177 | **yes** |
| planted leak | q=1.0, r=0 | 0.4588 | yes | 0.4588 | **yes** |
| leak masked by abstention | q=0.6, r=0.4 | 0.2417 | yes | 0.2559 | **yes** |
| leak masked by abstention | q=0.3, r=0.6 | 0.1749 | yes | 0.1130 | **yes** |

The no-leak arm's decision is `sha256(pair identity)`; gold is never one of its
inputs, so its zero label dependence is structural, not estimated.

## Closure on the executed lineage

ARN v4 (`results_v4_reducer/`) terminated at
`NEGATIVE__BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE` on B3 advantage `0.1347`.
Its measured `CANNOT_CHECK` rate on CONFIRM is `0.5629`; the identity predicts
`0.2304 * 0.5629 = 0.1297`, against a single-shuffle noise sd of about `0.012`.

**v4's battery failure is accounted for by differential abstention alone.** It is
not evidence of label leakage, and the `INSTRUMENT_NOT_PROBATIVE` reading of that
terminal is withdrawn as unsupported.

ARN v3 (`results_v3_reducer/`) has `r = 0.0123`, predicting `0.0028` against a
recorded `0.0044` — its B3 pass was never at risk from the confound.

## What this does and does not license

- **Does**: read v4's terminal as a diagnosed instrument defect rather than a
  measured non-probative instrument; use `b3_prime` in successor epochs.
- **Does not**: promote v4, reverse any confirmatory terminal, or touch v1/v3's
  `NEGATIVE__CAPABILITY_ABSENT`, which did not turn on B3. Re-reading v4 requires
  executing the full battery under `b3_prime` in a new versioned epoch; nothing
  here rescores a frozen artifact.
- The original B3 receipts stay verbatim. This is a successor probe, not an edit.

## Files

| file | contents |
|---|---|
| `KNOWN_ANSWER_RECEIPT.json` | machine-readable sweep, both arms, executed-lineage closure |
| `../../src/rakl/battery_probes.py` | derivation in the module docstring; `b3_prime`, `abstention_confound` |
| `../../tests/test_b3_abstention_confound.py` | the 14 known-answer tests |
| `../paper2_external_corpus_v1/results_v3_reducer/` | reproduced v3 receipt |
| `../paper2_external_corpus_v1/results_v4_reducer/` | reproduced v4 receipt |
