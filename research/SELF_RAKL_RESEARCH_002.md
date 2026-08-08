# Self-RAKL Research 002 — Truth Maintenance, Argument Structure, Evidence Provenance, and Typed Equivalence

Date: 2026-08-09

Starting main: `6d6ee5f54a7607765d5d1779859151f562030918`

## Why this round was opened

The first self-RAKL round was non-flat. This round deliberately moved away from the previous agent-framework-heavy route and searched older knowledge-representation theory, computational argumentation, claim-evidence benchmarks, and active systematic-review stopping.

A native code audit also found a concrete RAKL self-contradiction: `KnowledgeFiber.equivalence_classes()` treated exact isomorphism, generator equivalence, observational equivalence, asymptotic equivalence, QoI equivalence, and approximate representation as one transitive graph. A chain such as `A EXACT B` and `B QOI_EQUIVALENT C` could therefore yield `{A,B,C}` as one equivalence class. That violated the existing Knowledge Atlas rule that weaker relationship layers never silently upgrade to stronger ones.

The hostile benchmark was frozen before the challenger implementation in `SELF_RAKL_RESEARCH_002_FROZEN_BENCHMARK.json`.

## Retained semantic objects

### META_N002A — typed/scoped relation closure

**Projection:** equivalence is a family of relations, not a single relation.

RAKL now closes a graph transitively only inside one licensed relationship type and one declared scope. Approximate representation remains pairwise unless a separate bound licenses composition. This is an implementation correction of an existing principle, not a philosophical amendment.

Implemented in `src/rakl/core.py` and covered by hostile cases for exact transitivity, cross-layer non-upgrade, scope partition, pairwise approximation, and global-portrait visibility.

### META_N013 — assumption-environment truth maintenance

Johan de Kleer's assumption-based TMS (Artificial Intelligence 28(2), 1986; DOI `10.1016/0004-3702(86)90080-9`) contributes a different projection on contradiction handling. Rather than globally retracting beliefs when inconsistency appears, an ATMS labels conclusions by assumption sets, supports efficient context switching, and can explore multiple candidate solutions simultaneously.

**Retained RAKL projection:** claims should eventually be supportable under explicit assumption environments; contradictions should identify minimal inconsistent assumption combinations rather than forcing a global winner. This fits `context before contradiction`, immutable negative history, and the ResearchTree.

**Boundary:** classical ATMS machinery does not determine source quality, statistical uncertainty, or causal authority. Those remain RAKL evidence-layer responsibilities.

### META_N014 — structured evidence argumentation

Phan Minh Dung's abstract argumentation framework (Artificial Intelligence 77(2), 1995; DOI `10.1016/0004-3702(94)00041-X`) makes attack and acceptability relations first-class rather than leaving disagreement as prose. The 2025 MArgE work (`arXiv:2508.02584`) independently shows a modern LLM-specific projection: structured argument trees can produce inspectable claim-verification paths and outperform unstructured multi-LLM debate in its reported experiments.

**Retained RAKL projection:** add a claim-level support/attack/rebuttal/undercut graph as a future child fiber, but never let graph structure or LLM votes manufacture evidence authority. Arguments must terminate in source-grounded evidence packets or explicit assumptions.

### META_N015 — atomic claim-evidence provenance and omission coverage

CLAIM-BENCH (IJCNLP-AACL 2025, DOI `10.18653/v1/2025.ijcnlp-long.127`) evaluates claim-to-evidence extraction/validation over more than 300 annotated claim-evidence pairs and reports that decomposed multi-pass prompting can improve linking at added computational cost. EvidenceBench (`arXiv:2504.18736`, COLM 2025) evaluates hypothesis-conditioned evidence extraction against expert annotation. PaperTrail (`arXiv:2602.21045`, CHI 2026) decomposes generated answers and sources into discrete claims/evidence and makes unsupported claims and omissions visible.

**Retained RAKL projection:** a citation or free-form evidence ID is too coarse for high-authority synthesis. RAKL needs exact atomic claim-to-evidence links, relation labels (support / contradiction / mixed / cannot-check), and coverage accounting for important source evidence omitted from synthesis.

**Boundary:** provenance visibility is not verification by itself. PaperTrail's user study is a useful caution that making support structure visible need not make users act on it.

### META_N011A — route-local active-search stopping

ASReview (Nature Machine Intelligence 3, 125–133, 2021; DOI `10.1038/s42256-020-00287-7`) contributes active-learning prioritization plus simulation benchmarking for systematic screening. The SAFE procedure (Systematic Reviews 13, 81, 2024; DOI `10.1186/s13643-024-02502-7`) contributes a conservative, multi-heuristic stopping view that balances screening cost against risk of missed records and explicitly warns against universal fixed thresholds.

**Retained RAKL projection:** add a route-local *source-recall risk* diagnostic so a literature route can decide when further document screening is low value.

**Critical non-equivalence:** document-recall stopping is not semantic saturation. RAKL's stronger saturation certificate still requires semantic deduplication, route diversity, and independent flat rounds.

## Native self-refutation and repair

The mixed-layer closure bug was repaired in commit `e68ac7e07a28d696a198a59fc8a86375e60fccee` after the benchmark was frozen in commit `9a573279814e17cc0df8e02302439fd708bc22e8`.

The new implementation:

- defines which relationship types permit transitive closure;
- partitions closure by exact relationship type and `scope`;
- makes exact isomorphism the safe default for `equivalence_classes()`;
- emits all typed/scoped components through `equivalence_layers()`;
- keeps `APPROXIMATE_REPRESENTATION` as explicit pairwise edges;
- exposes these layers in `global_portrait()`.

GitHub Actions run `31284668383` completed successfully for the repair commit, including the full repository `pytest` job.

## Process residual discovered by doing the work

The implementation commit was fast-forwarded to `main` and then its push-triggered CI ran. It passed, so no invalid behavior survived. However, this sequence is not literally consistent with the intended gate “tests pass before active main moves.”

A new fiber `META_N016_PREPROMOTION_STAGING` is therefore opened. The next implementation round should benchmark a two-phase candidate workflow: candidate branch/check first, then fast-forward main only after a successful check. A failed candidate must leave `main` unchanged.

This process defect is preserved rather than hidden because RAKL's negative-history rule applies to RAKL itself.

## Semantic saturation update

This round is **NON_FLAT**. It retained multiple genuinely new method objects from research traditions that were materially different from round 001:

```text
knowledge representation / truth maintenance
computational argumentation
scientific claim-evidence benchmarking
provenance / omission analysis
active systematic-review stopping
native self-audit of relation algebra
```

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
knowledge_saturated = false
```

## Next high-value fibers

1. `META_N016_PREPROMOTION_STAGING` — make the direct-to-main gate transactional.
2. `META_N015_CLAIM_EVIDENCE_PROVENANCE` — exact evidence spans and omission coverage.
3. `META_N013_ASSUMPTION_TRUTH_MAINTENANCE` — labels/nogoods for assumption-conditioned worlds.
4. `META_N006_INFORMATION_GAIN` — expected information gain for next query/experiment.
5. `META_N007_RAKLBENCH` — executable atomic fixtures, including the new claim-evidence cases.
6. `META_N014_EVIDENCE_ARGUMENTATION` — support/attack/undercut graph with strict evidence authority.

Do not implement these merely because the source traditions are attractive. Each requires its own frozen discriminator and hostile cases.
