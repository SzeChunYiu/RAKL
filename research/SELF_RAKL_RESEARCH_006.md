# SELF-RAKL Research Round 006

Date: 2026-08-09

Starting `main`: `d1ef1507153b57da8a77a0af4b6318c6f80589de`

Global status entering the round: `ACTIVE_NON_FLAT`.

## Frozen expert panel

The panel was defined before the active method change.

1. **Research-synthesis statistician**. Background in dependent-effect meta-analysis, cluster/robust variance estimation and hierarchical evidence synthesis. Task: determine what shared samples, datasets and studies do to an "independent" saturation round.
2. **Scientific provenance engineer**. Background in W3C PROV-style entities, activities, derivations and provenance-of-provenance. Task: define the smallest evidence-lineage representation that can be tested rather than narrated.
3. **Formal-methods engineer**. Background in graph algorithms, partial identification and conservative lower bounds. Task: construct a counting rule that cannot manufacture independence when lineage is incomplete.
4. **CI/evaluation systems engineer**. Background in GitHub Actions event/checkout semantics and execution attestation. Task: continue the open integration-subject audit without allowing that software residual to dominate the whole research portfolio.
5. **Adversarial red-team reviewer**. Background in benchmark gaming, evaluator leakage and scientific double-counting. Task: design cases in which cosmetically different papers/routes/agents all descend from the same evidence and would falsely satisfy the old saturation rule.

Each panel member received the same frozen object: RAKL's current saturation contract, round-005 evaluator residuals, Constitution and current meta-fiber ledger. Their findings were compared only after their individual atomic questions were fixed.

## 1. Native defect targeted this round

Before this round, `ResearchRound.independent=True` was a single boolean. `SaturationTracker.independent_flat_count()` counted every flat round carrying that label after the last non-flat round.

That is too weak for the epistemic meaning of "independent" used by RAKL.

Three independent agents can read three different papers and still inherit the same experiment. Three papers can reanalyse one dataset. Two codebases can consume the same upstream benchmark artifact. Independent prose generation does not imply independent evidence.

The frozen counterexample was therefore:

```text
paper/route A -> dataset D
paper/route B -> dataset D
paper/route C -> dataset D
```

The old binary rule could grant three independent-flat rounds. The correct conservative answer is at most one fully evidence-independent lineage unless additional structure shows otherwise.

## 2. External projections and what each contributed

### 2.1 Dependent-effect meta-analysis

Hedges, Tipton and Johnson's robust-variance work begins from exactly the kind of failure RAKL must avoid: conventional independence assumptions fail when multiple effect estimates come from the same individuals or otherwise clustered studies. Later robust-variance work expands the working models used when dependent effects occur.

RAKL does **not** copy a meta-regression estimator into semantic saturation. It absorbs the structural lesson:

> Different estimates are not independent merely because they have different labels or publications.

This projection also prevents an overreaction. Dependence is not synonymous with zero information. RAKL should not throw all shared-lineage evidence away; it should refuse to count it as multiple **full independent** saturation rounds unless the dependence structure is identified.

### 2.2 W3C PROV

W3C PROV provides an orthogonal chart. It models provenance through entities, activities, agents and derivations and explicitly supports provenance about provenance and relations between entities referring to the same thing.

RAKL absorbs the graph idea, not an authority claim. An ancestry record says where evidence came from; it does not make the evidence true.

This suggested the executable distinction:

```text
process/context independence
!=
evidence-lineage independence
```

and the longer-term target:

```text
raw entity
-> transformation/activity
-> derived entity
-> analysis
-> evidence packet
-> claim
```

### 2.3 OpenLineage

OpenLineage adds a software/data-engineering view that is useful precisely because it is not a scientific meta-analysis framework. Its core model distinguishes jobs, runs, datasets, input/output relationships and dataset/run facets, and emphasizes consistent identity/naming plus version information.

RAKL absorbs a new atomic warning: one lineage string is not a sufficient ontology. Dataset version, run, transformation and derived artifact are distinct coordinates.

This opens `META_N025_LINEAGE_IDENTITY_NORMALIZATION` because two aliases for the same underlying dataset could otherwise evade a string-overlap test.

### 2.4 GitHub Actions execution identity

The CI expert revisited the round-005 residual using GitHub's current documentation and the preserved native run. For `pull_request`, the GitHub execution ref/GITHUB_SHA represents the pull-request merge branch, while the workflow/check-suite `head_sha` represents the source head. `actions/checkout` documents an explicit override when the user wants the PR source head rather than the merge result.

The preserved native merge revision `33a8f0aea308ab6b26410f85dbb074159ed8517e` has two parents: round-005 base `b8287ad...` and hostile source head `f4e5a5ac...`.

Therefore `META_N024_INTEGRATION_SUBJECT_IDENTITY` is reinforced, not closed:

```text
source_head
base_revision
integration/merge_revision_or_tree
actually_executed_revision
```

must remain typed separately.

