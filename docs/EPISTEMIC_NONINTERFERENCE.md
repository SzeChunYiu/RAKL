# EPISTEMIC_NONINTERFERENCE

Formal, executable specification of Paper II's authority-noninterference claim.
Proposal-only: wired into no promotion gate, mints no authority.

Implementation: `src/rakl/epistemic_noninterference.py`,
`src/rakl/v3_scientific_authority.py`.
Planted worlds: `tests/test_epistemic_noninterference.py`,
`tests/test_v3_scientific_authority_noninterference.py`.
Refs #152, #242. The issue requests this note at `research/PAPER2_EPISTEMIC_NONINTERFERENCE.md`;
it lives here instead, so the issue's acceptance checklist should be read against this path.

**Status change at #242.** The v3 runtime now composes a scientific-authority
coordinate, so the invariant is exercised against a real composition surface
instead of returning `NO_INTEGRATION_SURFACE`. §2.1, §4 and §7 below are written
against the integrated revision; the superseded pre-#242 findings are preserved
verbatim in §9. This establishes an executable architecture invariant only — no
model capability, empirical superiority, or authority-leakage claim.

## 1. The property

Persistent experience is *supposed* to change what RAKL tries next. The claim is
narrower than "state never changes":

> Behaviour-changing state and authority-changing state have a protected
> interface. Only an explicitly registered evidence-bearing promotion may move
> the scientific-authority projection.

For a transition sequence `tau` built only from experience, retrieval,
workspace, strategy, reflection or routing operations:

```text
pi_auth(tau(X_t)) == pi_auth(X_t)
```

`pi_auth` is *non-monotone*: refutation-driven revocation shrinks it. The
invariant constrains **which transition families may move it**, not its direction.

## 2. State decomposition mapped onto the current revision

The issue's conceptual `X_t = (K_t, E_t, R_t, G_t)`, mapped to what exists. No
parallel ontology is introduced; gaps are recorded as gaps.

