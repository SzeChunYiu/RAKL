# Epistemic Mechanics saturation audit — 2026-08-12

Status: `RESEARCH_AUDIT / NO_RUNTIME_PROMOTION / PRIMARY_SOURCES_FIRST`

Repository subject at freeze: `bd6b0e3edeb2b94b3f31b17e111c7a278f461f96`.

This note records the research result for issue #426. It narrows rather than broadens the novelty claim: RAKL should adopt stronger generic provenance/authority mechanisms where prior work is better, while retaining as its candidate residual the **scientific claim-type authority system** and the separation

```text
experience / search / routing / proposal != scientific authority.
```

No literature finding in this note grants framework-promotion or scientific authority.

## 1. Primary-source findings

### 1.1 Memory authority and non-amplification are not generic RAKL novelty

**TMA-NM — arXiv:2606.24322** demonstrates that long-term-memory authority can be laundered through summarization, trusted-tool echo, and manufactured corroboration. Its strongest reusable principle is write-time non-malleable origin binding plus Sybil-resistant corroboration-gated elevation. This is stronger than ordinary lineage metadata on the attacked memory surface.

**PPMF — arXiv:2607.29167** independently formalizes provenance non-amplification under lossy consolidation and uses platform-maintained provenance to gate action risk.

**AuthMem-Bench — arXiv:2608.01679** shows that authority collapse at consolidation is not a corner case: its paired benchmark reports collapse in 48/49 tested consolidator/backbone configurations and demonstrates that preserving authority metadata can remove unauthorized actions without materially harming benign success in its tested setting.

**MemTX — arXiv:2607.23929** contributes transactional staging, evidence/provenance/permission-bearing commit, irreversible-action gating, and typed cascade repair after retraction. RAKL must treat these as nearest-parent mechanisms, not rename them as Epistemic Mechanics novelty.

**RAKL residual:** apply non-amplification/origin/root semantics to **typed scientific claim authority** (grounding/representation/mechanism/identification/decision), not only action permission or generic belief state. Scientific authority must not be laundered by memory operations, derivation, delegation, corroboration, or self-evolution.

### 1.2 Claim-level semantic provenance is a real residual gap

**AAR / From Fluent to Verifiable — arXiv:2602.13855** argues that report-level provenance is insufficient; the auditable unit is the claim-to-evidence relation, including conflicts, with provenance coverage, provenance soundness, contradiction transparency, and audit effort.

**Evidence Tracing and Execution Provenance — arXiv:2606.04990** similarly identifies claim-level and semantic provenance, provenance-aware safety, realistic trace benchmarks, and recovery as open design problems.

**BibAgent / MisciteBench — arXiv:2601.16993** provides large-scale evidence that citation integrity needs explicit verification rather than trusting bibliographic presence.

**Current RAKL coverage:** `src/rakl/claim_evidence.py` already binds exact source snapshots, exact text spans, selector chronology, external semantic-review identities, and scope. It deliberately grants no scientific authority. `src/rakl/v3_scientific_authority.py` separately binds promotions to exact claim text, axis, scope, evidence content digests and protected attestation.

**Residual gap:** there is no first-class object that proves the **bridge** between those two layers: that the exact reviewed claim–evidence relations, including contradiction/context/root structure, are sufficient for the exact requested authority coordinate. A correct terminal answer with the wrong evidence IDs must fail this bridge.

### 1.3 Auditability must cover lifecycle and recovery, not logs alone

**Auditable Agents — arXiv:2604.05485** separates accountability, auditability, and auditing and decomposes auditability into action recoverability, lifecycle coverage, policy checkability, responsibility attribution, and evidence integrity, with detect/enforce/recover mechanism classes.

**No Certificate, No Execution — arXiv:2605.24462** provides a useful generic pattern: proposal != permission, and execution should depend on checkable certified traces rather than fluent reasoning alone.

**RAKL coverage:** protected attestations, transition ownership, immutable authority projections, pre-action receipts, TaskEpisodes, and append-only authority events already cover substantial detect/enforce history.

**Residual gap:** recovery semantics need to be explicit for authority descendants after root refutation, scope downgrade, origin corruption, or missing provenance. A stale derived certificate must not silently survive a revoked/root-narrowed parent.

### 1.4 Abstention is sequential

**AgentAbstain — arXiv:2607.10059** uses paired executable tasks and distinguishes should-act from should-abstain worlds, including post-hoc abstention after irreversible action.

**Agentic Abstention — arXiv:2606.28733** formalizes answer / abstain / gather-more-information as a sequential decision and shows that timing is a major failure mode.

**Abstention-Aware Scientific Reasoning — arXiv:2602.14189** decomposes scientific claims into minimal conditions and treats evidence sufficiency as distinct from raw task accuracy.

**RAKL coverage:** `CANNOT_CHECK`, blocker states, discriminator selection, pre-action receipts, and authority-inert search actions exist.

