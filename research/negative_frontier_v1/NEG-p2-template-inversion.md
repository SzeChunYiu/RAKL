# `INSTRUMENT_NOT_PROBATIVE__TEMPLATE_INVERSION`

**Paper:** II  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/05_instrument_falsifiability.tex:55`
- `publication/papers/paper-02-structural-mechanics/sections/07_natural_domain.tex:20`

## Receipt

- **`receipt_path`:** `research/paper2_prose_transfer_v1/results/CONFIRMATORY_RESULT.json` — **verified present**
- supporting: `research/paper2_prose_transfer_v1/PROTOCOL.json`
- supporting: `research/paper2_prose_transfer_v1/README.md`
- supporting: `experiments/paper2/run_prose_transfer_confirmatory_v1.py`

## What happened

Heldout confirmatory n=576. The instrument passed six of seven registered gates (G1 advantage 0.4722, McNemar p=1.8e-80; G2 ceiling; G4 joint property; G5 paired variance; G6 twelve-seed spread; G7 all three negative controls failed as required) and demonstrably reads its text (scrambling collapses 0.9722 to 0.2500). G3, the error-diversity gate, failed: all 55 coordinate errors fall in exactly one of seven registered ambiguity classes -- the held-out qualitative-degree lexicon -- with zero errors in the other six classes across 3,077 realizations. Probe H matched pairs: 1.0000 on the development surface vs 0.9792 on the heldout surface with identical latent draw and gold.

## One-stage attribution

instrument-construct. Manuscript: 'what the instrument currently measures is how much of the surface its author templated' (05:55). Single-author coupling between renderer and extractor produced the zero-error classes (05:57).

## Lever

Registered revival specification, 05:57: (a) the successor's renderer must not be authored by whoever writes the extractor; (b) every ambiguity class needs a held-out realization, not just one; (c) the ceiling must not be raised -- a successor reporting a LOWER exact score with errors spread across classes is strictly better evidence. Explicitly rejected as a repair: widening the extractor's cue lists.

## Class justification

Fully deterministic renderer/extractor code. The author-separation requirement is a separate authoring process, not a second human annotator; no hosted model or accelerator is named anywhere in the revival spec.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
