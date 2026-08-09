# SELF-RAKL Research Round 030 — Exact claim–evidence provenance

Date: 2026-08-09

## Live starting state

Starting `main`: `93ad54f362a590d47d58c5b7e619e811048edf25` (`Record Round 029 evidence-lineage validation`). Its exact-head `test` workflow run `31325926326` completed successfully before this round. There were no open issues or pull requests.

`FRAMEWORK_FIBER_INVENTORY_029` registered all 24 required method surfaces, zero unclassified high-impact surfaces, and 24 surfaces with at least one remaining empirical/trust-boundary/benchmark blocker. `META_N015_CLAIM_EVIDENCE_PROVENANCE` remained explicitly open: Round 029 had improved evidence-to-evidence ancestry but did not bind atomic claims to exact immutable source spans.

This is directly relevant to the Apple / generator lane. A `GLUE`, `LIFT`, `JUMP`, `PROJECT`, generator relation, or bridge witness can be carefully typed yet still rest on an opaque source string. Exact provenance is therefore a support prerequisite for later real generator/gluing/bridge benchmarks, but it must not be confused with semantic entailment or target authority.

## Frozen question and chronology

The Round-030 hostile benchmark was frozen first at commit `bc1b81135db550660f1bb631b4e5f217c69120a4`, before implementation.

Frozen question:

> Can a minimal fail-closed exact claim-to-source-span provenance contract improve evidence identity and failure localization without pretending that locator fidelity establishes semantic support or scientific authority?

The change is classified as a Class-A support layer. It does not alter search, routing, promotion, generator evaluation, or canonical knowledge activation.

## Six-role panel

These are role-separated passes in one orchestration context, not independent human review.

1. **Cognitive-science / analogy lead** — focused on the Apple-to-banana failure mode where an apparently relevant sibling passage is remembered or paraphrased correctly but attributed to the wrong source/version. Required exact source/span identity before an analogy witness can be treated as evidence-grounded.
2. **Knowledge-representation / ontology lead** — separated four objects: claim identity, source snapshot identity, text-span locator, and semantic evidence relation. Required immutable IDs/hashes and explicit relation typing rather than embedding all semantics in one citation field.
3. **Scientific-information-retrieval lead** — compared source-level citations with passage-level evidence retrieval and warned that retrieval/locator success is not support validation. Required stale-source and duplicate-passage hostile worlds.
4. **Applied-mathematics / dynamical-systems lead** — insisted that exact locator verification is a structural identity invariant only. It cannot be mapped to a probability of truth or support without a separately calibrated semantic evaluator.
5. **Computational-creativity / search lead** — wanted exact links exposed to future JUMP/generator search as auditable witnesses, but accepted that current search policy must remain unchanged until a real matched benchmark shows utility.
6. **Adversarial scientific-method reviewer** — attacked source-version drift, wrong source IDs, repeated quotes, Unicode offsets, post-hoc span selection, post-hoc semantic review, claim/scope mismatch, support/refutation disagreement, and authority escalation.

### Cross-role delegation and disagreements

- Ontology + IR jointly defined source snapshot + exact span as a locator layer separate from semantic support.
- Analogy + adversarial review jointly required the future generator/gluing benchmarks to use exact evidence links rather than opaque citation strings.
- Applied math + adversarial review jointly rejected any rule that turns locator fidelity into semantic-support confidence.
- The search lead proposed immediately making exact-span links mandatory for generator corroboration. The IR and adversarial leads rejected activation because no matched real benchmark yet shows that the extra representation improves scientific outcomes or cost-adjusted failure localization. The support API is therefore exposed but not integrated into active generator/search behavior.
- The ontology lead proposed normalizing source text before hashing. The adversarial reviewer rejected hidden normalization because it can silently relocate evidence across versions. The final contract hashes the exact UTF-8 snapshot supplied to the evaluator and performs no silent relocation.

## External projections and semantic deduplication

The external search deliberately moved outside analogy research into scholarly claim verification, annotation standards, and open-source evidence extraction.

- **W3C Web Annotation Data Model** already defines text-position and text-quote selectors, including exact text plus optional prefix/suffix context and code-point indexing. Selector machinery is therefore prior art, not a RAKL novelty.
- **CLAIM-BENCH (IJCNLP-AACL 2025)** evaluates more than 300 scientific claim-evidence pairs and reports meaningful limitations in LLM claim/evidence linking, with multi-pass strategies improving performance at extra cost. Generic claim-evidence linking is prior art and remains empirically hard.
- **EvidenceBench (COLM 2025)** is an open-source biomedical evidence-extraction benchmark with sentence-level evidence annotations and human validation. It provides a plausible future real-corpus route; RAKL does not claim evidence retrieval benchmarks as novel.
- **PaperTrail (CHI 2026 preprint)** decomposes scholarly answers and source documents into claims/evidence because source-level citations are too coarse for rigorous verification. Granular scholarly provenance is prior art.
- **ProvenanceGuard (2026 preprint)** explicitly treats source ownership as an axis distinct from pooled factual support and reports that source-plus-relation attribution remains difficult in close multi-source cases. This reinforces RAKL's separation of locator identity from semantic relation.
- **ProvenAI (2026 preprint)** further separates citation fidelity from behavioral document influence. That causal influence layer is intentionally out of Round-030 scope; evidence support provenance is not a claim that a source causally shaped model generation.

