# Token Budget Authority

Status: supporting engineering contract  
Date: 2026-08-09

## Problem

RAKL stores declared `token_cost` values for context selection, but a declared estimate is not the same epistemic object as a count produced by the tokenizer/counter used for a particular model or adapter. Different tokenizer pipelines, special-token rules, templates, or model-specific settings may produce different counts for the same text.

RAKL therefore treats token count as a **scoped engineering measurement** rather than one global property of text.

## Authority levels

The runtime distinguishes:

```text
DECLARED_ESTIMATE
EXACT_EXECUTED_COUNTER
```

A declared estimate is useful for planning and heuristic context compilation. It may not silently become exact budget authority.

For strict certification, RAKL executes a declared counter contract:

```text
counter ID
counter revision
absolute argv
argv SHA-256
timeout
protocol version
```

The counter receives canonical JSON containing the exact UTF-8 payload text and its SHA-256. A valid response must be a JSON object with a non-negative integer `tokens` field.

The resulting certificate binds:

```text
exact payload SHA-256
payload byte size
measured token count
counter ID
counter revision
counter argv SHA-256
```

Its authority scope is explicitly:

```text
ENGINEERING_TOKEN_MEASUREMENT_ONLY
```

It does not certify scientific truth, evidence quality, mechanism identity, or model capability beyond the declared counter scope.

## Strict packet certification

For a reference profile, the currently registered strict packet ceiling is:

```text
profile.input_budget_tokens + profile.reserved_protocol_tokens
```

A packet measured at or below that ceiling is `WITHIN_BUDGET`; one above it is `OVER_BUDGET`.

If no exact counter is available, strict certification returns:

```text
CANNOT_CHECK
```

It does not substitute the context compiler's declared token metadata and call it exact.

## User command

```bash
python -m rakl certify-packet ./project ./task.json \
  --counter-id my-tokenizer \
  --counter-revision tokenizer-revision \
  --exec /absolute/path/to/counter \
  --arg optional-counter-argument
```

The external counter must read one canonical JSON request from stdin and return, for example:

```json
{"tokens": 4312}
```

The command executes the argv directly with `shell=False`. Shell metacharacters supplied as arguments remain literal arguments.

## Why RAKL does not ship a universal counter

The reference runtime is provider-neutral. Shipping one built-in whitespace/BPE approximation and labeling it exact for every model would create a false authority upgrade. Exact model-specific counters should live in provider/local-model adapters and carry their own revisions.

A future adapter may provide both:

```text
packet token certificate
runner execution receipt
```

so the same model/tokenizer revision can be bound to both context compatibility and execution provenance.

## Remaining scope

This module does not yet prove that a hosted provider uses the same tokenizer implementation/revision as a local counter. Where provider-side tokenization cannot be independently established, equivalence remains externally attested or partially identified.
