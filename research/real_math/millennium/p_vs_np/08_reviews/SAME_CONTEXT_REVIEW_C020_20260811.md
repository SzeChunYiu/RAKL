# Same-context five-role review — C020

**Independence status:** `SAME_CONTEXT_ONLY`. This file does not satisfy the three-isolated-review gate.

## Frozen claim under review

For every odd prime `p`, with `n=ceil(log2 p)`, the quadratic-residue difference graph `QR_p` has

`rho(QR_p,G_{p,p}) <= D_intersection(QR_p | G_{p,p}) = O(n^3)`.

The proof uses free unions of row/column stars for input-bit predicates, a dual-rail gate-to-set simulation, elementary `O(n)` modular addition, `O(n^2)` double-and-add modular multiplication, `O(n^3)` fixed-exponent powering, and Euler's criterion.

## Complexity-theory lens

**Vote: ACCEPT AS PROOF DRAFT.** The argument attacks full intersection/cover complexity, not the already-retired canonical lane. The non-power-of-two side size is handled directly by unions of valid row/column labels, so no padding-to-`2^n` transference claim is needed for this upper bound.

**Concern CT-M1, blocking for theorem promotion:** do not infer a lower bound from high GF(2) rank after C020. This family now has a direct polylogarithmic full-cover upper envelope despite rank `p`.

**Resolution test:** preserve C019 rank only as an admission screen and make C020's polylog ceiling part of every later Paley-family claim.

## Meta-complexity lens

**Vote: ACCEPT WITH SCOPE WARNING.** C020 has no MCSP threshold-magnification consequence and no P-versus-NP implication. It is route pruning inside R004.

**Concern MC-M1:** an `O(log^3 p)` upper bound leaves open `omega(log p)` cover complexity, so C019 is not refuted as a super-log target.

**Resolution test:** require either an `O(log p)` construction or a genuine super-log lower-bound invariant before changing C019's target status.

## Adversarial proof-review lens

**Vote: REVISE BEFORE THEOREM AUTHORITY.** The central hidden-operation risk is complement. Graph intersection complexity does not grant arbitrary set complement for free. C020 avoids this by maintaining both Boolean polarities as dual rails, where AND/OR duality uses only intersections and unions.

**Concern AP-M1, blocking:** every arithmetic subcircuit used in a later formal version must be compiled into the same fan-in-two Boolean basis. Statements such as comparator, conditional subtract, or mux cannot become undeclared primitives.

**Resolution test:** formalize a basis-level ripple-carry modular adder and one double-and-add multiplication step, then compose the fixed exponent schedule.

## Formal-methods lens

**Vote: REVISE.** The finite Python checker now exhaustively validates the specified double-and-add multiplication and square-and-multiply recurrence on small primes, checks the Euler predicate against direct quadratic-residue membership, and checks the schedule accounting. It is still not a proof-producing Boolean-circuit compiler.

**Concern FM-M1, blocking:** no formal statement binding, theorem-prover artifact, proof receipt, dependency/axiom audit, or isolated recheck exists.

**Resolution test:** encode C020-L1 through C020-L5 in a proof assistant or proof-producing circuit framework, bind exact hashes, and recheck independently before `VERIFIED_LEMMA` authority.

## Novelty/research-value lens

**Vote: ACCEPT ONLY WITH `NO_NOVELTY_CLAIM`.** Euler criterion and elementary modular circuits are classical ingredients. A bounded search was not used to claim originality. The value is diagnostic: it demonstrates that the strongest surviving R004 admission screens still do not prevent a polylogarithmic full-cover construction.

**Concern NV-M1:** do not publish C020 as a new circuit upper-bound theorem without a dedicated prior-art search.

**Resolution test:** if C020 later matters as a standalone result, run a bounded structural-equivalence search for Paley/Legendre graph star complexity, intersection complexity, cyclic constructions, and Boolean complexity of quadratic characters.

## Synthesis

Consensus is that C020 is safe to retain as a bounded proof draft and route-control checkpoint. It blocks any narrative that C019's full rank or density suggests near-linear cover complexity. It does not settle whether the family is `O(log p)` or super-logarithmic, and it has no root authority.
