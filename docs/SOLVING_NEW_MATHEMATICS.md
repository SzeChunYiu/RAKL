# Solving New Mathematics with Orion — an explicit protocol

How the framework solves a *new* math problem, including one that needs a *new method* --
derived from how LLMs actually solve math today, and mapped onto Orion's two-stroke
GROW/CLOSE loop (`docs/GENERATIVE_MECHANICS_PROGRAMME.md` §1a). Proposal-only; honest about
what is built, what is proposed, and what no framework can guarantee.

---

## 1. How LLMs actually solve math today (the one lesson)

Every system that has produced real mathematical results shares one mechanism:

> **an LLM proposes (GROW), a formal verifier or executable evaluator selects (CLOSE), and
> search + memory accumulate what survived.**

- **AlphaProof (IMO 2024).** A Gemini model *autoformalizes* natural-language problems into
  Lean, generates candidate proof steps, and **Lean formally verifies correctness** --
  "formal languages offer the critical advantage that proofs can be formally verified,"
  preventing "plausible but incorrect" natural-language steps. AlphaZero-style search explores
  proof steps; **every verified proof self-trains the model** on harder problems.
- **AlphaGeometry.** A neuro-symbolic hybrid: the **neural net proposes auxiliary
  constructions** (a genuinely new object added to the diagram), the **symbolic engine
  deduces** the consequences. The creative act is proposing the right construction; the
  closing act is deduction.
- **FunSearch / AlphaEvolve.** The LLM writes **programs** (functions); an automated
  **evaluator executes them and keeps only what scores**, "guarding against hallucinations."
  An evolutionary loop (population -> LLM mutates best -> evaluate -> retain) discovered the
  **largest cap sets found in 20 years** -- genuinely new mathematics, because novelty is
  bounded by the *evaluator*, not by prior knowledge.

Three invariants fall out, and they are exactly Orion's:
1. **Verification is the enabler.** You can only trust generation that a sound oracle can check.
2. **The LLM is the GROW/mutation operator**; the verifier is the CLOSE/selection oracle.
3. **What verifies is retained and reused** (self-training / evolutionary pool) -- method evolution.

---

## 2. The Orion protocol (the two-stroke loop, instantiated for math)

Each step lists: real-system analogue -> Orion machinery that exists -> proposed generative
mechanic where a gap remains.

### Phase 0 -- Intake and framing
- **Autoformalize** the problem: natural language -> a formal statement in a checkable system
  (Lean-style). *[AlphaProof autoformalization -> Orion `math_context.py`, autoformalization in
  `MATHEMATICAL_RESEARCH_ASSURANCE.md`]*
- **Well-posedness certificate**: is the statement decidable/answerable as posed; are the
  load-bearing terms unambiguous? An ambiguous term whose senses change the answer opens a
  fiber, not a proof. *[proposed Mechanic VI well-posedness]*
- Extract the **ProblemSignature** and the initial **atom basis**: known definitions,
  hypotheses, goal, available lemmas. *[`problem_solving_algebra.py`]*
- **Fidelity check**: a proof of the *wrong* formalization is worthless -- flag autoformalization
  loss as a first-class failure mode.

### Phase 1 -- CLOSE with the current basis (solve with known methods)
- **Proof-scheme selection**: instantiate induction / contradiction / infinite-descent /
  extremal / pigeonhole as typed obligation sets. *[proposed Mechanic IV `PROOF_SCHEMA`;
  `strategy_motifs.py`]*
- **Operator-path / backward search** over known methods toward the goal.
  *[`backward_multiseed.py`, `problem_solving_algebra.py`]*
- **Experimental mathematics**: compute many examples, detect a pattern, form a conjecture.
  *[`symbolic_discovery.py`, `math_oracles.py`; FunSearch-style]*
- **Every candidate step is checked by the formal oracle.** Verified steps mint authority;
  unverified steps are proposals with none. *[`formal_oracles.py`, `proof_dag.py`]*
- If the goal closes under verification -> **done, with assurance**. This is the "solution is a
  compatible gluing of known atoms" case: the deductive, parallelizable, compressible half.

### Phase 2 -- the residual: when no known method closes it (GROW)
This is the crux -- *the problem needs a new method*. A stalled CLOSE leaves a **typed residual/
obstruction**: "need a map with property P," "the inductive step is too weak," "no lemma bridges
A and B." The generative moves fire in escalation (`SEARCH -> JUMP -> GLUE -> LIFT`):
- **SEARCH** -- retrieve a same-domain method (method memory, nearest-work).
- **JUMP** -- transport a method from another domain through a **directional structural witness**
  (Paper II): e.g. a probabilistic argument onto a combinatorial goal, licensed only if the
  witness's obligations hold. *[Paper II]*
- **GLUE** -- compose verified partial lemmas/methods into a route. *[`proof_dag.py` composition]*
- **LIFT** -- specify the **missing operator as a new subproblem**: "I need an object $X$ with
  properties $P_1,\dots,P_n$ that I do not have." *This is where a new method is born:* the need
  for it is a residual, so the framework **recurses** -- treats "construct $X$ with $P$" as a
  fresh problem and runs the whole loop to invent it, FunSearch-style (propose candidate
  constructions -> score against the property-oracle -> evolve). *[`invention.py`,
  `constructive_lattice.py`, `symbolic_discovery.py`; AlphaGeometry auxiliary construction]*
