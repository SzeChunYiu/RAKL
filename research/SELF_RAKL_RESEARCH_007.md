# SELF-RAKL Research Round 007

Date: 2026-08-09

Starting `main`: `d2ff33148cd30a6b33a23205783666d29b456130`

Global status entering the round: `ACTIVE_NON_FLAT`.

## Frozen expert panel

The panel and atomic questions were defined before behavior implementation.

1. **Scientific provenance and identifier engineer** — background in PID metadata, dataset versioning, W3C-style provenance and research-object packaging. Task: distinguish exact identity, version membership, derivation and unresolved aliasing without collapsing them into one relation.
2. **Dependent-evidence statistician** — background in clustered/dependent-effect evidence synthesis. Task: determine how identity mistakes propagate into false independent-saturation credit.
3. **Formal methods / graph identity engineer** — background in equivalence relations, DAG ancestry, entity resolution and conservative partial identification. Task: define a deterministic executable identity algebra and hostile graph cases.
4. **CI execution-identity engineer** — background in Git object models and GitHub Actions event/checkout semantics. Task: continue META_N024 and distinguish source, integration-state and executed-subject identity.
5. **Adversarial benchmark reviewer** — background in benchmark gaming and data leakage. Task: find renaming/version/derivation attacks that make shared evidence appear independent and reject any convenient identity guess.

The experts worked from the same frozen Constitution, round-006 receipt/validation, saturation implementation, preserved round-005 hostile PR trace and round-007 frozen benchmark. The implementation was not treated as evidence until the hostile worlds existed.

## 1. Native defect targeted

Round 006 improved saturation by requiring pairwise-disjoint declared evidence-lineage identifiers. But the comparison remained string-level.

That permits a false-independence attack:

```text
round A -> doi:10.x/data
round B -> https://repository.example/data
```

If those identifiers denote the exact same dataset, simple string disjointness grants two full independent credits when the correct conservative credit is one.

A second failure appears with versions and derived data. Treating every related identifier as exact identity would overcorrect:

```text
dataset:v1 != dataset:v2
```

as specific entities, even if both are versions of one dataset family. Likewise two transformed artifacts can remain distinct while sharing one raw source.

The identity layer therefore needs typed relations, not a generic same/different flag.

## 2. External projections

### 2.1 DataCite: exact identity is narrower than version membership

Current DataCite guidance uses `IsIdenticalTo` for the exact same research output under alternate identifiers/locations. Version relationships use separate relation types such as `IsVersionOf`, `HasVersion`, `IsNewVersionOf` and `IsPreviousVersionOf`.

RAKL absorbs the structural distinction, not DataCite-specific authority:

```text
exact alias
!=
version membership
```

A DOI or URL by itself is therefore not treated as proof that two evidence objects are byte/content identical. RAKL requires an explicit identity assertion at a declared scope.

### 2.2 W3C PROV: provenance relations have different semantics

PROV distinguishes alternates, specialization and derivation and gives them different formal behavior. RAKL uses this as an orthogonal warning against flattening all evidence relationships into transitive equivalence.

The v1 ledger therefore allows exact aliases to collapse but keeps version/derivation directed and ancestry-bearing.

### 2.3 Software Heritage: identity is object-type scoped

Software Heritage assigns different intrinsic object types to content, directories, revisions, releases and snapshots. This is a useful alien-domain projection because it makes an implicit scientific problem visible: “same evidence” is underspecified unless the object layer is named.

Two artifacts can share content while differing as revisions/history objects. Two repository snapshots can contain a common directory or content object while remaining different snapshots.

This yields a new retained semantic object:

`SUBJECT_IDENTITY_TYPED_BY_OBJECT_SCOPE`.

### 2.4 Git/GitHub: integration identity remains partially identified

Git separately represents a tree state and a commit that places that state in a parent/history/metadata context. GitHub documents that normal `pull_request` workflows use the synthesized merge branch/commit by default, while an explicit checkout of `pull_request.head.sha` selects the source head.

The preserved round-005 native trace remains decisive:

```text
source head = f4e5a5ac...
base       = b8287ad...
merge      = 33a8f0ae...
workflow_run API head_sha = f4e5a5ac...
actual PR checkout observed in platform log = 33a8f0ae...
```

So META_N024 stays open. A source-head identifier cannot be silently upgraded into an executed-integration-subject identifier.

## 3. Frozen benchmark

`SELF_RAKL_RESEARCH_007_FROZEN_BENCHMARK.json` was committed before behavior code.

Its known-answer worlds require:

