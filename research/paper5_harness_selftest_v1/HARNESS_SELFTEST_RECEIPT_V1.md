# Paper 5 attribution harness — instrument self-test v1

**Status:** `HARNESS_VALIDATED / NOT_A_PAPER5_RESULT`
**Grants scientific authority:** no
**Model invoked:** no
**Date:** 2026-08-11
**Issue:** #254

## What this is, and what it is not

This is the first execution of anything in the Paper 5 four-arm attribution
pipeline. It is **instrument validation**, not evidence about RAKL. No model was
called. Every score below was produced by
`experiments/paper5/selftest_adapter.py`, a synthetic adapter with answers known
in advance.

Nothing here supports any claim about architecture, experience, content or total
lift. The real confirmatory study remains unexecuted and blocked — see
"Why the real study still cannot run" below.

## Why an instrument self-test was needed first

Before this run the pipeline had never executed, so it had never been shown to
report the truth. Two failure modes are invisible from a single run:

- an instrument that can only report **success**;
- an instrument that can only report **null**.

Checking only that the harness stays quiet on null data catches the first and
misses the second. So the self-test runs three frozen modes, and the harness is
trusted only if it recovers the correct answer in all three.

| Mode | Construction | Correct answer |
|---|---|---|
| `NULL_CONSTANT` | score depends on `task_id` alone | every paired delta exactly `0.0` |
| `NULL_NOISE` | one fixed distribution per run, identical parameters for every arm | non-zero realized deltas, intervals covering `0` |
| `PLANTED_LIFT` | `NULL_NOISE` plus a known `+0.20` on `RAKL_LEARNING` only | `+0.20` recovered on the three `RAKL_LEARNING` contrasts, ~`0` on `ARCHITECTURE` |

`PLANTED_LIFT` is the load-bearing one. A pipeline hard-wired to report nothing
passes both null modes perfectly.

## Execution

12 tasks (4 per stratum) x 4 arms. Three modes at 1 repetition (48 runs each) plus
`PLANTED_LIFT` at the preregistered 3 repetitions (144 runs) = **288 runs**.
Driver:

```bash
python experiments/paper5/run_harness_selftest.py --mode <MODE> --out-root <DIR>
python experiments/paper5/run_harness_selftest.py --mode PLANTED_LIFT --out-root <DIR> --repetitions 3
```

Analysis parameters are pinned by the driver rather than inherited from
`analyze_attribution_results.py` CLI defaults, so every interval and p-value
below is reproducible from the driver alone: `bootstrap_seed 20260811`,
`bootstrap_iterations 20000`, `permutation_iterations 100000`, schedule seed
`20260811`. They are recorded in each `selftest_receipt.json`.

The driver chains the real production path — `build_attribution_schedule.py`,
`build_executor_contract.py`, `run_attribution_schedule.py`,
`analyze_attribution_results.py` — so the orchestrator's hash, packet-identity,
per-arm state-identity, non-mutation, output-binding and resource-ceiling checks
were all genuinely exercised.

## Results — mean paired score delta

| Contrast | `NULL_CONSTANT` | `NULL_NOISE` | `PLANTED_LIFT` |
|---|---|---|---|
| `ARCHITECTURE` (RESET − MODEL_ONLY) | `+0.000000` | `+0.1043` | `−0.0541` |
| `EXPERIENCE` (LEARNING − RESET) | `+0.000000` | `−0.0181` | **`+0.2123`** |
| `CONTENT` (LEARNING − SHAM) | `+0.000000` | `+0.0134` | **`+0.2448`** |
| `TOTAL` (LEARNING − MODEL_ONLY) | `+0.000000` | `+0.0862` | **`+0.1582`** |

Interval and permutation behaviour:

- `NULL_CONSTANT` — all four intervals `[0.0, 0.0]`, all `p = 1.0000`. Plumbing,
  task/arm pairing and contrast direction are correct.
- `NULL_NOISE` — all four intervals cover `0`, all `p >= 0.19`. No false positive
  despite realized deltas up to `+0.104`.
- `PLANTED_LIFT` — the planted `+0.20` is recovered on all three
  `RAKL_LEARNING` contrasts (`p = 0.0025`, `0.0012`, `0.0197`) and does **not**
  appear on `ARCHITECTURE`, which compares two arms carrying no offset. The
  effect is attributed to the correct arm.

**Verdict: the instrument reports the truth in both directions.**

