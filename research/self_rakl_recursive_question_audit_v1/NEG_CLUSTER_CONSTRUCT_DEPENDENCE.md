# Negative-cluster research: construct dependence

Recursive step on the dominant cluster found by the question audit (`CORE.md` §3). The cluster is
treated here as a research object in its own right, not as 18 separate repairs.

Machine records: `CONSTRUCT_INDEPENDENCE_CENSUS.json` (measurement),
`AUDIT_RESULT.json` (cluster derivation). Status: **proposal-only**; no mechanic is promoted.

## 1. Object

> **Construct dependence.** An instrument reads something other than its target because the target
> signal and whatever generated or graded it share a channel or an author.

Not a synonym for "the instrument failed". It is a specific, pre-execution-checkable property of an
instrument's *design*, distinct from the two admissibility questions the programme already asks:

| Question | Asks | Registered? |
|---|---|---|
| falsifiability | can the gate fail at all? | yes (P2 gate audit) |
| ceiling / expressibility | can it express an effect above the MDE? | yes — `instrument_admissibility.py` |
| **construct independence** | **does it read its target through an independent channel?** | **no** |

The repository states the shape itself, unprompted, in `research/paper3/PAPER3_TRACK_A_REGISTRATION_V1.md`:
a design in which the answer is written and the witness reads it back would be *"the same
self-grading defect this repository has now hit six times."*

## 2. Evidence: the check is not registered anywhere

A census over every tracked, in-scope instrument-design artifact — `PROTOCOL` / `CONTRACT` /
`FROZEN` / `REGISTRATION` / `SPEC` files under `research/`, `experiments/`, `publication/`,
excluding goal contracts, ledgers, prompts and manifests — asks only what each design *declares
before execution*. **No outcome label is read, so the census cannot be circular with the cluster
that motivated it.**

```text
artifacts in scope                       248
declaring any construct-independence control   38   (15%)
```

| Control family | Declared in |
|---|---|
| label permutation / shuffle null | 21 |
| negative control / sham / placebo | 16 |
| blind or held-out grader | 6 |
| input corruption / scramble | 4 |
| gold independence | 2 |
| **author separation** | **0** |

Author separation is declared by **no registered design**, although "renderer author ≠ extractor
author" is the frontier's own named lever for the template-inversion negative
(`NEG-p2-template-inversion.md`). The two controls that map most directly onto the dominant failure
sub-shapes — gold independence and author separation — are the two that are effectively absent.

*Checker validated before reporting.* Hits were read individually: `E_SHAM_LESSON`, a preregistered
paired permutation test, `MAP04_SHUFFLED_STRUCTURE_NULL`, "two independent annotations plus
adjudication". One false positive was found and fixed — `separate authorization` matched an
`author_separation` pattern lacking a word boundary — which is why that family now reads 0 rather
than 1. Non-hits were sampled and genuinely declare no control.

## 3. Candidate mechanic (proposal-only, not built)

A **construct-independence admission gate**, applied to an instrument's frozen design *before* the
epoch is spent, beside the existing ceiling gate. Four obligations, each already demonstrated
somewhere in the programme as one-off practice:

```text
CHANNEL_SEPARATION   no answer-correlated field reaches any arm through a channel
                     other than the one under test
AUTHOR_SEPARATION    generator/renderer and extractor/grader do not share an author
GOLD_INDEPENDENCE    gold is a function of substantive state alone, never of the candidate
PERMUTATION_NULL     the reported statistic must die under label shuffling
```

Verdicts mirror the existing gate: `ADMISSIBLE` / `INADMISSIBLE` / `CANNOT_CHECK`, with
`CANNOT_CHECK` for an undeclared obligation — an undeclared control is an unrun check, not a pass.

**It already discriminates when run.** Five frontier records were caught by exactly these checks:
shuffle controls killed ARN v2 and v4, a scramble control validated the prose instrument's text
reading, the coordinate-ablated-twin circularity attack rejected its own generator.

## 4. The retrospective test is UNDERPOWERED — declared, not run

The tempting test — do instruments that declared a control close construct-defective less often? —
cannot be run honestly on this frontier:

```text
frontier records in the construct cluster                13
   ... with a pre-execution design artifact on disk       4
```

Four exposed units cannot separate the hypothesis from chance, and scoring the other nine from
their post-mortems would read the outcome into the predictor — the very defect under study. Filed
as `UNDERPOWERED`, not as a null.

## 5. Frozen forward falsifier

Registered now, before any gate is built, so it cannot be tuned to the result:

> Over the next 12 instrument closures, partition by whether the frozen design declared all four
> obligations. If the construct-defect rate is **not lower** among instruments that declared them,
> the gate is unnecessary and this cluster is a coincidence of naming rather than a mechanism.

Failure of that test is a real outcome for this line, not a prompt to redefine the cluster.

## 6. What this does not claim

No mechanic is promoted; nothing here is scientific or method-promotion authority. The census is a
measurement of declaration practice, not of instrument quality: a design that declares a control
may still be defective, and one that declares none may be sound. The 15% figure bounds how often
the programme *writes the check down* — nothing more.

## Reproduce

```bash
python research/self_rakl_recursive_question_audit_v1/run_construct_independence_census.py
```
