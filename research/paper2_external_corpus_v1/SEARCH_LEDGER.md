# Paper II external-corpus search ledger — bounded saturation pass

Date: 2026-08-14. Same-context analysis. Not independent review. Promotes nothing.

Question: does a PUBLISHED corpus exist whose items fit the transfer-instrument
shape — (source text, target text) pairs with THIRD-PARTY gold judgements usable
as ACCEPT/REJECT transfer-validity decisions, n >= 48 usable items, obtainable
on laptop billy — such that the external-label author-independence requirement
of `admit_reducer` (src/rakl/reduction_validation.py) is satisfied mechanically,
because the labels' authors are not the reducer's author?

Search basis: the verified GREEN list of `research/paper2_nearest_work_2026/`
(eight analogy/transfer works, all primary-source verified there) plus targeted
primary-source verification of the two strongest fits. Bounded: candidates below
were checked against primary records only; entries marked CANNOT_CHECK were not
fully verified in this pass and remain candidates, not rejections.

## FIT — selected

**ARN: Analogical Reasoning on Narratives** (Sourati, Ilievski, Sommerauer,
Jiang; TACL 12:1063–1086, 2024; doi:10.1162/tacl_a_00688).

- Shape: 1,096 triples (query narrative, analogous narrative, distractor
  narrative) over the four quadrants of near/far (surface) × analogy/disanalogy
  (system mapping). Each triple yields two labelled pairs:
  (query, analogy) = ACCEPT and (query, distractor) = REJECT. Far-analogy pairs
  are the Q2 analogue (low surface, shared system mapping); near-distractor
  pairs are the Q3 analogue (high surface, no system mapping). Paper-reported
  distractor-pair counts: 294 far, 254 near.
- Gold provenance (third-party, verified against arXiv:2310.00996v4 full text):
  system mappings derive from shared proverbs in the crowdworked ePiC corpus;
  triples were manually investigated by the first and last ARN authors; two
  research assistants validated 120 datapoints (>10%). Near analogies were
  partially GPT-3.5-generated and then author-edited — recorded as a provenance
  fact. None of these people is the author of this programme's reducer, so
  `external_label_author != reducer author` holds mechanically.
- Availability: Zenodo record 11044026 (doi:10.5281/zenodo.11044026), single
  CSV, ~1.3 MB, license **CC BY 4.0**. Obtainable on laptop billy over HTTPS.
- Contamination: public since 2023-10 (arXiv) — any pretrained-model component
  would require a contamination declaration. The registered reducer for this
  epoch is deterministic (no trained weights), so training contamination is not
  applicable; the residual author-knowledge channel (the reducer's author knows
  the analogy literature) is mitigated by freezing the reducer before first
  dataset contact and by the reducer containing no ARN-specific vocabulary.
- n: 1,096 triples -> up to 2,192 labelled pairs >> 48.

## PARTIAL FIT — reserve

**StoryAnalogy** (Cheng Jiayang et al., EMNLP 2023; arXiv:2310.12874;
github.com/loginaway/StoryAnalogy). 24K story pairs with human 0–3 ratings on
entity similarity and relation similarity (extended SMT). Fits the shape only
after thresholding graded labels into ACCEPT/REJECT, which adds a frozen-rule
degree of freedom; candidate stories are LLM-generated with human annotation.
Reserved as the successor corpus if ARN fails schema or acquisition checks.

## CANNOT_CHECK — candidates not fully verified in this pass

- **E-KAR** (Chen et al., Findings of ACL 2022): analogical QA with human
  explanations; per-pair transfer-validity reading not verified against the
  primary record in this pass.
- **SCAN** (Czinczoll et al., 2022): scientific/creative analogies; items are
  concept pairs, not text pairs; shape fit not established.
- **AnaloBench** (EMNLP 2024): abstract/long-context analogy identification;
  candidate-ranking format; per-pair accept/reject reading not verified.
- **ReTRE** (ACL 2026): structure-preserving variants; label provenance
  relative to construction not verified in this pass.

## Verdict

A suitable third-party-labelled corpus EXISTS (ARN). The epoch proceeds under
`PROTOCOL.json` in this directory: reducer and protocol frozen before first
dataset contact; acquisition, admission, battery and confirmatory executed on
laptop billy; every terminal in the protocol, including the negative and
infeasibility terminals, is a first-class outcome.
