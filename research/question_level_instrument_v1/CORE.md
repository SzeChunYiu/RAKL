# Question-level instrument v1 — CORE

**Terminal: `INSTRUMENT_UNINFORMATIVE_ON_THIS_POPULATION__VOCABULARY_POSTDATES_THE_CORPUS`.**
The audit's `CANNOT_CHECK` on the QUESTION coordinate stands, and now has a cause.

The recursive question audit could not measure the QUESTION coordinate because the frontier's
attribution vocabulary has no question-level category. Its programme-level `RUN_DISCRIMINATOR` asked
for an instrument that could. This is the smallest one — covering a single Q subtype, *regime
conflation* — frozen in its own commit before execution, and it fired its own falsifier.

## What was measured

For each of the 38 frontier records, read the **pre-execution design artifacts only** — never the
terminal, the attribution or the narrative — and look for four regime markers: is the acquisition
regime named, are the licensed input sources enumerated, is semantic normalization explicitly
permitted or forbidden, is external knowledge explicitly permitted or forbidden?

| Verdict | n |
|---|---|
| `CANNOT_CHECK__NO_DESIGN_ARTIFACT` | 22 |
| `Q_REGIME_CONFLATION_NOT_EXCLUDED` | 11 → **12** after correction |
| `REGIME_PARTIAL` | 5 → **4** after correction |
| `REGIME_DECLARED` | **0** |

Zero of 16 scored records declare their acquisition regime. Under the frozen two-sided falsifier
that is `INSTRUMENT_UNINFORMATIVE__NO_SCORED_RECORD_DECLARES`: *a marker set that nothing satisfies
measures the marker set, not the designs.*

## Two corrections to the instrument, both reported

**Marker false positives (2).** The frozen probe accepted a bare `regime`, which fired on
*problem*-regime prose — "must not gut the easy regime", "refutes the benefit claim in this regime"
— rather than an acquisition regime. `MARKER_VALIDITY.json` records both with context.

Correcting them moves records from `REGIME_PARTIAL` to `NOT_EXCLUDED`. `REGIME_DECLARED` stays at
zero either way, so **the terminal is unchanged**. The correction can only strengthen the
instrument's negative verdict about itself, never rescue it — which is why applying it after seeing
outcomes carries no incentive problem. `RESULT.json` is preserved exactly as executed.

**The anachronism, which is the real finding.** The observation contract that *defines* acquisition
regimes landed at `2026-08-15T15:21:37+02:00` — the same day this probe ran. Every scored design
predates it. **No record could have declared an acquisition regime even in principle.**

So the instrument is uninformative on this population by anachronism, not because the designs were
careless. It tested a corpus for a property the vocabulary made expressible only after that corpus
was frozen.

## What this actually establishes

The audit's `CANNOT_CHECK` was correct and is now explained rather than merely reported. The
QUESTION coordinate is unmeasurable on the historical frontier because the concept that would make
one Q subtype checkable did not exist while those questions were being registered. That is a
finding about the programme's own vocabulary history, not about the quality of its questions.

It also bounds what any retrospective question-level audit can achieve: **no re-reading of the
existing frontier will recover the QUESTION coordinate.** The coordinate becomes measurable
prospectively or not at all.

## Forward use

Apply to designs authored *after* the observation contract landed. On that population
`REGIME_DECLARED` is reachable and the falsifier becomes informative. The first such designs are
this session's own: the ARN discriminator protocol declares its contract explicitly, and the
construct-independence gate's obligations are declared per instrument.

## Scope limit inherited from the gate

The construct-independence gate cannot certify this probe: `GOLD_INDEPENDENCE` and
`PERMUTATION_NULL` are not applicable to a census with no gold and no statistic, so the gate
returns `CANNOT_CHECK`. That is a **scope limit of the gate** — it was specified for scored
comparisons — declared in this instrument's frozen protocol rather than worked around.

## Non-claims

A `NOT_EXCLUDED` verdict is not evidence that a question *was* malformed; it records that the
design cannot rule the cause out. Excluding one Q subtype would not clear the QUESTION coordinate.
No frontier terminal is retracted, promoted or reinterpreted. Grants no authority.

## Reproduce

```bash
python research/question_level_instrument_v1/run_probe.py
python research/question_level_instrument_v1/run_marker_validity.py
```
