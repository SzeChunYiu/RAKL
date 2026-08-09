# Claim–Evidence Provenance

RAKL treats a citation, an exact evidence locator, a semantic support judgment, and scientific authority as different objects.

The core rule is:

```text
exact source/span identity
    != semantic support or refutation
    != causal influence on the generated claim
    != scientific/target authority
```

This prevents a precise citation from becoming stronger evidence merely because it is precisely located.

## Atomic objects

`ClaimAtom` freezes one claim and its scope/QoI. `EvidenceSourceSnapshot` freezes one exact textual source representation with a SHA-256 over its UTF-8 bytes. `TextSpanSelector` identifies one exact code-point range and may carry immediate prefix/suffix anchors. `ClaimEvidenceLink` proposes a typed relation (`SUPPORTS`, `REFUTES`, or `QUALIFIES`) between the claim and that exact span. `EvidenceJudgment` is a separate externally supplied semantic review record.

The support layer never computes semantic entailment itself.

## Fail-closed locator contract

`validate_claim_evidence_link` checks:

1. claim, link and source identities;
2. the source snapshot hash against the actual supplied text;
3. the hash pinned by the claim-evidence link;
4. selector freeze chronology;
5. start/end bounds using Python Unicode code-point indexing;
6. exact selected text;
7. optional immediate prefix and suffix anchors.

No normalization or silent relocation is performed. If a source version changes, the old link becomes stale rather than being silently moved to a similar passage.

W3C Web Annotation is prior art for position and quote selectors. RAKL's narrower concern is evidence governance: source identity, pre-outcome chronology, semantic-review separation, negative-history preservation and authority non-escalation.

## Semantic review is a separate layer

A valid locator without a semantic review returns:

```text
LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED
```

A semantic review must refer to the same frozen claim/link/scope, must expose its known-answer validation state, and must have been frozen before downstream synthesis. Accepted review records can yield only proposal states such as:

```text
REVIEWED_SUPPORT_PROPOSAL_ONLY
REVIEWED_REFUTATION_PROPOSAL_ONLY
REVIEWED_CONTEXT_PROPOSAL_ONLY
REVIEWED_INSUFFICIENT_EVIDENCE
```

If the proposed relation and validated semantic review disagree, RAKL records `REVIEW_CONTRADICTION`; it does not rewrite the original proposal to make the record look consistent.

Every `ClaimEvidenceReport` deliberately returns false for scientific authority, target authority and canonical activation. Ordinary RAKL promotion/evidence gates remain separate.

## Apple / Knowledge-Atlas role

A theory chart or generator witness should eventually be able to point to exact claim-evidence links instead of opaque citation strings. That integration is not activated by this support layer. It first needs a matched real benchmark.

This distinction is especially important for `GLUE -> LIFT -> JUMP -> PROJECT`: a banana paper may contain an exactly located passage that appears relevant to a shared generator, but exact location does not prove the generator relation, the transport mapping, or the projected apple hypothesis.

## Capability shaping

The model strength being amplified is identification of candidate evidence passages. The weakness being externalized is unstable source/span identity and post-hoc citation movement. The smallest compensator is a deterministic hash-plus-selector validator. The verification oracle is the frozen hostile benchmark. Semantic relation recognition remains outside the deterministic support layer.

## Empirical closure

This support layer is not evidence that RAKL improves real scientific claim grounding. The remaining discriminator is a frozen real claim-evidence packet comparing source-level citations, exact-span provenance, and exact-span-plus-reviewed semantic relations under the same model, corpus, evaluator and cost budget. If the richer representation does not improve wrong-source/stale-span error rates or failure localization, it should remain optional audit metadata rather than mandatory workflow complexity.
