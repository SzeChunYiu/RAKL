# Paper II external-corpus epoch — executed, honest terminal

Terminal: `NEGATIVE__CAPABILITY_ABSENT`

Authority: same-context analysis over third-party labels. Not independent
review. Promotes nothing. `grants_scientific_authority: false`.

## What this epoch did

The external-label residual of Paper II required labels whose authors are
independent of the instrument's author. Published corpora satisfy that
mechanically. The bounded search (`SEARCH_LEDGER.md`) selected **ARN**
(Sourati, Ilievski, Sommerauer, Jiang; TACL 12, 2024; Zenodo
10.5281/zenodo.11044026, CC BY 4.0): 1,095 rows, four quadrants of near/far
surface x analogy/distractor, gold system mappings from shared ePiC proverbs.

Chronology: `PROTOCOL.json`, the deterministic reducer
(`src/rakl/narrative_reducer.py`) and the runner were frozen and committed
**before first dataset contact**; planted-world tests validated the instrument
before any real-data run; `AMENDMENT_01.json` bound the actual multiple-choice
schema at the binding stage, before any arm scoring; execution was one pass on
laptop billy. Vendored data copy: `data/arn.csv`
(sha256 `a866fe53...ad4a7a8`, attribution per CC BY 4.0).

## Result (receipts in `results/`)

| stage | outcome |
| --- | --- |
| acquisition | 1,095 rows -> 2,190 pairs (648 dev / 1,542 confirm), 0 skipped |
| reducer admission | **ADMITTED at `EXTERNAL_LABEL`** (`admit_reducer`; scramble-sensitive, parity obstruction surfaced, label authors independent) |
| battery B2 text destruction | witness output changed 1,542/1,542; scrambled exact 0.500 <= null upper 0.509 — **pass** |
| battery B3 shuffled gold | advantage -0.001, CI [-0.034, 0.032]; G1 fails as required — **pass** |
| battery B4 trivial floor | no trivial arm attains G2 — **pass** |
| battery B5 paired variance | 0.230 / 0.230 — **pass** |
| G1 advantage vs strongest control (band) | **-0.016**, CI **[-0.0498, +0.0162]**; upper bound < 0.05 MDE — fail |
| G2 joint | valid_accept **0.023** at false-accept **0.044** (reported as a pair) — fail |
| G3 abstention | 0.000 |

Per quadrant (accept rates, always paired with the FA column above):
far-analogy (Q2 analogue) **0.013** (n=386); near-analogy 0.034 (n=385);
far-distractor FA 0.015 (n=396); near-distractor (Q3 analogue) FA 0.075
(n=375). Witness exact 0.490; lexical 0.475; band 0.506.

## The honest reading

Because the battery passed, this negative is a **measurement**, not an
apparatus artifact — the first in this programme's transfer line. It relocates
the external-label residual:

- **It is not a data-availability gap.** Third-party-labelled data exists, was
  acquired, and was used at n = 1,542 confirmatory pairs (>> the n≈48 power
  requirement; the CI half-width is ±0.033 against the 0.05 MDE).
- **It is a measured extraction-capability gap.** The registered deterministic
  reducer — admissible, text-reading, obstruction-surfacing — recovers no
  usable system-level structure from natural narratives: the witness gate
  collapses to near-total rejection (retention 2.3%) and chance-level Brier.
  Cross-domain analogies share almost no surface roles, and surface roles are
  all this reducer can see.

Scope: "capability absent" is scoped to the registered reducer and this
programme, not to all possible reducers. The revival path is a *capable*
reducer (in practice, a learned/LLM extractor), which then owes the same
admission gate plus a contamination declaration (ARN is public since 2023-10)
— named as the successor epoch, not executed here.

## Reproduction

```
PYTHONPATH=src:. .venv/bin/python scripts/paper2_external_corpus_confirmatory.py \
  --csv research/paper2_external_corpus_v1/data/arn.csv \
  --out research/paper2_external_corpus_v1/results
.venv/bin/python -m pytest tests/test_paper2_external_corpus.py -q
```

Execution host: laptop billy, `~/rakl-verify-p2rescope`, Python 3.11.
