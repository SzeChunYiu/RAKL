# SELF-RAKL Research Round 029 — Evidence-lineage dependence

Date: 2026-08-09

## Live starting state

Starting `main`: `134aee702c48601d716b7de435dc30bd6c6938ba` (`Refine runner and evaluator influence fibers`). The exact-head `test` workflow for that main commit was completed successfully before this round. There were no open issues or pull requests at round start.

The latest complete framework inventory was `FRAMEWORK_FIBER_INVENTORY_027B`. It registered all 24 required method surfaces, zero unclassified high-impact surfaces, and 24 surfaces with at least one remaining empirical/trust-boundary/benchmark blocker. The similarity/generator lane remained non-flat. Among its unresolved children, `META_N064_EVIDENCE_LINEAGE_DEPENDENCE` was a bounded, high-value gap: current generator-family support used distinct flat `evidence_lineage_ids`, but did not represent shared ancestry through datasets, analyses, alternate IDs, or multi-parent provenance.

## Frozen question

Can an explicit evidence-lineage graph reduce false generator corroboration without claiming more than provenance can establish?

The benchmark was frozen first in `SELF_RAKL_RESEARCH_029_FROZEN_BENCHMARK.json` at commit `9deb34b922a859df63e639ca6573e301aeb220a9` before implementation.

## Six-role panel

These are role-separated review passes within one orchestration context; they are not independent human reviews.

1. **Cognitive-science / analogy lead** — asked how repeated analogies can be retrieved from one conceptual ancestor and masquerade as independent rediscovery. Requested explicit ancestry checking before treating sibling analogies as corroboration.
2. **Knowledge-representation / ontology lead** — modeled derivation, alternate identity, specialization/versioning, dangling references, and graph validity. Recommended a typed provenance DAG rather than one lineage string.
3. **Scientific-information-retrieval lead** — focused on duplicate publications, common registries, shared data windows, and alternate identifiers. Required unknown ancestry to remain unknown rather than being scored independent.
4. **Applied-mathematics / dynamical-systems lead** — objected to deriving a numeric effective sample size from graph topology alone. Approved a structural provenance-component count only if it is explicitly separated from statistical independence.
5. **Computational-creativity / search lead** — argued that lineage diversity is useful for search diversification, but only as a coverage coordinate; raw domain distance or source count cannot become evidence authority.
6. **Adversarial scientific-method reviewer** — attacked false independence from renamed sources, remote common roots, mixed shared/unique roots, incomplete ancestry, cycles, dangling parents, post-hoc graph construction, and generator-family authority escalation.

### Cross-role delegation and disagreements

- The ontology and IR leads jointly specified typed derivation plus alternate/specialization identity handling.
- The analogy and search leads jointly specified the generator-family downgrade use case.
- The applied-math and adversarial leads jointly rejected a graph-derived numeric `effective_n` or probability of independence.
- The ontology lead initially favored calling disjoint complete roots `INDEPENDENT_PROVENANCE`; the applied-math and adversarial leads rejected that wording because hidden shared causes can remain outside the registered graph. Final wording is `NO_KNOWN_SHARED_ANCESTRY`.
- The search lead proposed automatically rewarding more provenance components during JUMP portfolio selection. The adversarial reviewer rejected activation without a matched real benchmark; the current implementation therefore exposes structure but does not alter routing/search policy.

## External projections

The search angle deliberately left the analogy literature and looked at provenance, duplicated evidence synthesis, and evolutionary shared-history correction.

- **W3C PROV-DM** provides typed provenance concepts including derivation and separate alternate/specialization relations. This is prior art for provenance representation, not a RAKL novelty.
- **A 2025 Journal of Clinical Epidemiology primary study on duplicated registry data** reports that overlapping registry evidence can alter meta-analytic estimates and develops a decision framework based on source, sampling timeframe, and inclusion characteristics. This supports the premise that publication/source count is not independent support count.
- **Hibbins, Breithaupt & Hahn (PNAS 2023)** show that shared evolutionary history can be mosaic through discordant gene trees and that single-tree comparative methods can be biased. This is an alien-domain reminder that a single flat ancestry label can be structurally inadequate.
- The open-source **`trungdong/prov`** Python project implements W3C PROV assertions, serialization, and graph conversion. RAKL therefore does not claim generic provenance-graph machinery as novel and does not add that dependency for this small support layer.

