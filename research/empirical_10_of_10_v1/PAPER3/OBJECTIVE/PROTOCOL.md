# Paper III / publication-series-v2 Paper II — objective Track A (#444)

**Status:** `OBJECTIVE_PRIMARY_CONFIRMATORY_COMPLETE`  
**Parent registration:** `research/paper3/PAPER3_TRACK_A_REGISTRATION_V1.md`  
**Executable transport contract:** `src/rakl/structural_transport_v2.py` (#491 / #486)  
**Objective benchmark instrument:** `src/rakl/objective_transfer_benchmark.py`  
**Frozen confirmatory runner:** `scripts/paper2_objective_track_a_confirmatory.py`

## Purpose and claim boundary

Track A tests objective machine-verifiable transfer discrimination without inventing human labels. The question is whether an explicit directional applicability/transport representation adds information beyond surface similarity and simpler relation/mechanism projections about whether transfer is valid for the target context and quantity of interest.

This lane is deliberately model-independent. It does **not** establish natural-language witness extraction, frontier-model superiority, natural-domain validity, independent-human confirmation or downstream research utility.

## Chronology

```text
Track-A preregistration
  -> generator/verifier implementation
  -> development-only outcome access
  -> failed first circular design preserved
  -> redesigned development + hostile checks
  -> power/comparator/seed freeze
  -> pre-confirmatory freeze merged to main as 7d67a18...
  -> fresh seed 2026081202 generated and scored
  -> paired inference + family robustness + packet hashes frozen
```

The confirmatory seed was not generated until the design/power/comparator freeze had passed CI and was merged to `main`.

## Primary v1 scope

The preregistered primary contains four exact-verifier families:

1. finite graph flow / mapped-path feasibility;
2. logical entailment / Horn closure;
3. unit and coordinate transforms / dimensional invariants;
4. finite state-transition systems / candidate-sequence reachability.

The originally named additional six families remain a **separate robustness extension** rather than a post-outcome enlargement of this primary epoch.

Primary item types:

- `VALID_DISTANT_TRANSFER`;
- `SEMANTIC_NEAR_MISS_INVALID_TRANSFER`;
- `DIRECTION_REVERSED_INVALID`;
- `BOUNDARY_QOI_MISMATCH`;
- `PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK`.

`VALID_NEAR_CONTROL` and `INVALID_DISTANT_CONTROL` prevent surface distance from being the answer.

## Ground truth and leakage control

A label is assigned only by executing a family-specific verifier on the target instance. Hidden perturbation identity is diagnostic-only and is never read by the verifier. Unit tests mutate that hidden identity and require the decision to remain unchanged. Candidate-facing data omit the gold decision, verifier trace, item type, family label and hidden perturbation identity.

The first development design failed the preregistered coordinate-ablated-twin attack and is preserved in `DEVELOPMENT_NEGATIVE_HISTORY.md`; it was not promoted. The redesigned instrument passed the development difficulty/decorrelation/twin gates before confirmatory freeze.

## Frozen design

Development seed `2026081201`, n=1080. Registered paired binary-Brier MDE `0.05`. Development `sigma_d = 0.3705043712` implied 431 decidable cases. After the observed unknown fraction and cell granularity, confirmatory values were frozen at:

```text
seed               = 2026081202
n per base cell    = 16
total n            = 576
expected decidable ≈ 512
lexical threshold  = 0.2761904761904762
```

## Confirmatory result

The fresh packet contains 256 `ACCEPT`, 256 `REJECT` and 64 `CANNOT_CHECK` gold states; decidable n=512 exceeds the registered 431-case requirement.

- lexical/Jaccard: decidable accuracy 0.4961;
- relation/invariant-only: exact three-way accuracy 0.8194; invalid false-accept 0.375;
- derived-effect/mechanism-only: exact 0.875; invalid false-accept 0.25;
- coordinate-ablated twin: exact 0.8472; invalid false-accept 0.25;
- full applicability contract: exact 1.0; valid accept 1.0; invalid false-accept 0; unknown abstain 1.0.

The primary residual is full applicability versus the stronger mechanism-only control. Paired binary Brier improves by `0.120`, with item-bootstrap 95% interval `[0.09375, 0.148125]` from 20,000 resamples, exceeding the registered 0.05 material-effect threshold.

The full-vs-mechanism residual is positive in all four primary families. Four family clusters are nevertheless not enough for a broad generalization claim: the two-sided sign-test value for four positive signs is p=0.125. `FAMILY_ROBUSTNESS.json` therefore records `broad_generalization_supported=false`.

## Reproducibility

The four full synthetic confirmatory packets are byte-reproducible from the committed generator, frozen seed and canonical JSONL serialization. `CONFIRMATORY_PACKET_MANIFEST_V1.json` freezes exact byte sizes and SHA-256 identities; the committed runner aborts on any mismatch.

Primary machine-readable evidence:

- `PREDICTIVE_RESULTS.json`;
- `PAIRED_INFERENCE.json`;
- `FAMILY_ROBUSTNESS.json`;
- `DEGENERACY_AUDIT.json`;
- `CONFIRMATORY_PACKET_MANIFEST_V1.json`;
- `FINAL_OBJECTIVE_RECEIPT.json`.

## Remaining coordinates

A flagship Paper II claim still requires separately registered evidence for:

1. the named six-family robustness extension;
2. disjoint downstream routing utility;
3. a strong current semantic reranker/cross-encoder;
4. a direct LLM transfer-validity comparator and mechanism-alignment LLM control under matched context/budget;
5. natural-domain independent-human validation if obtainable.

## Current terminal

`PAPER2_OBJECTIVE_PRIMARY_SUPPORTED__FLAGSHIP_CLAIM_NOT_YET_COMPLETE`.

The allowed objective claim is scoped to the generated exact-verifier, machine-readable setting. No external-model, independent-human, universal cross-domain or end-to-end utility claim is licensed by Track A alone.
