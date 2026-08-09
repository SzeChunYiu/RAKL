# SELF-RAKL Research Round 003

## Object and evidence cutoff

- Object: `RAKL_METHOD`
- Frozen incumbent: `0a5fd25ad59175277ad47061f280b3a82c40e8a4`
- Frozen benchmark commit on active main: `3bddb6a43a6206dc4a8360b0c769af1bc3ad6572`
- Candidate ref: `self-rakl/round-003-candidate`
- Global saturation at start: `ACTIVE_NON_FLAT`

This round deliberately moved away from the prior ATMS/argumentation/evidence-linking route. It used release engineering, property-based testing, provenance algebra, signed atomic scholarly assertions, durable execution, and a native code audit as different projections on the same self-improvement object.

## Expert panel

Five isolated working lenses were fixed before implementation.

1. **Release/formal-verification engineer** — exact-SHA validation, trusted checks, fast-forward promotion and rollback.
2. **Software-testing researcher** — generated hostile worlds, metamorphic properties and counterexample reduction.
3. **Scientific knowledge/provenance engineer** — immutable semantic identity, derivation lineage and replay safety.
4. **Bayesian scientific-method reviewer** — blocking validity, scoped improvement and cannot-check calibration.
5. **Adversarial red-team reviewer** — evaluator tampering, status-source spoofing and false-green self-certification.

The panel converged on one central process residual: a candidate cannot be allowed to move `main` and then use the resulting push CI as retrospective permission. It also cannot be allowed to rewrite the evaluator that judges the same candidate.

## Source projections retained

### GitHub rulesets and required status checks

Source: official `github/docs` repository, rulesets documentation.

Retained projection:

- required checks should gate changes before merge/promotion;
- a required check can be bound to an expected source integration;
- a check needs a successful conclusion, not merely an existing workflow configuration.

RAKL extension: bind the evidence to the exact candidate SHA, freeze the incumbent and evaluator fingerprints before challenger creation, and treat a premature main movement as a process violation.

### Hypothesis / property-based testing

Source: `HypothesisWorks/hypothesis`, project paper and implementation.

Retained projection:

- write properties over families of inputs rather than only individual examples;
- generated cases actively seek a refutation;
- reduction/minimization makes a discovered counterexample understandable and reusable.

RAKL extension: RAKLBench should have metamorphic research-method invariants such as context-symmetry, relation-order invariance, replay idempotency and immutable projection identity. Generated testing supplements rather than replaces source-grounded scientific benchmarks.

### W3C PROV and provenance implementations

Source: W3C PROV repository, plus ProvSQL.

Retained projection:

- provenance is a first-class graph of derivation/process rather than an annotation hidden in prose;
- multiple derivation paths can be composed algebraically;
- provenance circuits can remain inspectable while downstream computations reuse them.

Scope guard: provenance records *how* a result was derived. It does not by itself certify that the evidence is true, strong, independent or causally identifying. Those remain RAKL authority-layer questions.

### Nanopublications

Source: `Nanopublication/nanopub-java`.

Retained projection: an atomic scholarly object benefits from separating assertion content, provenance, and publication/process information, with stable identity/signing support.

Scope guard: signature or stable identity establishes attribution/integrity, not truth.

### Temporal durable execution

Source: `temporalio/temporal` architecture documentation.

Retained projection:

- append-only event history enables replay/reconstruction;
- deterministic/replayable workflow logic and side-effectful activities require different correctness rules;
- retryable side effects need idempotency discipline.

RAKL extension: planning, source selection and promotion verdict computation should be replay-safe; commits, branch moves and physical/remote experiments are side effects with explicit identities and receipts so retry does not create duplicate semantic or experimental history.

## Native self-audit residuals

### Assumptions were missing from default context alignment

`Context` stored assumptions, but `compare_contexts()` and `Context.comparable_key()` omitted them from their default coordinates. Therefore two claims differing only in assumptions could be treated as context-aligned even though Constitution invariant 3 explicitly requires assumptions to be aligned before contradiction.

Challenger: include assumptions in the default context coordinates and add generated symmetry/assumption tests.

### Projection identity could be overwritten

`KnowledgeFiber.add_projection()` assigned directly into a dictionary. Reusing a `projection_id` with different content silently destroyed the old semantic object. This conflicts with negative-history preservation and makes retry/replay unsafe.

Challenger: identical replay is an idempotent no-op; different content under an existing identity is rejected.

## Transactional promotion design

The round implements a candidate-only `PromotionGate` with these decisions:

```text
PROMOTE
BLOCK
CANNOT_CHECK
PROPOSAL_ONLY
PROCESS_VIOLATION
```

A Class A/B candidate may promote only when the frozen benchmark, receipt/history, exact-SHA trusted checks, protected evaluator fingerprints, blocking invariants, fast-forward compatibility and applicable Class B improvement rule all pass while active `main` is still the incumbent.

Class C remains proposal-only.

## New semantic objects

1. **Two-phase self-promotion** — candidate validation is evidence for a future main move, not retrospective justification for an already-active move.
2. **Evaluator non-self-modification** — the candidate's validator is part of the experimental apparatus and must be frozen or independently validated.
3. **Property/metamorphic RAKLBench** — invariant families expand hostile coverage beyond fixed examples.
4. **Immutable projection identity with idempotent replay** — retries must not mutate semantic history.
5. **Compositional provenance algebra** — keep alternative derivation paths inspectable and composable while separating lineage from evidence strength.
6. **Durable research execution** — replayable reasoning and side-effectful research actions need different execution semantics.
7. **Assertion/provenance/process separation** — an atomic claim packet should not mix the claim, its evidence lineage and publication/execution metadata.

The round is therefore `NON_FLAT`. No same-context or independent flat-round counter is advanced.

## Next discriminators

- Run the exact candidate SHA through GitHub Actions while `main` remains frozen, then fast-forward only on success.
- In a future round, stage a deliberately failing candidate and prove operationally that `main` does not move.
- Add stateful generated long-horizon RAKLBench worlds where retries, branch changes and supersessions occur in different orders and failing sequences are minimized.
- Formalize claim/evidence lineage as a provenance DAG/semiring-like object while keeping evidence authority separate.
- Extend atomic claim packets toward assertion + exact evidence spans + provenance/process metadata + contradiction/omission coverage.
