# Semantic Shortcut Research Synthesis

**Status:** design research for the Class-B semantic-shortcut challenger.  
**Authority:** research/design rationale only; this document does not establish method improvement or theorem authority.

## Research question

The framework extension is organized around one question:

> **Has this relational obstruction — and a transformation that breaks it — occurred anywhere in recorded knowledge?**

The intended use is broader than retrieving a similar theorem. A hard proof or research problem is first converted into a domain-light relational obstruction. RAKL then searches recorded experience for an episode with the same obstruction morphology and a transformation whose *observed effect* moves that morphology toward the desired target state.

## Expert cell

The design was challenged through five same-context lenses. These are role-separated design passes, not independent peer review.

### 1. Proof-discovery / formal-methods lead

Focus: premise selection, auxiliary lemmas, proof-state search, theorem-statement invariance and verifier boundaries.

Main conclusion: retrieval can materially change proof success, but a retrieved method remains a proposal until target proof obligations close. A semantic shortcut must therefore output a candidate route plus explicit validation debt, never theorem authority.

Relevant primary work includes LeanSearch v2 (arXiv:2605.13137), Lean Hammer premise selection (arXiv:2506.07477), Prover Agent (arXiv:2506.19923), Lemmanaid (arXiv:2504.04942), Seed-Prover (arXiv:2507.23726), and recent work on representation sensitivity in theorem proving (arXiv:2605.22257).

### 2. Analogy / cognitive structure-mapping lead

Focus: why distant analogies help and why surface similarity is dangerous.

Main conclusion: abstraction can expose shared relational structure across different vocabularies, but the useful object is a mapping of roles, relations, constraints and enabling conditions. The target must retain explicit disanalogies. The abstraction level itself can be wrong, so a mapping witness is falsifiable rather than authoritative.

Relevant primary work includes Semantic Structure-Mapping in LLM and Human Analogical Reasoning (arXiv:2406.13803), YARN (arXiv:2603.29997), and Unlocking LLM Creativity in Science through Analogical Reasoning (arXiv:2605.11258).

### 3. Case-based / relational retrieval lead

Focus: what should be stored and retrieved.

Main conclusion: whole documents are a poor primitive for reusable reasoning. The reusable object should be a structured episode that separates the obstruction, transformation, preconditions, resulting relations, preserved invariants, broken/relaxed constraints, breakpoints, provenance and authority. Retrieval should compare substructure and effects, then leave transport to a separate witness.

Relevant primary work includes StructCBR (arXiv:2301.04110), CAST (arXiv:2605.15041), and recent structure-aware memory work (arXiv:2606.14047).

### 4. Program-synthesis / abstraction-invention lead

Focus: what happens when the current vocabulary cannot efficiently express a solution.

Main conclusion: search inside a fixed primitive vocabulary and invention of a new primitive are different operations. New abstractions can compress future search, but they need a specification and later transfer evidence. LIFT should therefore synthesize a *missing-transformation specification* from repeated residuals rather than directly hallucinating a new operator.

Relevant primary work includes DreamCoder (arXiv:2006.08381), TheoryCoder-2 (arXiv:2602.00929), Beyond Fixed Representations (arXiv:2607.09560), and A Compositional Framework for Open-ended Intelligence (arXiv:2606.15386).

### 5. Scientific-discovery / RAKL-governance lead

Focus: iterative falsification, residual learning, no-match claims, consolidation and authority.

Main conclusion: counterexamples and failed attempts are not waste; they constrain the next candidate. However, one failure is not evidence that a new representation is required. RAKL must separate retrieval failure, transfer failure, composition failure and true representation/method-basis insufficiency. Coverage of the searched universe must be explicit before a cross-domain no-match claim can justify LIFT.

Relevant primary mechanisms include counterexample-guided inductive synthesis/control synthesis, RAKL's existing failure lattice and memory-coverage receipt, and evaluator-driven discovery systems such as AlphaEvolve.

## Saturated design findings

Across the five lenses, later searches largely reinforced rather than changed the following requirements. That convergence is the stopping condition for this design pass.

### A. Search the obstruction, not the topic

A newspaper story, biological process, scheduling problem and theorem can be far apart in vocabulary while sharing the same relational obstruction. The retrieval key therefore includes:

```text
roles
relations
constraints
failure mechanisms
invariants that must survive
desired transition
forbidden losses
```

### B. Retrieve episodes of change, not only facts

The central memory atom is:

```text
O --T--> O'
```

where the episode records why `T` was available, what it changed, what it preserved and where it fails.

