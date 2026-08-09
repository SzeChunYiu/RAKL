# SELF-RAKL Research Round 008

Date: 2026-08-09

Starting `main`: `a0e3c535412ce790d6baea8f997b689253c3a48a`

Global status entering the round: `ACTIVE_NON_FLAT`.

## Frozen expert panel

The panel and its atomic questions were fixed before behavior implementation.

1. **CI execution-provenance engineer** — background in Git object identity, GitHub Actions event semantics, trusted-parent workflows and integration testing. Task: separate source, base, synthesized integration and actually executed subjects.
2. **Formal methods / typed-identity engineer** — background in partial identification, state machines and fail-closed validators. Task: define which subject coordinates can be glued and which must remain separate.
3. **Software supply-chain attestation engineer** — background in subject digests, builder identity, signed provenance and resolved dependencies. Task: bind execution claims to externally observed subjects without upgrading provenance into correctness.
4. **Scientific provenance epistemologist** — background in evidence scope, observation operators and reproducibility. Task: distinguish content/tree authority from revision/history authority.
5. **Adversarial benchmark reviewer** — background in CI spoofing, metadata confusion and benchmark gaming. Task: plant subject-swapping and self-report attacks and require rejection or cannot-check.

All experts worked from the same frozen Constitution, round-007 receipt, current evaluator/parent-evaluator code and the round-008 benchmark committed before implementation.

## 1. Native defect targeted

RAKL already knew conceptually that source head, base, synthesized merge state and executed subject are different coordinates. It did not yet have an executable object that enforced the distinction.

That leaves an authority-upgrade failure mode:

```text
source-head test passes
        ↓
result is described as if the source integrated with the current base also passed
```

The two claims are not equivalent. A source head can pass alone while the synthesized integration state fails, and a pull-request platform may expose source-head metadata while executing a merge/integration ref.

The frozen benchmark therefore requires a declared evaluation target before observing the result.

## 2. External projections

### 2.1 GitHub pull-request semantics

GitHub's current event documentation distinguishes the pull-request head SHA from the merge-branch commit used by normal pull-request execution. The `actions/checkout` documentation separately shows how to request the PR head instead of the merge subject.

RAKL absorbs a typed subject vector:

```text
source revision
base revision
integration revision/tree
actually executed revision/tree
```

These are coordinates, not synonyms.

### 2.2 Git tree versus commit identity

Git's object model gives a useful local-to-global warning. A tree represents recursive content state. A commit points to a tree but also carries parent/history and other commit metadata.

Therefore:

```text
same tree
!=
same revision/history object
```

RAKL now represents a matching integration/executed tree with unresolved revision identity as a **tree-scoped partial identification**, not as global subject identity.

### 2.3 Supply-chain provenance and attestation

SLSA build provenance and GitHub/Sigstore attestation traditions separately represent the subject digest, builder/run context and resolved dependencies. RAKL borrows the separation of coordinates, not their domain authority. Knowing what exact software subject a trusted process evaluated is evidence about execution identity; it is not evidence that the underlying scientific claim is correct.

This distinction keeps the implementation constitutional: representation/provenance is not mechanism/truth.

## 3. Frozen benchmark

`SELF_RAKL_RESEARCH_008_FROZEN_BENCHMARK.json` was committed as `743441d82dd6663d239d7658c842801a85d927f6` before implementation.

Its worlds require:

1. exact integration revision and tree -> `VALID_REVISION_AND_TREE`;
2. source head masquerading as integration -> `INVALID`;
3. explicitly declared source-head evaluation -> `VALID_REVISION`;
4. matching integration/executed tree with unresolved revision -> `PARTIALLY_IDENTIFIED_TREE_ONLY`;
5. executed tree mismatch -> `INVALID` even if revision labels match;
6. base mismatch -> `INVALID`;
7. candidate-produced subject observation -> `CANNOT_CHECK`;
8. missing integration identity -> `CANNOT_CHECK`.

A ninth hostile test checks that the same tree under a different revision never upgrades revision identity.

## 4. Implemented supporting challenger

`src/rakl/subject_identity.py` adds:

