# RAKL Quickstart

RAKL now includes a provider-neutral reference runtime. The base executable path is `python -m rakl`; no model-provider SDK is required for project state, evidence storage, diagnostics, or task-packet compilation.

## Install

```bash
python -m pip install .
python -m rakl profiles
```

For development/testing:

```bash
python -m pip install -e ".[test]"
pytest
```

## Start a project

```bash
python -m rakl init ./my-rakl-project \
  --project-id my-study \
  --profile ordinary-8k
```

## Ingest evidence

```bash
python -m rakl ingest ./my-rakl-project ./source.txt \
  --record-id source-001 \
  --tokens 800 \
  --fiber mechanism \
  --coverage observation_model
```

Important negative history can be marked mandatory for subsequent bounded context compilation:

```bash
python -m rakl ingest ./my-rakl-project ./refutation.txt \
  --record-id refutation-001 \
  --tokens 320 \
  --kind FAILURE \
  --coverage negative_history \
  --mandatory
```

## Verify the project

```bash
python -m rakl doctor ./my-rakl-project
python -m rakl status ./my-rakl-project
```

`doctor` checks record metadata, referenced payload existence, and exact SHA-256 payload integrity. It reports corruption instead of silently repairing evidence.

## Compile a bounded LLM task packet

```bash
python -m rakl packet ./my-rakl-project \
  --operation contradiction_diagnosis \
  --question "Do these observations identify the proposed mechanism?" \
  --budget 6000 \
  --fiber mechanism \
  --require negative_history \
  --output ./task.json
```

The generated task packet is deliberately provider-neutral. Send `task.json` to a model that satisfies the declared reference profile, then preserve its raw response separately. The model response is **proposal-only** and must not be written directly into promoted scientific knowledge.

## Check an ordinary model profile

```bash
python -m rakl check-profile \
  --profile ordinary-8k \
  --model-id my-model \
  --context-window 8192 \
  --instruction-following yes \
  --json-output yes \
  --native-tool-calls no
```

Unknown required capabilities return `CANNOT_CHECK`; known shortfalls return `INCOMPATIBLE`.

## Scope

This quickstart covers the tested reference runtime. Automated provider invocation, durable multi-step checkpointing, exact tokenizer calibration, claim/evidence extraction, and scientific authority promotion remain separate governed fibers.

For reviewer-style reproduction, see `docs/ARTIFACT_EVALUATION.md`. For architecture details, see `docs/REFERENCE_RUNTIME.md` and `docs/ENGINEERING_CLOSURE.md`.
