# Observation Contract v1 — claim boundary

Source packet: `RAKL_RECURSIVE_QUESTION_CLOSURE_2026-08-15`, bound to repository snapshot
`cf5085650e17469f72a2c27bfc060d415cbeca6b`. All 24 packet files verified byte-identical to
`MANIFEST.json` before porting; the packet's own reference tests were executed first (14 passed).

Implementation: [src/rakl/observation_contract.py](../../src/rakl/observation_contract.py).
Production tests: `tests/test_observation_contract.py`.

## What this is

A **pursuit-side plugin**. It gives a question one frozen object stating what information the
solver may read: input sources, acquisition regime, allowed semantic normalizers,
external-knowledge policy, provenance requirement, abstention policy, evaluator policy and
evaluator epoch.

Without it, a persistent negative collapses by default into "the mechanic is inadequate", when the
cause may be that the question demanded structure the licensed inputs never contained. The contract
makes that separable, and makes the recall ceiling it implies computable before an epoch is spent:

```text
E_Ω(B) ⊆ { g : Lic_Ω(g) = 1 }        ⟹        Recall_G(E_Ω) ≤ |G_Ω| / |G|
```

The bound is **contract-relative**. It states what an extractor confined to this contract cannot
reach. It is not a theorem that semantic inference or declared world knowledge cannot recover the
remaining targets.

## What this is not

- **Not a core reopen.** No new authority dimension, privileged effect, certificate class,
  protected service or recursion layer above L7. Every transition is ordinary pursuit state plus an
  append-only receipt.
- **Not an authority path.** Changing a contract changes what is searched for, never what is true.
  The authority projection is unchanged unless a separately certified protected operation is
  invoked: `α(A_Ω(S)) = α(S)`.
- **Not an evaluator-mutation API.** The module records which evaluator epoch was in force and
  refuses comparison across a change. Changing evaluator *policy* remains the protected evaluator
  path's business.
- **Not scientific evidence.** No verdict, receipt or ceiling promotes anything. Passing an audit
  means the question's information assumptions are explicit, not that its answer is right.

## Integration

The contract does not introduce a second decision chain. Verdicts project into the existing
`AuditResidual` and run through the frozen `decide()`:

| Verdict | Coordinates | Frozen chain returns |
|---|---|---|
| `EVALUATOR_CONTRACT_TENSION` | `EVALUATOR` (+ `evaluator_invalid`) | `AUDIT_EVALUATOR` |
| `REQUIRES_NORMALIZATION` | `QUESTION`, `MEASUREMENT` | `RUN_DISCRIMINATOR` |
| `REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE` | `EVIDENCE` | `SOLVE_CURRENT` |
| `CANNOT_CHECK` | — (resource bound) | `CANNOT_CHECK` |
| `LICENSED_*` | — | `SOLVE_CURRENT` |

A gold-versus-source contradiction is carried as `evaluator_invalid`, not merely as an `EVALUATOR`
cause, so it inherits the chain's top priority: an evaluator asserting what its licensed sources
deny must be audited **even under a resource bound**, or the bound would mask it. This was found by
a production test, not by inspection — the first mapping let a resource bound outrank the tension.

`REQUIRES_NORMALIZATION` deliberately yields two coordinates. Whether the question over-demands or
the observation operator is wrong is exactly the ambiguity the framework refuses to resolve by
revision, so the chain discriminates first.

## Preserved history

The ARN acquisition negative stands unchanged under its original contract. A later semantic or
external successor, if positive, is a **different frozen acquisition regime**: it neither erases nor
retroactively confirms its predecessor. Contract change stales dependent results under the
predecessor's digest; nothing is deleted and nothing is relabelled as evidence for the successor
question.

## Open, not closed

The specification question is closed at v1. The empirical programme is not:

```text
RFA_FRESH_UTILITY_ASSURANCE          = OPEN_EMPIRICAL
SEMANTIC_PARENT_EXECUTION            = CANNOT_CHECK_RESOURCE_BOUND
SCAR_FRESH_FORMULATION_DIAGNOSTIC    = PASS_EXPLORATORY
```

The 37/42 SCAR figure is a contract-relative diagnostic for one untouched 12-record block. It is
neither a corpus-wide rate nor evidence that SCAR is invalid.
