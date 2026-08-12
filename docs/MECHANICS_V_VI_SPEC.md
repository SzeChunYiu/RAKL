# Orion Mechanics V & VI — Testable Specification

The **Severity coordinate `S`** and the **Value/Promise projection `v(g)`** — the two
highest-leverage, most self-contained mechanics from
`docs/GENERATIVE_MECHANICS_PROGRAMME.md` §4. Status: engineering spec, proposal-only.

Attaches to the Paper I authority product order `(G,R,M,I,D)` and its no-scalar-collapse
theorem; validated under the Paper II confirmatory-lane protocol; attribution per
`docs/AI_CAPABILITY_SHAPING.md`.

**Four global invariants (binding on both):** (a) proposal-only — neither mints canonical
authority; (b) poset, never scalar — every ranking is a product order; (c)
freeze-before-outcome — thresholds/seeds/estimators/benchmark hashes frozen before result
access; (d) explicit model-vs-system attribution — gains reported as system-level via a
`ΔC` vector, never "the model reasons better."

Sign note: the programme defines `s(t,c) = P(test t passes | c false)` — the *false-pass*
probability, so **low `s` = severe test**. We also write the severity weight `σ = 1 − s`.

---

## Mechanic V — Severity coordinate `S`

**Purpose.** A non-compensatory sixth coordinate on the authority order that separates a
claim which survived a brutal, could-have-killed-it test from one which survived many weak
checks. `α = (G,R,M,I,D,S)`.

**Types (frozen-dataclass idiom).**
- `Test = (test_id, claim_id, context, prediction, pass_predicate, rival_set_id, independence_key, frozen_before_outcome)`
- `SeverityEstimate = (test_id, claim_id, s_false_pass: Optional[float], method, rival_set_id, rival_coverage_audited: bool, s_max)`; `method ∈ {ANALYTIC, SIMULATED, FREQUENTIST, WORST_CASE_SET(default), CANNOT_ESTIMATE}`.
- `SevereTestCertificate = (test_id, claim_id, context, verdict, estimate, observed_outcome: Optional[bool], independence_key, checker, proposal_only=True)`; `verdict ∈ {SEVERE_PASS, UNSEVERE_PASS, REFUTED, CANNOT_CHECK}`.
- `SeverityLevel = (level:int≥0, independent_severe_keys:frozenset, refuted_in_regime:frozenset)` — the `S` value.

**Semantics.**
- Severity: `s(t,c) = sup_{r ∈ R} P(t passes | r)` over the **live** rival set `R = {r ⇒ ¬c}` drawn from the current epistemic state (worst case: a test is only as severe as its easiest-to-fool rival). `σ = 1 − s`.
- Verdict (fail-closed): undecidable pass-predicate or missing outcome → `CANNOT_CHECK`; observed FAIL → `REFUTED`; passed but `s` unestimable or rival set unaudited → `CANNOT_CHECK`; passed with audited rivals → `SEVERE_PASS` iff `s ≤ s_max`, else `UNSEVERE_PASS`.
- Update (non-compensatory, product coordinate): `SEVERE_PASS` with a *new* `independence_key` increments `level`; `REFUTED` records the regime (revokes in-regime via the Paper I validity view, append-only, never deletes); `UNSEVERE_PASS` and `CANNOT_CHECK` are the identity.

**Three load-bearing, testable properties.** (1) An unsevere pass can never raise `S` — ten weak passes leave `level` unchanged, one severe pass increments it. (2) Independence required — same evidence lineage counts once (so `level ≥ 2` already carries a consilience flavor). (3) Refutation is append-only and revoking within a regime.

**Integration (no minting).** New `src/rakl/severity.py`; add `ObstructionKind.UNSEVERE_EVIDENCE_GAP` and a `severe_test` operator (family `FORMAL_VERIFICATION`) to `problem_solving_algebra.py` that complements the existing `counterexample_first`; the `S` coordinate is added to the authority ledger. The pass-predicate is executed by an **independent checker** and rivals audited before the certificate contributes to the authority view. For transferred claims (Mechanic II), `R` and `s` are computed against the witness's `NOT_PRESERVED` set and target boundary. A validated severe-test template consolidates (Mechanic III) with *method* authority only.

**Falsifiable success criterion (Paper II style).** Frozen `n`-claim benchmark across ≥4 exact-verifier families; a target-world executor computes the **true** `s*(t,c)` by exhaustive rival evaluation and a held-out TRUE/FALSE label; each claim carries weak tests and (where it exists) a severe test. Four arms: A pass-count baseline, B weighted-confidence scalar, C severity-blind evidence-count, D full severity gate. Primary: paired binary-Brier reduction of D vs A predicting held-out TRUE, **MDE 0.05**, 20k item-bootstrap CI. Co-primary **false-promotion rate**: fraction of FALSE claims reaching `S.level ≥ 1` (target 0). Decisive pre-registered test: a claim passing `k` weak tests must **not** outrank one passing 1 severe test — A/B must fail this, D must not. Freeze seed + generator + `s_max` + packet SHA public before execution; development instrument first survives a coordinate-ablated-twin circularity attack; failed instruments preserved as negative history.

**Goodhart guardrails.** Author-chosen weak rivals → `rival_coverage_audited=False` forces `CANNOT_CHECK`, and `sup_r` (worst case) not average. Cherry-picking / hiding failures → append-only negative history; `REFUTED` can't be dropped. Post-hoc test design → `frozen_before_outcome` required. Replay-to-inflate → `independence_key` dedup. Guessing `s` → `CANNOT_ESTIMATE → CANNOT_CHECK`. Scalar masking → product order mandatory (no-scalarization theorem).

