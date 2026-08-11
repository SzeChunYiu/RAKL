# BSD-A1 rank-two theorem-dependency audit — 2026-08-11

**Parent atom:** `BSD-A1-RANK2-BRIDGE`  
**Root:** issue #91  
**Authority:** `SOURCE_BOUND_FRONTIER_AUDIT / ROUTE_PRUNING / NO_MATHEMATICAL_CANDIDATE / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

This audit executes the `NEXT_STEP_PROPOSED` action frozen in the strict pre-candidate packet. It does **not** introduce a new theorem candidate. Its purpose is to classify the arrows between complex analytic rank two and the full BSD arithmetic package before candidate generation.

## Expert cell

The following are role-separated same-context passes, not independent peer review.

1. **Arithmetic-geometry lead — Mordell–Weil/Sha interface.** Tracks what a Selmer statement actually implies about rational points, independence, the Néron–Tate regulator, and the Tate–Shafarevich group.
2. **Analytic/automorphic lead — complex L-function interface.** Tracks the exact central order, functional-equation parity, auxiliary Rankin/triple-product nonvanishing hypotheses, and whether a p-adic class is genuinely forced by the complex condition `ord_{s=1}L(E,s)=2`.
3. **Euler-system/Iwasawa lead — cohomological bridge.** Tracks classical Heegner/Kolyvagin scope, generalised Kato classes, p-adic Selmer dimension, main-conjecture inputs, and localization maps.
4. **Adversarial falsification lead — implication breaker.** Searches for the cheapest logical counterexample to each attempted arrow: torsion witnesses, collinear classes, Sha contributions, local-global loss, or p-adic/complex normalization mismatch.
5. **Formal-assurance lead — dependency and quantifier audit.** Keeps `rank equality`, `Sha finiteness/order`, `regulator identity`, and `full leading coefficient` as separate proof obligations and rejects circular use of a rank-two regulator before two independent global points are established.
6. **Novelty/research-value lead — frontier calibration.** Separates accepted theorems, conjectural implications, preprint/book-chapter updates, and mere route synthesis. No result below is represented as new mathematics.

### Cell consensus

The strongest re-representation is no longer generic “rank-two determinant/exterior object.” Primary sources identify a more precise intermediate object: a **generalised Kato class** in the p-adic Selmer group. The highest-information unresolved arrow is therefore the non-circular bridge

`complex analytic rank exactly 2 -> nonvanishing of a suitable generalised Kato class`,

followed separately by the Selmer-to-Mordell–Weil/Sha and p-adic-to-complex-leading-term bridges.

The classical Heegner-point witness is route-pruned at rank two: Darmon–Rotger explicitly identify its limitation as torsion in analytic rank greater than one. This is a known structural limitation, not a new impossibility theorem.

## Primary-source refresh

### P1 — Darmon–Rotger, 2016

Henri Darmon and Victor Rotger, *Elliptic curves of rank two and generalised Kato classes*, Research in the Mathematical Sciences **3** (2016), article 27, DOI `10.1186/s40687-016-0074-9`.

Primary URL: `https://link.springer.com/article/10.1186/s40687-016-0074-9`

Load-bearing scope:

- classical Heegner points encode first derivatives but are torsion in analytic rank `>1`;
- generalised Kato classes are proposed as the replacement in double-zero settings;
- their nonvanishing in the relevant rank-two situation is a conjectural arithmetic bridge, not an automatic consequence of `L''(E,1) != 0`.

### P2 — Castella–Hsieh, 2022

Francesc Castella and Ming-Lun Hsieh, *On the nonvanishing of generalised Kato classes for elliptic curves of rank 2*, Forum of Mathematics, Sigma **10** (2022), e12, DOI `10.1017/fms.2021.85`.

Primary URL: `https://www.cambridge.org/core/journals/forum-of-mathematics-sigma/article/on-the-nonvanishing-of-generalised-kato-classes-for-elliptic-curves-of-rank-2/72ED842AB428A7ED619B1B84287A6864`

Load-bearing scope:

- for `E/Q`, a good ordinary prime `p>3`, sign `+1`, `L(E,1)=0`, a CM auxiliary weight-one eigenform `g`, nonvanishing `L(E,ad^0(g),1)`, and the paper's residual/local hypotheses, Theorem A proves

  `kappa != 0  =>  dim_{Q_p} Sel(Q,V_pE) = 2`;

