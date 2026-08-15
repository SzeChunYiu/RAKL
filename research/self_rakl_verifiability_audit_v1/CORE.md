# Are this session's mechanics verifiable? — CORE

**Mostly not.** Of ten mechanics added, five are `INTERNALLY_CONSISTENT_ONLY`: their tests show the
code does what its docstring says, which is not evidence that they measure anything. **Zero have an
executed falsifier. One has a caller outside its own tests.**

The programme's own rule is that conformance is instrument evidence and never utility evidence. That
rule was applied to the RFA controller and *not* to the mechanics built on top of it. This applies
it.

| Mechanic | T R F X C | Grade |
|---|---|---|
| `decide` (frozen chain) | `TRF--` | falsifier registered, unrun |
| interface: ten bindings | `T----` | **internally consistent only** |
| atomicity: five conditions | `T----` | **internally consistent only** |
| bounded node closure: eight conditions | `T----` | **internally consistent only** |
| value-of-audit selection | `T----` | **internally consistent only** |
| question/framework adequacy vectors | `T----` | **internally consistent only** |
| ancestor challenge packet | `TR---` | exercised, unfalsifiable as built |
| observation contract | `TR--C` | exercised, unfalsifiable as built |
| construct-independence gate | `TRF--` | falsifier registered, unrun |
| `SUPPORT_DECLARED` | `-----` | **unimplemented** |

`T` tests · `R` run on real recorded data · `F` registered falsifier · `X` falsifier executed ·
`C` caller outside tests

## The sharpest case

The **question and framework adequacy vectors** — nine coordinates and ten. I transcribed them from
the handoff packet and wrote tests proving they are noncompensatory and that an unrated coordinate
is not a pass. Both tests pass. **Nothing tests that these are the right coordinates**, or that
scoring a question on them predicts anything at all. The same holds for the eight closure
conditions, the five atomicity conditions and the ten interface bindings: each is a list I asserted
and then verified I had implemented faithfully.

That is formalism as a hypothesis written in type declarations. It constrains what can be
expressed. Nothing yet shows that constraining it improves a research outcome.

## The asymmetry worth naming

The **audits** run this session are verifiable and were verified: the question audit, the
construct-dependence census, the power re-analysis, the frontier revalidation, the P4 admissibility
finding. Each reads committed artifacts, is reproducible by a committed script, and several were
attacked and corrected — a false-positive marker fixed here, a denominator bracketed there.

It is the **mechanics** that are unverified. Roughly: the measurements earned their keep; the types
did not.

## What would change each grade

```text
INTERNALLY_CONSISTENT_ONLY            run it against recorded instruments whose outcomes are
                                      known, as the construct gate was
EXERCISED_BUT_UNFALSIFIABLE_AS_BUILT  register a falsifier before the next use, stating what
                                      result would retire the mechanic
FALSIFIER_REGISTERED_UNRUN            execute it — for the construct gate, 12 instrument closures
UNIMPLEMENTED                         implement it, or delete the name so it stops looking
                                      like a mechanic
```

## The recommendation

**Stop adding formalism until the two registered falsifiers are run.** Five untested type-level
mechanics is already more than the evidence supports, and each new one dilutes rather than
strengthens: an obligation nobody has tested against a real instrument is indistinguishable from a
preference.

The construct gate is the one to run first — its falsifier is frozen, its cost is twelve instrument
closures, and it is the only mechanic that has already been shown to catch a real recorded defect
and to miss another.
