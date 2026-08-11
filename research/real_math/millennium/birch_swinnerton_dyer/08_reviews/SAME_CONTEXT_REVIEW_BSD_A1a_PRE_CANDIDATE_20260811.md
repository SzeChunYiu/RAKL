# Same-context expert review — BSD-A1a Kato nonvanishing bridge

**Atom:** `BSD-A1a-KATO-NONVANISHING-BRIDGE`  
**Authority:** `SAME_CONTEXT_REVIEW_ONLY / PRE_CANDIDATE / NOT_INDEPENDENT`

This review follows the source-bound dependency audit. It does not propose a theorem.

## 1. Arithmetic-geometry lead

**Background:** elliptic curves over `Q`, Mordell–Weil groups, Selmer groups, Tate–Shafarevich groups, heights.

**Finding:** A nonzero generalised Kato class is an interesting p-adic Selmer witness, but the target chain must preserve three distinct steps: class nonvanishing, p-adic Selmer dimension, and actual Mordell–Weil rank. The exact Selmer sequence permits a Sha Tate-module contribution, so `dim Sel=2` cannot be silently rewritten as `rank E(Q)=2`.

**Strongest objection:** a proof that ends at Selmer dimension two does not yet close the Clay rank statement, much less the refined leading coefficient.

**Vote:** `ACCEPT_CHILD_ATOM`; keep Sha/Mordell–Weil descent as a downstream residual.

## 2. Analytic/automorphic lead

**Background:** modular L-functions, Rankin/triple-product L-functions, central derivatives, functional equations.

**Finding:** Exact analytic rank two is a complex statement about the second-order central zero. Darmon–Rotger identify classical Heegner points as torsion in analytic rank greater than one, so the scalar first-derivative witness is not the right object. The current primary rank-two results introduce generalised Kato classes together with auxiliary automorphic data and p-adic L-functions.

**Strongest objection:** an auxiliary nonvanishing condition such as `L(E,ad^0(g),1) != 0` is not contained in the bare condition `ord L(E,s)=2`; any claimed generic implication must prove the existence/choice of admissible auxiliary data or state it as a hypothesis.

**Vote:** `ACCEPT_CHILD_ATOM`; first audit the exact complex-to-p-adic implication chain.

## 3. Euler-system / Iwasawa lead

**Background:** Euler systems, Kolyvagin systems, anticyclotomic Iwasawa theory, p-adic Selmer structures.

**Finding:** Castella–Hsieh 2022 supplies a real rank-two theorem: under explicit hypotheses, nonzero generalised Kato class implies two-dimensional p-adic Selmer group. Castella 2026 sharpens the converse by identifying nonzero localization as necessary and sufficient once Selmer dimension is two. This makes localization a load-bearing coordinate rather than a technical afterthought.

**Strongest objection:** starting from `dim Sel=2` to obtain `kappa != 0` would bypass the desired analytic-to-arithmetic bridge. Likewise, importing an Iwasawa main conjecture without decomposing its logical content can hide arithmetic strength comparable to the target.

**Vote:** `ACCEPT_CHILD_ATOM`; use explicit reciprocity/main-conjecture statements only after arrow-by-arrow strength audit.

## 4. Adversarial falsification lead

**Background:** counterexample-first theorem auditing, local-global failures, dependency analysis.

**Cheapest failure modes:**

1. class exists but vanishes;
2. complex `L'' != 0` maps to a p-adic quantity with an exceptional/kernel zero;
3. auxiliary twisted L-value needed for the construction vanishes;
4. Selmer dimension two is entirely or partly supported by Sha rather than two rational generators;
5. localization vanishes, defeating the converse nonvanishing route;
6. p-adic derived-height nonzero does not identify the real Néron–Tate regulator.

**Vote:** `ACCEPT_CHILD_ATOM`; require a transfer-kernel audit before formula invention.

## 5. Formal-assurance lead

**Background:** statement binding, proof DAGs, dependency/axiom audits, formalization boundaries.

**Finding:** The child atom is well-typed only if its conclusion is exactly `kappa_p(E) != 0` for a specified class, prime and auxiliary datum. It must not be phrased as “rank-two BSD follows” unless every subsequent Selmer/Mordell–Weil/Sha/regulator/local-factor edge is separately closed.

**Required candidate contract:** any future candidate must list all hypotheses, the exact definition of `kappa_p(E)`, the intermediate p-adic L-function/reciprocity object, and the nonvanishing-preserving theorem at every arrow.

**Vote:** `PASS_PRE_CANDIDATE_ONLY`.

## 6. Novelty / research-value lead

**Background:** primary-source frontier search, theorem-equivalence and rediscovery audit.

**Finding:** The current advance is a research-control refinement, not new mathematics. Darmon–Rotger 2016, Castella–Hsieh 2022 and Castella 2026 already identify the generalised-Kato/Selmer interface. RAKL's contribution in this packet is to locate the first unresolved generic arrow and prevent rank-one or p-adic statements from being over-promoted.

**Vote:** `NO_NOVELTY_CLAIM`; the next high-value action is the source-level implication graph.

## Cell decision

**Selected mode:** `REFLECTIVE_RESTRUCTURE + CONTRASTIVE_DISCRIMINATION + EFFECTUAL_PROBE`.

**Next action:** after the context, memory and trace gates pass, construct the explicit implication graph

`complex L''(E,1) != 0`
`-> relevant complex/triple-product nonvanishing data`
`-> p-adic L-function leading term`
`-> explicit reciprocity / derived-height quantity`
`-> kappa_p(E) != 0`

and annotate every arrow with theorem, hypotheses, possible kernel, and logical strength. Do not generate a mathematical candidate until the graph identifies a bounded missing bridge that does not assume its own conclusion.