- **DIALECTIC** -- if a conjecture/definition is refuted by a counterexample, *evolve the
  statement* (monster-bar, exception-bar, lemma-incorporation) instead of only rejecting it.
  This is how the new **concept** the problem needed gets created. *[proposed Mechanic IV
  `DIALECTIC`; counterexample-first exists]*
- **STRENGTHEN_TARGET** -- if the induction is too weak, prove a *stronger* statement (inventor's
  paradox), with $\tau'\Rightarrow\tau$ verified first. *[proposed Mechanic IV]*

### Phase 3 -- the new method earns authority (severity)
A candidate new method or construction has **no authority until it verifies.** The formal oracle
is ground truth: a proof that passes a sound checker is the ultimate **severe test**
($P(\text{pass}\mid\text{false})=0$ for a sound checker), so it maxes the severity coordinate
$S$. *[Mechanic V severity; Paper V assurance; byte-reproducible `proof_dag.py`; verified-lemma
checkpointing; the five non-compensatory math coordinates of `MATHEMATICAL_RESEARCH_ASSURANCE.md`]*

### Phase 4 -- the method becomes reusable (method evolution)
A one-off verified proof is not yet a *method*. It becomes a retained, transferable method only
after it is (a) abstracted into a scheme/motif and (b) **transfers to fresh problems** under the
Paper III governed-upgrade protocol (content-identified challenger vs frozen baseline on fresh
transfer). Only then does the invented method earn *method authority* -- and this is how the
framework **accumulates** new methods over time (the civilizational memory that compresses
generations). *[Paper III; `strategy_motifs.py`, experience-to-method]*

### Phase 5 -- bounded saturation over BOTH strokes
Stop when the goal is closed, or when neither **growing the basis** (new atoms/methods via
heterogeneous, lexically-independent routes) nor **closing the lattice** (new verified
consequences) adds anything substantive. Reopen on any new primitive. *[Paper I bounded saturation]*

---

## 3. Worked shape of the "needs a new method" case

```
autoformalize + well-posedness
        |
   try known schemes/methods  ---- verified? --> DONE (assurance)
        |  (stall: typed residual "need X with property P")
        v
   SEARCH -> JUMP -> GLUE -> LIFT
        |            (LIFT: "construct X with P" is a NEW subproblem)
        v
   recurse the whole loop to INVENT X   (propose -> oracle-score -> evolve)
        |     (counterexample? -> DIALECTIC evolves the concept)
        v
   X verified by the formal oracle  --> new method earns AUTHORITY (severity S)
        |
   X transfers to fresh problems    --> new method earns METHOD authority (Paper III)
        |
   compose back: does the goal now close?  -- yes --> DONE ;  no --> reopen residual
```

The engine never *conjures* the missing method by closing a too-small lattice; it **grows the
basis** by recursively inventing the missing operator, and lets the **verifier**, not fluency,
decide whether the invention is real.

---

## 4. Honest limits (what no framework can promise)

1. **Verifier-gated.** The whole protocol works because a *sound formal oracle* decides
   correctness. For **formalizable** problems (Lean-checkable) it delivers assurance. For
   **informal frontier mathematics** -- proved by human argument, not yet formalizable -- there is
   no decidable oracle, so the framework degrades to `CANNOT_CHECK` / proposal-only: it can
   propose a method and a candidate proof but **cannot certify** them; authority stays external
   (human referees). This is the boundary, stated plainly.
2. **Model-vs-system.** The verifier, search and memory are *system* capability. When Lean or a
   symbolic engine does the deduction, that is external substitution -- report it as a system
   result, never "the model is a better mathematician." FunSearch's cap-set discovery is a
   *system* result (LLM mutation + evaluator selection + evolutionary search).
3. **Model-bounded creative leap.** *Which* auxiliary construction, *which* operator to LIFT,
   *which* reframe -- candidate generation is bounded by the model. The framework amplifies the
   *search* (parallel, memory, pruning) but cannot guarantee the key idea is ever proposed
   (AlphaGeometry finishes only if the net proposes the right construction).
4. **Retrieval vs. invention.** A "new method" may be memorized. Genuine novelty needs the
   nearest-work/prior-art audit (Paper I); FunSearch's result is credibly new because the
   evaluator beat 20 years of human constructions *by the objective*.
5. **Autoformalization loss.** Translating an informal problem into a faithful formal statement
   can distort meaning; a proof of the wrong statement is worthless. Fidelity is a real failure
   mode, checked in Phase 0.

---

## 5. What is built vs. what is the gap

- **Already in Orion (the CLOSE stroke):** `proof_dag.py`, `formal_oracles.py`, `math_oracles.py`,
  `symbolic_discovery.py`, `strategy_motifs.py`, `backward_multiseed.py`, `constructive_lattice.py`,
  `invention*.py`, `math_research_assurance.py`, autoformalization, counterexample-first,
  verified-lemma checkpointing, and Paper V's assurance architecture.
- **The gap (the GROW stroke):** the generative mechanics as *executable, saturation-certified*
  operators -- `PROOF_SCHEMA`, `STRENGTHEN_TARGET`, `DIALECTIC` (concept-evolution), the LIFT
  recursion as a first-class invention loop, well-posedness, and the value/promise projection to
  choose which residual to attack. The severity coordinate $S$ formalizes "a proof that clears a
  sound checker is the most severe test," tying Phase 3 to Mechanic V.

The honest headline: **Orion can solve a *formalizable* new math problem, including one needing a
new method, by recursively inventing the missing operator and letting a sound verifier confer
authority -- as a system, not a smarter model. For non-formalizable frontier math it assists but
cannot certify.** That is exactly the boundary its own ethos demands.
