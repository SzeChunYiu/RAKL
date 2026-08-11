# EPISTEMIC_NONINTERFERENCE

Formal, executable specification of Paper II's authority-noninterference claim.
Proposal-only: wired into no promotion gate, mints no authority.

Implementation: `src/rakl/epistemic_noninterference.py`.
Planted worlds: `tests/test_epistemic_noninterference.py`.
Refs #152. The issue requests this note at `research/PAPER2_EPISTEMIC_NONINTERFERENCE.md`;
it lives here instead, so the issue's acceptance checklist should be read against this path.

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
| `G_t` scientific authority | `authority_ledger.AuthorityLedger` over `AuthorityAxis` = G/R/M/I/D | **exists as a module, not composed into `RAKLV3State`** |
| `K_t` canonical scientific state | `claim_evidence.ClaimAtom` / `EvidenceSourceSnapshot` / `ClaimEvidenceLink` provide claim and evidence identity, but no persistent canonical store is composed into `RAKLV3State` | **partial** |

### 2.1 What does not exist (recorded, not invented)

1. `RAKLV3State` composes **no** `AuthorityLedger` and **no** canonical-knowledge
   store. Its fields are experience-side only.
2. `AuthorityAxis` / `AuthorityLedger` are referenced by their own module and
   their own test, and by nothing else in `src/`.
3. There is therefore **no code path in the current revision that connects
   experience to scientific authority** — and equally none that *enforces* the
   separation. The separation is a consequence of the modules never having been
   wired together.

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
| **evidence-bearing promotion** | — | yes | **yes** | registered promotion satisfying §5 |

## 4. Report status semantics

| Status | Meaning |
|---|---|
| `PASS` | authority ledger composed, trace exercised, invariant held |
| `LEAK_DETECTED` | a family-attributed violation, with the offending grants |
| `NO_INTEGRATION_SURFACE` | the two state families are not composed, so no channel exists to exercise |
| `CANNOT_CHECK` | reserved for unresolvable inputs |

`NO_INTEGRATION_SURFACE` is deliberately **not** `PASS`. On the current revision
that is what the checker returns for `RAKLV3State`. Reporting an accidental
absence of a channel as an enforced invariant would manufacture the result.
`describe_integration_surface()` derives this structurally from the live
dataclass, so if a future revision wires the two families together the
corresponding test fails — the intended signal to re-scope the invariant from
prospective to enforced.

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

## 7. What this does not claim

- Not an enforced property of the current revision. `NO_INTEGRATION_SURFACE`.
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

Requires narrowing — any sentence asserting RAKL **enforces**, **prevents** or
**guarantees** that experience cannot mint scientific authority. On this revision
the correct scope is:

> The reference architecture specifies epistemic noninterference for the
> registered transition families and provides an executable checker for it; the
> v3 experience runtime does not currently compose a scientific-authority ledger,
> so the invariant constrains integration code rather than shipped behaviour.

The manuscript change is deliberately not made in this lane; it belongs in a
follow-up governed PR.
