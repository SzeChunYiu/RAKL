# Paper V–VI RSHEA literature/mechanism saturation — round 005

Status: **NOT_SATURATED**. This pass changes domains to formal program synthesis, property-directed verification and exact active automata learning. No evaluated outcome is accessed and no authority is granted.

Parent candidate-basis head: `rshea/p5-p6-saturation-round-004@89026784f0f87f52fc2bfc2e84c15fc8944d2f8c`.

## Newly retained load-bearing objects

### CEGIS / syntax-guided synthesis as a direct parent for residual-guided invention

Program sketching and Counterexample-Guided Inductive Synthesis (CEGIS) formalize a loop in which a synthesizer proposes a candidate, a validation procedure finds a counterexample, and the counterexample constrains the next candidate. Syntax-Guided Synthesis (SyGuS) makes the candidate language/grammar itself explicit alongside the semantic specification.

This is a close formal parent to Orion's residual-driven mechanism/formalism invention. Therefore the generic pattern

`candidate -> verifier/falsifier -> residual -> new candidate`

is not itself a novelty claim.

**New requirement for Orion mechanism invention:** benchmark against a CEGIS/SyGuS-style parent whenever the candidate representation can be expressed in a finite/SMT-checkable grammar. The Orion-specific residual, if any, must come from capabilities the parent lacks: typed multi-representation mechanism objects, SEARCH/JUMP/GLUE/LIFT routing across evidence, non-symbolic or mixed scientific evidence, scoped authority governance, explicit negative-history reuse, or improved fully-costed search.

### PDR / IC3: learned clauses that become inductive reachability facts

Property Directed Reachability (PDR/IC3) derives clauses from counterexamples to induction and strengthens successive reachability approximations until a safety property is proved or a counterexample is found. This is stronger than merely recording a local conflict: the learned object can become an inductive blocking fact over an entire frontier.

**Consequence for verified failure-constraint compilation:** add PDR/IC3 as a strongest parent on transition-system safety/reachability families. Distinguish three levels of negative knowledge:

1. failed attempt / warning — no pruning authority;
2. local verified nogood/conflict — scoped pruning authority;
3. inductive invariant/blocking clause — stronger reusable reachability authority inside the exact transition/property scope.

Orion may not promote level 1 into level 2 or level 2 into level 3 without the corresponding proof obligation.

### Angluin L* / active model learning

Angluin's L* learns a regular language using membership queries and equivalence queries with counterexamples. This is a direct parent for an Orion operational-map lane when a finite-state transition/language model is queryable.

**Consequence for operational maps:** compare passive map accumulation with active model learning. When a membership/equivalence-query oracle exists, the problem is not simply `explore more edges`; it is to choose queries that identify the minimal behavior model or expose a counterexample to the current model. The learned model remains an operational representation, not theorem/scientific authority.

### Synthesis over a grammar is an explicit operator-basis test

SyGuS makes the syntax/grammar of allowed candidates a first-class object. Failure of all candidates in a grammar is not failure of the semantic objective; it can indicate that the **candidate language/operator basis is inadequate**.

This maps directly to Self-RAKL's method-basis-gap distinction. A strong implementation should therefore record whether a synthesis failure is:

- `NO_SOLUTION_IN_REGISTERED_GRAMMAR`;
- `VERIFIER_COUNTEREXAMPLE_REFINES_CURRENT_VERSION_SPACE`;
- `GRAMMAR_OR_REPRESENTATION_BASIS_GAP`;
- `CANNOT_CHECK`.

## New candidate

`COUNTEREXAMPLE_GUIDED_MECHANISM_SYNTHESIS` — a proposal-only synthesis mechanic whose candidate language, parent algorithms, verifier, counterexample policy, total cost and grammar-expansion rules are frozen before outcomes. It competes against CEGIS/SyGuS where applicable and against the incumbent Orion residual-guided invention operator basis.

## Round 005 saturation verdict

`NOT_SATURATED`.

New retained semantic objects not present in rounds 001–004:

- CEGIS/SyGuS as a direct parent for residual-guided mechanism invention;
- candidate grammar/version-space as a first-class representation of the invention basis;
- PDR/IC3 inductive blocking facts as a stronger tier above local nogoods;
- active exact model learning from membership/equivalence queries and counterexamples;
- an explicit grammar/basis-gap terminal distinct from semantic impossibility.

These additions materially change mechanism invention, operational-map acquisition and verified negative-knowledge compilation. Implementation remains blocked until these parents and authority levels are packet-bound.
