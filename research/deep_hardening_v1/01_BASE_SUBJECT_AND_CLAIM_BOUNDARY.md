# Exact subject, trust boundary, and claim boundary

## Frozen repository subject

This handoff was reconciled against:

```text
SzeChunYiu/RAKL
main@3c24a9f78722ee5fa47ee3527e7e0e774aff91c6
```

That commit reports that the earlier P0/P1/P2 formal/engineering register has been worked down: U1–U6, I1–I6 and associated CI/reproducibility fixes are already on `main`. However, the current open-gap register still contains one unchecked P2 workflow-path item despite calling P2 empty; treat that as reconciliation finding C0, not as proof of zero open engineering TODOs. Therefore older handoffs are evidence/history, **not authoritative replacement source**.

## Authority hierarchy used by this packet

1. **Current live repository at the frozen base** — implementation subject.
2. **Exact current repository tests/docs** — executable/documentary evidence, still scope-limited.
3. **Original handoff artifacts** — candidate patches, audits and research memory; never allowed to overwrite stronger current behavior blindly.
4. **Primary external literature/standards** — novelty/mechanism/security constraints; no automatic RAKL authority.
5. **This integration packet** — additive implementation proposal + preregistration, not scientific promotion.

## Four kinds of claims kept separate

### Software-contract claim

A module/test establishes behavior on its registered known-answer inputs. Local tests can support this.

### Formal/mathematical claim

Requires explicit assumptions, domain, quantifier, exact object, proof/counterexample or carefully scoped finite verification. A class name such as `Certificate` does not create a theorem.

### Empirical mechanism claim

Requires a frozen comparator, split, estimator, total-cost accounting, uncertainty and fresh evaluation. Development known worlds are not confirmatory evidence.

### Novelty claim

Requires a bounded literature world, equivalence notion, search routes and cutoff. “Not found” is not “never existed”. The strongest surviving RAKL candidate is currently a conjunction, not a single primitive.

## No “zero unknown defects” terminal

The correct terminal is closer to:

```text
KNOWN_ACTIONABLE_CODE_GAPS_AT_FROZEN_CUTOFF = 0   # only after full repo validation
OPEN_SCIENTIFIC_COORDINATES = explicit
GLOBAL_BIBLIOGRAPHIC_COMPLETENESS = false
INDEPENDENT_REVIEW = pending
```

Unknown defects remain possible after any finite audit.

## Migration rule

Legacy identities that may be externally referenced are not silently redefined. In particular:

- keep current `state_fingerprint` v1 semantics;
- keep current `state_fingerprint_v2` as a legacy identity until a migration is deliberately approved;
- add a new canonical V3 commitment and dual-write it alongside legacy values;
- add canonical training-assurance sidecars without rewriting historical `snapshot_hash` values.

A cryptographic hardening change that changes old identifiers without an explicit migration is itself an integrity defect.