## `PLANTED_LIFT` at the preregistered 3 repetitions

At 1 repetition the analyzer's `success = successes > repetitions/2.0` collapses
to `successes > 0.5`, so the majority-vote aggregation the confirmatory packet
depends on is never exercised, and neither is the within-task mean over
generations. Validating the instrument only in a configuration the real study
will not use would leave that rule untested, so `PLANTED_LIFT` was rerun at 3
repetitions:

| Contrast | mean score delta | 95% interval | permutation p | success-rate delta |
|---|---|---|---|---|
| `ARCHITECTURE` | `−0.0079` | `[−0.0572, +0.0458]` | `0.7722` | `+0.0000` |
| `EXPERIENCE` | `+0.2127` | `[+0.1633, +0.2602]` | `0.0005` | `+0.5833` |
| `CONTENT` | `+0.2112` | `[+0.1603, +0.2541]` | `0.0004` | `+0.6667` |
| `TOTAL` | `+0.2048` | `[+0.1366, +0.2663]` | `0.0010` | `+0.5833` |

All three `RAKL_LEARNING` contrasts recover the planted `+0.20` to within
`0.013`, on both the mean-score path and the majority-vote success path, and
`ARCHITECTURE` stays at zero.

## Caveat found at 1 repetition, and resolved at 3

At 1 repetition the `PLANTED_LIFT` `ARCHITECTURE` contrast had a bootstrap
percentile interval of `[−0.1042, −0.0005]` — marginally excluding `0` — while
its permutation `p = 0.0811` did not reject. The two uncertainty procedures
disagreed at the margin.

At 3 repetitions the disagreement disappears: the interval becomes
`[−0.0572, +0.0458]`, covering `0`, at `p = 0.7722`. That confirms it was a
small-sample artefact of a 12-task, 1-generation dry run against a 120-task,
3-generation preregistered packet, not a defect in the analyzer. Both readings
are recorded rather than dropped, and the episode is a reason to read the
permutation `p` and the bootstrap interval together rather than either alone.

## Contamination controls

- Mode is bound by `packet_id` (`paper5-harness-selftest-<MODE>`), not an
  environment variable, so it is covered by the identity the orchestrator already
  cross-checks across task file, schedule and contract.
- The adapter refuses any packet whose ID does not start with
  `paper5-harness-selftest-`, so it cannot be pointed at a real Paper 5 packet.
- Every record carries a `harness_self_test` block.
- `analyze_attribution_results.py` hard-fails on a results file that mixes
  self-test records with model records, or that mixes two self-test modes.
- Every summary produced from self-test records is stamped
  `grants_scientific_authority: false` with a `claim_boundary` beginning
  `HARNESS SELF-TEST ONLY`.
- The synthetic per-arm state hashes are distinct per arm so the orchestrator's
  state-identity and non-mutation checks are exercised, not bypassed. They stand
  for no real RAKL state.

Run artifacts (envelopes, raw outputs, records, analyses) are synthetic and were
deliberately **not** committed to the evidence tree. Regenerate them with the
driver above; `tests/test_paper5_harness_selftest.py` re-executes all three modes
and asserts every number in this receipt.

## Why the real study still cannot run

Instrument validation removes one blocker. Four remain, and none is fixed by this
receipt:

1. **No provider-specific adapter.** `run_attribution_schedule.py` is
   provider-neutral by design and cannot call a model. A real adapter must be
   written and byte-frozen in the executor contract.
2. **No frozen task packet.** The preregistration targets 120 tasks
   (40 repeated-family, 40 cross-domain, 40 hostile-near-miss), disjoint from
   development, frozen before outcome access. None exist.
3. **No sham policy, evaluator or per-arm state hashes.** All must be frozen
   before outcomes; `build_executor_contract.py` requires `--sham-policy-hash`
   for any non-self-test contract.
4. **Learning semantics are upstream-blocked.** Per #138 (2026-08-11T19:36:24Z),
   the Paper V packet must not be frozen around the old learning semantics:
   #238 must be stabilized first, and #242 for any governance claim. Job 3476548
   showed the LEARNING arm used failure-only pseudo-lessons and whole-state
   prompt stuffing rather than verified lessons and selective retrieval.
   Freezing on those semantics would measure the defect, not the method.

A null, harmful or mixed attribution result remains a valid outcome and must be
preserved verbatim when the real study runs.
