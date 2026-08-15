# `NEGATIVE__CAPABILITY_ABSENT`

**Paper:** II  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/07_natural_domain.tex:34`
- `publication/papers/paper-02-structural-mechanics/sections/01_introduction.tex:13`

## Receipt

- **`receipt_path`:** `research/paper2_external_corpus_v1/results/RESULT.json` — **verified present**
- supporting: `research/paper2_external_corpus_v1/PROTOCOL.json`
- supporting: `research/paper2_external_corpus_v1/AMENDMENT_01.json`
- supporting: `research/paper2_external_corpus_v1/SEARCH_LEDGER.md`
- supporting: `research/paper2_external_corpus_v1/results/ACQUISITION_RECEIPT.json`
- supporting: `research/paper2_scientific_analogy_external_v1/predecessors/ARN_NEGATIVE_RESULT.json`

## What happened

ARN corpus (Sourati et al. 2024), 1,095 query-choice-choice triples; 1,542 held-out confirmatory pairs split by proverb. The falsifiability battery PASSED in full (text destruction changed the witness arm's output on 1542/1542 pairs and collapsed accuracy to the shuffled-gold null; shuffled-gold control failed the advantage gate as required; no trivial arm attained the joint property; both arms carried per-item loss variance). Because the battery passed, the outcome is a measurement: paired-Brier advantage -0.016, item-bootstrap 95% CI [-0.0498, +0.0162], upper bound below the registered 0.05 MDE; joint property failed with valid-transfer retention 0.023 at invalid false-accept 0.044. On the Q2-analogue quadrant (far analogies) the gate retained 1.3% (n=386).

## One-stage attribution

capability (extraction). Manuscript verbatim: 'The residual is a measured extraction-capability gap: no admissible reducer in this programme recovers system-level structure from natural narratives' (07:36). Explicitly NOT power ('n=1,542 >> 48; CI half-width +/-0.033 ... leaves no power excuse') and explicitly NOT label availability.

## Lever

'the named successor is a capable learned extractor, which owes the same admission gate plus a contamination declaration (ARN has been public since 2023)' (07:36). Admission gate is implemented at src/rakl/reduction_validation.py.

## Class justification

The admission gate requires external labels authored outside the programme -- ARN satisfies this mechanically -- and nowhere requires a hosted model or accelerator. A locally-runnable learned extractor is admissible. Risk flag: if the required capability is only reachable with a hosted frontier model, the record reclassifies to REVIVABLE_EXTERNAL, and the contamination declaration becomes load-bearing. **Gate read (src/rakl/reduction_validation.py):** the implemented admission gate applies exactly three checks -- scramble-invariance (one scramble-invariant source is disqualifying), obstruction-surfacing on a fixed calibration source, and author independence of the validation labels (`external_label_author` must differ from `author`, else admission is capped at `ADMITTED_AT_FLOOR` / `CertificateKind.ASSERTED`). There is NO contamination check in code and NO model-class restriction: the gate does not distinguish a deterministic reducer from a learned one, nor a from-scratch extractor from a pretrained encoder. The contamination declaration is a manuscript-level obligation (sec.7:36, sec.8:22), not a code gate. A locally-runnable learned extractor therefore passes the same three checks a hosted one would, which is what keeps this REVIVABLE_LOCAL.

## Successor lineage

- `NEG-p2-arn-v2-battery-failed.md`
- `NEG-p2-arn-v3-capability-absent.md`
- `NEG-p2-arn-v4-battery-failed.md`

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
