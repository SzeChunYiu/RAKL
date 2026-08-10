# Mathematical Research Assurance in RAKL

Status: candidate hardening layer for mathematical discovery  
Date: 2026-08-10  
Scope: theorem discovery, formalization, proof assurance, novelty screening, and long-horizon mathematical research. This document does not claim that RAKL or any LLM can certify global novelty or autonomously solve arbitrary open problems.

## 1. Why solving problems is not the same as doing mathematical research

A model can be very strong at selecting plausible next proof moves while remaining unreliable as a research authority. Mathematical research adds four independent burdens that ordinary problem solving can avoid:

1. **truth** — every load-bearing implication must be valid;
2. **specification** — the proved formal theorem must be the theorem that was actually intended;
3. **novelty** — an equivalent or stronger result must not already exist in the registered literature world;
4. **research value** — a true, apparently new fact must still be worth attention.

RAKL therefore represents mathematical authority as a product of partially ordered coordinates rather than a single confidence score:

\[
\alpha_{\mathrm{math}}(c)=
(A_{\mathrm{spec}},A_{\mathrm{truth}},A_{\mathrm{novel}},A_{\mathrm{value}},A_{\mathrm{trust}}).
\]

No coordinate may silently mint another. In particular,

\[
A_{\mathrm{truth}}\not\Rightarrow A_{\mathrm{novel}},\qquad
A_{\mathrm{novel}}\not\Rightarrow A_{\mathrm{truth}},\qquad
A_{\mathrm{value}}\not\Rightarrow A_{\mathrm{truth}}.
\]

## 2. Typed mathematical research state

For a scoped mathematical program define

\[
\mathfrak M_t=(I_t,F_t,D_t,X_t,P_t,V_t,N_t,Q_t,H^-_t),
\]

where:

- \(I_t\): frozen informal targets, assumptions, notation, domains and intended quantifiers;
- \(F_t\): formal statements and informal-to-formal alignment witnesses;
- \(D_t\): persistent dependency DAG of definitions, lemmas and theorem obligations;
- \(X_t\): counterexamples, failed proof branches and falsification results;
- \(P_t\): candidate proof artifacts;
- \(V_t\): proof-checker receipts, dependency/axiom audits and verifier identities;
- \(N_t\): novelty dossiers and bounded novelty certificates;
- \(Q_t\): research-value/interestingness assessments;
- \(H^-_t\): immutable negative history.

The language model may propose changes to any proposal surface, but only typed gates may change the authority coordinates.

## 3. Promotion states

A claim moves through a non-compensatory state machine:

```text
CONJECTURE
-> COMPUTATIONALLY_SUPPORTED
-> FORMALIZED_UNPROVEN
-> MACHINE_PROVEN
-> BOUNDED_NOVEL_RESULT
-> NEW_MATHEMATICS_CANDIDATE
```

There are explicit side outcomes:

```text
BLOCKED_PROOF_ASSURANCE
VERIFIED_REDISCOVERY
MACHINE_PROVEN_NOVELTY_UNRESOLVED
CANNOT_CHECK
```

Important non-implications are hard invariants:

```text
1,000,000 successful cases != proof
no counterexample found != proof
formal proof accepted != intended statement aligned
machine proven != novel
no prior art found != globally novel
interesting != true
```

## 4. Counterexample-first search

Before large proof search, attack the conjecture using the cheapest sound or falsifying tools available:

- exact finite enumeration when the domain permits it;
- randomized/property-based tests;
- boundary and degenerate cases;
- computer algebra for exact identities and simplification;
- SAT/SMT/model finding for encodable fragments;
- adversarial parameter search;
- search for stronger known theorems that make the proposed result trivial or false.

The result of this pass changes **search priority**, not theorem authority. A failure to find a counterexample is never interpreted as proof.

## 5. Formalization is its own proof obligation

A formal proof proves exactly the formal statement supplied to the checker. It does not establish that the statement faithfully represents the intended informal theorem.

RAKL therefore requires a `FormalizationWitness` containing hashes of both statements and checks such as:

```text
round-trip paraphrase
quantifier-order audit
domain/codomain audit
assumption audit
positive examples
negative examples
boundary/degenerate cases
independent review
```

