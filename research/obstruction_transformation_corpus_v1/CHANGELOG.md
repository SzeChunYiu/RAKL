# CHANGELOG — obstruction_transformation_corpus_v1

## 2026-08-12 — v1 seed

- Freeze ontology/identity/authority/provenance/hash/leakage rules before bulk collection.
- Seed 15 episodes across 10 domain lanes.
- Verify two in-repo RAKL events as `VERIFIED_LOCAL` with receipts.
- Keep remaining structural exemplars as `PROPOSAL_ONLY` (and one `SUPERSEDED`).
- Emit dedup, coverage, split, leakage, and deterministic `snapshot_hash`.
- Register retrieval metrics without confirmatory scores (#401 owns efficacy).
