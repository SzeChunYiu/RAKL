# Obstruction–Transformation Episode Corpus v1

**Issue:** [#402](https://github.com/SzeChunYiu/RAKL/issues/402)  
**Status:** provenance-first seed release  
**Runtime loader:** `rakl.obstruction_transformation_corpus.load_transformation_memory`

## What this is

A content-bound `ObstructionTransformationMemory` seed with:

- frozen ontology/identity/authority rules before collection
- heterogeneous domain lanes (structural diversity)
- explicit `PROPOSAL_ONLY` defaults for synthetic exemplars
- `VERIFIED_LOCAL` only when a source verification receipt exists
- deterministic `snapshot_hash` consumable by the strict runtime
- disjoint splits reserved for confirmatory evaluation on **#401**

## What this is not

- complete knowledge
- theorem or scientific authority
- #401 confirmatory efficacy scores
- permission to promote proposal episodes to verified routes without receipts

## Reproduce

```bash
python scripts/build_obstruction_transformation_corpus_v1.py
pytest tests/test_obstruction_transformation_corpus.py -q
python -c "from pathlib import Path; from rakl.obstruction_transformation_corpus import load_transformation_memory, validate_corpus; r=validate_corpus(Path('.')); print(r.ok, r.snapshot_hash, r.episode_count)"
```