**Residual gap:** the scientific authority layer does not yet expose an explicit evidence-sufficiency transition contract distinguishing `COMMIT`, `RESTRICT_SCOPE`, `GATHER_MORE_EVIDENCE`, `RUN_DISCRIMINATOR`, and genuine terminal `CANNOT_CHECK`, nor does it measure premature vs post-hoc abstention.

### 1.5 Prediction success cannot stand in for mechanism or identification

**Correct Answer, Wrong Mechanism — arXiv:2606.23175** reports right-looking outcomes supported by mechanisms contradicted by the agent's own adjacent-regime data and shows that a lightweight regime-shift test can expose the failure in the studied setting.

**AI scientists produce results without reasoning scientifically — arXiv:2604.18805** reports >25,000 runs across eight domains and finds evidence frequently ignored, refutation-driven belief revision uncommon, and base-model effects much larger than scaffold effects in their decomposition.

**RAKL coverage:** `AuthorityAxis.REPRESENTATION`, `.MECHANISM`, `.IDENTIFICATION`, strict axis escalation checks, noninterference threat families, and legal revocation/supersession controls already encode the distinction.

**Residual gap:** the distinction is stronger formally than empirically. RAKL needs objective regime-shift / observational-equivalence worlds that separately score task outcome, mechanism fidelity, and identification survivor-set correctness.

## 2. Current RAKL completeness matrix

