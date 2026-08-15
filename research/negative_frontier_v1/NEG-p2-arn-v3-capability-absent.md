# `NEGATIVE__CAPABILITY_ABSENT (probative instrument)`

**Paper:** II (successor lineage; NOT in the current manuscript)  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** no (successor lineage / receipt-level)  
**Artifact immutable:** no

## Where the manuscript states it

Nowhere. This terminal is not in any of the three current manuscripts; it is successor-lineage history recorded only in the repository / open PRs.

## Receipt

- **`receipt_path`:** `research/paper2_external_corpus_v1/results_v3_reducer/RESULT.json @ PR #703 head ef42786e8bb2e3fc658ce483b0d281d048ffad7e` — **verified present**
- Branch-only, open PR #703. **Local ref `arn/v3-instance-paired-reducer` is stale** (ecce469e) and does not contain this file; fetch from the PR head instead: `gh api "repos/{owner}/{repo}/contents/research/paper2_external_corpus_v1/results_v3_reducer/RESULT.json?ref=ef42786e" -q .content | base64 -d`. Verified this way: line 154 carries `"terminal": "NEGATIVE__CAPABILITY_ABSENT"`, admission verdict ADMITTED / EXTERNAL_LABEL, pairs total 2190 (dev 648, confirm 1542), acquisition sha256 a866fe5341ce4a29f00f24987a12278303b2b8ad788352f549b0fe051ad4a7a8.
- supporting: `arn/v3-instance-paired-reducer:research/paper2_external_corpus_v1/PROTOCOL_V3_REDUCER.json`
- supporting: `PR #703 body (gh pr view 703)`

## What happened

Instance-paired correspondence scoring: every score term consumes a specific (query-instance, candidate-instance) pair, so no marginal component is computable from one narrative alone. B3_shuffled_gold PASSED -- advantage 0.0044, CI [-0.029, 0.038], g1_fails_as_required true. The instrument is now probative. Confirmatory nonetheless NEGATIVE__CAPABILITY_ABSENT: witness exact 0.495 vs band 0.506; G1 advantage -0.0018, CI [-0.036, 0.031]; G2 valid_accept 0.0, invalid_false_accept 0.0.

## One-stage attribution

capability (feature adequacy). PR body: 'The instance-paired correspondence ... yields insufficient signal. The scoring is strict and principled, but the extracted features (typed roles, typed relations) may not capture the analogical structure that ARN requires.'

## Lever

The v4 relation-triple attempt was the first response and regressed the battery. The manuscript's own named lever -- a capable learned extractor under the admission gate plus a contamination declaration -- remains untried.

## Class justification

Same reasoning as the manuscript-reported ARN negative: probative deterministic instrument in hand, external labels already acquired, admission gate does not require a hosted model. This is the cleanest live entry point to the ARN capability question. **Gate read (src/rakl/reduction_validation.py):** the implemented admission gate applies exactly three checks -- scramble-invariance (one scramble-invariant source is disqualifying), obstruction-surfacing on a fixed calibration source, and author independence of the validation labels (`external_label_author` must differ from `author`, else admission is capped at `ADMITTED_AT_FLOOR` / `CertificateKind.ASSERTED`). There is NO contamination check in code and NO model-class restriction: the gate does not distinguish a deterministic reducer from a learned one, nor a from-scratch extractor from a pretrained encoder. The contamination declaration is a manuscript-level obligation (sec.7:36, sec.8:22), not a code gate. A locally-runnable learned extractor therefore passes the same three checks a hosted one would, which is what keeps this REVIVABLE_LOCAL.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
