# Paper 2 V4 native result and V4.1 freeze

Date: 2026-08-11

## Authority boundary

The frozen V4 bridge executed one sealed pendulum task at seed 17 under
`DIRECT_CORPUS` and `RAKL_CONTEXT`.  It is a non-confirmatory engineering unit,
not the registered architecture-by-evidence-access study.

## Native receipt chain

LUNARC job `3475193` ran from clean detached checkout
`3bf46b505af249802faa277d3ec865f4d9664853`, tree
`28db27a0440ca197eb30dc56283ba7e64ba594c2`, with packet parent
`af2d0be61522d1f8f657a48daaf6369ff3e44a3e`.  The scheduler root row is
`COMPLETED`, `SUCCESS`, return code 0, elapsed 64 seconds.  The governed harvest
is `HARVEST_TASK_SEED_PASS_NONCONFIRMATORY`.  All eight model/tokenizer files
have identical pre/post byte and SHA-256 attestations.

## Preserved negative outcome

Both frozen evaluator parses are invalid and both scores are null:

- `RAKL_CONTEXT`: 1,140 input tokens, 108 output tokens, 20,021 ms; raw output
  is exactly one lowercase `json` fence, but V4 accepts only a bare JSON object;
- `DIRECT_CORPUS`: 638 input tokens, 320 output tokens, 39,121 ms; raw output is
  fenced JSON followed by prose.

These resource coordinates describe execution, not scientific success.  There
is no valid arm score, win/loss, effect estimate, cost-per-success or quantitative
figure.  Post-hoc inspection of the apparent JSON body does not re-score V4.

The exact archive, 19 extracted evidence files and every byte/hash are bound in
`research/paper2_microtrial_v4/PAPER2_V4_NATIVE_JOB_3475193_INGEST_RECEIPT_20260811.json`.

## Typed residual and V4.1

The immediate residual is `R1_SCHEMA_PARSER_TRANSFORMATION`: both generations
used Markdown fences while the frozen parser required a bare object.  This does
not establish that the answer content was scientifically correct.  A distinct
V4.1 candidate is frozen after preserving V4 and before any V4.1 output:

- accept a bare JSON object; or
- remove exactly one lowercase newline-delimited `json` fence with whitespace
  only outside it;
- reject trailing prose, multiple/uppercase/unlabelled fences, substring
  extraction, invalid JSON and non-object JSON.

V4.1 changes neither the answer schema nor score thresholds.  It has not been
merged, submitted or executed, and cannot retroactively authorize a V4 score.
The broader Paper-2 matched empirical claim remains unevaluated.
