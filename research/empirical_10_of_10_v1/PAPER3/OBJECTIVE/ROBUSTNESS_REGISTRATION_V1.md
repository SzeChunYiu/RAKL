# Paper II objective robustness extension — preregistration v1

Status: `FROZEN_PRE_DEVELOPMENT_OUTCOME`

This extension was named before the four-family primary confirmatory outcomes and is executed only after that primary epoch closed. It is a **new evidence epoch**, not a post-outcome enlargement of the successful primary benchmark.

## Scientific question

Does the residual value of the full directional applicability contract over a derived-effect / mechanism-only control reproduce across six new exact-verifier families whose mathematical semantics differ materially from the primary flow/logic/units/state set?

The primary contrast is again:

```text
FULL_APPLICABILITY_CONTRACT - MECHANISM_DERIVED_EFFECT_ONLY
```

Lexical similarity is a diagnostic control, not the load-bearing scientific baseline.

## Frozen extension families

1. `linear_systems_invariant_maps`
   - exact verifier: mapped linear-dynamics consequence under registered discrete/continuous regime and stability/controllability preconditions;
   - hostile invalids include time-regime reversal, unstable target dynamics and violated applicability assumptions.

2. `probabilistic_graphical_models`
   - exact verifier: graph-theoretic conditional-independence / d-separation consequence under registered observation/intervention semantics;
   - hostile invalids include collider/conditioning changes and intervention-vs-observation boundary mismatch.

3. `algorithm_datastructure_invariants`
   - exact verifier: candidate algorithm transformation executes correctly only when target ordering/data-structure invariants and operation preconditions hold;
   - hostile invalids include sortedness/comparator failures and direction-sensitive operation reversal.

4. `synthetic_causal_graphs_interventions`
   - exact verifier: registered adjustment/transport operation identifies the target intervention effect only when target graph, positivity and transport/invariance assumptions hold;
   - hostile invalids include unblocked backdoor paths, positivity failure and population-mechanism shift.

5. `optimization_feasibility_obligations`
   - exact verifier: candidate transformed optimum/KKT consequence is licensed only when target feasibility, convexity/constraint qualification and QoI are satisfied;
   - hostile invalids include stationarity-without-feasibility and boundary/constraint-qualification failure.

6. `local_global_gluing_interfaces`
   - exact verifier: local components compose only when registered overlap/interface constraints admit a global assignment;
   - hostile invalids include pairwise-compatible but globally inconsistent parity/cocycle cases.

## Item strata

Each family must contain fresh instances of:

- `VALID_DISTANT_TRANSFER`;
- `SEMANTIC_NEAR_MISS_INVALID_TRANSFER`;
- `DIRECTION_REVERSED_INVALID`;
- `BOUNDARY_QOI_MISMATCH`;
- `PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK`;
- `VALID_NEAR_CONTROL`;
- `INVALID_DISTANT_CONTROL`.

Surface similarity must be balanced independently of verifier validity. Hidden family/item/perturbation identities are not candidate-visible.

## Ground-truth rule

Gold is produced only by executing a family-specific verifier on the target-world contents. No verifier may branch on item type, semantic-near/far label or hidden perturbation identity. Tests must mutate hidden metadata and require identical gold outcomes.

## Candidate arms frozen before confirmatory outcomes

- lexical/Jaccard diagnostic;
- relation/invariant projection;
- derived-effect / mechanism-only projection;
- coordinate-ablated twin;
- full applicability contract.

The mechanism-only arm must see the same machine-readable world evidence as the full arm except the separately registered applicability coordinates (QoI/boundary/precondition/forbidden-loss or family-equivalent obligations). No token/resource advantage may be used to explain the residual.

## Development and circularity gate

Development seed: `2026081211`.

Development may tune only:

- representation bugs;
- semantic-text generator balance;
- lexical threshold;
- confirmatory sample size from a registered paired-Brier MDE;
- deterministic verifier/extractor correctness.

Before confirmatory freeze require:

1. lexical decidable accuracy in `[0.35, 0.75]`;
2. within-family semantic similarity ACCEPT-vs-REJECT mean differences small / permutation check non-significant at 0.05;
3. coordinate-ablated twin retains signal beyond lexical but is imperfect;
4. hidden metadata mutation cannot change gold;
5. constant/ID/family shortcuts fail the joint metric vector;
6. no family is a trivial label template.

A failed development design is preserved and replaced under a new version before confirmatory outcome access.

## Power / confirmatory freeze

Primary paired loss: binary Brier over decidable `ACCEPT` vs `REJECT` cases.

Registered material effect: `0.05` paired Brier reduction of FULL relative to MECHANISM_ONLY.

Confirmatory n is determined from development paired-difference variance using two-sided alpha `0.05`, target power `0.80`, then rounded upward to complete family/item cells. Confirmatory seed is chosen/frozen only after development and before confirmatory generation.

## Family-level generalization criterion

A broad robustness extension is supported only if all of the following hold:

1. the full-minus-mechanism paired Brier residual is beneficial in **all six** extension families;
2. the exact two-sided sign test across six family-level residual signs is therefore `p = 0.03125`;
3. no family crosses a registered harm condition on valid-transfer retention;
4. full invalid-transfer false-accept is no worse than mechanism-only in every family and lower in aggregate;
5. the item-level paired primary effect exceeds the registered MDE with a 95% interval excluding zero.

If fewer than six family residuals are positive, classify the result as scoped/heterogeneous rather than broad generalization, regardless of pooled item-level significance.

## Valid-transfer safety / abstention

- valid-transfer retention noninferiority floor: FULL must be no more than 0.02 below MECHANISM_ONLY in any family;
- `CANNOT_CHECK` cases are scored separately; blanket refusal fails valid-transfer controls;
- average accuracy/AUC cannot compensate for catastrophic invalid transfer in a registered hostile stratum.

## Separately registered downstream study

Classification robustness does not establish action utility. A disjoint downstream routing epoch must use fresh seeds/tasks and compare transfer-routing policies under matched candidate sets. It is registered separately before any downstream outcome access.

## Claim boundary

Success can support broad **known-world exact-verifier family robustness** of the applicability residual. It cannot establish natural-language witness extraction, frontier-model superiority, natural-domain scientific transfer, independent-human validation or universal scientific applicability.
