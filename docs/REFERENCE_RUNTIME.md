# RAKL Reference Runtime

Status: supporting implementation, scoped engineering closure only  
Date: 2026-08-09

## Why a runtime is necessary

RAKL cannot be publishable as a scientific method if using it requires one very large prompt, one vendor-specific agent product, or the model itself to remember the evolving knowledge lattice.  The package therefore separates three objects:

1. **canonical project state**, stored outside the LLM;
2. **a deterministic epistemic working set**, compiled for one atomic operation;
3. **a replaceable model invocation**, which receives a typed task packet and returns a proposal.

The model never owns canonical state and its response never self-promotes.

## Ordinary-model reference profile

The baseline profile is `ordinary-8k`:

```text
minimum context window     8192 tokens
RAKL packet input budget   6144 tokens
reserved output            1536 tokens
reserved protocol           512 tokens
instruction following      required
parseable JSON             required
native tool calling        not required
```

Tool access may be mediated by an external RAKL orchestrator.  This deliberately makes the base workflow usable with a broad class of ordinary chat/instruct LLMs instead of requiring a frontier native-agent interface.

Profile assessment is fail-closed:

```text
PASS
INCOMPATIBLE
CANNOT_CHECK
```

An unknown context limit is `CANNOT_CHECK`, not a guessed pass.

## Canonical payload storage

`CanonicalPayloadStore` stores exact bytes under their SHA-256 identity:

```text
.rakl/store/sha256/<first-two-hex>/<full-digest>
```

Properties:

- the digest is over exact bytes;
- equal bytes deduplicate naturally;
- different bytes have different identities except under a cryptographic collision;
- existing content is verified before reuse;
- a corrupt object is reported, not silently overwritten;
- there is no delete operation in the support API.

This is the missing payload layer under the metadata-only reconstructable-memory contract introduced in Round 021.

## Project layout

A project initialized with `python -m rakl init` contains:

```text
project/
└── .rakl/
    ├── project.json
    ├── records/
    ├── packets/
    └── store/
        └── sha256/
```

Record identifiers never become filesystem paths.  The metadata filename is derived from a SHA-256 of the logical record ID, while the original ID remains inside the immutable record envelope.

## Reference workflow

```bash
python -m rakl init ./my-project \
  --project-id apple-study \
  --profile ordinary-8k

python -m rakl ingest ./my-project ./paper-a.txt \
  --record-id paper-a \
  --tokens 900 \
  --fiber mechanism \
  --coverage observation_model

python -m rakl ingest ./my-project ./old-refutation.txt \
  --record-id negative-mechanism-a \
  --tokens 420 \
  --kind FAILURE \
  --coverage negative_history \
  --mandatory

python -m rakl doctor ./my-project

python -m rakl packet ./my-project \
  --operation contradiction_diagnosis \
  --question "Do the observations identify mechanism A?" \
  --budget 6000 \
  --fiber mechanism \
  --require negative_history \
  --output ./task-packet.json
```

`task-packet.json` is provider-neutral.  It contains the selected source text, exact source digests, reference profile, epistemic rules, required output fields, and this explicit boundary:

```json
{
  "llm_output_authority": "PROPOSAL_ONLY",
  "may_promote_canonical_knowledge": false,
  "may_mint_mechanistic_or_decision_authority": false
}
```

The packet can be sent to any model adapter capable of satisfying the declared reference profile.

## Determinism and replay

For unchanged project state and identical task arguments, the canonical JSON task packet has no timestamp or random identifier and is deterministic.  This makes model-independent packet replay possible and gives future matched-model experiments a stable input artifact.

This does **not** make model output deterministic.  Model/version, decoding parameters, tool results, and environment still belong in execution receipts.

## Diagnostics

`python -m rakl doctor <project>` validates:

- the project manifest;
- the declared reference profile;
- record metadata structure;
- metadata-file identity;
- referenced payload existence;
- SHA-256 payload integrity.

A missing or tampered payload makes the project unhealthy.  Diagnostics do not repair evidence silently.

## What this round does not close

This reference runtime does not yet:

- call a hosted or local model automatically;
- tokenize text with a model-specific tokenizer;
- execute a durable multi-step workflow/checkpoint engine;
- automatically extract claims/evidence spans;
- promote LLM responses;
- prove real-agent scientific utility;
- close the evaluator dependency trust chain.

Those remain separate fibers because collapsing them into one runtime would make failures harder to localize and would weaken the paper's authority boundary.

## Publication role

For the paper, this runtime is an **executable artifact boundary**, not a headline novelty claim.  Provider-neutral capability contracts, content-addressed storage, deterministic task packets, CLIs, and external workflow persistence all have substantial prior art.  Their value here is to make the RAKL epistemic method inspectable, reproducible, and executable by ordinary models.