**Amplification (system gain).** Where the target world is executable, the machine exhaustively enumerates rivals and computes `sup_r P(pass|r)` by execution — `EXTERNAL_CAPABILITY_SUBSTITUTION`: the solver computes the false-pass rate, the model only *proposes* tests/rivals. Reported as system uplift via four-arm + `ΔC`. Non-executable world → `CANNOT_CHECK` (honest fallback).

---

## Mechanic VI — Value/Promise projection `v(g)`

**Purpose.** A multi-objective, incomparable value profile over a candidate research goal
that triages the agenda ("research taste") as a **search-priority signal only**, replacing
the scalar `review_research_value` stub with a Pareto agenda that never collapses to one
number. `v(g) = (I, N, T, D, C, R)` = importance, novelty, tractability, discriminatory
leverage, cost, risk.

**Types.** `CoordinateEstimate = (axis, level: Optional[OrdinalLevel], higher_is_better, evidence_pointers, method, human_weight_required)`; `level=None` ⇒ `CANNOT_ESTIMATE`. `ValueProfile = (goal_id, importance, novelty, tractability, leverage, cost, risk, ethics_gate, proposal_only=True)`. `EthicsVerdict ∈ {CLEAR, REVIEW_REQUIRED, BLOCKED}`. `PolicyProjection = (goal_id, scalar, weights, owner, authoritative=False)` — the ONLY place a scalar may appear.

**Semantics.**
- `v(g)` is an incomparable poset element; comparison is the **sign-corrected product order** (Pareto dominance): `g1` dominates `g2` iff ≥ on every axis (sign-corrected: lower is better for C, R) and strictly > on at least one; **any `CANNOT_ESTIMATE` axis makes the pair incomparable, never favorable**.
- Per-coordinate provenance: `I` importance (human_weight_required); `N` novelty from frozen nearest-work witness; `T` tractability from operator-atlas reachability; `D` leverage = expected separation over the **live rival set** (shares Mechanic V's `σ`); `C` cost from the operator cost ledger; `R` risk + the fail-closed `ethics_gate`.
- Agenda = non-dominated sorting into Pareto layers; **Layer 0 is the agenda**, exposed with trade-offs, not tie-broken by a hidden scalar. A `PolicyProjection` scalar may be computed for one decision under named human weights but is `authoritative=False` and never re-enters the order. Ethics gate is non-compensatory: `BLOCKED` removes from every layer; `REVIEW_REQUIRED` demands human signoff before Layer 0.

**Integration.** Replaces the `review_research_value` stub with `project_research_value` (family `META_DISCOVERY`) which introduces obligations `{human_importance_signoff, ethics_review}` and **does not self-clear** `RESEARCH_VALUE_GAP`. New `src/rakl/research_value.py`. `N` uses Mechanic II nearest-work; `D` shares Mechanic V's rival set; consolidates (Mechanic III) with method authority only.

**Falsifiable success criterion (Paper II style).** Retrospective corpus of `n` goals with **known downstream outcomes** (realized importance, tractability-within-horizon, whether it actually discriminated, realized cost), lexically-independent sources. Four arms: A direct scalar "how promising?", B single-coordinate, C fixed-weight aggregate, D full Pareto. Metrics: top-k agenda precision/recall of Layer 0 vs realized-high-value; paired Brier reduction D vs A (**MDE 0.05**, bootstrap CI); **trade-off preservation** (pre-registered pass/fail) — scalar arms A/C force a total order and *must* mis-order truly-incomparable pairs (a direct empirical instance of the no-scalarization theorem), D must preserve them. Freeze estimators + bucket boundaries + weight-elicitation + packet SHA before any label; development instrument survives a lexical-novelty circularity attack.

**Goodhart guardrails.** Lexical-novelty inflation → `N` bound to frozen nearest-work with coverage audit. Scalarization creep → `ValueProfile` forbids storing a scalar; any scalar is a labeled non-authoritative `PolicyProjection`. `CANNOT_ESTIMATE` laundering → `None` ⇒ incomparable on that axis. Importance capture → `I.human_weight_required`; gap won't clear without human signoff. Dual-use → non-compensatory fail-closed ethics gate. Tractability optimism → `T`,`C` grounded in reachability + cost ledger + negative history.

**Amplification (system gain).** Wide parallel option survey with broad nearest-work retrieval and exhaustive rival enumeration for `D` — `Amplify + Externalize + Route`, reported as system gain via four-arm + `ΔC`, not "the model has better taste." Humans retain importance weights and ethics decisions; the machine ranks and exposes trade-offs.

---

## Shared implementation notes

- **Files:** new `src/rakl/severity.py`, `src/rakl/research_value.py`; edit `problem_solving_algebra.py` (add `UNSEVERE_EVIDENCE_GAP`, `severe_test`; replace `review_research_value` body with non-self-clearing `project_research_value`); authority ledger gains `S`.
- **One rival-set object `R`** (the live "not-c" alternatives), built once from the epistemic state: `S` consumes it for `σ`, `v(g).D` for expected separation.
- **Only two scalars in the whole design, both quarantined:** `s`/`σ` (a per-test statistic) and `PolicyProjection.scalar` (`authoritative=False`). Neither enters a product order.
- **`CANNOT_CHECK` / `CANNOT_ESTIMATE` are first-class terminals**, never coerced favorable.
- **Every benchmark follows the Paper II ritual:** frozen seed + generator + thresholds + packet SHA public before the seed executes; four arms; item-bootstrap CIs; sign test across ≥6 families for any broad law; `ΔC` reported with blocking regressions dominant; scope boundary stated so system uplift is never reported as model capability.