Semantic deduplication retained only the RAKL-specific authority and generator-integration rules.

## Implemented support

`src/rakl/evidence_lineage.py` adds immutable:

- `EvidenceLineageNode`
- `EvidenceLineageGraph`
- `LineageReport`
- `GeneratorLineageReport`

The evaluator:

- collapses alternate IDs for dependency checking;
- treats specializations/versions as distinct evidence with common ancestry;
- follows transitive multi-parent ancestry;
- detects remote shared ancestors;
- returns graph-structural provenance component counts;
- fails closed on unknown ancestry, unregistered selected evidence, dangling references, or unknown freeze chronology;
- invalidates duplicate IDs, derivation cycles, and post-hoc graph construction;
- returns `NO_KNOWN_SHARED_ANCESTRY` rather than `INDEPENDENT` for complete disjoint registered roots;
- exposes `statistical_effective_n = None` and never claims statistical independence;
- cannot grant scientific or target authority.

`assess_generator_family_with_lineage` wraps the existing generator-family evaluator. It can only preserve or downgrade the existing proposal. A family that appears multi-lineage under flat labels is downgraded if the explicit graph reveals a common ancestor. Unknown ancestry returns `CANNOT_CHECK`. Disjoint complete provenance may retain the original generator proposal, but separate target evidence and promotion are still required.

## Frozen hostile worlds and first exact-head result

The benchmark contains 20 registered worlds, including direct/remote common roots, disjoint roots, unknown ancestry, dangling references, cycles, alternate IDs, specialization, mixed shared/unique roots, component counting, duplicate IDs, input-order invariance, generator downgrade, unknown generator ancestry, authority non-escalation, and a prohibition on arbitrary numeric effective N.

The first implementation candidate was exact head `5d822d932a9f69ce1aebfd7bbd9d8d93ce9df4c1`. GitHub Actions run `31325710479` checked out and explicitly bound to that SHA, then completed successfully with **340 passing tests**. The log also exposed hosted-runner identity details, but those remain part of the separate Round-028 runner/evaluator-influence fiber and are not used to claim closure here.

## Capability-shaping attribution

- **Model strength amplified:** recognizing repeated provenance/ancestry patterns across sources.
- **Weakness constrained:** treating differently named papers or analogies as independent by default.
- **Smallest compensator:** deterministic typed provenance graph plus fail-closed evaluator.
- **Verification oracle:** frozen hostile worlds and exact-subject CI.
- **External-resource gain:** W3C provenance semantics and primary evidence-duplication/shared-history research informed the contract; no external runtime dependency was added.
- **Specialist complementation:** ontology/IR supplied provenance structure; applied math/adversarial review prevented overclaiming statistical independence.
- **Whole-system gain:** generator corroboration can now be downgraded by known evidence ancestry while authority boundaries remain unchanged.

No claim is made that this support layer improves real scientific outcomes yet.

## Disposition

`META_N064_EVIDENCE_LINEAGE_DEPENDENCE`: **VALIDATED_IMPROVEMENT_SUPPORT_LAYER / REAL_UTILITY_OPEN**.

This is a genuine semantic improvement, so the framework remains `ACTIVE_NON_FLAT` and flat-round counters reset to zero. No framework saturation certificate is allowed.

### Remaining falsifier / empirical closure

A real frozen duplicated-ancestry benchmark must compare:

1. raw source count,
2. flat lineage labels,
3. explicit lineage graph,

under the same model, corpus, evaluator, and cost budget. If explicit lineage graphs do not reduce false corroboration or improve failure localization relative to simpler baselines, retain provenance for audit only and remove any extra decision-layer complexity.

The next generator-lane empirical parent remains `META_N068_REAL_COMPARATIVE_GENERATOR_BENCHMARK`; the broader framework also retains the release/evaluator, durable execution, tokenizer, claim-evidence provenance, contextual-gluing, multi-hop-bridge, and registry-reconciliation blockers already present in the inventory.
