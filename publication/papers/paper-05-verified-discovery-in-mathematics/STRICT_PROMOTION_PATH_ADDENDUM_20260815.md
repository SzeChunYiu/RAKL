# Paper V — strict current promotion path (2026-08-15)

Status: binding local-closure addendum. Historical `math_research_assurance*` classifiers remain available for reproducibility, but **they are not the current closure-eligible promotion facade**.

The current local path is:

```text
MathResearchRecord
  -> content-addressed v4 assurance
     (current proposer + exact informal/formal pair + complete novelty dossier
      + exact value review + independent verifier attestation)
  -> exact proof-source dependency-manifest equality against ProofDAG
  -> strict_math_candidate(...)
  -> candidate eligibility for the existing protected research gate only
```

Implementation: `src/rakl/math_research_promotion_strict.py`.

A record that reaches `NEW_MATHEMATICS_CANDIDATE` through the historical v1 classifier is **not** current strict eligibility by itself. The strict facade additionally requires all load-bearing actor/procedure/artifact identities to be content-addressed through v4 and requires the proof-source transitive dependency manifest to equal the ProofDAG closure.

The facade is deliberately non-sovereign: even a positive `eligible_new_mathematics_candidate=true` grants no theorem, novelty, research-value, scientific or publication authority. Concrete novelty/value still require the external literature/reviewer trust roots represented by the supplied digests.
