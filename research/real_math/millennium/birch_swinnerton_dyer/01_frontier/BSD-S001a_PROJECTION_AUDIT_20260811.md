# BSD-S001a — fixed-p projection sufficiency audit

**Date:** 2026-08-11  
**Control issue:** #90  
**Authority:** `SOURCE_BOUND_ROUTE_REFINEMENT / NO_NEW_THEOREM / ROOT_AUTHORITY_NONE`

## Atomic question

Which coordinates of the full Birch–Swinnerton-Dyer target are directly contained in, or rigorously recoverable from, the fixed-prime Selmer/Iwasawa objects admitted by the frozen `BSD-S001` context, and which coordinates still require an additional comparison theorem?

This audit does **not** assert that one prime is fundamentally incapable of determining the global BSD package. A sufficiently strong arithmetic rigidity/comparison theorem could in principle relate apparently separate coordinates. The question here is narrower: what is actually supplied by the inspected theorem interfaces without importing the desired complex BSD conclusion as an assumption or definition?

## Same-context expert cell

These are role-separated analytical passes, not independent mathematical reviews.

1. **Arithmetic-geometry lead** — separates Mordell–Weil rank, Tate–Shafarevich factors, torsion, Tamagawa factors, Néron period, and Néron–Tate regulator; blocks any silent replacement of the complex BSD normalization by a p-adic analogue.
2. **Iwasawa/Selmer lead** — records exactly what fixed-p Selmer groups, Kato classes, main-conjecture statements, and control theorems determine and under which reduction, residual-representation, finiteness, and local hypotheses.
3. **Complex↔p-adic bridge lead** — searches explicit reciprocity, higher derivatives, determinant lines, p-adic heights, and Bockstein regulators for a genuine comparison interface.
4. **Adversarial local-global reviewer** — tests whether a claimed bridge merely renames a missing all-primes or archimedean coordinate, or assumes the relevant BSD statement in order to define the comparison object.
5. **Formal-assurance lead** — keeps assumptions and direction of implication explicit, especially `BSD_p(E)`, finiteness of `Sha[p^∞]`, analytic-rank hypotheses, and Iwasawa main conjectures.
6. **Novelty/research-value lead** — checks whether the proposed “missing determinant” already exists in the primary literature before allowing new invention.

### Cell disposition

The cell agrees that the original `BSD-S001b` wording was too broad. A higher-rank exterior/determinant and Bockstein-regulator interface already exists in Burns–Kurihara–Sano. The research value now lies in isolating the **independent comparison/circularity gap**, not inventing another determinant package.

## Projection matrix

| Root coordinate | Fixed-p Selmer/Iwasawa information | Higher-rank BKS interface | Remaining obligation |
|---|---|---|---|
| Algebraic rank `rank E(Q)` | Can be constrained or recovered in important regimes only after exact Selmer/Sha hypotheses are accounted for; Selmer corank must not be silently identified with Mordell–Weil rank. | Exterior powers are naturally rank-sensitive. | Connect the resulting algebraic rank data to `ord_{s=1}L(E,s)` in arbitrary rank without assuming the desired complex equality. |
| `Sha(E/Q)[p^∞]` | Fixed-p descent/Iwasawa theory can control the p-primary component under theorem-specific hypotheses. | The GPRC/BSD_p discussion records p-primary arithmetic factors. | Preserve all finiteness and main-conjecture assumptions; this is not the full all-primes order of Sha. |
| `Sha(E/Q)[q^∞]`, `q != p` | No direct q-primary object is present in a fixed-p Selmer group. | Not generated merely by the p-adic determinant/Bockstein construction. | Either supply an independent global comparison/rigidity theorem or retain these factors as separate root obligations. No non-determination theorem is claimed here. |
| Torsion and Tamagawa/local factors | Algebraic/local quantities can be computed or controlled separately, but are not identical to p-Selmer corank. | Enter refined BSD_p normalizations and source formulas with hypotheses. | Bind exact normalization and primes; do not treat p-local recovery as the entire global product automatically. |
| Real period and Néron–Tate regulator | Archimedean/global real objects are not literally the p-adic height/Bockstein regulator. | BKS construct a canonical Bockstein regulator and compare it to higher-rank Euler-system derivatives. | Prove the required comparison to the complex/real leading-term package, or keep it as an explicit dependency. |
| Complex analytic order | Not a direct coordinate of a fixed-p Selmer group. Restricted-rank p-converse theorems supply genuine bridges in special regimes. | GPRC predicts arbitrary-rank higher-derivative compatibility and proves an order-of-vanishing component under hypotheses. | Establish an arbitrary-rank implication strong enough for the Clay rank equality without assuming analytic rank or BSD in the needed direction. |
| Complex first nonzero Taylor coefficient | Not a direct fixed-p Selmer output. | A canonical `eta^BSD` is placed in an exterior-power line and its Bockstein image is compared conjecturally to a derivative of Kato's zeta element. | The source explicitly defines `eta^BSD` using the complex leading term in the relevant construction, so this formulation cannot itself be used as an independent reconstruction of that term. |

