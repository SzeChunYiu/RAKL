# Paper V external handoff — Lean mechanization + verified-math experiment

## Local boundary

The current local environment does not provide `lean`/`lake`, so no claim of Lean mechanization is made in this round. The branch does add an exhaustive finite known-world test of the five-coordinate authority product:

```text
tests/test_p5_finite_authority_product.py
```

That test is a mechanization precursor, not a replacement for Lean.

## Target Paper-V thesis

The strongest durable thesis should be executor-independent:

> Mathematical research authority is a product of separately governed specification alignment, theorem truth, bounded novelty evidence, research-value status, and verifier trust. Proposal/search systems may be arbitrarily fallible without being allowed to self-promote these coordinates.

Do not headline “LLMs can do mathematics.” Strong modern provers/research agents already occupy that capability space.

## Workstream A — formalize the minimum assurance nucleus in Lean

Create a new isolated package; do not modify historical frozen proof artifacts.

Suggested location:

```text
formal/paper5_assurance_product_v1/
  lean-toolchain
  lakefile.toml
  Paper5Assurance/
    Authority.lean
    Promotion.lean
    ProofDAG.lean
    Novelty.lean
    Main.lean
  AXIOM_AUDIT.md
  BUILD_RECEIPT.json
```

### Freeze before proof work

Record:

```text
RAKL subject SHA
Lean version
mathlib revision if used
platform/container identity
exact source hashes
allowed axioms
forbidden: sorry/sorryAx/admit/custom unregistered axioms
```

### Minimum theorems

#### T1. Generator-error containment

Formalize abstractly:

```text
Promote(T,p) -> SpecAligned(T_intended,T_formal)
                AND CheckerAccepts(p,T_formal)
                AND TrustedChecker

CheckerSound AND Promote(T,p)
-> IntendedClaimTrue
```

The theorem must make the remaining assumptions explicit. It does **not** prove the checker itself sound.

#### T2. Product noncompensation

For any load-bearing coordinate `c` in `{specification, truth, verifier trust}`:

```text
not c -> not ResearchPromotion
```

A positive novelty/value coordinate cannot compensate.

#### T3. Truth / novelty separation

Model literature worlds `L_t subseteq L_t1` and a fixed proved statement. Show the architecture permits:

```text
Truth(T,t) = Truth(T,t+1)
Novelty(T,t) = true
Novelty(T,t+1) = false
```

without contradiction. Novelty is a defeasible external-world coordinate, not a theorem property.

#### T4. Proof-DAG dependency closure

If a root certificate is promoted, every transitive dependency required by the root must have an admitted exact-statement proof receipt. Omission of one required dependency blocks root promotion.

#### T5. Proposal/search noninterference

SEARCH/JUMP/GLUE/LIFT, VTG scores, route lengths, quotient membership and model confidence cannot alter theorem authority without a separate registered proof/spec/trust transition.

### Required Lean release checks

```bash
lake build
# grep sources/build artifacts for sorry/admit
# run #print axioms on every public theorem
```

Prefer a second clean/containerized recheck. If a comparator/kernel path is available, record it as a separate verifier-trust coordinate.

Any `sorry`, unexpected axiom, or unbound toolchain -> `MECHANIZATION_NOT_CLOSED`.

## Workstream B — hostile five-coordinate assurance benchmark

Freeze before candidate outputs.

### Task families

At minimum:

1. valid proof, correct specification, known prior theorem;
2. valid proof of the **wrong formalization** of the intended claim;
3. false theorem with fluent/proposed derivation;
4. correct theorem with forbidden/undeclared axiom;
5. exact theorem/proof hash substitution;
6. omitted transitive ProofDAG dependency;
7. theorem true but novelty dossier stale;
8. apparent novelty that is a notation/parameterization rediscovery;
9. novel-looking but low/undetermined research value;
10. true CANNOT_CHECK novelty cases;
11. verifier-version/trust mismatch;
12. route/geometry succeeds while theorem proof fails;
13. proof succeeds despite the RAKL discovery chronology not being followed.

### Arms

```text
A MONOLITHIC_RESEARCH_MODEL
B PROOF_CHECKER_ONLY
C PROOF + EXACT_STATEMENT_BINDING
D FULL_RAKL_MATH_ASSURANCE
```

Optional ablations:

```text
D-no-spec
D-no-novelty
D-no-trust-audit
D-no-dependency-closure
```

### Co-primary outcomes

```text
unauthorized research promotion rate
valid theorem-promotion recall
wrong-specification false promotion
forbidden-axiom false promotion
stale/rediscovery novelty false promotion
CANNOT_CHECK precision/recall
proof-DAG dependency omission detection
wall time / verifier calls / model calls / tokens
```

Hard gate: unauthorized promotion of a planted invalid intended mathematical claim must be zero on the frozen hostile suite. Also require nonzero legitimate-promotion recall so “reject everything” cannot win.

## Workstream C — public verified-math benchmark

Use a frozen external benchmark version. The current strongest natural candidate is the 2026 **Formal Conjectures** corpus; freeze exact repository/dataset revision before outputs.

Keep two questions separate:

### C1. Assurance on solved/known-answer material

Use solved/formalized statements where proof validity is objectively checkable. Inject specification, novelty and verifier-trust attacks without changing hidden gold after outputs.

### C2. Discovery capability on open research statements

This is secondary and cannot use “not previously solved by the benchmark” as proof of novelty/value. Any genuinely new candidate requires ordinary proof + bounded literature novelty + value review.

## Workstream D — executor-independence test

Run the same assurance state machine with at least two proposal sources:

```text
1. LLM / neural theorem-proving proposer
2. LLM-free or substantially different symbolic/enumerative/tactic proposer
```

The primary executor-independence result is:

```text
authority safety semantics remain invariant under proposer replacement
```

not “both proposers have equal theorem-solving capability.”

## Workstream E — VTG only after strongest-parent comparison

Issue #528 / `PAPER5_PAPER6_SUCCESSORS.json` already freezes the correct comparison:

- scaled best-first/BFS-Prover-style search;
- HTPS-style AND/OR proof search;
- white-box/factorized Lean state search where applicable;
- policy/value formal search where reproducible;
- equality saturation on equational families;
- strong current Lean prover as a capability ceiling.

VTG earns a performance claim only from **fully-costed verified root-level search benefit**. Local distance correlation, pretty embeddings, or fewer apparent states are diagnostic only.

## Manuscript changes after evidence

If Workstreams A+B succeed, rename/reframe toward executor-independent verified mathematical discovery/assurance. Keep autonomous-mathematician claims explicitly out unless C2 independently earns them.

Every result sentence must identify which coordinate it supports:

```text
specification
truth
novelty
value
verifier trust
search efficiency
```

Never let one coordinate silently stand for another.