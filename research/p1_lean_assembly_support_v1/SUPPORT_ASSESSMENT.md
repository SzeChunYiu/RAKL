# p1-one-claim-not-machine-checked — support assessment

Not a revival. A support check run *before* committing effort, which is the precondition the last
three instruments skipped. It changes what is known about this negative without touching its status.

## The negative

Lean 4 machine-checks 17 of Paper I's 18 numbered formal claims. The exception is the workspace
top-`k` optimality theorem. Its lever:

> assemble the three checked Lean ingredients into the stated theorem; generalize naturals to reals

## Support: present, and better than assumed

| Question | Answer |
|---|---|
| Toolchain obtainable? | **Yes** — `leanprover/lean4:v4.14.0`, installed on laptop billy |
| Mathlib needed? | **No** — zero `import Mathlib`; the development is core Lean only |
| Baseline typechecks locally? | **Yes** — `lean RaklFormal.lean`, **1.2 s** |
| Iteration loop | **1.2 s per check** — fast enough to develop against |
| Ingredients present? | **Yes** — `sum_swap_ge`, `exchange_partner_exists`, `top_subset_optimal`, plus `sumU_keep_split` for the reserved/fill split |

The negative is therefore **effort-bound, not resource-bound.** That is a real reclassification: it
had been indistinguishable from the items blocked on hardware or authorization.

## Scope, measured rather than guessed

The assembly is not a short composition of the three lemmas. It needs objects the development does
not yet have:

1. a partition model — `part : I → P` with per-partition quotas `r : P → Nat`;
2. a feasibility predicate carrying the reservation lower bounds;
3. the reservation-first greedy selection itself, as a definition;
4. the induction that iterates the exchange across partitions while preserving feasibility;
5. the objective split across the reserved/fill boundary, which `sumU_keep_split` supports but does
   not discharge.

The second half of the lever — `Nat` → reals — has no Mathlib to borrow from: there is no
`OrderedAddCommMonoid` in scope, so it means defining the algebraic interface and re-proving the
chain (`sumU_dropOne`, `sum_swap_ge`, `top_subset_optimal`) against it. The current proofs use
`Nat.add_assoc`, `Nat.add_comm`, `Nat.add_le_add_right` directly.

Estimate: **several hundred lines of new core-Lean**, one focused work session, not one loop
iteration. Claiming it in a single pass would be the overclaim this programme exists to prevent.

## Constraint the development already carries

The axiom audit forbids `propext`, which is why `memB` exists instead of `List.elem` and why
`le_of_add_le_add_right` is hand-rolled — core's versions leak the axiom. Any assembly must respect
that, and the CI negative control asserts the kernel actually rejects a false lemma, so a green
build is load-bearing.

## Status

Unchanged: `PAPER_PROOF_COMPLETE`, 17/18 machine-checked. Nothing here upgrades it. What changed is
the estimate: the work is available, local, fast to iterate, and bounded — and the two halves of the
lever are separable, so the assembly can land before the real-valued generalization.
