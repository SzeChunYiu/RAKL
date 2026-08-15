# Self-RAKL recursive question audit v1 — CORE

**Question.** The programme carries persistent negatives across Papers I–IV. Are we asking the
wrong question?

**Answer.** From this evidence, no — and the evidence cannot say otherwise, which is itself the
finding. Machine record: `AUDIT_RESULT.json`. Source: `research/negative_frontier_v1/` (38
terminals, each traced to a verified receipt).

Status: **retrospective diagnostic, proposal-only.** The coordinate mapping was applied after the
outcomes were known. It grants no scientific or method-promotion authority, and it is not a
preregistered test.

## 1. Where the negatives actually localize

Every one of the 38 frontier records was mapped to a pursuit coordinate by an explicit rule table
(emitted in `AUDIT_RESULT.json` under `mapping_rules`, so the mapping can be attacked without
re-deriving it), then run through `rakl.recursive_framework_audit.decide`.

| Coordinate | Records | What it means |
|---|---|---|
| `EVIDENCE` | 17 | capability floor, resource envelope, power, absent independence, missing artifact |
| `MEASUREMENT` | 14 | the observation operator measured its own construction |
| `EVALUATOR` | 4 | the gate could not fail, or could not express what it gated |
| `DECOMPOSITION` | 1 | loss localized to one stage |
| `FRAMEWORK` | 1 | a parent verdict imported without its preconditions |
| `INTERFACE` | 1 | specification with no executable binding point |
| `QUESTION` | **0** | — see §2 |

Programme-level decision over all six implicated coordinates: **`RUN_DISCRIMINATOR`**. The frozen
chain refuses revision while more than one responsibility level is plausible. Reframing the
programme's question right now would be a revision without a discriminator — the framework's own
`FALSE_REFRAME_HARM` case.

## 2. The zero on QUESTION is a `CANNOT_CHECK`, not a clean bill

The inventory attributes *execution-stage* failure. Its attribution vocabulary has seven stems —
instrument-construct, capability, licence/abstention, hardware/environment, extraction, power,
mapping — and **none of them is question-level**. A search of every record's attribution, lever and
narrative for question-level language returns **zero hits**.

So a question-level cause could not have been recorded even if one were present.

```text
QUESTION coordinate verdict:
CANNOT_CHECK__SOURCE_VOCABULARY_CANNOT_EXPRESS_THE_COORDINATE
```

Reading `QUESTION: 0` as "the question is fine" would be exactly the error the programme keeps
catching in its own instruments: concluding from a measurement that cannot express the effect.
Deciding the question coordinate needs an instrument built to express it — that is the
discriminator §1 is asking for, and it does not exist yet.

## 3. What the frontier does say: one failure shape, 18 times

The `MEASUREMENT` and `EVALUATOR` records — **18 of 38** — are not 18 unrelated defects. They are
one shape in eight variants: *the instrument reads something other than its target, because the
target signal and the thing generating or grading it share a channel or an author.*

| Sub-shape | n |
|---|---|
| the answer shares a channel with the input | 3 |
| a statistic survives label shuffling | 3 |
| generator and evaluator share an author | 2 |
| gold is a function of the candidate | 2 |
| the gate cannot express the effect it gates | 2 |
| the comparator is an oracle, not a weaker parent | 1 |
| a registered arm is unconstructible | 1 |
| the abstention option is unreachable | 1 |

Under principle 30 (*repeated failure constrains invention*), a residual structure this stable
across distinct failures specifies what a missing operator must do — it is not 18 separate repairs.

**The check already works when it is run.** Five of these were caught by an explicit control:
shuffle controls killed ARN v2 and v4, a scramble control validated the prose instrument's text
reading, and the coordinate-ablated-twin circularity attack rejected its own generator. The
mechanic exists in one-off form; it is not a registered gate.

**The gate that exists covers something else.** `src/rakl/instrument_admissibility.py` is an
oracle-*ceiling* gate — can the instrument express an effect above the MDE — with one caller. It
does not ask whether the instrument reads its target through an independent channel. Ceiling and
construct independence are different admissibility questions, and only the first is registered.

## 4. The ancestor challenge that is nearly, but not, admissible

The ARN extraction lineage is the strongest ascent candidate on the frontier: three distinct
repaired reducer families (v2 deterministic, v3 instance-paired, v4 relational) all closed negative
against the same parent abstraction, *prose-level structural extraction by an admissible reducer*.

```text
frozen two-failed-families rule  -> ASCEND
complete challenge packet        -> False
escalation_admissible            -> False
```

Three failed local repairs establish that the local level is not responsible. They do not separate
parent from child. The packet is missing exactly one field — a registered local-vs-parent
discriminator — and without it, ascending would be promoting repeated raw failure into a
parent-level verdict.

## 5. What this licenses next

Proposal-only; none of this is authorized by this audit.

1. **Register a construct-independence admission gate** beside the existing ceiling gate: author
   separation, channel separation, and a shuffle-survival control, checked *before* an instrument
   is spent rather than after it fails. Five frontier records show the check discriminating; 18
   show what it costs to skip.
2. **Build the local-vs-parent discriminator for the ARN lineage.** It is the one missing field
   between the strongest negative on the frontier and an admissible ancestor challenge.
3. **Only then ask the question question.** An instrument whose vocabulary can express a
   question-level cause is the discriminator the programme-level `RUN_DISCRIMINATOR` is demanding.
   Until it exists, the honest status of "is the question right?" is `CANNOT_CHECK` — not yes.

## Reproduce

```bash
python research/self_rakl_recursive_question_audit_v1/run_self_audit.py
```