For a new-mathematics claim, the strict profile requires at least one independent reviewer of the statement alignment.

## 6. Proof assurance and trust-chain hardening

A `ProofReceipt` is bound to the exact formal-statement hash and proof-source hash. The strict profile requires:

1. the primary checker accepts the artifact;
2. transitive proof dependencies are audited;
3. `sorryAx` is absent;
4. unregistered custom axioms are absent;
5. compiler/native trust is rejected when the target assurance profile requires independent kernel-level checking;
6. an independent checker rechecks the proof artifact in isolation when supported by the ecosystem;
7. checker versions and dependency identities are pinned.

This is not theoretical paranoia. Lean's own documentation records that finished proofs should audit axiom dependencies and that `sorryAx` can prove anything. Lean 4.32.1, released 22 July 2026, fixed a kernel soundness bug and explicitly notes that the recommended external `comparator` path for checking potentially dishonest proofs was not affected. The operational lesson is that "formal verification" is itself a trust architecture, not a magic scalar.

## 7. Proposition: generator-error containment

Let \(G\) be an arbitrary proposal generator, \(K\) a sound proof checker for logic \(L\), and \(U\) the canonical-update rule. Suppose

\[
U(T,p)=\mathrm{promote}
\quad\Longrightarrow\quad
K(p,T)=\mathrm{accept}.
\]

Then, under the soundness assumptions of \(K\) and the declared axioms, an invalid theorem cannot enter canonical mathematical truth state solely because \(G\) generated a plausible but wrong proof step.

### Proof sketch

The generator has no direct write authority. Any invalid candidate is either rejected before promotion or would require a failure of the trusted checker/axiom assumptions. Therefore generator unreliability affects search efficiency, branch count and compute, but does not by itself license false mathematical authority. \(\square\)

This is the key difference between an unchecked 1,000-step natural-language derivation and a proof-producing search process.

## 8. Proposition: verified checkpointing changes the long-horizon error model

Suppose a research program is decomposed into a dependency DAG \(D\), and every lemma admitted into the trusted DAG is independently checked before downstream use. Then the probability that an LLM proposes an incorrect local step does **not** multiply directly into the logical validity of the accepted final theorem. Incorrect proposals become rejected branches or additional search cost.

This does not eliminate risk. Remaining assurance risks include:

```text
formalization mismatch
checker/kernel defects
untrusted axioms or native computation
incorrect external lemmas/libraries
artifact substitution
novelty mistakes
```

But it removes the most dangerous failure mode in a long free-form chain: hidden accumulation of unchecked implications.

## 9. Truth and novelty are orthogonal

A formally verified statement can be a classical theorem known for centuries. Conversely, a genuinely new conjecture can be unproved. Hence truth and novelty cannot be represented faithfully by one total scalar without collapsing distinct states.

A useful authority pair is

\[
(A_{\mathrm{truth}},A_{\mathrm{novel}}).
\]

For example:

```text
(machine-proven, known)          = verified rediscovery
(machine-proven, unresolved)     = theorem with open novelty status
(machine-proven, bounded-novel)  = bounded novel result
(unproved, plausible-new)        = conjecture only
```

## 10. Novelty is defeasible and non-monotone

Let \(C_t\subseteq C_{t+1}\) be literature corpora and define

\[
\mathrm{Novel}_{C_t}(T)=1
\]

when no registered equivalence/entailment search finds prior art for \(T\) in \(C_t\). It is possible that

\[
\mathrm{Novel}_{C_t}(T)=1,
\qquad
\mathrm{Novel}_{C_{t+1}}(T)=0,
\]

because a newly indexed, translated or rediscovered source contains an equivalent or stronger theorem.

Therefore novelty certificates are versioned and defeasible. A later prior-art hit demotes novelty authority but need not demote the proof of the fixed theorem statement.

## 11. Bounded novelty certificate

RAKL never claims to prove global novelty from a finite search transcript. Instead it records

\[
N(T)=
(C_{\le t},S,\nu,f(T),R),
\]

where:

