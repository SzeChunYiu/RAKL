# Same-context pre-candidate review — BSD-A1-RANK2-BRIDGE

Date: 2026-08-11  
Authority: `SAME_CONTEXT_REVIEW_ONLY / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`

This is a role-separated review inside one research context. It is **not** independent peer review.

## Shared frozen object

For an elliptic curve `E/Q` with `ord_{s=1} L(E,s)=2`, isolate the smallest unconditional bridge capable of producing two independent Mordell-Weil directions and eventually supporting the rank-two regulator/Sha leading-term contribution, without assuming BSD, an equivalent main conjecture, or a rank-one theorem outside its hypotheses.

Frozen context: `BSD_A1_RANK2_CONTEXT_FIBER_20260811.json`.

## Expert cell

### 1. Arithmetic-geometry lead

**Background:** elliptic curves, Mordell-Weil groups, Néron-Tate heights, Selmer groups, Tate-Shafarevich groups, descent.

**Evidence inspected:** Clay/Wiles refined formula; Gross-Zagier; Kolyvagin; Burns-Sano higher-rank systems.

**Finding:** rank two is an independence problem, not an existence problem. A single non-torsion point, a single Selmer class, or two dependent classes cannot support a nonzero rank-two regulator.

**Strongest objection:** a proposed Selmer-corank-two statement can still fail to prove rank two if the relevant Sha/divisible contribution is not controlled.

**Delegated check:** every future route must state exactly where two independent `E(Q)` directions enter, and whether Sha finiteness is proved or assumed.

**Vote:** `ACCEPT_CONTEXT / BLOCK_CANDIDATE_UNTIL_DEPENDENCY_AUDIT`.

### 2. Automorphic/L-function lead

**Background:** modular forms, functional equations, Rankin-Selberg L-functions, central derivatives, special-value formulae.

**Evidence inspected:** Wiles official statement; Gross-Zagier; current Clay status; Kim higher-Gross-Zagier preprint.

**Finding:** the classical rank-one bridge is first-derivative specific. Analytic rank two has even sign and vanishing first derivative, so a literal duplication of the Heegner-point narrative has no source-bound analytic justification.

**Strongest objection:** an arithmetic determinant without an exact theorem coupling it to `L''(E,1)` does not advance the analytic-to-arithmetic direction of BSD.

**Delegated check:** map every proposed arithmetic determinant to the exact complex or p-adic analytic quantity it is proven to detect; flag changes of L-function, field, twist, or normalization.

**Vote:** `ACCEPT_CONTEXT / PRIORITIZE_ANALYTIC_COUPLING_GAP`.

### 3. Euler-system / Iwasawa lead

**Background:** Euler systems, Kolyvagin/Stark systems, Iwasawa theory, p-adic L-functions, Selmer structures.

**Evidence inspected:** Burns-Sano; Kim; Kolyvagin; Burungale-Tian scoped converse.

**Finding:** higher-rank system machinery shows that exterior-power algebra is available, but target nontriviality and the correct local Selmer specialization are separate obligations. Several strong structural results become conditional exactly at a nontriviality or main-conjecture input.

**Strongest objection:** importing a localized main conjecture may simply relocate the desired BSD difficulty rather than solve the rank-two bridge.

**Delegated check:** build an assumption ledger for each higher-rank system theorem: representation hypotheses, reduction conditions, local conditions, nontriviality input, main-conjecture input, and exact arithmetic output.

**Vote:** `ACCEPT_CONTEXT / PRIORITIZE_NONTRIVIALITY_MAP`.

### 4. Adversarial falsification lead

**Background:** counterexamples, logical dependency audits, local-global pathologies, failure-mode classification.

**Evidence inspected:** all three transfer rows and the observability analogy.

**Finding:** the cheapest falsifier for a naive rank-two route is dependence: two nominal witnesses can span one direction. A second cheap falsifier is category leakage: a class over an auxiliary field or in a Selmer quotient may never yield two rational points over `Q`.

**Strongest objection:** “two classes” and “rank two” are not synonyms.

**Delegated check:** for every future candidate, demand a dependence counterexample, a field-of-definition check, a Sha absorption check, and a circular-regulator check before proof search.

**Vote:** `ACCEPT_CONTEXT / COUNTEREXAMPLE_FIRST`.

### 5. Formal-methods / assurance lead

**Background:** statement binding, proof obligations, dependency graphs, checker trust, formalizability.

**Evidence inspected:** current `AGENTS.md`, mathematical-research workflow, context/memory/trace schemas, Wiles exact statement.

**Finding:** the root must separate at least four claims: analytic rank equality, Mordell-Weil rank, Sha finiteness/order, and exact refined leading coefficient. A proof of one must not be serialized as the others.

**Strongest objection:** notation and normalization drift around completed/incomplete L-functions, periods, Tamagawa factors, and regulator conventions can silently change the statement.

**Delegated check:** the next artifact must be a theorem-dependency matrix with one row per logical arrow and explicit source/hypothesis/authority.

**Vote:** `ACCEPT_CONTEXT / MACHINE_AUDIT_REQUIRED`.

### 6. Novelty and breakthrough-method lead

**Background:** source verification, novelty risk, problem re-representation, contrastive learning, fixation detection, search-policy evaluation.

**Evidence inspected:** current Clay UNSOLVED status; accepted/scoped 2026 frontier result; Kim preprint; search results containing unreviewed complete-proof claims.

**Finding:** the useful re-representation is “rank-two observability”: existence, independence, nontriviality, and analytic coupling are distinct coordinates. This counters fixation on simply generalizing the rank-one narrative.

**Strongest objection:** recent unreviewed claims can distort the frontier if treated as established. They belong in novelty/adversarial review, not in the theorem DAG without verification.

**Delegated check:** maintain a bounded source ledger that labels `PEER_REVIEWED`, `PRIMARY_PREPRINT`, `OFFICIAL_STATUS`, and `UNVERIFIED_CLAIM`; do not average these authorities.

**Vote:** `ACCEPT_CONTEXT / REFLECTIVE_RESTRUCTURE`.

## Cross-review and disagreement

The automorphic lead would start from a candidate second-derivative formula; the Euler-system lead would start from a rank-two nontriviality statement. The arithmetic and adversarial leads object that either choice can be circular unless the full dependency chain is first exposed. The formal-methods lead agrees and makes the dependency matrix a prerequisite.

The cell therefore selects a **pre-candidate theorem-dependency audit** rather than a mathematical candidate.

## Selected next action

After the packet passes the executable context, memory, and trace gates, build a source-bound matrix for:

`analytic rank 2`
`-> rank-two arithmetic determinant/exterior class`
`-> target nontriviality`
`-> Selmer upper/lower control`
`-> two independent Mordell-Weil points`
`-> Sha finiteness/order`
`-> nonzero Néron-Tate regulator`
`-> exact complex leading coefficient with local factors`.

Each arrow must be labeled `UNCONDITIONAL`, `CONDITIONAL`, `CONJECTURAL`, or `ABSENT`, with primary-source anchors and the cheapest falsifier.

Only after this audit identifies the smallest genuinely missing arrow may a new mathematical candidate be generated.
