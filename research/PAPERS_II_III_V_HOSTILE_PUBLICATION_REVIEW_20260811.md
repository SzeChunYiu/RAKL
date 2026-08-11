# Papers II/III/V — hostile publication ingest review (#257)

Date: 2026-08-11  
Evidence cutoff SHA: `e602ac04e43f0ef5329e691983847661e5a8019a`  
Review class: same-context hostile overclaim audit — **not** independent peer review.

## Scope

Verify that the claim-to-evidence matrix ingests terminal negatives and `CANNOT_*` receipts without promotional lift, and that manuscript language at cutoff does not re-open closed empirical coordinates.

## Hostile checks

| Check | Result | Notes |
|-------|--------|-------|
| Paper II claims experience-learning lift at 0.5B | **PASS (honest negative)** | v1.2 job 3476548: 0/0 successes; ORACLE 3476730/3476731: `MODEL_CAPABILITY_FLOOR_0_5B` |
| Paper II factorial/ablation/promotion treated as positive pending | **PASS after ingest** | #155/#156/#157 terminal `CANNOT_IDENTIFY`; #158 negative/narrowing complete |
| Paper II universal continual-learning claim | **PASS** | Scoped negatives only; stronger-model claim not licensed |
| Paper III confirmatory result without labels | **PASS** | Zero external labels; #217 human gate open; #249 blocked |
| Paper III descriptor harvest mints training authority | **PASS** | `training_authorized=false` preserved |
| Paper V four-arm causal result implied | **PASS after ingest** | #250 `CANNOT_FREEZE`; #251 `CANNOT_EXECUTE`; harness is instrument-only |
| Paper V longitudinal pooled growth claim | **PASS** | #253 refuses cross-version pooling; cohort INTERNAL_METROLOGY only |
| Paper V independent novelty audit complete | **PASS** | #255 Phase 0 frozen; zero external labels |
| Cherry-picked microtrial wins in Paper II | **PASS** | V4–V4.3.1 explicitly non-confirmatory; zero exact conceptual passes |
| Post-cutoff commit silently promoted | **PASS** | Cutoff receipt binds SHA + terminal receipt hashes |

## Residual overclaim risks (accepted, not blockers to ingest close)

1. **PDF rebuild** — `publication-pdfs` CI may still be `AWAITING_GREEN` for papers 01–04 after recent TeX deltas (`research/receipts/PUBLICATION_PDF_HARVEST_AFTER_289_20260811.STATUS.md`). This is publication engineering residual, not missing empirical ingest.
2. **Paper I external reviewers (#216)** — out of scope for II/III/V ingest; remains human-open.
3. **Independent peer review** — not claimed anywhere in this ingest packet.

## Verdict

`HOSTILE_INGEST_PASS__NO_OVERCLAIM_DETECTED_AT_CUTOFF`

The strongest defensible Paper II thesis is architecture + formal obligations + auditable negatives under a capability floor. Paper III remains a formalism + blocked confirmatory programme awaiting humans. Paper V remains methods/metrology + scoped negative precursor + honestly refused four-arm study + human-blocked novelty audit.

No promotional scientific wins were invented to close #257.
