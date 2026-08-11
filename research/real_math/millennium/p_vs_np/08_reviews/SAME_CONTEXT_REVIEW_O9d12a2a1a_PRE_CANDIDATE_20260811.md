# Same-context pre-candidate review — O9d12a2a1a

**Date:** 2026-08-11  
**Authority:** `SAME_CONTEXT_PRE_CANDIDATE_REVIEW / NOT_INDEPENDENT / NO_THEOREM_AUTHORITY`

## Frozen atom

`O9d12a2a1a`: repair C024's loss of cross-fusion correlation by a joint-consistency lower-bound representation that still has a bounded one-fusion budget, recovers the exact logarithmic `G_NEQ` calibration, and leaves room for a super-logarithmic full-cover lower bound.

No mathematical candidate is proposed in this review.

## Role cell

### 1. Complexity / graph-cover lead

Background: unrestricted circuit lower bounds, fusion method, discrete complexity, two-dimensional graph cover complexity.

Finding: C024 has already supplied the right local object—the exact cover graph—and a sound per-pair LP dual budget. The new atom is specifically about simultaneous integral choice. Proposition 40 is the cheapest exact calibration because its proof already normalizes each chosen pair to a complementary cut for the canonical `G_NEQ` witness family.

Strongest objection: the normalization in Proposition 40 is special. Treating arbitrary full semi-filters as if they were pairwise generator-separation constraints would silently retreat to canonical cover complexity, a lane already capped by C009.

Delegated check: derive only the `G_NEQ` joint-signature calibration first; explicitly mark every step that uses Claim 41/Lemmas 42–43.

Vote: **ACCEPT** the calibration action; **BLOCK** any general full-cover claim at this stage.

### 2. Communication-complexity / LP-hierarchy lead

Background: rectangle/fractional covers, set-cover relaxations, lift-and-project hierarchies.

Finding: Karchmer–Kushilevitz–Nisan makes the fractional-cover transfer historically natural, while generic set-cover hierarchy results warn that adding consistency variables is not automatically enough to remove a logarithmic gap.

Strongest objection: naming Sherali–Adams, Lovász–Schrijver, entropy, or pseudo-distributions without specifying the semi-filter preservation variables and the exact one-fusion charging law would be analogy inflation.

Delegated check: classify the first successor as a **calibration of joint consistency**, not as a hierarchy theorem; if it fails by an information-capacity ceiling, route to a higher-order state question.

Vote: **ACCEPT** a bounded joint-signature probe; **REVISE** any generic hierarchy proposal lacking a bespoke cover-graph encoding.

### 3. Information / coding lead

Background: separating systems, coding arguments, entropy and information inequalities.

Finding: after Proposition 40 normalization, an integral family of `k` cuts gives each diagonal witness a common `k`-bit signature. Simultaneous coverage requires the relevant witnesses to be distinguished by the same family, so `2^k` is the natural first capacity scale.

Strongest objection: this repair may be *too* successful as a compression: any certificate depending only on binary signatures of polynomially many distinguished traces is automatically logarithmically capacity-limited.

Delegated check: make the capacity ceiling the first hostile branch. Recovering `log N` on `G_NEQ` is necessary but not route progress unless the representation can exceed logarithmic scale elsewhere.

Vote: **ACCEPT** with immediate adversarial capacity test.

### 4. Adversarial upper-bound / counterexample lead

Background: quotient/twin compression, pair multiplexing, constructive cover upper bounds, finite exact counterexamples.

Finding: C010, C021, C023, and C024 point to a common failure pattern: local correctness can coexist with a globally cheap representation. The next representation should be attacked before any QR evaluation.

Strongest objection: a conflict graph on original generator traces may merely repackage the already-dead canonical lane. Its chromatic number is at most its number of vertices, so a polynomial-size trace universe is a likely logarithmic ceiling.

