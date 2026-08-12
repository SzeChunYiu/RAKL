# Paper III / publication-series-v2 Paper II — objective Track A (#444)

**Status:** `DEVELOPMENT_COMPLETE / CONFIRMATORY_FROZEN_NOT_RUN`  
**Parent registration:** `research/paper3/PAPER3_TRACK_A_REGISTRATION_V1.md`  
**Executable transport contract:** `src/rakl/structural_transport_v2.py` (#491 / #486)  
**Objective benchmark instrument:** `src/rakl/objective_transfer_benchmark.py`

## Purpose

Track A tests objective machine-verifiable transfer discrimination without inventing human labels. The primary question is whether an explicit directional applicability/transport representation adds information beyond surface similarity and simpler structural/mechanism controls about whether transfer is valid for the target context and quantity of interest.

Natural-domain external-human validity is a separate coordinate and remains blocked until genuine independent annotators exist.

## Ordering and chronology

```text
Track-A preregistration
  -> generator/verifier implementation
  -> development-only generation and outcome access
  -> hostile circularity / difficulty / semantic-decorrelation checks
  -> power and comparator freeze
  -> CONFIRMATORY FREEZE (current state)
  -> fresh confirmatory generation
  -> candidate scoring / paired inference / LOFO
```

No confirmatory item or outcome has been generated or accessed at the current state.

## Primary v1 scope

The preregistration narrows the primary objective study to four heterogeneous exact-verifier families:

1. finite graph flow / mapped-path feasibility;
2. logical entailment / countermodel-style Horn execution;
3. unit and coordinate transforms / dimensional invariants;
4. finite state-transition systems / candidate-sequence reachability.

The original broader ten-family campaign list is retained as a later robustness extension rather than silently treated as part of the primary v1 confirmatory study.

Primary item types are:

- `VALID_DISTANT_TRANSFER`;
- `SEMANTIC_NEAR_MISS_INVALID_TRANSFER`;
- `DIRECTION_REVERSED_INVALID`;
- `BOUNDARY_QOI_MISMATCH`;
- `PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK`.

Two development/anti-degeneracy controls (`VALID_NEAR_CONTROL`, `INVALID_DISTANT_CONTROL`) prevent surface distance from becoming the answer.

## Ground truth

A label is assigned only by executing the family-specific verifier on the target instance. The hidden perturbation identity is never read by a verifier. Tests mutate that hidden identity and require the verifier outcome to remain unchanged.

The candidate-facing packet never exposes the gold decision, verifier trace, item type, family label, or hidden perturbation identity.

## Preserved negative development history

The first synthetic design failed the preregistered coordinate-ablated-twin falsifier: once the directly perturbed coordinate was removed from the structural extractor, accuracy collapsed near chance and invalid false-accept became extreme. That design is not confirmatory evidence and was rejected rather than repaired after confirmatory outcome access.

The redesigned development instrument adds independently derived target-effect obligations and surface-distance controls. Its development receipt is frozen in `DEVELOPMENT_RESULT_V1.json`.

## Development gates and freeze

Development seed: `2026081201`; development n: `1080`.

- lexical/Jaccard baseline accuracy on decidable cases: `0.50625`, inside the preregistered `[0.35, 0.75]` difficulty band;
- within-family semantic-similarity ACCEPT-vs-REJECT differences are small, with permutation p-values from `0.816` to `0.971`;
- coordinate-ablated twin exact three-way accuracy: `0.8472`, with `0.25` invalid false-accept: signal survives the circularity attack but the twin is deliberately not perfect;
- mechanism-alignment-style derived-effect control exact three-way accuracy: `0.875`;
- relational control exact three-way accuracy: `0.8194`;
- full exact known-world applicability contract matches the exact verifier on development; this is an instrument/conformance result, not a learned-extraction or natural-domain superiority claim.

The strong mechanism control is load-bearing: a confirmatory Paper II claim must establish residual applicability value beyond generic mechanism alignment, not merely beat lexical similarity.

## Power freeze

For the registered paired binary-Brier MDE `0.05`, development estimated `sigma_d = 0.3705043712`, requiring `431` decidable items. Accounting for the observed `8/9` decidable fraction and generator cell granularity yields the frozen confirmatory design:

```text
confirmatory seed = 2026081202
n per base cell   = 16
total n           = 576
expected decidable n ≈ 512
lexical threshold = 0.2761904761904762
```

These values are frozen before confirmatory item generation or outcome access. See `POWER_RECEIPT.json`.

## Confirmatory controls

The confirmatory report must include at minimum:

- lexical semantic baseline;
- relational-only control;
- mechanism/derived-effect control;
- coordinate-ablated twin;
- full applicability contract;
- constant/family shortcut attacks;
- exact `ACCEPT` / `REJECT` / `CANNOT_CHECK` metrics;
- valid-distant accept rate and semantic-near-miss false-accept rate;
- paired Brier inference and family-level robustness.

A strong modern semantic reranker and external LLM/mechanism comparator remain required for the strongest model-level / natural-language Paper II claim. Deterministic Track A cannot substitute for that validity coordinate.

## Artifact state

`DEVELOPMENT_RESULT_V1.json`, `GENERATOR_MANIFEST.json`, and `POWER_RECEIPT.json` contain outcome-bearing development evidence and the pre-confirmatory freeze. `OBJECTIVE_TASKS.jsonl`, `MACHINE_WITNESS_OUTPUTS.jsonl`, and `SEMANTIC_CONTROL_SCORES.jsonl` remain empty until the fresh confirmatory epoch is executed.

## Claim boundary

Current terminal: `DEVELOPMENT_COMPLETE__CONFIRMATORY_FROZEN_NOT_RUN`.

No confirmatory structural-superiority, learned-extractor, natural-domain, independent-human, or universal cross-domain claim is licensed by this protocol state.