1. exact aliases -> one full independent credit;
2. two versions -> remain distinct exact entities but share family ancestry for independence;
3. two derived datasets -> remain distinct but share raw ancestor;
4. unresolved possible alias -> partial identification and no full certificate;
5. genuinely disjoint entities -> independent credit preserved;
6. no identity ledger -> incumbent saturation behavior remains unchanged;
7. new semantic object -> saturation reopens;
8. integration source/base/merge/executed coordinates -> stay distinct.

## 4. Implemented challenger

The candidate adds `EvidenceIdentityLedger` with four v1 relations:

```text
IDENTICAL_TO
VERSION_OF
DERIVED_FROM
POSSIBLE_ALIAS
```

### Exact identity

`IDENTICAL_TO` forms deterministic equivalence classes. Canonical representatives are chosen deterministically so the result is invariant to relation insertion order.

### Version and derivation ancestry

`VERSION_OF` and `DERIVED_FROM` preserve the child entity's identity but contribute directed ancestor coordinates. Ancestry is transitively expanded and must be acyclic.

This enables the saturation layer to notice common ancestry without making the scientifically stronger statement that the two artifacts are exactly identical.

### Partial identity

`POSSIBLE_ALIAS` never guesses. If it touches a lineage used for an independent-flat certificate, the round is reported as identity-unresolved and receives no full evidence-independence credit until resolved.

### Opt-in integration with saturation

`IdentityAwareSaturationTracker` normalizes complete raw lineages before invoking the incumbent conservative disjoint-lineage count. The original `SaturationTracker` remains unchanged for callers that already supply canonical lineages.

## 5. Hostile tests and intermediate execution

A supplemental hostile test file attacks:

- alias renaming;
- relation insertion order;
- version siblings;
- transitive derivation;
- unresolved aliases;
- ancestry cycles;
- disjoint resolved datasets;
- backward compatibility;
- semantic reopening.

Intermediate exact candidate SHA `1c89c40631bdf14a3bb9729152b3830067ed4b29` was checked by GitHub Actions run `31295229498`; the `pytest` job completed successfully on that exact SHA. This was an intermediate check only; a final exact-SHA run is required after all research/docs/receipt commits are staged.

The container available to this run could not resolve `github.com`, so it was not used as an alternative local test authority. That transport limitation does not upgrade or downgrade the GitHub-hosted result.

## 6. Panel synthesis and challenges

The provenance engineer accepted the four-relation v1 as a minimum viable ontology but rejected any rule that derives `IDENTICAL_TO` merely from normalized URL/DOI text. Persistent identifiers name objects; they are not automatically content-equality proofs.

The statistician accepted ancestry expansion as a necessary precursor to full-independence certification but reiterated that this does not solve fractional/effective dependence. META_N026 remains open.

The formal-methods engineer required deterministic canonicalization, directed acyclic ancestry and an explicit unresolved state. Those are now executable.

The CI engineer argued that the Git/Software-Heritage distinction creates a broader identity principle relevant to META_N024: content/tree identity and revision/history identity are separate coordinates. No new active CI attestation is promoted in this round.

The red-team reviewer opened the next identity gap: the ledger currently receives identity assertions from outside. Their authority is not yet graded. A metadata statement, a cryptographic content hash and a human/LLM inference must not silently receive the same epistemic weight.

This opens `META_N027_IDENTITY_ASSERTION_AUTHORITY`.

## 7. Semantic novelty verdict

Retained non-duplicate objects:

1. `TYPED_EVIDENCE_IDENTITY_ALGEBRA`
2. `UNRESOLVED_IDENTITY_BLOCKS_INDEPENDENCE`
3. `SUBJECT_IDENTITY_TYPED_BY_OBJECT_SCOPE`
4. `PERSISTENT_IDENTIFIER_IS_NOT_CONTENT_PROOF`
5. `META_N027_IDENTITY_ASSERTION_AUTHORITY`

META_N024 is reinforced, not double-counted as new. W3C/OpenLineage provenance ancestry already existed in the atlas; only the new identity consequences are counted.

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

No saturation counter advances.

## 8. Next discriminators

Highest-value next experiments are:

1. **META_N024** — parent-controlled execution-subject attestation with source commit, base commit, integration commit/tree and actual executed commit/tree as separate fields; plant mismatches and require rejection without executing candidate-controlled evaluator code.
2. **META_N027** — known-answer identity-authority worlds: metadata-declared alias, content-hash identity, mutable landing resources, conflicting identity assertions and identity at different object scopes.
3. **META_N015** — exact claim/evidence span provenance so the evidence entities feeding the lineage/identity graph are themselves auditable.
4. **META_N026** — only after dependence structure is available, study effective/fractional evidence contribution; do not infer a number from graph overlap alone.

The Constitution is unchanged.
