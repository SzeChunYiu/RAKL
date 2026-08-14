# Local compute results and implemented patches

Scope: model-free / finite known-world development only. None of these results grant manuscript efficacy, production-policy, theorem, novelty, or scientific authority.

## A. Paper IV — allocator audit

### Existing v1 production failure mechanism

`src/rakl/training_scheduler.py` chooses one target coordinate and fills the non-repetition batch from that coordinate. The already-preserved model-free development result localized a concentration/forgetting failure.

### Existing marginal-gain challenger v1

`src/rakl/training_scheduler_challenger.py` improves two things:

- mastery level -> believed marginal gain;
- whole-round target -> per-slot water filling.

However, it computes one `worst_mastery[coordinate] = min_over_structures mastery[structure, coordinate]` and scores **every** candidate against that global value. Selecting any candidate then updates that global coordinate as if it repaired whichever structure supplied the minimum.

### New atomic defect: structure-identity collapse

Minimal frozen counterexample:

```text
S1 composition mastery = 0.10; C1 is bound to S1; expected composition gain = 0.20
S2 composition mastery = 0.90; C2 is bound to S2; expected composition gain = 0.30
```

Global-worst score:

```text
C1 = 0.20 * (1 - 0.10) = 0.18
C2 = 0.30 * (1 - 0.10) = 0.27  -> chooses C2
```

Structure-conditioned score:

```text
C1 = 0.20 * (1 - 0.10) = 0.18  -> chooses C1
C2 = 0.30 * (1 - 0.90) = 0.03
```

The v1 challenger therefore can spend a slot on an already-mastered structure because the low mastery belonged to another structure.

Counterexample protocol SHA256: `5b06869dd04cde7b5c89e29a3a35e551d64947215741bed0b04ec93198650aa7`.

### Fresh multi-structure known-world assurance

Frozen protocol SHA256: `dcbdb9b9ce710cf266b18eca89a832ce58c55455a7ca4ac45800898fa8013211`.

Design:

- 4 structural identities;
- 6 mastery coordinates each;
- candidate effects scoped to the candidate's own structural identity;
- 6 rounds × 8 slots;
- 512 development random worlds;
- 1,024 disjoint fresh-assurance worlds;
- primary metric: mean over structures of each structure's minimum mastery coordinate (`noncompensatory structural coverage`).

Fresh assurance:

| arm | structural coverage | balanced mastery | global worst | cost | misattributed slots |
|---|---:|---:|---:|---:|---:|
| Current global-worst marginal gain F | 0.413958 | 0.705068 | 0.245199 | 55.2225 | 0.822347 |
| Static structural | 0.500288 | 0.717172 | 0.429827 | 55.2025 | 0 |
| Structure-conditioned SC-v1 | **0.593695** | **0.747377** | **0.496810** | 55.2117 | **0** |

Paired fresh differences:

```text
SC - F structural coverage = +0.179737
bootstrap 95% CI = [0.176294, 0.183262]

SC - F balanced mastery = +0.042309
bootstrap 95% CI = [0.041429, 0.043163]

SC - Static structural coverage = +0.093407
bootstrap 95% CI = [0.090803, 0.096032]
```

Interpretation: strong **software-mechanic / known-world** evidence that preserving structural identity matters. It is not evidence that an LLM training policy is effective.

### Implemented successor

New branch file:

`src/rakl/training_scheduler_challenger_v2.py`

Properties:

- keeps believed state at `(structure_id, coordinate)` resolution;
- scores a candidate against its own bound structure;
- selecting a candidate updates its **full expected gain vector** only on its own structure;
- preserves candidate-level forgetting/negative-transfer hard gates;
- preserves the snapshot repetition floor;
- leaves production scheduler and challenger-v1 untouched;
- cannot mint scientific, structural-transfer, or training-policy authority.

Tests:

`tests/test_training_scheduler_challenger_v2.py`

The first test is deliberately adversarial: v1 must select C2 and v2 must select C1 on the frozen counterexample.

## B. Paper IV — additional negative design work

### Cost-aware direct scalarization

Frozen protocol SHA256: `d69b756471031a6caaa57060e739ef0cd055987e86809a8bf75566d8446de99a`.

A cost-aware capped challenger reduced cost but lost a small amount of balanced mastery versus F. Treat cost as a Pareto coordinate, not a score that can silently replace structural value.

### Near-tie cost selector

Frozen protocol SHA256: `2424f416be20cb3873f45549e75fe6c53e40aa49c3f8e0115ae8be8768ad0f78`.

Fresh vs F:

```text
balanced mastery: -0.0000495, 95% CI [-0.0001598, +0.0000597]  (indistinguishable)
hard-safety minimum: +0.007633, 95% CI [0.006608, 0.008657]
cost: -0.60724, 95% CI [-0.66086, -0.55421]
```

But per-world hard-safety harm below -0.01 occurred in 14.5% of cases. A favorable mean cannot compensate for this tail under RAKL's hard-safety semantics.

### Fixed safety-floor target chasing — rejected in development

Frozen protocol SHA256: `0e66205f5c06cf6d851d29466c8a061768988f0815af59f36d26df1be7b6deb1`.

No candidate met the frozen development selection rule. Do **not** spend a fresh-assurance seed on this family. Fixed per-slot floor chasing is too blunt; preserve safety as a hard feasibility/admission condition rather than turning every safety coordinate into a budget-consuming target.

## C. Paper V — finite authority-product counterexample

New branch test:

`tests/test_p5_finite_authority_product.py`

Exhaustive Boolean world over:

```text
SPECIFICATION
TRUTH
NOVELTY
VALUE
VERIFIER_TRUST
```

For a novelty-bearing theorem candidate, a hard product gate requires specification + truth + novelty + verifier trust. `VALUE` stays separate.

Exhaustive result over all 32 states:

```text
product gate: 2 promoted, 0 invalid intended-claim promotions
4-of-5 scalar/majority gate: 6 promoted, 3 invalid intended-claim promotions
```

The three scalar false promotions are exactly the states missing one load-bearing coordinate:

- specification;
- theorem truth;
- verifier trust.

The test also verifies that theorem truth can remain fixed while novelty decreases after literature expansion.

This is finite conformance evidence for the product architecture, not a Lean proof or autonomous-discovery result.

## D. Paper VI / framework — registry-bound closure

New branch module:

`src/rakl/bounded_closure.py`

New tests:

`tests/test_bounded_closure.py`

The certificate binds:

```text
exact subject SHA
cutoff
exact mechanic registry hash
mechanic IDs
closed mechanic IDs
```

Semantics:

- `CLOSED_AT_REGISTERED_CUTOFF` is permitted only when every mechanic in the exact registry satisfies the local closure coordinates;
- `global_completeness_claimed` is always false;
- adding a new mechanic changes the registry hash and invalidates the old certificate for the new roster;
- the historical old certificate remains valid for its old roster/cutoff;
- a decisive negative can count as `evidence_present`; closure is not a positive-benefit claim.

This is the appropriate replacement for unqualified present-tense wording such as “all thirteen mechanics are closed” after M1–M16 have been registered as new research candidates.

## Next local gate

Run exact repository tests/CI on the branch. If any test reveals a contract mismatch, fix the challenger/spec under a new commit without modifying frozen scientific results.