| Surface | Current RAKL | Nearest external strength | Residual / action |
|---|---|---|---|
| exact source/span provenance | `claim_evidence.py` | AAR / tracing / BibAgent broaden auditability | keep; do not duplicate |
| claim-level semantic support | external `EvidenceJudgment`, proposal-only | AAR stronger as explicit claim graph/audit target | add exact authority-binding bridge (#427) |
| evidence root lineage | `ScientificEvidenceBinding.upstream_evidence_id` | TMA-NM stronger on non-malleable origin; PPMF on laundering | adopt origin/non-amplification principles (#428) |
| independent corroboration | terminal-root collapse check | TMA-NM explicitly Sybil-resistant | formalize root-accounting policy (#428) |
| experience->authority separation | executable noninterference + real v3 surface | nearest work largely action/belief authority | candidate RAKL residual; retain |
| authority coordinates | G/R/M/I/D | nearest systems generally do not expose same scientific axis split | candidate RAKL residual; benchmark rather than assume novelty |
| promotion binding | protected subject hash + attestation | generic certificate ideas exist | retain scientific specialization |
| revocation/supersession | append-only history + active view | MemTX stronger on cascade-repair completeness | add descendant propagation/recovery audit (#428) |
| abstention | terminal statuses and blockers | AgentAbstain/Agentic Abstention stronger on timing | add sequential sufficiency semantics (#429) |
| mechanism fidelity | axis distinction + leakage tests | CAWM gives direct empirical discriminator | build objective regime-shift benchmark (#430) |
| auditability | receipts, histories, transition ownership | Auditable Agents provides broader lifecycle card | map detect/enforce/recover coverage; add recovery where missing |
| search/ranking | fibres, retrieval, routing, GPS/JUMP work | 2026 agentic retrieval stronger on interaction spaces and evolving retrieval | #433; ranking remains authority-inert |

## 3. Threat-model delta

### Already substantially covered by existing families

- `EXPERIENCE_TO_EVIDENCE`
- `REPETITION_TO_AUTHORITY`
- `ROUTING_TO_AUTHORITY`
- `REFLECTION_TO_AUTHORITY`
- `FAILURE_TO_IMPOSSIBILITY`
- `PROVENANCE_TO_INDEPENDENCE`
- `PREDICTION_TO_MECHANISM`
- `MECHANISM_TO_IDENTIFICATION`
- `WORKSPACE_TO_AUTHORITY`
- `SELF_EVOLUTION_TO_AUTHORITY`
- `UNATTESTED_REVOCATION`

### Genuinely distinct candidate additions

1. `SUPPORT_EDGE_TO_WRONG_EVIDENCE` — terminal claim may be correct while its support binding is wrong.
2. `CONTRADICTION_HIDDEN_DURING_SYNTHESIS` — preferred support is retained while valid conflict edges disappear.
3. `CONSOLIDATION_AUTHORITY_AMPLIFICATION` — summary/consolidation preserves claim but loses origin/scope restrictions.
4. `DERIVATION_AUTHORITY_AMPLIFICATION` — derived report inherits a stronger coordinate than its registered transformation permits.
5. `DELEGATION_AUTHORITY_AMPLIFICATION` — trusted agent/tool echo upgrades a low-authority source.
6. `SYBIL_CORROBORATION_AS_INDEPENDENCE` — multiple descendants/agents masquerade as independent roots.
7. `STALE_DESCENDANT_AUTHORITY` — root refutation or restriction does not invalidate/narrow dependent active certificates.
8. `PREMATURE_ABSTENTION` and `POST_HOC_ABSTENTION` — epistemic timing failures, distinct from ordinary `CANNOT_CHECK` accuracy.
9. `CORRECT_ANSWER_WRONG_MECHANISM` — task success with falsified mechanism narrative.
10. `SCOPE_GENERALIZATION_AFTER_LOCAL_SUCCESS` — local/regime success silently broadens authority scope.

## 4. Formal-law gaps

The next Epistemic Mechanics version should research typed laws rather than a scalar trust score.

### 4.1 Authority transport

For a registered transformation `f`, successor authority must be admitted by a typed transport relation:

```text
A(y) admissible_from A(x), f, certificate
```

not an assumed total order. The transport may preserve or narrow coordinates/scope; it cannot create a stronger coordinate without an evidence-bearing certificate for that coordinate.

Required transformations: derivation, summarization/consolidation, delegation/tool echo, corroboration, supersession, and self-evolution.

### 4.2 Claim-evidence completeness

A scientific promotion should be able to require a certificate binding:

```text
claim/version
requested authority axis
scope/context/QoI
support relations
refutation/conflict relations
missing-evidence obligations
root/derivation identities
independence grouping
allowed transition
forbidden stronger transitions
```

The existing span validator remains proposal-only; this certificate is the authority-transition precondition, not a replacement.

### 4.3 Recovery / revocation propagation

The framework needs a deterministic policy for which dependent active certificates become invalid, narrowed, or `CANNOT_CHECK` when a root certificate/evidence origin is revoked or loses scope. Independent descendants must survive where their own certificates remain valid.

### 4.4 Sequential evidence sufficiency

Scientific state should represent whether the next epistemically licensed move is commit / restrict / measure / discriminate / align / external-check / abstain. Search/acquisition itself remains authority-inert until the resulting evidence is registered and certified.

## 5. Search-engine implications

The 2026 retrieval literature supports #433 but also sharpens its boundary:

- PaSaMaster (`arXiv:2605.14306`) treats literature retrieval as an evolving search process with separate expensive planning and low-cost retrieval/ranking while preserving source authenticity.
- RISE (`arXiv:2606.06880`) reframes retrieval as construction of a bounded tool-interactable **interaction space**, which maps naturally onto a strengthened `ProblemFibre` rather than prompt stuffing.
- Agentic-R (`arXiv:2601.11888`) trains retrieval using downstream answer utility, highlighting that local similarity != agent utility; RAKL must prevent this feedback from becoming authority feedback.
- SciRAG (`arXiv:2511.14362`) combines adaptive sequential/parallel retrieval, citation-graph reasoning, and attribution-aware synthesis.
- STEM (`arXiv:2604.22282`) projects semantic questions into structural query graphs for evidence retrieval.

RAKL should therefore maintain a **multi-index search layer** (lexical, semantic, structural, claim/evidence, citation/derivation, failure, method, temporal), but rank signals remain routing authority only. Search telemetry can improve retrieval/ranking policy; it cannot train scientific truth from exposure/click/reuse frequency.

## 6. Prioritized implementation order

1. **#427 claim-level EvidenceBindingCertificate** — smallest high-value bridge; enables wrong-evidence detection before scientific promotion.
2. **#428 authority transport / origin/root non-amplification** — adopt stronger generic principles from TMA-NM/PPMF/MemTX while specializing to scientific axes.
3. **#429 sequential evidence sufficiency** — build objective paired act/gather/restrict/abstain worlds.
4. **#430 mechanism-fidelity benchmark** — use generated observational-equivalence/regime-shift worlds.
5. **#433 search-engine challenger** — initially proposal/routing-only; integrate authority filters only through #427/#428 outputs.
6. **#431 integrated Grand Challenge** — after child intervention identities freeze.
7. **#434 Self-RAKL tournament** — promote only from fresh assurance; retain rejected variants.

## 7. Novelty boundary after saturation

Do **not** claim generic novelty for:

- provenance-bearing memory;
- non-amplification in generic agent memory;
- transactional commit/cascade repair;
- claim-level auditability as a general concept;
- abstention as an agent capability;
- citation graphs / PageRank / agentic retrieval.

The strongest residual candidate is narrower:

> RAKL composes continually learned search/method state with a separately typed scientific-authority state whose claim-level promotions, revocations and scope changes can be certified against exact evidence/root/context relations, while experience/search/ranking transformations are formally prevented from minting scientific authority.

This residual remains a **candidate novelty claim** until the nearest-work audit and integrated empirical challenge survive.

## 8. Acceptance decision

Issue #426 research conclusion:

```text
SATURATION_COMPLETE_AT_2026_08_12_CUTOFF
NEW_LOAD_BEARING_GAPS = {
  CLAIM_LEVEL_AUTHORITY_BINDING,
  AUTHORITY_TRANSPORT_NON_AMPLIFICATION,
  SEQUENTIAL_EVIDENCE_SUFFICIENCY,
  MECHANISM_FIDELITY_EMPIRICS
}
SEARCH_ENGINE = ROUTING_LAYER_RESEARCH_ONLY_UNTIL_ASSURED
```

No runtime promotion is authorized by this note alone.
