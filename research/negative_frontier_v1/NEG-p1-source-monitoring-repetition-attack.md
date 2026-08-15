# `NEGATIVE (source-monitoring repetition attack; KEEP_PROPOSAL_ONLY)`

**Paper:** I (overlay branch publication-overlay-papers-123, PR #704)  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication-overlay-papers-123:publication/papers/paper-01-epistemic-mechanics/sections/06c_current_evidence_update.tex:7`
- `publication-overlay-papers-123:publication/papers/paper-01-epistemic-mechanics/sections/01a_executor_independence.tex:23`

## Receipt

- **`receipt_path`:** `publication-overlay-papers-123:experiments/paper1/source_monitoring_repetition_attack_v1/RESULTS.json` — **verified present**
- This receipt does NOT exist on main. It was added by the overlay branch; verify with `git show publication-overlay-papers-123:<path>`.
- supporting: `publication-overlay-papers-123:experiments/paper1/source_monitoring_repetition_attack_v1/PROMOTION_GATE_CANDIDATE.json`
- supporting: `publication-overlay-papers-123:experiments/paper1/source_monitoring_repetition_attack_v1/PROTOCOL.json`
- supporting: `publication-overlay-papers-123:experiments/paper1/run_source_monitoring_repetition_attack_v1.py`

## What happened

Under the frozen attack model, ten submitted identifiers for one claim collapsed to only eight normalized identities, giving a repetition ratio 0.2 against a registered 0.5 gate. The submissions were near-duplicates of one DOI (query-string variants ?v=1..?v=5, a case-varied 'DOI: ' prefix, an arXiv id). Typed outcome NEGATIVE; promotion verdict KEEP_PROPOSAL_ONLY; net_benign 0.0, net_adversarial 0.0.

## One-stage attribution

extraction. The identity normalizer fails to collapse trivially equivalent identifiers, so the firewall never gets to demonstrate authority-inertness.

## Lever

Manuscript: 'The next mechanism must therefore change source-identity and lineage resolution rather than the threshold' (06c:7). The receipt names four concrete next steps: proper DOI-to-arXiv mapping; case-insensitive matching; publisher-specific prefix handling; cross-venue citation detection.

## Class justification

Pure deterministic identifier-normalization work, fully specified by the receipt's own next_steps list. No model, no data acquisition.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
