# Minimal executable RAKL project

This folder is a reviewer-facing example for the provider-neutral runtime. Copy it to a writable directory and run:

```bash
python -m rakl init ./demo --project-id demo --profile ordinary-8k
python -m rakl ingest ./demo examples/minimal/source.txt --record-id source --tokens 24 --fiber mechanism --coverage observation
python -m rakl ingest ./demo examples/minimal/refutation.txt --record-id refutation --tokens 24 --kind FAILURE --coverage negative_history --mandatory
python -m rakl doctor ./demo
python -m rakl packet ./demo --operation contradiction_diagnosis --question "Does the observation identify the mechanism?" --budget 128 --fiber mechanism --require negative_history --output ./demo-packet.json
```

The produced packet is an input artifact for an LLM. Its output remains proposal-only until separately evaluated and promoted.