- \(C_{\le t}\): named corpora at a cutoff;
- \(S\): search routes and terminology/language variants;
- \(\nu\): normalization/equivalence procedure;
- \(f(T)\): canonical theorem fingerprint;
- \(R\): review and candidate-prior-art decisions.

Recommended routes include exact text, notation-normalized search, structural fingerprints, stronger-parent theorem search, citation neighborhoods, author/topic neighborhoods, translations and domain synonyms.

The licensed language is:

> no equivalent result was found within the registered novelty world at cutoff \(t\).

It is not:

> this theorem is globally new.

## 12. Search architecture for research rather than exercise solving

The working object is an AND/OR research graph, not one transcript.

Nodes may be:

```text
conjecture
lemma
definition
representation
counterexample
formalization
proof obligation
known theorem
open subproblem
computational experiment
```

Edges may be:

```text
implies
reduces-to
refutes
specializes
generalizes
equivalent-to
requires
suggests
```

The executive policy should optimize for expected closure of the current proof/novelty cut set per unit cost, while preserving diversity. High-value actions include proving a reusable bottleneck lemma, finding a counterexample that kills an entire branch, changing representation, identifying a missing invariant, or discovering that a proposed theorem is a corollary of known work.

## 13. Research-value gate

After truth and novelty are separately assessed, evaluate whether the result deserves further attention. Candidate dimensions include:

```text
generality
nontriviality
compression of many cases
new invariant or representation
connection to an open problem
new proof technique
explanatory value
new algorithm or construction
stronger bound
unexpected cross-domain transfer
downstream theorem yield
human interpretability
```

This is a prioritization layer, not truth authority.

## 14. Empirical evaluation plan

A serious benchmark for autonomous mathematical research must go beyond solved Olympiad problems. Required tracks include:

1. hidden-theorem proof search with fully formal statements;
2. false-conjecture rejection with difficult late counterexamples;
3. autoformalization traps where a nearby but wrong formal statement is easy to prove;
4. long-horizon proof DAGs with many reusable intermediate lemmas;
5. rediscovery vs novelty discrimination using notation/terminology variants;
6. stronger-parent theorem detection;
7. post-cutoff or withheld-corpus novelty evaluation;
8. open construction/optimization problems with executable evaluators;
9. proof-assistant trust attacks: `sorry`, custom axioms, native/compiler trust and artifact substitution;
10. research-value ranking blinded to provenance.

Primary metrics should include:

```text
false theorem promotion rate
formalization mismatch rate
counterexample discovery rate
verified lemma reuse
proof-search cost to accepted theorem
axiom/trust violation rate
novelty false-positive rate
rediscovery recognition rate
bounded-novelty recall
human research-value agreement
end-to-end cost per externally accepted result
```

## 15. Relation to current AI mathematics systems

Recent systems support the architectural split rather than the idea of an unconstrained LLM mathematician. FunSearch couples an LLM generator to executable evaluators and produced new constructions. AlphaProof places proof search inside Lean and uses formal verification as the environment. AlphaEvolve combines model-generated code with evolutionary search and automated evaluators, and later work applies the broader stack to dozens of mathematical problems. These systems show that generation becomes substantially more useful when embedded in search and verification loops.

RAKL's proposed contribution is narrower and complementary: make the *epistemic status* of every stage explicit, keep truth/specification/novelty/value separate, preserve failed branches, and harden the trust chain all the way to the release artifact.

## 16. Framework integration

Implementation: `src/rakl/math_research_assurance.py`  
Workflow: `skills/rakl-core/workflows/mathematical-research.md`  
Tests: `tests/test_math_research_assurance.py`

The layer composes with existing RAKL components:

```text
Epistemic pathfinding  -> proof/novelty cut sets
Constructive invention -> conjectures, lemmas, representations
Formal oracles         -> cheap exact checks and fail-closed specialist routing
Negative history       -> failed proofs and counterexamples
Authority poset        -> truth/specification/novelty/value separation
Structural witnesses   -> notation-independent prior-art and analogy search
Publication gate       -> exact claim/release identity
```

The intended invariant is simple:

\[
\boxed{\text{LLM creativity may expand the search space; only explicit assurance may expand mathematical authority.}}
\]
