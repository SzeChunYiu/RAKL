# P5/P6 operator absorption v1 — frozen protocol

Status: proposal/development protocol. Frozen **before implementation and before any evaluated outcome**. Grants no scientific or promotion authority.

## Subjects

- candidate-basis parent: `2f9f43b08c924a2fc5c30de1ade348715d1a9c49` (saturation round 009);
- current framework incumbent observed before this freeze: `b7747f21b58e8f827b1dab1a487739b83722af28`;
- frozen packets:
  - `failure_condition_minimization_v1`;
  - `minimal_conflict_correction_analysis_v1`.

## Change class

Additive proposal-only implementation of already-frozen operator candidates. No production routing, promotion, Constitution, evaluator or authority change. Promotion, if any, is a later Class-B event using the existing packet/evidence gate.

## Expert-cell split

1. **algorithms/debugging** — ddmin/failure minimization and conflict/correction semantics;
2. **formal methods/constraints** — consistency monotonicity, MUS/MCS/minimality definitions;
3. **adversarial correctness** — flaky/CANNOT_CHECK oracle, nonmonotone predicates, causal overclaim, identity drift;
4. **metrology** — consistency/failure-oracle calls, result size, minimality gap, downstream work;
5. **governance** — outputs are diagnostic/control artifacts only and never scientific/causal authority.

## Development implementation target

Create a pure proposal-only module providing:

- tri-state oracle result `PASS | FAIL | CANNOT_CHECK`;
- deterministic delta-debugging style **1-minimal failure-condition minimization**;
- deterministic deletion-based **inclusion-minimal conflict** under a registered monotone consistency oracle;
- deterministic deletion-based **minimal correction set** whose removal restores consistency;
- exhaustive small-world oracles for global minimum failure subset and all MUS/MCS objects used only by controlled benchmarks;
- receipts binding source condition IDs, context/revision, oracle identity, calls, output IDs, minimality kind and explicit non-authority flags.

The implementation must never call 1-minimal `minimum`, never call a conflict/correction a cause, and never treat `CANNOT_CHECK` as failure/inconsistency.

## Strongest-parent comparison

### Failure minimization
- classic `ddmin` semantics from delta debugging is the primary parent;
- exhaustive small-world global-minimum failure subset is the oracle ceiling;
- no-minimization baseline measures downstream benefit.

The Orion wrapper earns **no novelty credit** for reproducing ddmin. If its only residual is content-bound receipts/governance integration, state that exactly.

### Conflict/correction
- QuickXplain is the primary minimal-conflict parent concept;
- MARCO/MUS-MCS enumeration is the exhaustive-parent concept;
- deletion-based conflict/correction is the deliberately simple development treatment/baseline to validate semantics before optimized parent implementations;
- exhaustive subset enumeration is the controlled oracle.

A performance claim against QuickXplain/MARCO is forbidden until faithful parent implementations exist.

## Development cases

Use deterministic finite universes with opaque condition IDs.

1. `DEV_FAIL_SINGLE` — one condition sufficient to reproduce failure;
2. `DEV_FAIL_INTERACTION` — failure requires a conjunction; individual conditions pass;
3. `DEV_FAIL_IRRELEVANT` — many irrelevant conditions around a small failure core;
4. `DEV_FAIL_CANNOTCHECK` — some probes return `CANNOT_CHECK`, which may never be used as a failure witness;
5. `DEV_CONFLICT_PAIR` — a two-constraint MUS in a larger consistent background;
6. `DEV_CONFLICT_MULTIPLE` — multiple distinct MUSes/MCSes;
7. `DEV_CORRECTION` — removal of one of several alternatives restores consistency;
8. `DEV_MINIMALITY_TRAP` — inclusion-minimal object differs from minimum-cardinality/global-minimum object.

## Fresh assurance reserve

Case definitions remain separate from development and are not used to repair algorithms:

- `FRESH_FAIL_OVERLAP`;
- `FRESH_FAIL_NONTRIVIAL_CORE`;
- `FRESH_FAIL_CANNOTCHECK_BOUNDARY`;
- `FRESH_CONFLICT_THREEWAY`;
- `FRESH_MULTI_MUS_MCS`;
- `FRESH_PREFERENCE_ORDER_SHIFT`.

A later fresh-assurance script may instantiate these from separately frozen generators; this development tranche must not inspect their outcomes.

## Hard gates

- input source condition IDs unique and context-bound;
- initial failure/inconsistency must be verified before minimization;
- every returned failure subset reproduces the exact registered failure;
- every returned conflict is inconsistent and inclusion-minimal;
- every returned correction restores consistency and is inclusion-minimal;
- `CANNOT_CHECK` never counts as `FAIL`/inconsistent;
- no causal/scientific/theorem/method-promotion authority;
- exact negative history remains preserved.

## Development terminals

- `PARENT_SEMANTICS_ABSORBED` — implementation reproduces the established parent semantics and adds only scoped integration/governance value;
- `IMPLEMENTATION_DEFECT` — hard semantics fail;
- `CANNOT_CHECK` — oracle/assumption insufficient;
- `RAKL_SPECIFIC_RESIDUAL_CANDIDATE` — only if a measurable residual beyond the faithful parents is identified; this still requires a new preregistered comparative experiment.

No positive performance terminal is available in this tranche.
