# RAKL Research Memory Architecture

RAKL should accumulate **experience**, not merely accumulate candidate files.

The research system therefore keeps four complementary planes. They answer different questions and must not be collapsed into one scalar memory.

## 1. Knowledge / proof DAG — what is currently known?

Stores exact statements, dependencies, verified lemmas, refutations, open obligations and root closure state.

This is the truth/dependency plane. It must not be polluted by unverified heuristics merely because they were useful during search.

## 2. Scoped research tool inventory — what has worked?

A successful proof step, construction, representation change, falsifier, reduction, compiler, decomposition, invariant, search tactic or experimental discriminator may become a reusable `ResearchTool`.

Promotion is not automatic. The tool must state:

```text
source atom / candidate / result
source context hash
tool abstraction and operation
preconditions
structural signature
guaranteed effects
non-guarantees
validation obligations
evidence / proof backing
known failure ids
successful reuse ids
```

A success is local until scope is understood. `worked_once` does not mean `universally_valid`.

Future reuse requires a `ToolApplicabilityWitness` matching target preconditions/structure and reviewing known failure history. A changed context normally requires target-specific validation even for a strong tool.

## 3. Global failure experience lattice — what has failed and why?

Every material failure/refutation becomes a `FailureExperience` bound to its atom, candidate, context packet and public research trace.

The lattice separates:

- observation: what actually failed;
- diagnosis: why it may have failed;
- scope: where that diagnosis is claimed to apply;
- recurrence: where similar failure structures reappear;
- repair: what changes have escaped the failure;
- meta-gap: whether repeated unclassified failures expose a missing ontology or method family.

A local failure is never a global blacklist. Reusing an affected method requires a difference/scope witness and a targeted repeat-failure test. Only a verified impossibility result can block reuse, and only in its registered scope.

## 4. Public research trace — how did the state change?

The hash-chained `MathResearchTrace` records the chronology connecting context, experience and candidate actions.

The trace exposes reproducible research decisions without pretending to expose private model chain-of-thought. It records:

```text
current state / context
atomization result
analogy and method-transfer review
expert objections
success-tool and failure-lattice review
alternatives considered
concise evidence-grounded selection rationale
candidate/falsifier/result
uncertainty and residual
next action
artifact pointers and hashes
```

## 5. Metacognition — is the memory system itself missing something?

`src/rakl/metacognition.py` sits above the four planes.

Repeated failures that fit known classes should route back to known fibers/tools. Repeated **unclassified** residuals may indicate:

- missing structural coordinate;
- missing failure class;
- missing representation;
- missing research operator;
- missing discriminator;
- an epistemic cut that the incumbent method basis cannot cross.

Those cases become new RAKL child problems about the framework/method basis itself rather than being hidden under `other` or answered with more random candidate generation.

## Dual experience loop

```text
active atom
-> freeze context / analogues / method transfers
-> query success-derived tool inventory
-> query global failure lattice
-> run expert review
-> freeze public memory review + next-step trace
-> generate candidate
-> cheapest falsifier first
-> result

if success:
    -> update proof/knowledge DAG
    -> if reusable, distill scoped ResearchTool
    -> register preconditions, guarantees, non-guarantees, failures

if failure:
    -> preserve local result
    -> generate/test competing diagnoses
    -> add FailureExperience + typed links
    -> update global failure portrait
    -> reopen context or metacognitive gap if needed

-> recurse
```

## Why success and failure are asymmetric but complementary

A verified theorem/proof step may give truth authority to an exact statement. A reusable tool is a different claim: that a method can transfer under specified conditions. This requires scope and applicability evidence.

A failed candidate gives negative evidence about one attempted method/context pair. A reusable failure lesson is a different claim: that a recognizable failure mechanism recurs under specified conditions. This requires diagnosis and scope evidence.

Therefore neither `success -> universal tool` nor `failure -> universal ban` is allowed.

## Global research portrait

At any point a researcher should be able to inspect:

- current proof DAG and smallest open atoms;
- reusable tools ranked by structural fit and authority;
- dominant failure families and broken assumptions;
- methods with both successes and failures, partitioned by context;
- unresolved diagnoses;
- known repairs and escape conditions;
- repeated epistemic cuts;
- missing method-basis / ontology candidates;
- the chronological trace explaining why the current next step was selected.

This turns research history into a cumulative, auditable learning system instead of a folder of disconnected attempts.
