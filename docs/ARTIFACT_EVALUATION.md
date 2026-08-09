# RAKL Artifact Evaluation — Reference Runtime v1

Status: reviewer-facing instructions for the Round-022 executable artifact  
Date: 2026-08-09

## Evaluation boundary

This procedure validates installability and the provider-neutral RAKL project/task-packet runtime. It does **not** validate real-model scientific superiority or global method closure.

## Requirements

- Python 3.11+
- pip
- a checkout of the repository at the revision being evaluated

The reference runtime itself uses only the Python standard library. Test dependencies are separate.

## A. Package installation

From the repository root:

```bash
python -m pip install . --no-deps
python -m rakl profiles
```

Expected result: JSON containing at least the `ordinary-8k` profile.

For the exact test protocol used by CI, see `tests/test_package_install.py`, which installs the distribution non-editably into an isolated target directory with `--no-deps --no-build-isolation` and invokes `python -m rakl` from that target.

## B. Create a project

```bash
python -m rakl init ./demo-rakl \
  --project-id artifact-demo \
  --profile ordinary-8k
```

Expected result: a healthy JSON project status and a `.rakl/` directory with a project manifest, records directory, packets directory, and SHA-256 payload store.

## C. Ingest exact evidence

```bash
python -m rakl ingest ./demo-rakl examples/minimal/source.txt \
  --record-id source \
  --tokens 24 \
  --fiber mechanism \
  --coverage observation

python -m rakl ingest ./demo-rakl examples/minimal/refutation.txt \
  --record-id refutation \
  --tokens 24 \
  --kind FAILURE \
  --coverage negative_history \
  --mandatory
```

Expected result: two record envelopes with exact SHA-256 payload identities.

## D. Verify project integrity

```bash
python -m rakl doctor ./demo-rakl
```

Expected result: `healthy: true`, two records, and two canonical payloads.

A reviewer may make a copy of the project and alter or delete one object under `.rakl/store/sha256/`. `doctor` must then report the project unhealthy rather than repairing it silently.

## E. Compile an ordinary-LLM task packet

```bash
python -m rakl packet ./demo-rakl \
  --operation contradiction_diagnosis \
  --question "Does the observation identify the mechanism?" \
  --budget 128 \
  --fiber mechanism \
  --require negative_history \
  --output ./demo-task.json
```

Expected result:

- verdict `READY`;
- the mandatory refutation is present;
- source SHA-256 identities are present;
- the task packet declares `llm_output_authority: PROPOSAL_ONLY`;
- the task packet denies direct canonical/mechanistic/decision authority to model output.

Run the same command twice without modifying the project. Canonical packet JSON should be byte-identical.

## F. Model compatibility declaration

```bash
python -m rakl check-profile \
  --profile ordinary-8k \
  --model-id reviewer-model \
  --context-window 8192 \
  --instruction-following yes \
  --json-output yes \
  --native-tool-calls no
```

Expected result: `PASS`. Native tool calls are not a baseline requirement because an external RAKL orchestrator may mediate tools.

Omit `--context-window`. Expected result: `CANNOT_CHECK`, not a guessed pass.

Use `--context-window 4096`. Expected result: `INCOMPATIBLE`.

## G. Run the repository test suite

```bash
python -m pip install -e ".[test]"
pytest
```

The exact count is revision-dependent and must be taken from the revision's actual execution log, not from this document.

## Reproducibility interpretation

A pass means that the evaluated revision satisfies this scoped software artifact contract. It does not show that:

- the model profile is sufficient for every scientific domain;
- a particular model follows the packet correctly;
- RAKL improves scientific quality versus strong baselines;
- the full workflow is crash-safe;
- all evaluator dependencies are immutable.

Those are separate registered fibers and must remain open until executed evidence closes them.
