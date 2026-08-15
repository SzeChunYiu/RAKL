# Why the instruments failed — CORE

Three instruments built this session refuted themselves in a row. This asks whether that is three
accidents or one pattern, whether the pattern is already on the frontier, and whether the question
being asked was the right one.

Machine record: `RESULT.json`. Status: **proposal-only post-hoc reclassification.** Records whose
outcomes were already known are re-read under a lens named after the fact. Diagnostic, never
evidence; nothing is retracted.

## 1. The pattern

```text
POPULATION_INSTRUMENT_MISMATCH
the instrument's predicate was frozen before the population's support for that
predicate was characterised
```

All three failures are the same shape, and **not** the construct dependence this session spent the
day documenting:

| Instrument | How it failed | Support defect |
|---|---|---|
| ARN discriminator | chance aggregate | population heterogeneous by design; opposite-signed strata cancelled |
| construct-independence gate | admitted that instrument | obligation set is all aggregate properties; none conditions on strata |
| question-level probe | vacuous | predicate outside the population's era; no design could satisfy it |

Construct dependence is a property of an instrument — it reads its own construction. This is a
**relation between instrument and population**: the instrument can be perfectly construct-independent
and still learn nothing.

**Freezing does not prevent it.** Freezing prevents outcome-tuning, a different failure. A predicate
frozen against an uncharacterised population is honest and uninformative at the same time — which is
why three frozen instruments failed without a single dishonest step.

## 2. It is already on the frontier, unnamed

Re-reading all 38 frontier records for support markers — ceiling below gate, designed floor, below
MDE resolution, capability floor, outside domain:

| Family | n |
|---|---|
| `NEITHER` | 16 |
| `CONSTRUCT` | 10 |
| **`SUPPORT`** | **9** |
| `BOTH` | 3 |

**12 of 38 carry the support signature** — comparable to the construct cluster, and larger than it
if the overlap is counted on both sides. The audit's coordinate mapping scattered these across
`EVIDENCE` and `MEASUREMENT`, which is why the cluster analysis found only one shape.

The nine support-only records name themselves plainly: a packet below MDE resolution, a lift with
no transfer at 0.5B, a ceiling below its own gate, a deliberately tight resource floor, an arm
unconstructible under the shipped API, a specification with no executable binding point.

## 3. The framework already owns the missing check

The observation contract computes exactly this, before an epoch is spent:

```text
Recall_G(E_Ω) ≤ |G_Ω| / |G|
```

*What can be reached at all under this contract?* The programme has had that mechanic since #726 —
**merged by this session, hours before it froze three instruments without applying it to any of
them.**

Nothing in the framework requires it. That is the gap: not a missing verdict, but a missing
**precondition**.

```text
SUPPORT_DECLARED  — before an instrument is frozen, declare
  (a) the population it will run on
  (b) whether the predicate is in that population's domain
  (c) the conditioning variables the population is known to carry
  (d) the reachable ceiling for the statistic
undeclared support is an unrun check, exactly as an undeclared construct obligation is
```

**Deliberately not implemented.** Naming a precondition after three failures it would have caught is
proposal-side; folding it into the construct gate, whose falsifier is already frozen, is the
post-hoc amendment the invariants forbid. It belongs to a v2 with its own freeze.

## 4. Was the question right?

| | |
|---|---|
| asked | *which instrument closes this open item?* |
| skipped | *does this population admit any instrument for this predicate?* |

**The task was correct; the ordering was wrong.** Every one of the three failures is the prior
question going unasked, and each was answerable cheaply at design time — a per-stratum split on a
column the corpus already carried, an existing instrument the gate could have been tested against,
one `git log` on the module defining the vocabulary. None required new data, compute or authority.

This also reframes the four "actionable" items from the open-items run. They were called actionable
because no resource or authorization blocked them. Support was never checked, and for at least one
— the question-level probe — the population could not have supported the instrument at all. *No
blocker* is not the same as *feasible*.

## 5. What the chain already does right

Given a support failure, the frozen chain returns `CANNOT_CHECK` on an `EVIDENCE` cause under a
resource bound. It correctly routes responsibility away from the mechanic and abstains rather than
blaming the instrument. The verdict semantics were never the problem — the framework just never
required the check that would have stopped the instrument being spent.

## Reproduce

```bash
python research/self_rakl_failure_pattern_v1/run_failure_pattern.py
```
