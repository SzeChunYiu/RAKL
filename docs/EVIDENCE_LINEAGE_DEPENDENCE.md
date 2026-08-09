# Evidence lineage dependence

RAKL must not treat source count as independent corroboration. Two papers, datasets, analogies, or benchmark results can have different identifiers while descending from the same underlying evidence entity, registry, analysis, intellectual source, or other provenance root.

This support layer implements a deliberately narrow claim:

> A registered provenance graph can reveal known shared ancestry and can show that no shared ancestry is recorded among complete, disjoint roots. It cannot by itself prove statistical, causal, or epistemic independence.

## Why this matters for GLUE / LIFT / JUMP / PROJECT

A generator-family proposal can appear to be supported by several sibling systems while all of those siblings ultimately rely on one dataset or one derivational lineage. That is corroboration inflation. `assess_generator_family_with_lineage` therefore can preserve or downgrade an existing generator-family result, but it can never upgrade the result or grant target authority.

A successful chain is now conceptually:

`LIFT -> lineage-aware sibling evidence check -> generator proposal -> PROJECT -> target test -> separate promotion`

rather than:

`many source IDs -> independent support`.

## Graph contract

`EvidenceLineageNode` records:

- a stable evidence identifier;
- parent derivation / shared-data / shared-intellectual-source links;
- alternate identifiers for the same underlying evidence entity;
- specialization/version links;
- whether the registered ancestry is known to be complete.

`EvidenceLineageGraph` is frozen before outcome inspection for benchmark use. The evaluator fails closed on unregistered selected evidence, dangling references, unknown ancestry, and invalid derivation cycles.

Alternate identifiers are collapsed for dependency checking. Specializations remain distinct evidence entities but inherit ancestry from the common source. This follows the useful distinction in W3C PROV between derivation and alternate/specialized descriptions of entities, while keeping RAKL's scientific-authority semantics separate from generic provenance semantics.

## Verdicts

- `CORRELATED_SUPPORT_ONLY`: selected evidence has known shared registered ancestry.
- `NO_KNOWN_SHARED_ANCESTRY`: registered ancestry is complete and disjoint. This is intentionally not named `INDEPENDENT`.
- `CANNOT_CHECK`: ancestry or required graph references are incomplete.
- `TRIAL_INVALID`: the frozen trial contract is violated, for example by a derivation cycle, duplicate evidence ID, or post-hoc graph definition.

`provenance_component_count` is a graph-structural count only. It is not a statistical effective sample size. `statistical_effective_n` therefore deliberately returns `None`.

## Authority boundary

Lineage checks never activate canonical scientific knowledge and never grant target authority. A generator-family proposal that survives the lineage check remains a proposal requiring target-domain evidence and ordinary RAKL promotion.

## External projections

Three external projections materially shaped this support layer:

1. W3C PROV-DM separates derivation from alternate and specialization relations. This supports representing provenance identity and ancestry explicitly rather than encoding all dependence as a flat label.
2. Recent evidence-synthesis research shows that duplicated or overlapping registry data can materially distort meta-analytic estimates, so publication count is not an adequate independence proxy.
3. Phylogenomic comparative research shows that shared histories can be mosaic rather than reducible to a single tree, motivating a DAG-like ancestry representation and caution against one flat lineage label.

The open-source `trungdong/prov` package was inspected as a concrete W3C PROV implementation. RAKL does not vendor it for this small support layer; the frozen internal dataclasses keep the scientific contract minimal and avoid adding a runtime dependency. Generic provenance modeling is prior art and is not claimed as a RAKL novelty.

## Remaining empirical boundary

The support contract is validated only on frozen hostile synthetic worlds. It does not establish that lineage-aware analysis improves real scientific synthesis. The next empirical discriminator is a frozen real corpus containing duplicated registries, shared analysis pipelines, alternate publications, incomplete lineage information, and genuinely disjoint evidence, evaluated against flat-label and raw-source-count baselines under matched cost and model budgets.