## Primary-source refinement: the determinant interface already exists

Burns, Kurihara and Sano, **“On derivatives of Kato's Euler system for elliptic curves”**, arXiv:1910.07404, formulate a **Generalized Perrin–Riou Conjecture** connecting Darmon-type derivatives of Kato zeta elements to higher derivatives of the complex `L`-function. Their introduction explicitly constructs a canonical Bockstein regulator, places a canonical `eta^BSD` in a one-dimensional p-adic exterior-power line, and formulates a leading-term equality through the Bockstein map. The same source states an arbitrary-rank order-of-vanishing result under hypotheses and an arbitrary-rank connection between the p-part of BSD and an Iwasawa Main Conjecture.

This closes the *representation-search* subquestion that motivated `BSD-S001b`: the lane does not need to invent a determinant/exterior-power interface from scratch.

It does **not** close the BSD root bridge. In the source's finite-level formulation, `eta^BSD` is defined using the leading term of the complex `L(E,s)` at `s=1` (see the introduction around Definition 2.4 / Conjecture 1.1). Consequently, using the equality with `eta^BSD` as though it independently reconstructed the same complex leading term would be circular unless a separately algebraic/p-adic definition and a non-BSD-assuming comparison theorem are supplied.

Burns, Kurihara and Sano, **“On derivatives of Kato's Euler system and the Mazur–Tate Conjecture”**, arXiv:2103.11535, develops the sequel and gives unconditional evidence for positive-rank Mazur–Tate phenomena. It is a source for further algebraic reformulations and descent consequences, but every use in the BSD root DAG must preserve the assumptions of the exact theorem invoked; an implication proved under BSD or an Iwasawa main conjecture cannot be fed back as an unconditional proof of that assumption.

## Failure-cause normalization

**Supported diagnosis:** `P_ADIC_REPRESENTATION_EXISTS_BUT_COMPLEX_COMPARISON_CIRCULAR_OR_ASSUMPTION_BOUND`.

- **Observed route failure:** the original search question “find a determinant/higher-rank bridge” is no longer the correct first obstruction because a sophisticated determinant/Bockstein interface already exists.
- **Load-bearing cause:** the remaining root-critical information is in the direction and independence of the comparison. A p-adic/exterior object that is defined from the complex leading term, or a theorem whose hypotheses already contain BSD/BSD_p, cannot independently establish the root statement.
- **Authority:** `SUPPORTED_ROUTE_DIAGNOSIS`, not `VERIFIED_IMPOSSIBILITY`.
- **Non-guarantee:** this does not rule out a future independent comparison theorem, another prime-by-prime globalization argument, or a stronger motivic construction.

## Next atom — `BSD-S001c`

Freeze and audit the exact implication graph around the BKS Generalized Perrin–Riou / Bockstein interface:

1. identify every version of the determinant/exterior object that can be defined without using the target complex BSD leading term;
2. label each comparison theorem/conjecture by whether it assumes `BSD_p`, full BSD, Sha finiteness, an Iwasawa main conjecture, analytic-rank equality, or another open statement;
3. test whether any non-circular direction already yields arbitrary-rank `ord_{s=1}L(E,s)=rank E(Q)` or the required p-part/full leading term;
4. if not, isolate the smallest missing comparison identity and its exact input/output contract before generating a new mathematical candidate.

This is a source-bound re-representation milestone, not a theorem claim.