After semantic deduplication, the retained RAKL-specific contribution is narrow: fail-closed exact source/span identity, pre-review/pre-synthesis chronology, preservation of proposed-vs-reviewed contradictions, and an explicit prohibition on authority escalation from either a precise locator or a reviewed relation record.

## Implemented support

`src/rakl/claim_evidence.py` adds immutable:

- `ClaimAtom`
- `EvidenceSourceSnapshot`
- `TextSpanSelector`
- `ClaimEvidenceLink`
- `EvidenceJudgment`
- `ClaimEvidenceReport`

and typed relation/verdict enums plus `freeze_source_snapshot`, `sha256_text`, and `validate_claim_evidence_link`.

The evaluator:

- hashes the exact UTF-8 source snapshot and fails closed on stale content;
- requires the claim-evidence link to pin the same source hash;
- uses explicit code-point start/end offsets with an exact quote and optional immediate prefix/suffix anchors;
- performs no hidden normalization or silent relocation;
- rejects invalid bounds, wrong claim/source/link identity, source-version drift, and post-hoc selector construction;
- treats an exact locator with no semantic review as `LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED`;
- accepts only externally supplied semantic review records whose link/claim/scope identities match, whose known-answer validation state is positive, and whose review was frozen before synthesis;
- preserves a support/refutation disagreement as `REVIEW_CONTRADICTION` rather than rewriting history;
- distinguishes reviewed support, reviewed refutation, contextual qualification, and insufficient evidence;
- always returns false for scientific authority, target authority, and canonical activation.

## Exact candidate validation

Implementation candidate: `a3b88b125982ae03cb4a4c7c58b5b5bae345daeb`.

GitHub Actions run `31326491093` checked out and explicitly bound to that exact SHA. The `pytest` job completed successfully with **359 passing tests in 7.88s**.

The same job exposed the already-open evaluator-environment facts rather than hiding them: Ubuntu 24.04.4, runner image `ubuntu-24.04` version `20260720.247.2`, CPython 3.11.15, and dynamically resolved package versions. Those facts reduce ambiguity for this run but do not by themselves close the separate runner/environment/reproducible-release fibers.

## Capability-shaping attribution

- **Model strength amplified:** candidate evidence passage identification and scientific claim decomposition.
- **Weakness constrained/externalized:** unstable citation/source identity, stale source versions, repeated quotes, post-hoc locator movement, and accidental authority escalation.
- **Smallest compensator:** deterministic source SHA-256 + exact span + chronology validator.
- **Verification oracle:** 22 frozen hostile worlds plus exact-subject repository CI.
- **External-resource gain:** W3C selector semantics and current claim/evidence benchmarks informed the contract; no external runtime dependency was added.
- **Specialist complementation:** ontology/IR supplied provenance structure; applied math/adversarial review prevented precise locators from being relabeled semantic confidence.
- **Whole-system gain:** future generator/gluing/bridge witnesses can be made auditable at exact-source-span granularity without changing their evidence/authority gates.

No claim is made that this improves real scientific outcomes yet.

## Disposition

`META_N015_CLAIM_EVIDENCE_PROVENANCE`: **VALIDATED_IMPROVEMENT_SUPPORT_LAYER / SEMANTIC_AND_REAL_UTILITY_OPEN**.

The exact locator/identity subproblem is now executable and hostile-tested. Automatic claim extraction, semantic entailment quality, multi-span evidence aggregation, generation-influence provenance, and real cost/utility remain open. This is a retained semantic improvement, so framework growth remains `ACTIVE_NON_FLAT`; same-context and independent flat counters reset to zero. A framework saturation certificate is not allowed.

### Remaining falsifier / empirical closure

Freeze a real scientific claim-evidence packet using CLAIM-BENCH, EvidenceBench, or an equivalently auditable corpus, then compare under identical model/corpus/evaluator/cost budgets:

1. source-level citation only;
2. exact source + exact span provenance;
3. exact provenance + separate semantic review.

Measure wrong-source/stale-span false-pass rate, claim-evidence relation accuracy, failure localization, authority errors, token/time cost, and downstream generator/gluing/bridge witness quality. If exact-span provenance does not improve error detection or localization relative to source-level citations, keep it optional audit metadata rather than mandatory workflow complexity.

The broader closure frontier still includes runner/environment attestation, evaluator influence closure, durable execution, tokenizer calibration, reproducible distribution/release identity, real comparative-generator/gluing/bridge benchmarks, and deterministic meta-fiber registry reconciliation.