### C. Source validity and target applicability are independent

A proof-backed source episode can still be a bad analogy. Conversely, a useful everyday episode can suggest a candidate without supplying mathematical authority. Every strict SEARCH/JUMP route therefore needs target applicability accounting.

### D. Preconditions are first-class

A transformation often works because of an enabling assumption that is invisible in a superficial analogy. Every source precondition must be mapped to the target or explicitly remain unrepaired. Any unrepaired source precondition blocks strict transport.

### E. Search actual transformation effects

A source obstruction's desired goal is not evidence that its transformation achieved that goal. Retrieval therefore scores the recorded transformation's `resulting_relations` and `preserved_invariants`, not merely the source problem statement.

### F. Invention is last

The route order is:

```text
SEARCH
-> JUMP
-> GLUE
-> LIFT
```

`JUMP` cannot bypass an available same-domain route. `GLUE` cannot be declared from two attractive motifs unless their combined effects cover the target and interfaces are checked. `LIFT` is blocked until earlier candidates are individually accounted for.

### G. LIFT is inverse synthesis

LIFT does not mean "be creative." Repeated failed attempts produce a residual intersection. The system asks what an absent transformation would have to:

```text
preserve
break
expose
reduce
```

and freezes those properties as `MissingTransformationSpecification` before downstream invention.

### H. Cross-problem no-match requires coverage

"No relevant transformation exists" is a statement about a search universe. A local empty result cannot support it. LIFT therefore binds its exhaustion witness to a cross-problem coverage receipt and records the search boundary, domains, method families, rejected episodes/compositions and reasons.

### I. Successful inventions become cumulative experience only after validation

A successful new representation/operator may eventually produce:

1. a validated target result;
2. a scoped `ResearchTool` with applicability conditions;
3. an `ObstructionTransformationEpisode` describing the successful structural transition.

The episode memory remains a retrieval projection, not a truth-authority store. Tool promotion and mathematical authority continue through existing protected gates.

## Implemented architecture

```text
active atomic problem
      |
      v
MathContextFiber
      |
      v
success-tool + failure-lattice review
      |
      v
ObstructionFingerprint
      |
      v
content-bound ObstructionTransformationMemory
      |
      +--> SEARCH: same-domain applicable episode
      |
      +--> JUMP: cross-domain structural mapping witness
      |
      +--> GLUE: effect-covering composition + interface witness
      |
      +--> LIFT: bounded exhaustion + repeated residuals
                     |
                     v
            MissingTransformationSpecification
                     |
                     v
            typed mechanism/formalism invention
      |
      v
formal/empirical validation
      |
      +--> failure -> failure lattice + new residual
      |
      +--> success -> scoped tool / episode consolidation candidate
```

## Canonical ownership

This challenger does not propose a new 25th RAKL method surface. It extends existing canonical responsibilities:

- **memory** owns content-bound episode storage and reconstructable snapshots;
- **equivalence/similarity** and **generator transport** own structural source→target witnesses;
- **routing** owns SEARCH/JUMP/GLUE/LIFT route selection;
- **contextual gluing** owns composition/interface obligations;
- **gap discovery** owns the LIFT missing-transformation specification and epistemic cut;
- **mechanism/formalism invention** owns downstream synthesis of new typed candidates;
- **authority promotion / formal assurance** remain unchanged.

This division prevents a semantic-shortcut result from becoming an alternate authority channel.

## Hostile controls derived from the research

The implementation should fail closed when:

- an episode id is asserted but absent from the bound memory;
- the memory snapshot hash is stale or tampered;
- a proposal-only episode is treated as a strict reusable route;
- source and target share words but not the relevant failure mechanism/effect;
- a source transformation sacrifices a target-forbidden invariant;
- one source precondition is ignored;
- JUMP is selected while a viable SEARCH route exists;
- GLUE components do not jointly cover the desired transition;
- GLUE has no interface/incompatibility witness;
- LIFT follows one failure;
- LIFT uses an unbounded no-match claim;
- LIFT omits a retrieved candidate from its rejection accounting;
- a LIFT specification asks to break a property not supported by repeated residuals;
- a shortcut review is written after candidate generation.

## Remaining empirical question

This implementation makes the mechanism explicit and testable. It does **not** establish that the challenger improves RAKL on fresh mathematical problems. That claim remains a Class-B empirical question requiring matched parent/challenger evaluation, hostile near-misses, resource comparability and fresh assurance under the existing RAKL upgrade protocol.
