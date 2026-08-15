# `demoted external-model comparator -- on the hardest semantic near-miss decoys the gate does not beat Direct`

**Paper:** II  
**Class:** `REVIVABLE_EXTERNAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/06_known_world.tex:26`
- `publication/papers/paper-02-structural-mechanics/sections/06_known_world.tex:30`

## Receipt

- **`receipt_path`:** `research/llm_comparator_confirmatory_v1/summary.json` — **verified present**
- Located via `git log --all -- publication/papers/paper-02-structural-mechanics/figures/llm_comparator.*` (commit 53d32148 'Paper II: wire real external-model applicability-gate comparator') and `find ... -iname '*comparator*'`. An earlier pass recorded this as NOT_FOUND; that was a miss, corrected here.
- supporting: `research/llm_comparator_confirmatory_v1/raw_results.jsonl`
- supporting: `research/llm_comparator_confirmatory_v1/run.py`
- supporting: `research/llm_comparator_confirmatory_v1/README.md`
- supporting: `research/llm_comparator_dev_v1/ (development lane, preserved separately)`

## What happened

Model glm-5.2, seed 20260812, n=504 (gold ACCEPT 224 / REJECT 224 / CANNOT_CHECK 56), zero parse failures in any arm. False-accept on invalid: DIRECT 0.5268, FREE_COT 0.5357, RAKL_GATE 0.3393 -- the gate roughly halves the odds while the compute-matched control moves nothing. Three-way accuracy 0.6369 / 0.5774 / 0.7083. **The reported negative, confirmed in the receipt:** false_accept_on_hostile_decoys is DIRECT 0.2679, FREE_COT 0.3571, RAKL_GATE 0.3571 -- on the hardest semantic near-miss decoys the gate is not merely no better than Direct, it is measurably WORSE (0.3571 vs 0.2679) and exactly ties the Free-CoT control. Three demotions bound the whole result: one model / one seed / one family-set; a structured-inference scaffold rather than a smarter model; and, after probe G, a benchmark whose coordinates travel in pre-parsed form.

## One-stage attribution

instrument-construct + capability. The benchmark carries no extraction requirement (probe G), so the comparator measures obligation application over structured facts, not prose reading. The hostile-decoy regression is a capability gap of the gate's own decoy discrimination, not a scaffolding failure -- the scaffold works everywhere else.

## Lever

'A cross-model, cross-seed replication on a battery-compliant benchmark is the named next coordinate before any external-model claim' (06:30).

## Class justification

Cross-model, cross-seed replication requires hosted frontier models. Note the hostile-decoy sub-result is a sharper negative than the manuscript's wording ('does not beat Direct') conveys: the receipt shows it loses.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
