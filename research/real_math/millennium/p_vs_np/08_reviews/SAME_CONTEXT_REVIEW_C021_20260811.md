# Same-context five-role review — C021

**Independence status:** `SAME_CONTEXT_ONLY`. This review is not independent peer review and does not satisfy the three-isolated-review gate.

## Frozen claim under review

For every odd prime `p`, with `n=ceil(log2 p)`,

`rho(QR_p,G_{p,p}) <= D_intersection(QR_p | G_{p,p}) = O(n log^3 n)`.

The source chain is Brent–Zimmermann Jacobi time, Harvey–van der Hoeven multiplication time, Pippenger–Fischer machine-to-network simulation, then C020's dual-rail network-to-intersection construction.

## Complexity-theory lens

**Vote: ACCEPT AS PROOF DRAFT.** The asymptotic composition is coherent and materially sharpens C020 from `O(n^3)` to `O(n log^3 n)`.

**Concern CT-M1, blocking for theorem promotion:** the statement must not silently identify all bit-complexity machine models. Brent–Zimmermann's `M(n)` convention, Harvey–van der Hoeven's fixed-multitape model, and Pippenger–Fischer's machine model must be bound explicitly.

**Resolution test:** formalize or source-check a single deterministic multitape machine model carrying the Jacobi algorithm with `O(n log^2 n)` time, then instantiate the network simulation on that exact machine.

## Meta-complexity lens

**Vote: ACCEPT WITH ROOT SCOPE ZERO.** C021 is an upper bound on an R004 candidate's cover complexity. It has no MCSP threshold consequence and no direct P-versus-NP implication.

**Concern MC-M1:** near-linear-log cover complexity does not rule out a super-logarithmic lower bound. The residual window is narrow but nonempty.

**Resolution test:** either construct `O(log p)` cover complexity or develop a lower-bound invariant that provably separates `omega(log p)` from the `O(log p (log log p)^3)` ceiling.

## Adversarial proof-review lens

**Vote: REVISE BEFORE THEOREM AUTHORITY.** Three interface risks remain.

1. The combinational network may use a gate basis different from De Morgan.
2. The graph side has `p` rather than `2^n` rows/columns.
3. The three-valued Jacobi output must be bound to the Boolean `+1` predicate with zero excluded.

The draft addresses each at paper level: fixed bounded-fanin gates have constant De Morgan simulations; bit predicates are unions over valid rows/columns only; the zero-difference boundary is explicit and finitely tested.

**Resolution test:** encode these interfaces as formal lemmas rather than relying on prose.

## Formal-methods lens

**Vote: REVISE.** The finite checker validates the Jacobi/QR statement binding on small primes but does not certify the fast algorithm, machine-time analysis, or circuit compilation.

**Concern FM-M1, blocking:** no theorem-prover artifact, formalization witness, proof receipt, dependency/axiom audit, or isolated recheck exists.

**Resolution test:** formalize the generic machine-to-De-Morgan-to-intersection wrapper first; source the fast Jacobi algorithm as an external theorem only after its machine-model contract is exact.

## Novelty/research-value lens

**Vote: ACCEPT ONLY WITH `NO_NOVELTY_CLAIM`.** The ingredients are established results. The combined corollary may be implicit or standard. Its present value is route control: it shows that the Paley candidate lies only a polylog-log factor above the target logarithmic scale and exposes an adjacency-circuit explicitness screen for future families.

**Concern NV-M1:** do not publish C021 as a standalone new theorem without a dedicated structural prior-art search across graph complexity, intersection complexity, Paley graphs, and circuit complexity of Jacobi/Legendre predicates.

## Synthesis

All five lenses agree that C021 is safe to retain and merge as a bounded proof draft if CI is green and its status remains non-novel and non-root. The main disagreement is not about the asymptotic arithmetic but about whether source-model alignment is sufficiently formal for theorem authority. It is not. Promotion remains blocked.
