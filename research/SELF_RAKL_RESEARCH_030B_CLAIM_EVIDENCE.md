# SELF-RAKL Research 030B — Exact Claim–Evidence Provenance

Date: 2026-08-09

## Live truth and concurrency reconciliation

This lane began from `main` `93ad54f362a590d47d58c5b7e619e811048edf25`, where `META_N015_CLAIM_EVIDENCE_PROVENANCE` was still open after Round 029 improved evidence-to-evidence ancestry but did not bind atomic claims to exact source spans.

A 22-world benchmark was frozen **before implementation** at commit `bc1b81135db550660f1bb631b4e5f217c69120a4`. The first implementation candidate `a3b88b125982ae03cb4a4c7c58b5b5bae345daeb` passed exact-head CI (`359 passed in 7.88s`), and the first full research/validation branch head `dfb4c2955df4312f0eceb8fa729bc47ccbc3ae22` also passed exact-head CI.

Before promotion, `main` independently advanced through a different Round 030 (scoped self-evolution) and Round 031 (contextual method capability frontier), reaching `260d9dcdc47cfc7c3dce0bd9d4379fd17ef55f3a`. Those histories occupied the generic Round-030 filenames. The stale branch was therefore **not force-promoted and not allowed to overwrite concurrent research**. The exact support change was reapplied linearly on current main as `7506ac5c5d21410538640817604eaa073c840c18`; exact-head workflow run `31326775246` succeeded with **378 passed in 8.29s**. This report uses the `030B` namespace to preserve both valid parallel histories.

The frozen benchmark itself remains immutable at the original benchmark commit. `SELF_RAKL_RESEARCH_030B_CLAIM_EVIDENCE_BENCHMARK_POINTER.json` records that chronology rather than pretending the benchmark was re-frozen after implementation.

## Atomic question

> Can RAKL bind an atomic scientific claim to an exact immutable source span, fail closed on stale/post-hoc/identity errors, and still refuse to treat a precise locator as semantic support or scientific authority?

This is a Class-A support-layer question. It does not change active search, routing, generator transport, promotion, or canonical-knowledge policy.

## Six-role panel

These are role-separated passes in one orchestration context, not independent review.

1. **Cognitive-science / analogy expert** — examined the Apple→banana failure mode where a remembered sibling passage is semantically plausible but belongs to the wrong source/version.
2. **Knowledge-representation / ontology expert** — separated claim identity, source snapshot identity, span locator, semantic relation, and authority into distinct typed objects.
3. **Scientific-information-retrieval expert** — required stale-source and repeated-passage worlds and insisted that retrieval/locator success is not relation correctness.
4. **Applied-mathematics / systems expert** — treated locator fidelity as an identity invariant only, not a calibrated probability of truth/support.
5. **Computational-creativity / search expert** — proposed making exact evidence links available to future JUMP/generator packets but accepted no active search-policy change before a real matched utility benchmark.
6. **Adversarial scientific-method reviewer** — attacked version drift, wrong IDs/hashes, Unicode positions, post-hoc locators/reviews, claim/scope mismatch, proposal-vs-review contradiction, and authority escalation.

Joint decisions: ontology+IR designed the locator/semantic split; analogy+adversarial review made exact links a future real-generator benchmark dependency; applied-math+adversarial review rejected any locator→confidence shortcut. A proposal to normalize text before hashing was rejected because hidden normalization can silently relocate evidence across versions.

## External projections and novelty boundary

Current primary/open-source neighbors narrow the claim substantially:

- W3C Web Annotation already specifies text position/quote selectors, including exact text and context anchors. Selector mechanics are prior art.
- CLAIM-BENCH (IJCNLP-AACL 2025) already benchmarks scientific claim↔evidence linking and shows meaningful model errors plus a cost/accuracy tradeoff for multi-pass validation.
- EvidenceBench (COLM 2025) is an open-source sentence-level biomedical evidence-extraction benchmark with human validation.
- PaperTrail (CHI 2026 preprint) already argues that source-level citations are too coarse and exposes claim-level evidence grounding.
- ProvenanceGuard (2026 preprint) separates source attribution from pooled factual support and reports difficulty in joint source+relation attribution.
- ProvenAI (2026 preprint) further separates citation fidelity from causal document influence on generation.

RAKL therefore claims no novelty for generic claim/evidence mapping, span selectors, evidence extraction, granular citations, or provenance interfaces. The retained object is narrower: **fail-closed immutable source/span identity + chronology + preserved semantic-review contradiction + authority non-escalation inside RAKL's evidence governance**.

## Implemented support

`src/rakl/claim_evidence.py` adds `ClaimAtom`, `EvidenceSourceSnapshot`, `TextSpanSelector`, `ClaimEvidenceLink`, `EvidenceJudgment`, typed relation/verdict enums, and `ClaimEvidenceReport`.

`validate_claim_evidence_link` checks exact UTF-8 SHA-256 source identity, claim/link/source identities, code-point bounds, exact text, optional immediate prefix/suffix anchors, and selector chronology. It performs no silent normalization or relocation. A valid locator without semantic review returns `LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED`.

Semantic review is a separate externally supplied record. It must bind the same link/claim/scope, expose positive known-answer validation, and be frozen before synthesis. Proposal/review disagreement is preserved as `REVIEW_CONTRADICTION`; insufficient evidence remains insufficient. Every report deliberately refuses scientific authority, target authority, and canonical activation.

This is important for `GLUE → LIFT → JUMP → PROJECT`: an exactly located banana passage may be a good auditable candidate witness, but exact location proves neither a shared generator nor valid projection to apple.

## Capability-shaping attribution

- **Model strength amplified:** candidate passage finding and atomic scientific claim decomposition.
- **Weakness externalized:** stale/wrong source identity, repeated quote ambiguity, post-hoc locator movement, and authority leakage.
- **Smallest compensator:** deterministic exact snapshot hash + exact span + chronology validator.
- **Verification oracle:** the frozen 22 hostile worlds and exact-subject repository CI.
- **External-resource gain:** annotation/provenance standards and current evidence benchmarks informed the contract; no runtime external dependency was added.
- **Specialist complementation:** ontology/IR supplied identity structure; applied math/adversarial review prevented identity precision from becoming semantic confidence.
- **Whole-system claim:** support-layer auditability improved; real scientific-outcome gain remains `CANNOT_CHECK`.

## Disposition and next discriminator

`META_N015_CLAIM_EVIDENCE_PROVENANCE` is now **VALIDATED_IMPROVEMENT_SUPPORT_LAYER / SEMANTIC_AND_REAL_UTILITY_OPEN**.

Exact locator identity is implemented and hostile-tested. Automatic claim extraction, automatic semantic entailment, multi-span aggregation, causal generation influence, and real scientific utility remain open.

The decisive real benchmark should compare, under matched model/corpus/evaluator/token/time resources:

1. source-level citation only;
2. exact source + exact span provenance;
3. exact provenance + separately validated semantic relation.

Measure stale/wrong-source false passes, relation accuracy, failure localization, authority errors, cost, and downstream generator/gluing/bridge witness quality. If exact-span provenance does not improve error detection or localization over source-level citations, it remains optional audit metadata rather than mandatory workflow complexity.

## Saturation

Round 030B retains genuinely new RAKL semantic/support objects after deduplication, so the framework remains `ACTIVE_NON_FLAT`. Same-context and independent flat counters are zero. No framework saturation certificate is permitted.
