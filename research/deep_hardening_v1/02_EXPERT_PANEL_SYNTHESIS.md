# Same-context expert panel synthesis

These are **role-separated analytical passes inside one AI orchestration context**. They are not independent reviewers and must not be reported as external replication.

## Panel

| Seat | Background | Delegated responsibility | Veto / challenge |
|---|---|---|---|
| Formal semantics lead | rewriting systems, abstract interpretation, order/category semantics | quotient, path equivalence, reachability quantifiers, composition laws | veto any theorem implied by names/counts alone |
| Representation & ML lead | metric learning, relational representation, curricula | TCSQ/neural bridge, asymmetric witness learning, checkpoint state | veto novelty that collapses to conditional metric learning or skill-aware selection |
| Verification engineer | theorem provers, replay kernels, proof DAGs | edge assurance, root replay, trajectory/certificate separation | veto candidate/replay edges being treated as kernel proof |
| Systems & security lead | deterministic serialization, supply chain, capability security | commitments, receipts, trust roots, CI/release migration | veto environment-dependent commitments or caller-created authority roots |
| Scientific-method lead | falsification, adaptive evaluation, causal/empirical design | fresh assurance, contamination, total cost, negative history | veto development evidence promoted as confirmatory evidence |
| Complexity & adversarial auditor | graph/search complexity, counterexamples, leakage | hidden oracles, compilation barrier, OOD/staleness, local minima | veto “geometry” that has already solved the search problem during construction |

## Delegated findings and cross-review

### Formal semantics → ML challenge

A QoI/context quotient and a directional transfer witness are not one mathematical object. Quotient geometry can legitimately be equivalence-like/symmetric; a genuinely directional `StructuralWitness` cannot be represented exactly by a scorer that depends only on symmetric pair similarity. The ML lane therefore needs at least two typed heads/operators.

**Cross-review:** systems lead requires the two objects to have distinct content IDs and receipts so model convenience cannot merge their authority semantics.

### ML → formal challenge

The current `StructuralWitness` type stores `non_preserved_properties`, but the basic transfer gate does not make them operationally decisive. Merely retaining a list is insufficient.

**Disposition:** add a use-site contract. Every known loss must be explicitly acknowledged as irrelevant to the requested use; every required property must have a preservation receipt; any required property intersecting a known non-preserved property rejects the transfer.

### Systems → formal challenge

Canonical commitments in the inherited hardening packet used `Decimal.normalize()`. Python Decimal normalization applies context rounding first, so the same exact Decimal can produce different encodings under different ambient precision. The original claim of environment-independent commitment was therefore too strong.

**Disposition:** replace arithmetic normalization with a context-free tuple derived from `Decimal.as_tuple()`. Preserve numeric equality across trailing zeros without invoking the decimal context. Add regression tests across several precisions.

### Standards cross-check on Unicode

The inherited canonicalizer normalized Unicode to NFC while calling itself canonical JSON. RFC 8785/JCS requires strings to be preserved as parsed rather than normalized. RAKL may choose an NFC semantic scheme, but it must call that choice out and version it rather than implying JCS compatibility.

**Disposition:** the new general canonical commitment defaults to `PRESERVE`, also supports `REQUIRE_NFC` and explicit `NORMALIZE_NFC`. The inherited hardening serializer is version-bumped and documented as a RAKL-specific scheme.

### Verification → solver challenge

A search trajectory is not the same object as a proof. Search may branch, backtrack and traverse failed states; the final proof may be a DAG/hypergraph of jointly required premises.

**Disposition:** keep trajectory receipts routing-only. Root authority requires the repository's existing proof DAG/verification path, plus explicit child overlap/substitution/assumption/representation/joint-obligation checks before root replay.

### Complexity → VTG challenge

A learned “distance to proof” can contain hidden oracle information through route labels, shortest distances, future edges or behavior-policy selection. A useful geometry must demonstrate **closed-loop local value after construction cost**, not one-step label accuracy.

**Disposition:** geometry receipts bind behavior policies, sampling process, label source, code/model, train/dev/fresh split, operator/chart/scale support, leakage flags, OOD detector and reopen policy. VTG Phase 1 has a kill criterion before natural dynamics are attempted.

### Scientific-method → training challenge

Adaptive training must not be justified by old Phase-1 v1 outcomes because that instrument is retracted. Training-state estimates are checkpoint-bound and can become stale after weight changes.

**Disposition:** keep adaptive allocation blocked until corrected v2 learner signal is valid. Add canonical assurance sidecar; retain separate train/probe/fresh splits and interval effects. No scheduler effectiveness is implied by a “ready” projection.

### Security → authority challenge

Internal HMAC fixtures are useful regression roots, not production custody. A caller-supplied key must never become a new trust root merely because the HMAC validates.

**Disposition:** classify trust backends explicitly. Production promotion requires externally governed trust-policy/configuration and evidence bindings. Derived views default to provenance reference only; they do not inherit source authority automatically.

## Panel consensus

The strongest coherent architecture is a **typed composition**:

```text
canonical evidence / authority plane
        ^ registered verification/promotion only
        |
problem + exact operational subject
        -> TCSQ / abstractions
        -> structural witness / portals
        -> solvability geometry (pi_solve)
        -> search policy / trajectory
        -> solution constellation / proof DAG
        -> root verifier

external structural identities
        -> checkpoint-bound pi_train
        -> bounded model update
        -> fresh assurance
        -> model promotion (not scientific promotion)
```

No panel seat considers implementation of the type system itself to resolve the remaining empirical questions.
