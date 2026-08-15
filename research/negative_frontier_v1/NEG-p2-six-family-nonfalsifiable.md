# `SCOPED (six-family gate passed and was shown non-falsifiable; probes A, B, F, G failed)`

**Paper:** II  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-02-structural-mechanics/sections/05_instrument_falsifiability.tex:24-39`
- `publication/papers/paper-02-structural-mechanics/sections/06_known_world.tex:14`

## Receipt

- **`receipt_path`:** `research/paper2_six_family_audit_v1/results/SIX_FAMILY_AUDIT.json` — **verified present**
- supporting: `research/paper2_six_family_audit_v1/results/PROBE_G_TEXT_INERTNESS.json`
- supporting: `research/paper2_six_family_audit_v1/README.md`
- supporting: `research/paper2_six_family_audit_v1/run_audit.py`

## What happened

Seed 2026081212, n=810, every registered gate passed with empty gate reasons. The audit then showed the pass carries no generalization content. Probe A: the full arm IS the gold function, per-item Brier loss constant 0.0004, measured variance 1.24e-37. Probe B: 12/12 arbitrary non-registered seeds reproduce 6/6 positive families and p=0.03125 -- no seed can fail the gate. Probe F: two strata invisible to the control by design score exactly 0.000 and supply 66.7% of the headline advantage. Probe G: replacing every source and target text with noise leaves gold and all six coordinates unchanged on 810/810 cases.

## One-stage attribution

instrument-construct. Manuscript: 'the answer travelled alongside the text in a pre-parsed sibling field, so no arm ever read the text' (05:51); 'a gate no seed can fail is not a test' (05:33).

## Lever

The named successor already exists and was executed: the prose-transfer instrument of Case 3, built to the repaired specification (probe-G repair: destroying the text must destroy performance; probe-F repair: sampled rather than assigned discriminating coordinate). That successor terminated at INSTRUMENT_NOT_PROBATIVE__TEMPLATE_INVERSION -- see NEG-p2-template-inversion.

## Class justification

sec.8:18: 'a benchmark that fails the battery is repaired in a new versioned epoch, never rescored.' The audit artifact and the registered outcome are preserved verbatim; the live frontier is the Case 3 successor.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