Delegated check: test four branches in order: (a) does `G_NEQ` recover `log N`; (b) is the certificate universally bounded by the number of trace signatures; (c) does C010-style multiplexing collapse it; (d) only if all survive, inspect a target.

Vote: **ACCEPT** as a route-pruning discriminator.

### 5. Formal-methods / verifier lead

Background: exact specification, proof DAGs, executable combinatorics, trust boundaries.

Finding: the next useful theorem object is small enough to state exactly: a signature-counting lemma under explicitly frozen hypotheses, followed by a scope theorem saying which first-order signature certificates it caps.

Strongest objection: terms such as “generator trace”, “conflict”, and “binary coordinate” must be defined as part of the candidate; no statement may quantify over arbitrary covers unless a map from arbitrary cover pairs to those objects has been proved.

Delegated check: require a regression test for the pure combinatorial capacity identity and an explicit source-scope assertion for the `G_NEQ` normalization.

Vote: **ACCEPT** a precisely scoped candidate after the process gate passes.

### 6. Novelty / primary-source lead

Background: circuit-complexity literature, source equivalence, bounded novelty review.

Finding: the binary-signature counting mechanism is elementary and should be presumed classical. The potential research value is not novelty of `2^k >= N`; it is the route-specific diagnosis that **restoring joint compatibility at generator-signature level still cannot supply a super-log full-cover invariant**.

Strongest objection: do not call this a new lower-bound technique. Chlamtac–Friggstad–Georgiou also cautions that strong generic consistency hierarchies can retain logarithmic set-cover gaps, but that result is not a theorem about this cover graph.

Delegated check: make no novelty claim; source-bind every imported fact and defer novelty review unless a genuinely stronger higher-order theorem survives.

Vote: **ACCEPT** as bounded route-pruning / representation diagnosis.

### 7. Learning-control / metacognition lead

Background: representation learning, fixation control, contrastive discrimination, search-policy evaluation.

Finding: C024 was a productive failure: it separated local fusion accounting from cross-fusion compatibility. The appropriate mode is `CONTRASTIVE_DISCRIMINATION + EFFECTUAL_PROBE`, not unconstrained hierarchy escalation.

Retrieval assessment: the new C024 tool/failure was retrieved immediately, together with the older multiplexing/scalar/cheap-target warnings. The currently merged Yang–Mills memory has no structurally applicable promoted tool for this atom, so cross-Millennium transfer is correctly left as `NO_SAFE_TOOL_TRANSFER`.

Fixation risk: high if “hierarchy” becomes a new vocabulary fixation. A tiny signature-capacity probe has much higher partition power: either compatibility restoration already fails, or it succeeds and exposes the next state-capacity obstruction.

Delegated check: if first-order signatures are logarithmically capped, open the next child around **higher-order semi-filter closure state**, not “a stronger hierarchy” generically.

Vote: **ACCEPT**.

## Cell synthesis

The seven roles agree on one next action **after** machine-auditing the strict packet:

1. instantiate a joint binary signature representation only for the source-justified `G_NEQ` normalization;
2. require it to recover the exact `log_2 N` lower bound that C024's fractional relaxation lost;
3. immediately attempt a general **low-order signature-capacity no-go**: any certificate whose entire state is the joint binary signatures of only polynomially many distinguished traces is at most `O(log N)`;
4. if that no-go holds, preserve the correlation repair as a calibration tool but open a fresh residual requiring higher-order semi-filter/closure correlations.

This action has high partition power because it distinguishes **compatibility failure** from **state-capacity failure** before any target-specific search.

## Unresolved warnings

- Proposition 40's complementary-cut normalization is not licensed outside its `G_NEQ` canonical witness family.
- A logarithmic capacity ceiling for first-order signatures would not rule out tuple signatures, lifted closure states, non-binary coordinates with separately bounded fusion information, or other higher-order invariants.
- Generic hierarchy integrality-gap results are method warnings only.
- Same-context agreement here is not independent review and creates no theorem authority.
- The breakthrough-learning modes used here are proposal-only.