| Issue coordinate | Current projection | Status |
|---|---|---|
| `E_t` experience | `experience_substrate.ExperienceLedger` (episodes, lessons, nodes, edges); `failure_lattice.FailureExperienceLattice`; `research_tool_inventory.ResearchToolInventory` — all fields of `v3_runtime.RAKLV3State` | **exists** |
| `R_t` retrieval/routing | **not stored.** Recomputed on demand from `E_t` by `experience_policy.rank_operators_with_experience`, `rank_paths_with_experience`, `induce_strategy_motifs` | **derived, no persistent coordinate** |
| `G_t` scientific authority | `authority_ledger.AuthorityLedger` over `AuthorityAxis` = G/R/M/I/D, held as the immutable `v3_scientific_authority.ScientificAuthorityProjection` field of `RAKLV3State` | **composed (#242)** |
| `K_t` canonical scientific state | `claim_evidence.ClaimAtom` plus `v3_scientific_authority.ScientificEvidenceBinding` (content digest + frozen provenance class + supported axes + upstream lineage), both persisted in the same projection | **composed, minimal (#242)** |

### 2.1 What is composed, and how (#242)

1. `RAKLV3State.scientific_authority` carries the certificate history, the
   non-monotone active view, the event log, the canonical claims, and the
   content-bound evidence roots. It is appended **last** in the dataclass so
   positional construction by existing consumers keeps working, and defaults to
   empty so experience-only callers are unaffected.
2. The projection is **immutable**. `AuthorityLedger` is a mutable dataclass over
   `dict`/`set`/`list`; embedding a live one would alias it across
   `dataclasses.replace`, so `pi_auth(before)` and `pi_auth(after)` would read
   the same mutated object. That failure was *reproduced* before the integration
   was written: with one shared ledger, a real mint under `RECORD_EPISODE`
   reported `PASS`. Every transition therefore rebuilds a working ledger from the
   snapshot, mutates it, and snapshots back.
   Guarded by `test_authority_projection_does_not_alias_across_transitions`.
3. Authority is **certificate-bound, not declaration-bound**.
   `AuthorityLedger.commit_verified` accepts a caller-supplied
   `VerificationOutcome`, which is a declaration; the runtime never exposes that
   path. `promote_scientific_authority` resolves a `ProtectedAttestation` whose
   `subject_hash` must equal a digest computed over the *actual* claim text,
   axis, scope and registered evidence content digests. Reusing an attestation
   for a different claim, or altering the proposition behind a stable claim id,
   invalidates it.
4. Three new `AttestationPurpose` values —
   `SCIENTIFIC_AUTHORITY_PROMOTION` / `_REVOCATION` / `_SUPERSESSION` — keep
   scientific authority separate from the `LESSON_*` / `TOOL_PROJECTION`
   *method*-authority purposes. A method-authority attestation is refused for a
   scientific grant; accepting it would be the cross-authority flattening this
   invariant exists to forbid.

### 2.1.1 Fingerprint contract versioning

Adding a coordinate changes `repr(state)`. Rather than silently changing
historical benchmark identity, the contract is versioned:

| Function | Covers | Note |
|---|---|---|
| `state_fingerprint` (v1) | experience, tools, failures, saturation, evolution | byte-identical to the pre-#242 bytes; `RAKLV3State()` still fingerprints `ca002a22…` |
| `state_fingerprint_v2` | all coordinates including scientific authority | benchmarks needing authority sensitivity must pin v2 explicitly |

`test_v1_fingerprint_is_unchanged_by_the_new_coordinate` pins the v1 literal
captured at the pre-integration parent commit `f5a6a11`.

### 2.1.2 Transition ownership (#242 §3)

`v3_scientific_authority.TRANSITION_OWNERSHIP` classifies every public v3
transition against `{EXPERIENCE_ROUTING, CANONICAL_SCIENTIFIC_CONTENT,
SCIENTIFIC_AUTHORITY}`. Exactly three transitions own the authority coordinate:
`promote_scientific_authority`, `revoke_scientific_authority`,
`supersede_scientific_authority`. Registration of claims and evidence owns
canonical content only — adding an observation is not evidence *for* anything.

`test_every_public_v3_transition_is_classified` introspects the live modules, so
an unclassified new transition fails the suite rather than passing on a stale
list.

### 2.2 The distinctions that must not collapse

`NonAuthorityCoordinate` keeps these separate and independently observable:
computational access, retrieval priority, proposal probability, strategy
preference, lesson reuse, scientific evidence. None is an `AuthorityAxis`.

**`LessonAuthority` is the trap.** It is the one authority-shaped coordinate that
lives *inside* `ExperienceLedger`, so experience transitions can legitimately
reach it. It is *method* authority — authority over how to search — not authority
over claims about nature. Modelling choice:

- It is **not** part of `pi_auth`. If it were, every legitimate `add_lesson`
  promotion would violate the invariant.
- It **is** tracked as `NonAuthorityCoordinate.LESSON_REUSE`, so the collapse
  channel stays visible.
- What is forbidden is **flow from it into `pi_auth`**.

`experience_memory.lesson_memory_view` already states this intent in prose
("Method authority remains inside the Lesson object and is not converted into a
scientific authority certificate"). This module makes it checkable.

### 2.3 Concrete collapse hazard found in-tree

`unified_substrate.materialize_unified_substrate` is a real composition point.
It flattens **three different authority ontologies** into one string metadata key
named `"authority"`: `LessonAuthority`, `ResearchTool.authority`, and
`KnowledgeFiber` projection authority. The overlay erases the type distinction
between them, while `AuthorityAxis` — the actual scientific-authority coordinate
set — appears nowhere in it. Any future integration reading `"authority"` off a
substrate node cannot tell which ontology it got. This is the most likely place
a real leak would be introduced.

## 3. Operation table

| Operation | May alter routing? | May alter canonical scientific content? | May alter scientific authority? | Required certificate |
|---|---|---|---|---|
| `record_task_episode` | yes (via derived ranking) | no | **no** | none |
| `consolidate_lesson` | yes | no | **no** | `ProtectedAttestation` for *method* authority only |
| failure record / `FailureDiagnosisStatus` raise | yes | no | **no** | `VERIFIED_IMPOSSIBILITY` gates reuse, not truth |
| tool projection | yes | no | **no** | attestation for tool authority |
| retrieval / workspace load / evict | yes | no | **no** | none |
| routing-policy update | yes | no | **no** | none |
| reflection | yes | proposal only | **no** | none |
| self-evolution win | yes | no | **no** | fresh assurance, separate signer |
| `register_scientific_claim` / `register_scientific_evidence` | no | yes | **no** | none — registering an observation is not evidence *for* anything |
| **`promote_scientific_authority`** | — | yes | **yes** | `SCIENTIFIC_AUTHORITY_PROMOTION` attestation subject-bound to claim text, axis, scope and evidence digests, satisfying §5 |
| **`revoke_scientific_authority`** | — | no | **yes** | `SCIENTIFIC_AUTHORITY_REVOCATION` attestation plus registered non-experience refuting evidence (§6.4) |
| **`supersede_scientific_authority`** | — | yes | **yes** | `SCIENTIFIC_AUTHORITY_SUPERSESSION` attestation binding both retired and replacement assertions; history preserved |

## 4. Report status semantics

| Status | Meaning |
|---|---|
| `PASS` | authority ledger composed, trace exercised, invariant held |
| `LEAK_DETECTED` | a family-attributed violation, with the offending grants |
| `NO_INTEGRATION_SURFACE` | the two state families are not composed, so no channel exists to exercise |
| `CANNOT_CHECK` | reserved for unresolvable inputs |

`NO_INTEGRATION_SURFACE` is deliberately **not** `PASS`. Before #242 that is what
the checker returned for `RAKLV3State`; reporting an accidental absence of a
channel as an enforced invariant would have manufactured the result. As of #242
the integrated runtime returns a real `PASS`/`LEAK_DETECTED`, and the status was
**not** repurposed — a caller supplying an uncomposed state still gets
`NO_INTEGRATION_SURFACE` (`test_uncomposed_state_still_reports_no_integration_surface`).

`describe_integration_surface()` derives composition structurally by *resolving*
the annotations and walking to a real `AuthorityLedger` / `AuthorityCertificate`
/ `AuthorityAxis` carrier. It previously did a substring match on the annotation
text, which could only return the answer an integrator named into it and would
have missed a carrier reached through a differently-named wrapper.

## 5. Promotion contract

A registered promotion that moves `pi_auth` must satisfy all of:

1. **not self-attested** — assurance not produced by the proposer;
2. **not experience-backed only** — `TASK_EPISODE` / `LESSON` /
   `ROUTING_STATISTIC` roots are experience, never evidence about nature;
3. **independent lineage** — claimed roots must not collapse to fewer terminal
   roots after following `upstream_root_id`;
4. **no axis escalation** — `MECHANISM` needs mechanism-supporting evidence, not
   representation-supporting evidence; `IDENTIFICATION` likewise over mechanism.

`supports_axes` is a frozen property of the registered evidence. The checker
consults no semantic oracle and reads no model chain-of-thought.

## 6. Threat families and planted worlds

Ten families, each with a planted world failing closed under its own distinct
reason, so a null is attributable rather than undifferentiated:
`EXPERIENCE_TO_EVIDENCE`, `REPETITION_TO_AUTHORITY`, `ROUTING_TO_AUTHORITY`,
`REFLECTION_TO_AUTHORITY`, `FAILURE_TO_IMPOSSIBILITY`,
`PROVENANCE_TO_INDEPENDENCE`, `PREDICTION_TO_MECHANISM`,
`MECHANISM_TO_IDENTIFICATION`, `WORKSPACE_TO_AUTHORITY`,
`SELF_EVOLUTION_TO_AUTHORITY`.

Attribution follows the **transition family that produced the change**, so a
caller can neither supply nor suppress its own diagnosis. Mislabelling a
promotion as retrieval fails harder, not softer.

Benign controls: experience/routing/workspace/reflection movement with `pi_auth`
invariant; a legitimate `LessonAuthority` promotion; a legal evidence-bearing
promotion; a refutation-driven revocation. The first benign control is paired
with an assertion that the **non-authority** projection actually moved —
otherwise a system that learns nothing would also pass.

### 6.1 Checker validation

Three mutations of the checker were run against the frozen suite; all were
caught. (i) never report a leak → 11 leak tests fail. (ii) downgrade
`NO_INTEGRATION_SURFACE` to `PASS` → the manufactured-pass test fails.
(iii) flag every transition as a leak → the benign controls fail, so the
no-alarm case is asserted too.

### 6.2 Two strata of evidence — not a flat 10/10 (#242)

The families are **not** uniform in strength. Reporting them as one number would
overstate the result.

**Contract-enforced.** Attacks on `promote_scientific_authority` /
`revoke_scientific_authority` — the only functions that can move `pi_auth`.
These go red if the runtime contract is removed, so they are genuinely
falsifiable: experience-backed evidence, derivative lineage, axis escalation,
self-attestation, purpose mismatch, absent manifest entry, subject mismatch,
unregistered evidence, unattested revocation.

**Structural + anti-vacuity.** The derived families — retrieval, routing,
workspace, reuse, reflection, self-evolution, tool projection — for which the v3
runtime holds no persistent coordinate (`R_t` is recomputed on demand). These
assert `pi_auth` invariance **and** that the non-authority projection actually
moved, so a runtime that learns nothing does not pass by doing nothing. They
remain weaker: they would also hold under unreachability. Recorded as such.

### 6.3 Integration mutation testing (#242 §6)

Six leaks were planted in the **integration path** (not the checker — §6.1
already covers that, and re-planting there would validate nothing new). Each was
caught, each by a distinct test set, and the tree restored clean (0 failures
after revert).

| Mutation | Site | Tests reddened |
|---|---|---|
| experience-evidence guard removed | `v3_scientific_authority.py` | 3 (lesson-confidence, routing-score, repeated-failure shortcuts) |
| independent-lineage guard removed | `v3_scientific_authority.py` | 1 (source count → independent evidence count) |
| axis-escalation guard removed | `v3_scientific_authority.py` | 1 (predictive success → mechanism authority) |
| attestation resolution skipped (declaration-bound regression) | `v3_scientific_authority.py` | 6 (subject mismatch, altered proposition, no attestation, self-attested, purpose mismatch, absent manifest entry) |
| `record_task_episode` mints authority | `v3_runtime.py` | 4 (aliasing guard, integrated verdict, episode and failure invariance) |
| `UNATTESTED_REVOCATION` check removed | `epistemic_noninterference.py` | 1 (revocation smuggled under a promotion label) |

### 6.4 A hole found while integrating: unattested revocation

`pi_auth` is non-monotone, so **withdrawing** authority moves it exactly as
minting does. Before #242, `_check_promotion` inspected only *added* grants and
`legal_promotions` incremented only under `if added and not step_findings`. A
revocation with a bare `reason` string, labelled `EVIDENCE_BEARING_PROMOTION`,
therefore produced **zero findings and reported `PASS`**. Verified against the
pre-fix code before the fix was written.

This made the §5 "refutation-driven revocation" control vacuous: it could not
fail. The old `test_registered_revocation_is_legal` passed while declaring no
refuting evidence at all.

Fixed by strengthening, not by relaxing: `Transition` gained
`claimed_refutation_root_ids`, an eleventh family `UNATTESTED_REVOCATION` was
added with its own planted worlds, and `revoke_scientific_authority` requires
registered non-experience refuting evidence plus a subject-bound attestation.
`legal_revocations` is reported separately from `legal_promotions`.

## 7. What this does not claim

- **No empirical superiority claim, and no model-capability claim.** #242
  establishes an executable architecture invariant only. Nothing here was
  executed against a model. Model-level authority-leakage rate remains #154;
  learning × governance remains #155.
- The enforced property is narrow: *registered* transitions cannot move
  `pi_auth` outside a subject-bound promotion, revocation or supersession. It
  says nothing about an integrator who bypasses the runtime and mutates a
  reconstructed ledger directly, nor about unregistered transition families.
- The derived-coordinate stratum (§6.2) is structural, not contract-enforced.
- The release-manifest fixtures are **internal assurance fixtures**. They pin
  exact attestations for the test scenario. Deployment roots still require a
  separately reviewed manifest update and external evaluator custody, and the
  HMAC fixture should be replaced by an externally governed public-key verifier.
- Not a guarantee about deployments, model behaviour, or unregistered families.
- Not a claim of novelty over AutoSci (`arXiv:2605.31468`) or MemTX
  (`arXiv:2607.23929`). The residual-claim audit those require is **not done**;
  until it is, no novelty claim is licensed. Recorded as missing evidence.
- No empirical superiority claim. Nothing here was executed against a model.

## 8. Paper II impact

Supports, once cited:

- that the reference architecture **specifies** typed scientific-authority
  coordinates distinct from method/routing authority;
- that the required distinctions are enumerated and executably non-collapsible;
- that the threat families are enumerated with per-family falsifiers.

Still requires narrowing — any sentence asserting RAKL **enforces**, **prevents**
or **guarantees** that experience cannot mint scientific authority *in general*.
After #242 the defensible scope is:

> The v3 runtime composes a scientific-authority coordinate whose only movement
> paths are subject-bound promotion, revocation and supersession; the registered
> experience, routing and reflection transitions are executably checked not to
> move it, and the checker is validated by planted leaks in the integration path.
> This is an architecture invariant over registered transitions, not a claim
> about model behaviour, empirical superiority, or authority leakage under
> generated outputs.

**No manuscript wording is changed in this lane.** #242's acceptance criteria
defer Paper II wording until the integrated result is frozen; the change belongs
in a follow-up governed PR that cites the receipt at
`research/receipts/RAKL_V3_NONINTERFERENCE_INTEGRATION_20260811.json`.

## 9. Preserved historical finding (pre-#242, superseded)

Recorded verbatim as negative history, following
`docs/RAKL_UPGRADE_PROTOCOL.md:91`. This described the framework **before** the
#242 integration and is **not** a description of current `main`. It is retained
because a negative result that gets overwritten stops being evidence.

> ### 2.1 What does not exist (recorded, not invented)
>
> 1. `RAKLV3State` composes **no** `AuthorityLedger` and **no** canonical-knowledge
>    store. Its fields are experience-side only.
> 2. `AuthorityAxis` / `AuthorityLedger` are referenced by their own module and
>    their own test, and by nothing else in `src/`.
> 3. There is therefore **no code path in the current revision that connects
>    experience to scientific authority** — and equally none that *enforces* the
>    separation. The separation is a consequence of the modules never having been
>    wired together.

> `NO_INTEGRATION_SURFACE` is deliberately **not** `PASS`. On the current revision
> that is what the checker returns for `RAKLV3State`. Reporting an accidental
> absence of a channel as an enforced invariant would manufacture the result.
> `describe_integration_surface()` derives this structurally from the live
> dataclass, so if a future revision wires the two families together the
> corresponding test fails — the intended signal to re-scope the invariant from
> prospective to enforced.

> - Not an enforced property of the current revision. `NO_INTEGRATION_SURFACE`.

> The reference architecture specifies epistemic noninterference for the
> registered transition families and provides an executable checker for it; the
> v3 experience runtime does not currently compose a scientific-authority ledger,
> so the invariant constrains integration code rather than shipped behaviour.

The predicted signal fired exactly as written:
`test_current_framework_revision_has_no_integration_surface` failed on
composition and was inverted to
`test_current_framework_revision_composes_an_integration_surface`.

Two further negative findings from the #242 integration are recorded in §6.4
(unattested revocation passed silently) and §2.1 item 2 (a shared mutable ledger
made a real leak report `PASS`). Both were reproduced against the pre-fix code
before being fixed.