- the converse is proved under an additional nonzero localization condition;
- the paper explicitly notes that the BSD conjecture would identify `dim Sel = 2` with complex analytic rank two; that identification is not supplied for free by the theorem;
- the resulting class is naturally interpreted through a `P wedge Q` / p-adic logarithmic regulator picture, but this is not yet the full complex BSD regulator formula.

### P3 — Castella, 2026

Francesc Castella, *Nonvanishing of Generalised Kato Classes and Iwasawa Main Conjectures*, in *Elliptic Curves and Modular Forms in Arithmetic Geometry* (Springer, 2026), pp. 23–50, DOI `10.1007/978-3-032-13123-2_2`; preprint `arXiv:2312.01481`.

Primary URLs:

- `https://arxiv.org/abs/2312.01481`
- `https://link.springer.com/book/10.1007/978-3-032-13123-2`

Load-bearing scope:

- generalised Kato classes are available for positive even analytic rank at good ordinary primes in the stated setup;
- the paper reproves the implication `kappa_p(E) != 0 => dim Sel(Q,V_pE)=2`;
- when the Selmer group is two-dimensional, the converse holds **if and only if** the localization map `loc_p` is nonzero;
- this sharpens the logical boundary: Selmer dimension two alone does not automatically deliver generalised-Kato nonvanishing.

### P4 — Clay/Wiles root contract

Andrew Wiles, official Clay problem description, *The Birch and Swinnerton-Dyer Conjecture*.

Primary URL: `https://www.claymath.org/wp-content/uploads/2022/05/birchswin.pdf`

The official root statement identifies the order of vanishing at `s=1` with `rank E(Q)`; the refined formula adds the leading coefficient data. This audit never substitutes a p-adic Selmer statement for that complex root contract.

## Dependency matrix

| Arrow | Classification at this audit | Exact reason / scope | Cheapest failure test |
|---|---|---|---|
| `analytic rank 2 -> classical Heegner point gives a non-torsion direction` | **ROUTE-PRUNED** | Darmon–Rotger state the classical Heegner-point limitation: torsion in analytic rank `>1`. The rank-one first-derivative witness cannot simply be duplicated. | Check whether the proposed witness is genuinely a classical Heegner point governed by the first-derivative setting; if so, test its rank-`>1` torsion consequence before any independence argument. |
| `analytic rank >=2, even sign -> a suitable generalised Kato class can be constructed in the stated p-adic/auxiliary setup` | **UNCONDITIONAL-CONSTRUCTION-WITH-HYPOTHESES** | Darmon–Rotger/Castella construct the relevant p-adic classes under explicit ordinary/auxiliary-form conditions. Construction is not nonvanishing. | Verify good-ordinary and auxiliary Rankin/triple-product hypotheses and that the constructed projection really lands in `Sel(Q,V_pE)`. |
| `complex analytic rank exactly 2 -> kappa_p(E) != 0` | **CONJECTURAL / PARTIAL SPECIAL-CASE SUPPORT** | Darmon–Rotger formulate the rank-two nonvanishing expectation. Castella–Hsieh prove first cases of the Selmer-dimension/nonvanishing conjecture under CM auxiliary hypotheses; Castella 2026 sharpens the Selmer/localization criterion. None of these, at the recorded scope, gives a generic theorem `ord L = 2 => kappa != 0` for every `E/Q` without additional arithmetic input. | Look for an argument whose only load-bearing analytic assumption is `ord_{s=1}L(E,s)=2`; reject it if it silently invokes Selmer dimension two, a main conjecture, localization nonvanishing, or a BSD-strength converse. |
| `kappa_p(E) != 0 -> dim_{Q_p} Sel(Q,V_pE)=2` | **UNCONDITIONAL UNDER EXPLICIT THEOREM HYPOTHESES** | Castella–Hsieh Theorem A proves this under its good-ordinary, residual, auxiliary CM/nonvanishing and level hypotheses; Castella 2026 gives a new proof in its stated setup. | Check every prime, residual representation, auxiliary form/character, root-number, and local level condition before reuse. |
| `dim Sel(Q,V_pE)=2 -> kappa_p(E) != 0` | **CONDITIONAL ON LOCALIZATION** | Castella 2026 gives the converse iff `loc_p` is nonzero; the 2022 result has the corresponding localization condition in its theorem. | Test whether `Sel(Q,V_pE)=ker(loc_p)`. If yes, Selmer dimension two cannot be promoted to nonvanishing by this route. |
| `dim Sel(Q,V_pE)=2 -> rank E(Q)=2` | **NOT AUTOMATIC / SHA-SEPARATION REQUIRED** | The p-adic Selmer group contains the Mordell–Weil image and can also carry a Tate-module contribution from Sha. Selmer dimension is not definitionally Mordell–Weil rank. | Audit the Selmer exact sequence and independently control the relevant p-primary Sha contribution; reject dimension counting that omits it. |
| `rank E(Q)=2 -> exact rank-two regulator and Sha factor` | **SEPARATE OBLIGATIONS** | Two independent points make a rank-two regulator definable, but BSD requires the exact Néron–Tate determinant and the order/finiteness of Sha, not merely rank. | Check for circular use of a nonzero regulator to prove the independence needed to define the intended basis; independently bind Sha finiteness/order. |
| `p-adic derived height / regulator data -> full complex BSD leading coefficient` | **ABSENT GENERIC BRIDGE IN THIS AUDIT** | The primary rank-two generalised-Kato results use p-adic L-functions, localization and derived p-adic heights. The Clay refined formula is a complex leading-term statement with real period, Néron–Tate regulator, Tamagawa/local factors, torsion and Sha. | Require an explicit comparison theorem with all normalizations; reject any argument that identifies a p-adic leading term with the complex BSD constant by analogy alone. |

