# Core-vs-plugin decision

## Reopen test

A new finding reopens the bounded core only if at least one load-bearing transition cannot be represented with the existing type/effect/certificate/authority vocabulary.

The Observation Contract does not meet that threshold.

| Test | Result |
|---|---|
| Requires new scientific-authority dimension | No |
| Requires a fifth privileged effect | No |
| Requires deleting/revising historical negatives | No |
| Requires new installation authority | No |
| Cannot be represented as local pursuit state + append receipt | No |
| Requires a new external action lifecycle | No |
| Requires evaluator changes outside protected evaluator service | No |
| Requires a new recursion layer above L7 | No |

Terminal:

```text
CORE_REOPEN = NO
PLUGIN_DELTA = OBSERVATION_CONTRACT_V1
```

## What would reopen the core later

Reopen only if a future audited task demonstrates, with a concrete transition witness, that a scientifically load-bearing operation cannot be represented as:

1. an ordinary typed pursuit/justification mechanic with declared effects;
2. an append-only receipt/history event;
3. a governed capability action;
4. an existing protected authority/registry/kernel/evaluator service;
5. or a certified migration between versions of those objects.

Merely finding a new question type, benchmark, domain, semantic normalizer, or external knowledge source is plugin novelty.
