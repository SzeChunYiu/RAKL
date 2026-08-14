# METRIC-NEAR-V1 Stage A — run receipt

Executed 2026-08-14 on laptop billy, fresh isolated shallow clone
`~/rakl-qaudit` at branch commit `5c171737` (freeze commit of
PROTOCOL_METRIC_V1.json + EVALUATOR_STAGE_A.py), Python 3.8.10, runtime 1.4 s.
Evaluator sha256 verified on the execution host before running:
`beb4b630...8fa2fa355` (matches the protocol's frozen hash). Exit code 0;
in-run determinism check passed (two full world-builds + evaluations byte-identical);
self-test passed (hand-computed GED case, iso-zero, refusal, Spearman
conventions); the planted-fail candidate (`M_refuse_all`) was caught by the
evaluator (`iso_zero_rate` 0.0), validating the checker before trusting it.

## Typed outcome: `NEGATIVE_AT_FROZEN_GATE`

No candidate passes the frozen `TRACKS_GRADED >= 0.80` gate.

| metric | Spearman k=1..4 (MEASURED) | decoy sep | gate |
|---|---|---|---|
| M0_exact_signature_v1 | 0.061 | 0.0 (CONF) | fail (predicted: binary blindness confirmed) |
| M1_signature_l1 | 0.583 | 0.0 (CONF) | fail (predicted below M3 — confirmed) |
| M2_wl3 | 0.620 | **1.0 (MEASURED — pass ≥0.50)** | fail (prediction ≥0.80 **REFUTED**) |
| M3_ged_exact | **0.797548** | 1.0 (CONF, shared oracle) | **fail by 0.0025 — no threshold rescue** |

Conformance cells all landed as declared (iso_zero 1.0 for M0–M3; refusal on
empty structures for all; M0/M1 decoy blindness by construction). These are
not findings.

## Honest reading

1. The frozen 0.80 gate is not met by any candidate, including exact GED at
   0.7975. The gate stays as frozen; the outcome is a negative.
2. The strongest MEASURED positive is M2's decoy separation 1.0 (20/20
   signature-equal non-isomorphic pairs separated) — graded WL sees strictly
   more than the v1 exact signature on exactly the pairs v1 cannot
   distinguish. Note the non-compensatory design earning its keep: refuse-all
   also scores decoy_sep 1.0, and only the iso-zero gate exposes it — decoy
   separation alone is gameable by maximal refusal.
3. M0's 0.061 exhibits the motivating constraint: the incumbent exact
   signature carries no graded signal at all.

## Residual and revival path (registered, not executed)

Attribution hypothesis (single stage, instrument-side): the planted edit
count k is an UPPER BOUND on realized structural distance — cumulative edits
partially cancel — so Spearman against k has a ceiling below 1.0 for ANY
correct metric. The revival is a NEW versioned instrument (Stage A v2, to be
frozen separately): score rank agreement against the realized minimal edit
distance (M3-oracle value or verified-minimal plantings) instead of raw k,
with M3 then excluded from candidates (it would share the oracle:
conformance, not measurement). Running v2 in this same pass would be a
post-result instrument change; it is registered as the next step instead.

## Scope

Instrument-grade only. Nothing here says any metric captures NEAR in an
analogy-semantic sense (that is Stage B, external labels, reducer-blocked).
Grants no scientific or promotion authority.
