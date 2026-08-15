# Construct-independence admission gate v1 — CORE

The third admissibility question, implemented: **does an instrument read its target through a
channel independent of whatever generated or graded it?**

Implementation: [src/rakl/construct_independence.py](../../src/rakl/construct_independence.py).
Tests: `tests/test_construct_independence.py`. Validation against recorded instruments:
`VALIDATION.json`.

Status: **pursuit-side plugin, validated with one known miss.** Admission means an instrument's
construct claims are checkable, not that its results are true. Grants no authority.

## Why

The negative frontier's dominant shape is 18 of 38 terminals dying the same way. The programme
already gates falsifiability (*can the gate fail?*) and ceiling (*can it express an effect above
the MDE?*). Neither asks the construct question, and a census of 248 registered instrument designs
found it written down in 15–21% of them — with author separation declared by none.

## The four obligations

```text
CHANNEL_SEPARATION   no answer-correlated field reaches any arm through a channel
                     other than the one under test
AUTHOR_SEPARATION    generator/renderer and extractor/grader do not share an author
GOLD_INDEPENDENCE    gold is a function of substantive state alone, never of the candidate
PERMUTATION_NULL     the reported statistic must die under label shuffling
```

Verdicts are `ADMISSIBLE` / `INADMISSIBLE` / `CANNOT_CHECK`, and the ordering is fail-closed in two
directions:

- an **undeclared** obligation yields `CANNOT_CHECK`, never a pass — an unrun check is an unrun
  check, and `PERMUTATION_NULL` satisfied without a witness counts as unrun;
- a **violated** obligation outranks a missing one, because an instrument shown to read its own
  construction is inadmissible whether or not its other checks ran.

`PERMUTATION_NULL` is checked twice over: a statistic that *survives* shuffling is reading something
other than the labels (the ARN v2/v4 defect), and a statistic *indistinguishable from its own null*
cannot express what it reports.

## Validated on real instruments, not fixtures

| Instrument | Recorded outcome | Gate verdict | |
|---|---|---|---|
| ARN v2 deterministic reducer | `BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE` | `INADMISSIBLE` | ✅ caught |
| P2 prose-transfer confirmatory | probative; scrambling collapses 0.9722 → 0.2500 | `ADMISSIBLE` | ✅ no false alarm |
| ARN local-vs-parent discriminator v1 | `DISCRIMINATOR_NOT_PROBATIVE` | `ADMISSIBLE` | ❌ **missed** |

**2 of 3.** The no-alarm case matters as much as the catch: a gate that flags everything gets
switched off.

## The miss, stated plainly

The gate **admits** this session's own ARN discriminator. Its best statistic sits far enough from
chance to clear the separation check and dies under shuffling as required, so all four obligations
pass — and the instrument is still not probative, because its aggregate is opposite-signed strata
cancelling (high-similarity band 0.396, low-similarity band 0.612 on the same feature).

No registered obligation can see that. The missed class is **stratum cancellation**, and the
candidate fifth obligation is:

```text
STRATUM_HOMOGENEITY   registered blocking factors declared before execution, with the
                      statistic reported per stratum as well as in aggregate
```

**It is deliberately not implemented here.** The forward falsifier frozen for this gate covers the
four obligations as registered. Adding a fifth after seeing the miss, without re-freezing, is the
post-hoc amendment the programme's own invariants forbid. It belongs to a v2 with its own freeze.

## Integration

No second decision chain. Verdicts project into the existing `AuditResidual` and run through the
frozen `decide()`:

| Verdict | Coordinate | Chain returns |
|---|---|---|
| `INADMISSIBLE` | `MEASUREMENT` | `REVISE_MEASUREMENT` |
| `CANNOT_CHECK` | — (resource bound) | `CANNOT_CHECK` |
| `ADMISSIBLE` | — | `SOLVE_CURRENT` |

## Standing falsifier

Unchanged from the cluster research that specified this gate: over the next 12 instrument closures,
if the construct-defect rate is **not** lower among designs declaring all four obligations, the gate
is unnecessary and the cluster is a coincidence of naming. That test is not yet due.

## Reproduce

```bash
python research/construct_independence_gate_v1/run_validation.py
```
