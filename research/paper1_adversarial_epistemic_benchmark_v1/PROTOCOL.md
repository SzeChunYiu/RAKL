# Paper I adversarial epistemic benchmark protocol (#489)

Status: `PROJECTION_SUBSTUDY_COMPLETE__BEHAVIOURAL_PRE_OUTCOME`

The programme has two evidence layers that must not be conflated.

## Layer 1 — deterministic projection sufficiency (completed)

For each of the 15 registered episode families, construct a minimal twin pair that differs in exactly one scientific coordinate and requires different canonical actions. Freeze the strongest fair state projection compatible with each comparator abstraction A–G. A projection collision is a pair with identical represented state but different gold update.

The projection-collision impossibility result gives an information bound: no deterministic policy operating only on a colliding projection can be correct on both worlds. This layer therefore evaluates **representational sufficiency**, not language-model reasoning.

Executable implementation: `src/rakl/epistemic_projection_benchmark.py`.  
Frozen result: `PROJECTION_SUFFICIENCY_RESULT_V1.json`.  
Formal mapping: `FORMAL_TO_EXECUTABLE_MATRIX.md`.

## Layer 2 — behavioural adversarial benchmark (still pre-outcome)

```text
design freeze
  -> episode generator + hidden gold (objective/semi-objective)
  -> freeze behavioural comparator implementations A–G
  -> development set + anti-degeneracy
  -> confirmatory set freeze BEFORE outcome access
  -> score + preserve negatives
```

Layer 2 must use the existing opaque-ID authority panels where applicable and retain legitimate promotion/revocation controls so blanket refusal cannot appear safe.

## Claim and independence boundary

The projection study does not establish natural scientific construct validity, LLM accuracy, or empirical superiority in open-ended research. Same-session critique is not independent review. External humans for Paper I remain a separate coordinate (#216).