Round 006 does not promote a new integration-subject authority. This is recorded as partial identification rather than patched with candidate-produced metadata.

## 3. Frozen known-answer worlds

The benchmark was committed before the implementation in `SELF_RAKL_RESEARCH_006_FROZEN_BENCHMARK.json`.

The principal worlds were:

1. three flat rounds with one shared dataset lineage -> full independent credit at most 1;
2. three flat rounds with pairwise-disjoint complete lineages -> credit 3;
3. partial overlap `{D1}`, `{D1,D2}`, `{D3}` -> explicit dependence and conservative credit 2;
4. unknown/incomplete lineage -> partial identification and no full lineage-independent credit;
5. a new semantic object -> `ACTIVE_NON_FLAT` regardless of lineage;
6. round-005 source/base/merge/execution identity -> keep the coordinates separate.

## 4. Implemented challenger

The candidate adds two fields to each research round:

```text
evidence_lineage
lineage_complete
```

The original `independent` field is retained, but its meaning is narrowed to **process/context independence**.

Full independent-flat saturation credit now requires both process independence and sufficiently complete evidence ancestry.

For complete lineage declarations, the tracker constructs overlap relationships and chooses a maximum subset of rounds whose lineage sets are pairwise disjoint. This is a set-packing problem.

For small collections, the implementation solves the subset exactly. Above a configured exact-search limit, it switches to a deterministic greedy **lower bound** and marks the result `exact_count=false`.

This asymmetry is intentional:

> Computational approximation may delay a saturation certificate; it must not manufacture one.

The diagnostic exposes:

```text
declared_process_independent_flat_rounds
lineage_complete_flat_rounds
unknown_or_incomplete_lineage_rounds
overlap_pairs
conservative_full_independent_rounds
credited_round_ids
count_method
exact_count
```

## 5. Panel challenge after implementation

The statistician accepted the full-independence interpretation but rejected an inference that shared lineage should receive zero total scientific value. That becomes a future graded-dependence problem, not a change to this v1 conservative certificate.

The provenance engineer accepted canonical lineage sets as a minimum viable representation but identified a false-negative failure mode: aliases or versions can hide common ancestry. This opens `META_N025_LINEAGE_IDENTITY_NORMALIZATION`.

The formal-methods engineer required the large-N fallback to be labelled as a lower bound rather than an approximate exact answer. That requirement is now executable.

The CI engineer concluded that N024 remains partially identified and should not be bundled into this method activation merely because the old native trace is persuasive.

The red-team reviewer verified that the new hostile tests directly attack the old false-saturation path and preserve the new-semantic-object reopening rule.

## 6. New residual: effective dependence is not binary

The combined atlas now distinguishes three questions:

```text
Are the research processes independent?
Do the evidence lineages overlap?
If they overlap, how much effective independent information remains?
```

Round 006 implements only the first two strongly enough for saturation certification.

The third opens `META_N026_EFFECTIVE_EVIDENCE_DEPENDENCE`. Fractional credit must not be invented from overlap counts alone. It needs domain-specific covariance, sample overlap, causal/hierarchical structure or another validated dependence model.

## 7. Validation evidence

Intermediate candidate SHA:

`c4c08e8feb52edddc95ca592d0651ff934b7b968`

GitHub Actions run `31292916558` checked out that exact SHA and completed successfully with:

```text
65 passed in 2.77s
```

The compare against the frozen incumbent showed only:

```text
research/SELF_RAKL_RESEARCH_006_FROZEN_BENCHMARK.json
src/rakl/saturation.py
tests/test_saturation.py
```

at that intermediate point. Protected evaluator/configuration inputs were untouched.

A final candidate validation is still required after this research/documentation packet is staged. The active `main` must remain at the frozen incumbent until that exact final SHA passes.

## 8. Semantic novelty verdict

Retained non-duplicate objects:

1. `PROCESS_VS_EVIDENCE_INDEPENDENCE`
2. `LINEAGE_SET_PACKING_SATURATION`
3. `LINEAGE_PARTIAL_IDENTIFICATION`
4. `CONSERVATIVE_LINEAGE_COUNT_FALLBACK`
5. `LINEAGE_IDENTITY_NORMALIZATION_GAP`
6. `EFFECTIVE_EVIDENCE_DEPENDENCE_GAP`
7. `INTEGRATION_SUBJECT_COORDINATE_GAP_REINFORCED`

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

No saturation counter advances this round.

## 9. Next discriminators

Highest priority remains `META_N024`: build a trusted parent-owned subject attestation that binds source, base, synthesized integration tree/revision and actual execution subject without trusting candidate-produced logs or metadata.

Then attack `META_N025` with alias/version known-answer worlds. An evidence-lineage model that can be bypassed by renaming a dataset must not become a saturation authority.

In parallel, `META_N015_CLAIM_EVIDENCE_PROVENANCE` should provide the claim/evidence packet whose derivation graph can eventually feed the lineage layer.
