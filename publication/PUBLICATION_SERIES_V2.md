# Orion Publication Series V2 (internal namespace: RAKL)

**Effective date:** 2026-08-12  
**Migration owner:** #475  
**Rule:** publication numbering may change; frozen experiment, job, schema, receipt, issue and historical namespace identities do not.

## Canonical order

| V2 paper | Canonical role | Historical publication namespace | Current publication status |
|---|---|---|---|
| Paper I — **Epistemic Mechanics for Evidence-Governed Scientific Research** | foundational scientific-authority/state mechanics | `paper-01-epistemic-mechanics`, `paper1*` | `ARXIV_PREPRINT_READY`; no independent-human-review claim |
| Paper II — **Structural Mechanics: Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer** | relational/QoI/boundary/preservation mechanics | historical Paper III, `paper3*` | `READY_WITH_EXPLICIT_LIMITATIONS`; strongest objective/external-validation version still active |
| Paper III — **Method-Evolution Mechanics: From Experience to Method** | failure→diagnosis→lesson/method→fresh assurance / Self-Orion (self-application) mechanics | historical Paper V, `paper5*` | `READY_WITH_EXPLICIT_LIMITATIONS`; four-arm causal attribution and prospective metrology remain active |
| Paper IV — **Structural Learning Mechanics** | learner-conditioned structural saturation and training allocation | training-time extension (`#455/#461/#462/#466/#467/#468`) | design-and-protocol preprint present (no empirical claim); standalone *empirical* paper `CONDITIONAL` until #462 authorizes |
| Paper V — **Verified Discovery in Mathematics** | mathematical assurance application | historical Paper IV, `paper4*` | `ARXIV_PREPRINT_READY` as assurance-architecture paper |
| Paper VI — **Orion Scientific Research Engine** | capstone integration/application of Papers I–V | historical Paper II, `paper2*` | `CAPSTONE_NOT_READY`; active capability/causal/competitive evidence should land before final release |

## Conceptual stack

```text
Paper I   Epistemic Mechanics
   ↓
Paper II  Structural Mechanics
   ↓
Paper III Method-Evolution Mechanics
   ↓
Paper IV  Structural Learning Mechanics (conditional)
   ↓
Applications
   ├─ Paper V  Verified Discovery in Mathematics
   └─ Paper VI RAKL Scientific Research Engine (capstone integration)
```

The order is conceptual, not a claim that every later paper requires every earlier empirical result. Paper IV is conditional: if the training-time decision gate rejects a standalone paper, its supported fragments fall back to Paper II/Paper III/Paper VI as specified by #462, and the publication sequence must be compacted in a later versioned migration rather than fabricating a paper.

## Immutable legacy aliases

The following strings are historical evidence identities, not publication numbers after this migration:

- `paper2_*`, `PAPER2/`, jobs and schemas created for historical Paper II → **V2 Paper VI** unless a claim-to-receipt map says otherwise.
- `paper3_*`, historical Paper III artifacts → **V2 Paper II**.
- `paper5_*`, historical Paper V artifacts → **V2 Paper III**.
- `paper4_*`, historical Paper IV mathematical-assurance artifacts → **V2 Paper V**.

Do not rename these frozen identities. Manuscripts cite them as legacy namespaces when required.

## Release policy

`ARXIV_PREPRINT_READY` means the manuscript can be released honestly with its current limitations. It does **not** mean external peer review or the strongest empirical version is complete.

`READY_WITH_EXPLICIT_LIMITATIONS` means the paper is coherent enough for a transparent preprint, but an active experiment can materially strengthen or narrow the empirical headline; freeze a release cutoff if publishing before that result.

`CAPSTONE_NOT_READY` means do not treat the current architecture draft as the final Paper VI: the capstone should ingest the strongest mechanics, active empirical campaign, scientific-search-engine integration and fair competitor evidence first.
