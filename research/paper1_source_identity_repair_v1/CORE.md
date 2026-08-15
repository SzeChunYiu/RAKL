# Paper I — source-identity repair v1

**Targets** `research/negative_frontier_v1/NEG-p1-source-monitoring-repetition-attack.md` · **Terminal** `ATTACK_DETECTED_CONTROLS_PASSING` (proposal-only; grants no authority) · [`RECEIPT.json`](RECEIPT.json) · frozen slot [`PROTOCOL_V2.json`](PROTOCOL_V2.json) · [`run_source_identity_repair_v1.py`](run_source_identity_repair_v1.py)

## Attack

Ten submissions for one claim under trivially-equivalent surface forms of one DOI (`?v=1..?v=5`, a case-varied `DOI: ` prefix) plus a repeated arXiv id. The v1 normalizer — an inline `lower().replace("?v=","").replace("doi:","").replace("arxiv:","")` in the frozen harness — resolved them to **8** identities, ratio 0.20 vs the registered 0.5 gate, so the firewall never fired.

## Lever applied (extraction stage; threshold untouched)

Scheme-aware canonicalization in `src/rakl/source_identity.py` replaces the blanket rewrite. A transformation applies only where the scheme's own spec says the part is not identity-bearing: DOI handles are case-folded and stripped of query/fragment; arXiv ids are case-folded with the `vN` suffix **kept** (versions stay distinct entities joined by a `VERSION_OF` edge to a shared root); everything else is **opaque** and byte-exact, so `?id=1` vs `?id=2` on a plain URL still separates. Cross-venue DOI↔arXiv identity is never guessed from strings — it enters only as a declared record, tracked separately from syntactically-minted edges.

Gate formula, threshold (0.5) and denominator (10) are byte-identical to the parent protocol, and `PROTOCOL_V2.json` froze *before the run* which count feeds the gate (`distinct_canonical`; `distinct_roots` is diagnostic only).

## Controls first — no-false-merge **PASSED**

| Control | Corpus | v1 | v2 | Verdict |
|---|---|---|---|---|
| C1 no false merge | 8 genuinely distinct sources | 8 distinct | **8 distinct, 0 false merges** | PASS |
| C2 near-miss pairs separate | 6 planted pairs | over-merged **2/6** | **0/6 over-merged** | PASS |
| C3 arXiv versions | `2401.00111v1`/`v2` | — | 2 entities, 1 root | PASS |
| C4 control can fail | same 6 pairs | over-merges `10.1000/x?v=1`≡`10.1000/x1`, and a case-varied URL path | — | PASS |
| C5 equivalent forms collapse | 7 surface forms of 1 DOI | 6 distinct | **1 distinct** | PASS |

C2 pairs: adjacent DOI · same-author consecutive arXiv ids · identity-bearing URL query · DOI supplement suffix · the v1 collision pair · case-varied opaque URL path. C4 matters: v1 was **simultaneously under-merging (the attack) and over-merging (2 pairs)** — the control discriminates, it is not a no-op.

## Attack: before → after

| Arm | distinct | repetition_ratio | gate ≥0.5 | detected |
|---|---|---|---|---|
| v1 baseline (reproduced in-process) | 8 | 0.20 | ✗ | no |
| **v2 repair** | **2** | **0.80** | **✓** | **yes** |
| v2 + declared DOI↔arXiv record *(diagnostic, ungated)* | 1 root | 0.90 | ✓ | yes |

The v1 row reproduces the frozen parent receipt exactly, so the delta is attributable to the normalizer alone.

## Residual (scoped)

Detection comes from **surface-form canonicalization alone**. The cross-venue coordinate is *not* resolved: nothing in `arXiv:1234.5678v1` supports the harness comment that it is the same work as the DOI, and the gate flips only because both arXiv submissions are byte-identical. A repetition attack citing one work under two *different* cross-venue surface forms still needs a declared mapping record — that coordinate is unsolvable from identifier strings and stays open.

## Code / tests

`src/rakl/source_identity.py` (new) · `src/rakl/identity.py` (`ancestry_roots`) · `src/rakl/__init__.py` (exports) · `tests/test_source_identity.py`. The frozen v1 harness, protocol and receipt on `publication-overlay-papers-123` are unmodified; `PROMOTION_GATE.json` is not written (single-writer registry).
