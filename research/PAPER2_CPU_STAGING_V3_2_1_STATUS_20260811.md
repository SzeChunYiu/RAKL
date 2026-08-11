# Paper 2 CPU staging V3.2 native result and V3.2.1 harvest repair

Date: 2026-08-11

## Object and decision boundary

This tranche asks whether the additive V3.2 archive extractor can promote the
already frozen 38-object CPU asset environment on LUNARC and whether the
governed harvest can verify that same evidence chain. It is staging evidence
only. It is not a model execution, evaluated microtrial result, performance or
efficiency estimate, independent review, acceptance or publication.

## Exact native scheduler result

The authorized V3.2 retry used merged subject
`c10ba7a261af02cc42690022226555a3197351ae` and submitted exactly two
staging-only jobs:

- network probe `3475123`: `COMPLETED`, exit `0:0`, elapsed 4 seconds, `cn004`;
- staging `3475124`: `COMPLETED`, exit `0:0`, elapsed 125 seconds, `cn004`.
- raw `sacct --json` stage-step maximum resident set size: 2,156,756,992
  bytes = 2,106,208 KiB (`2106208K`).

No additional job and no model execution occurred.

## Final-path staging receipt

The receipt harvested from the promoted final path has SHA-256
`f269788a78d216932879d2ea98eee3c1b84322b2345330406d8a7c6d81802c26`
and reports `STAGING_PASS_ATOMICALLY_PROMOTED`. Its exact attestations include:

- 38/38 manifest artifacts with exact path, byte count and SHA-256;
- standalone Python `3.11.13` on `x86_64` / glibc `2.34`;
- Torch `2.8.0+cpu`, `torch.version.cuda == null`, tensor device `cpu`;
- Transformers `4.55.0`, Tokenizers `0.21.4`, Safetensors `0.6.2`;
- exact 31-distribution installed map;
- `pip check` return code 0 and `No broken requirements found.`;
- FS9 free space above the frozen 6 GB minimum;
- zero model executions and zero evaluated result records.

The original V3.2 governed harvest nevertheless returned
`HARVEST_CANNOT_CHECK` with sole failure `staging_job_or_receipt_failed`. That
receipt is preserved at SHA-256
`2e2ecd6f5cb2ad84f17352fea598b30210de225f745e1d9c13154b8872a03e96`.
Therefore the current overall authority remains `CANNOT_CHECK`; the final-path
pass receipt is not silently promoted around its governed harvest.

## Typed residual and additive repair

The installed distribution map is exact, but the frozen standalone Python
bundles pip and setuptools from wheels. Native `pip freeze --all` therefore
records two exact PEP 508 direct references rather than equality lines:

- `pip @ file:///build/pip-24.3.1-py3-none-any.whl#sha256=3790624780082365f47549d032f3770eeb2b1e8bd1f7b2e02dace1afa361b4ed`
- `setuptools @ file:///build/setuptools-75.6.0-py3-none-any.whl#sha256=ce74b49e8f7110f9bf04883b730f4765b774ef3ef28f722cce7c273d253aaf7d`

The frozen V3.2 harvest parser required every line to contain exactly one
`==`; this representation mismatch is sufficient to explain its failed stage
predicate. V3.2 and its `HARVEST_CANNOT_CHECK` receipt remain immutable.

V3.2.1 is a harvest-only additive successor. It accepts only the two exact
direct-reference strings above, keeps every other distribution as one exact
equality, and still requires exact equality to the 31-distribution installed
map. Mutated hash, URL, generic remote direct reference, equality substitution,
duplicate or missing entries fail closed. It also binds the original
`HARVEST_CANNOT_CHECK`, scheduler rows and every source receipt hash before a new
verdict is possible.

## Current state

`HARVEST_REPAIR_READY_NOT_REHARVESTED`

V3.2.1 submits no job and exposes no evaluated result. After this repair is
reviewed, merged and checked by the trusted-parent evaluator, it may re-harvest
only jobs `3475123` and `3475124`. Until that new receipt exists, an execution
packet remains unauthorized and no quantitative Paper 2 figure is warranted.

The pre-reharvest machine synthesis is
`research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_SUCCESS_HARVEST_REPAIR_READINESS_RECEIPT_20260811.json`.
It derives the exact scheduler facts and cumulative six staging jobs, zero model
executions and zero evaluated result records from bound receipts rather than
from this prose.