## Atomic gap selected by the cell

### `BSD-A1a-KATO-NONVANISHING-BRIDGE`

**Question.** For an elliptic curve `E/Q` with exact complex analytic rank two, what is the weakest source-bound set of additional hypotheses under which the complex condition forces a suitable generalised Kato class `kappa_p(E)` to be nonzero, without importing `dim Sel=2`, BSD, or an Iwasawa/main-conjecture statement whose target specialization already contains equivalent-strength arithmetic rank information?

This is deliberately narrower than “prove BSD in rank two.” It isolates the first currently visible nontrivial arrow in the analytic-to-arithmetic chain.

### Required coordinates for the child context

- exact choice and independence of the good ordinary prime `p`;
- auxiliary weight-one form / CM character and the exact nonvanishing `L(E,ad^0(g),1)` input;
- complex order `ord_{s=1}L(E,s)=2` versus merely positive even order;
- which p-adic/triple-product L-function controls the class and what its leading term measures;
- whether an Iwasawa main-conjecture divisibility/equality is assumed or proved;
- localization `loc_p` and strict Selmer kernel;
- distinction between Selmer dimension, Mordell–Weil rank, and Sha Tate module;
- exact regulator object: derived p-adic height, `P wedge Q` logarithmic image, or Néron–Tate determinant;
- every period, Euler/Tamagawa, torsion and Sha normalization needed for eventual return to the Clay refined formula.

## Breakthrough-mode assessment

- **Reflective restructure:** retained. Replace the vague “rank-two determinant” search with the concrete `complex L'' -> generalised Kato nonvanishing -> Selmer dimension` interface.
- **Contrastive discrimination:** retained. Compare rank one (`L' -> Heegner point`) with rank two (`classical Heegner point torsion; higher-order class required`) and explicitly mark the broken derivative/witness assumption.
- **Fixation reset:** triggered for any attempt to produce two independent rational points by duplicating classical Heegner data.
- **Bounded recombination:** allowed only if a proved complex leading-term statement and a proved p-adic nonvanishing/localization theorem have compatible hypotheses and normalizations; no “Gross–Zagier twice” shortcut.
- **Effectual probe:** before theorem invention, build a source-level implication graph for one concrete theorem family and test where `ord L=2` first disappears and a Selmer/main-conjecture assumption enters.
- **Explanation reconstruction:** the load-bearing failure should be expressible without the original narrative: a rank-one scalar witness loses rank-two independence; the higher-order replacement exists, but its generic nonvanishing from the complex analytic condition is not yet supplied.

## Residual / handoff

No mathematical candidate is authorized by this audit. The next strict cycle should open a fresh context fiber for `BSD-A1a-KATO-NONVANISHING-BRIDGE`, query the now-updated BSD/cross-Millennium memories, and construct a theorem-hypothesis implication graph centered on Darmon–Rotger 2016, Castella–Hsieh 2022 and Castella 2026. Candidate generation should begin only after that child context/memory/trace sequence passes the current `main` gates.
