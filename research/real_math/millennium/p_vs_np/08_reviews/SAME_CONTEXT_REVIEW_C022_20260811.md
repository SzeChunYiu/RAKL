# C022 five-role review preflight — 2026-08-11

**Independence status:** `SAME_CONTEXT_ONLY`.

These five role passes share one research invocation. They do not satisfy the independent-review requirement and must not be cited as independent peer review.

## Frozen packet

- exact C019–C021 graph definition `QR_p`;
- C022 exact sign-matrix spectral derivation;
- Lokam 2003 source statement, especially Theorem 4.7 and Corollary 4.8;
- Cavalar–Oliveira 2025 cover/intersection model facts;
- merged C021 unrestricted upper-bound proof draft;
- exact finite QR Gram-matrix regression oracle.

## Role 1 — complexity theory

**Evidence inspected:** exact C022 derivation, Lokam theorem statement/model, C021 model and source packet.

**Strongest counter-hypothesis:** the classical “Paley-type” statement may concern a sibling Hadamard graph rather than the exact `QR_p` relation, so the restricted lower bound may not align.

**Attempted falsifier:** derive the operator norm directly for the frozen `+/-1` incidence matrix, including the diagonal convention. The derivation gives `sqrt(p+1)` for `p=3 mod 4` and `sqrt(p)+1` for `p=1 mod 4`; finite exact Gram checks agree.

**Residual uncertainty:** external theorem/model alignment is source-bound rather than formalized.

**Vote:** `ACCEPT_ROUTE_PRUNING`.

The important conclusion is not that QR is “hard” in the unrestricted target model. It is that spectral pseudorandomness already makes the restricted depth-3 model hard, yet does not prevent the C021 near-log unrestricted construction. Depth/reuse is therefore the live obstruction.

## Role 2 — meta-complexity

**Evidence inspected:** R004 root role, Cavalar–Oliveira transfer motivation, proof DAG.

**Strongest counter-hypothesis:** this restricted-depth lower bound may be mistaken for progress toward a general circuit lower bound.

**Attempted falsifier:** trace the implication direction. C022 proves no lower bound on `rho` or unrestricted Boolean circuits; C021 is an upper bound in the more permissive graph-construction model.

**Residual uncertainty:** whether a useful conditional depth reduction exists remains open.

**Vote:** `ACCEPT_ROOT_SCOPE_ZERO`.

C022 is valuable only because it localizes the gap. It does not close a P-vs-NP proof obligation.

## Role 3 — adversarial proof review

**Evidence inspected:** every algebraic identity in C022-L1, diagonal convention, asymptotic substitution into Lokam's theorem.

**Strongest counter-hypothesis:** `A_p=C_p-I` or the correlation identity may use the wrong orientation/sign at the diagonal, invalidating the norm.

**Attempted falsifier:** check the exact matrix entry contract and derive `C C^T=pI-J` from a self-contained count. Independently test integer Gram identities for small primes in both residue classes modulo four.

**Residual uncertainty:** the asymptotic depth-3 theorem itself is imported from the source, not re-proved here.

**Vote:** `ACCEPT_PROOF_DRAFT`.

Blocking warning: do not turn the lower-bound ratio into a lower bound on cover complexity. The direction `rho <= D_intersection` goes the other way.

## Role 4 — formal methods

**Evidence inspected:** executable checker, C022 dependency list, C021 promotion blockers.

**Strongest counter-hypothesis:** exact finite tests could be misrepresented as a proof of the asymptotic theorem.

**Attempted falsifier:** inspect authority labels and dependencies. The code checks only finite integer identities; the asymptotic source theorem and C021 source chain remain external.

**Residual uncertainty:** no proof assistant encodes the finite-field correlation argument, spectral step, Lokam theorem interface, or C021 model alignment.

**Vote:** `REVISE_BEFORE_THEOREM_AUTHORITY`.

No `VERIFIED_LEMMA` promotion is permitted from this packet.

## Role 5 — novelty and research value

**Evidence inspected:** Lokam 2003 source, Cavalar–Oliveira 2025 source, existing R004 history.

**Strongest counter-hypothesis:** the spectral calculation and restricted-depth conclusion are classical/implicit and therefore not novel.

**Attempted falsifier:** search by theorem, Paley/Hadamard graph, depth-3 graph complexity, operator norm, and cover complexity. Lokam explicitly records the Paley-type restricted-depth lower bound; no novelty should be asserted for that lower-bound phenomenon.

**Residual uncertainty:** whether the exact same-matrix derivation and quantified separation from the 2025 unrestricted model have appeared verbatim elsewhere was not exhaustively certified.

**Vote:** `ACCEPT_NO_NOVELTY_CLAIM`.

Research value is strategic rather than novelty-based: it identifies the precise model feature that a successful R004 invariant must survive.

# Post-review synthesis

## Consensus

C022 is internally coherent as a source-bound route-pruning checkpoint. The strongest safe conclusion is:

> the exact QR relation has a classical super-logarithmic depth-3 bipartite-formula lower bound, while the merged RAKL source chain gives a much smaller unrestricted intersection upper bound; therefore restricted-depth spectral hardness does not directly survive unrestricted reuse/cyclic fusion at the same scale.

## Blocking concerns for stronger promotion

- no proof-assistant formalization or isolated recheck;
- no bounded novelty certificate;
- C021 remains a proof draft at its machine-model/source interfaces;
- no independent reviewers;
- no cover lower bound above the logarithmic baseline.

## Next discriminator

Search for a preserving-semi-filter/cyclic-construction invariant with a proved per-fusion budget. Reject candidates immediately if C008–C021 furnish a construction on which the proposed invariant would incorrectly predict a larger lower bound.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.