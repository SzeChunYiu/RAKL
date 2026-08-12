# Hosted capability probe v1 — GLM-5.2, n=30 per arm

**Status:** `NON_SEALED_HOSTED_EVIDENCE`. Not a sealed local run, not confirmatory,
grants no scientific authority. Does **not** substitute for the frozen
local-provider protocol: a hosted endpoint cannot be weight-attested, so the
byte-exact model/tokenizer SHA-256 chain the sealed protocol depends on is
impossible here. Recorded as fast diagnostic evidence only.

## Provenance

| Coordinate | Value |
|---|---|
| model | `glm-5.2` (Z.AI, Anthropic-compatible endpoint) |
| temperature | 1.0 (independent draws; the sealed local runs used greedy seed-17) |
| prompts | `research/paper2_microtrial_v4_4` — the leak-free arm pair |
| evaluator | `rakl.matched_microtrial::score_pendulum_answer` (registered, unmodified) |
| normalizer | `normalize_pendulum_output_v4_4` (registered, unmodified) |
| n | 30 per arm, 60 total |
| model weight attestation | **IMPOSSIBLE_HOSTED_ENDPOINT** |
| `provider_api_transaction` | true |

No gate, threshold, evaluator or scorer was modified. Credentials are read from
the environment and never written to any artifact.

## Result 1 — the >=2/3 capability floor is cleared

```
DIRECT_CORPUS   parse 30/30   exact_conceptual_pass 30/30   rate 1.000  CI95 [0.886, 1.000]
RAKL_CONTEXT    parse 30/30   exact_conceptual_pass 30/30   rate 1.000  CI95 [0.886, 1.000]
```

`CAPABLE_MODEL_AVAILABLE = NO_REFUTED` was established from job 3476813 at
**n=5** (2 successes, rate 0.40). That evidence never supported a terminal
conclusion: exact one-sided binomial `P(X<=2 | n=5, p=2/3) = 0.2099`, and the
Wilson 95% interval `[0.118, 0.769]` **contains** the 0.667 floor. n=20 would
have been required to conclude a true rate of 0.40 lies below the floor.

A capable operating point therefore exists. This is a measurement correction, not
a gate flip: the floor stays at >=2/3 and is cleared on its own terms.

## Result 2 — the task cannot discriminate, in either direction

Primary endpoint is identical and saturated:

```
exact_conceptual_pass delta (RAKL - DIRECT) = 0.000   p = 1.0
mean conceptual delta                       = 0.000   (5.000/5 both arms)
misalignment_recall  1.00 both      refutation_recall  1.00 both
```

The single pendulum task is at **floor** for Qwen2.5 0.5B-7B (0-40% exact) and at
**ceiling** for GLM-5.2 (100%). There is no capability band in which it can
register a RAKL effect of any sign. Every prior arm comparison was run on this
one task at one seed (`PENDULUM_SEALED_KNOWN_ANSWER_001-seed-17`), which is why
the absence of discriminative range was never visible.

## Result 3 — one unsaturated coordinate, reported as a lead only

`required_support_recall` (7 required evidence IDs) is the sole coordinate not at
ceiling:

```
DIRECT_CORPUS   5/7 x30                      mean 5.000/7
RAKL_CONTEXT    5/7 x26, 6/7 x2, 7/7 x2      mean 5.200/7
Fisher exact, exceeding 5/7: 4/30 vs 0/30    p = 0.1124
```

Not significant, not preregistered, secondary coordinate, single task. It is
**not** evidence that RAKL helps. It is recorded because it localizes where
discriminative headroom exists: evidence-ID binding, not conceptual polarity.
`unsupported_source_count` is 0 in all 60 runs, so neither arm over-claims support.

## What this licenses

- Capability-gated work may proceed at a qualified operating point.
- No RAKL-vs-DIRECT superiority, null or capability claim on the saturated
  coordinates. A null at ceiling is uninformative by construction.
- Task-design work: a discriminating battery must place the baseline arm near
  mid-range rather than at floor or ceiling.