```text
EvaluationTarget
FrozenSubjectSpec
PlatformSubjectObservation
ExecutionSubjectObservation
SubjectAttestationReport
verify_execution_subject
```

The target is either `SOURCE_HEAD` or `INTEGRATION_RESULT` and must be declared in the frozen subject spec.

The validator fails closed when platform/execution observations are not external, rejects source/base drift, rejects integration tree mismatch, and exposes tree-only partial identification separately from revision identification.

`SubjectAttestationReport.valid` is intentionally false for `PARTIALLY_IDENTIFIED_TREE_ONLY`; callers must make an explicit future scope decision rather than receiving silent full authority.

The active trusted-parent workflow is **not changed in this round**. This module is supporting infrastructure. Workflow activation is a separate behavior change requiring its own frozen benchmark.

## 5. Execution evidence

Intermediate exact candidate `0844928275b11cdf253e2461a75d1f73576d645e` was checked by GitHub Actions run `31297080787`, job `93203847669`.

The log shows the candidate checkout at exactly `0844928275b11cdf253e2461a75d1f73576d645e` and `pytest` completed with:

```text
86 passed in 2.93s
```

This is intermediate authority only. Final exact-SHA CI is still mandatory after the research/receipt commits are staged.

## 6. A new residual discovered by the validator itself

The same execution log exposed another evaluator-identity coordinate that the current framework does not freeze.

The repository workflow text uses:

```text
actions/checkout@v4
actions/setup-python@v5
```

During this run GitHub resolved those tags to concrete action commits:

```text
actions/checkout -> 11d5960a326750d5838078e36cf38b85af677262
actions/setup-python -> a26af69be951a213d495a4c3e4e4022e16d87065
```

Thus unchanged workflow text is not the same thing as immutable transitive evaluator implementation identity. GitHub's security guidance recommends full-length action commit SHAs when immutable action identity is required.

This opens `META_N029_EVALUATOR_DEPENDENCY_PINNING`.

The panel explicitly rejected changing the protected workflow immediately. N029 was discovered after the round-008 benchmark was frozen, so changing action references now would violate RAKL's own pre-registration discipline. It must receive a separate benchmark.

## 7. Panel synthesis

The CI engineer accepted the source/base/integration/executed vector but rejected activation until the parent workflow itself can generate externally observed values for the vector.

The formal-methods engineer accepted tree-only partial identification and required that it remain non-valid for callers that demand revision authority.

The supply-chain engineer opened the transitive dependency problem: a trusted evaluator has an implementation closure beyond repository files, including actions, runtime/toolchain and potentially runner image.

The epistemologist required a claim-scope distinction: the same tree may be sufficient for a pure content-level behavior claim while insufficient for a historical/reproducibility claim tied to an exact revision.

The red-team reviewer required that candidate self-report remain `CANNOT_CHECK` even when every supplied identifier agrees.

This opens `META_N028_SUBJECT_SCOPE_AUTHORITY` in addition to N029.

## 8. Semantic novelty verdict

Retained non-duplicate objects:

1. `EXECUTION_SUBJECT_VECTOR`
2. `DECLARED_EVALUATION_TARGET`
3. `TREE_SCOPED_PARTIAL_AUTHORITY`
4. `META_N028_SUBJECT_SCOPE_AUTHORITY`
5. `META_N029_EVALUATOR_DEPENDENCY_PINNING`

External-observation requirements and Git tree/commit distinctions existed earlier; only their new executable/scoped consequences are counted.

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

No saturation counter advances.

## 9. Next discriminators

Highest-value next work is:

1. **META_N029** — freeze worlds for moved action tags, full-SHA pins, runtime-image drift and missing dependency attestations; do not mutate the protected workflow until the benchmark exists.
2. **N024 workflow activation** — separately freeze a trusted-parent workflow experiment that emits source/base/integration/executed revision/tree observations from trusted platform/VCS state, then feed the new module into promotion authority.
3. **META_N027** — evidence-bearing authority for identity assertions such as metadata alias, content hash and curator statement.
4. **META_N015** — exact claim/evidence span provenance so scientific evidence itself receives comparable auditability.
5. **META_N028** — claim-scoped rules for when tree-only versus revision-level identity is sufficient.

The Constitution is unchanged.
