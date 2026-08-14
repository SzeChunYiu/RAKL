# Framework refinement — Pursuit/Justification projections and bounded closure

## Keep one master mathematical spine

Use the existing completion model:

```text
S_t = (P_t, J_t)
P_t = (O_t, R_t, H_t, A_t)            # Pursuit
J_t = (C_t, E_t, N_t, Auth_t)         # Justification
```

Pursuit can search, construct representations, propose hypotheses and choose probes. It is not sovereign over canonical scientific authority.

Do not create a second master architecture just for Papers IV–VI. Add typed application/control projections over the same state.

## Required projections

Conceptually:

```text
pi_epi(S)       scientific authority / claim justification
pi_search(S)    inspection, retrieval, routing priority
pi_method(S)    method/experience evolution state
pi_train(S,θ)   training allocation for one learner/checkpoint
pi_math(S)      mathematical specification/proof/novelty/value/trust state
pi_engine(S)    integrated system-control / external-frontier state
```

These projections may share identities and evidence pointers; they must not share write authority by accident.

## Cross-projection write matrix

| Source transition | May change | Must not change without separate certified transition |
|---|---|---|
| search/routing | route priority, candidate set, interaction space | scientific authority, theorem truth, novelty, method-install authority |
| training projection | mastery estimates, allocation proposal, candidate utility | scientific authority, structural-transfer authority, method-install authority |
| structural transfer proposal | candidate mapping/witness obligations | source truth, target theorem truth, scientific authority until obligation gate |
| mathematical search/VTG | proof-state map, route/geometry, candidate proof | theorem truth, novelty, research value, verifier-trust coordinate |
| theorem proof receipt | theorem-truth coordinate for the exact bound formal statement | informal-spec alignment, novelty, value |
| novelty search | novelty dossier / CANNOT_CHECK | theorem truth |
| method-evolution challenger | method candidate / development status | production installation before fresh assurance/governance |
| capstone benchmark | integration-level measured frontier | component scientific promotion; historical paper authority |

## Noninterference rules to make executable

1. `training utility != scientific authority`.
2. `route score != evidence != authority`.
3. `valid source transformation != valid target transfer != theorem truth`.
4. `theorem truth != novelty != research value`.
5. `method learned/stored != method production-authorized`.
6. `system-level win != component-level causal credit`.
7. `publication closure != global framework completeness`.

For each transition type expose explicit `grants_*_authority` properties where applicable and unit-test them against false positives.

## Registry-bound bounded closure

The historical closure ledger correctly defines bounded method-saturation, but reader-facing text must bind any closure count to an exact roster.

New branch implementation:

```text
src/rakl/bounded_closure.py
tests/test_bounded_closure.py
```

A certificate contains:

```text
subject_sha
cutoff
registry_hash
mechanic_ids
closed_mechanic_ids
verdict
GLOBAL_COMPLETENESS_CLAIMED = false
grants_scientific_authority = false
```

### Reopen rule

Adding, removing, or changing a mechanic-closure record changes `registry_hash`.

Therefore:

```text
old certificate remains historically valid for old roster
AND
old certificate is invalid for the new roster
```

No rewriting is required.

### Negative results

A mechanic can be closure-complete with a decisive negative terminal:

```text
implementation exists
+ tests exist
+ evidence terminal exists (positive OR negative)
+ paper owner exists
+ open extension/falsifier registered
```

Closure means the registered question is accounted for, not that the mechanic is beneficial.

## M1–M16 status

The framework-completion handoff's M1–M16 are **research candidates**, not automatically part of a new “closed framework.” Each candidate must pass the existing `MECHANIC_RESEARCH_PACKET` gate, strongest-parent differential and fresh assurance before promotion.

Any reader-facing closure certificate should state something like:

> At subject `<SHA>` and mechanic-registry hash `<HASH>`, all mechanics in that exact registered roster satisfied the local closure contract. This is bounded closure, not a claim that no additional RAKL mechanic exists; later candidate registration reopens the current roster.

## Common mechanic lifecycle

Normalize all Papers IV–VI mechanics to one status machine:

```text
CANDIDATE
-> RESEARCH_PACKET_FROZEN
-> DEVELOPMENT
-> DEVELOPMENT_REJECTED | DEVELOPMENT_PROMISING
-> FRESH_ASSURANCE
-> PROMOTE_CONDITIONALLY | PROMOTE_TO_MECHANIC | REJECT
-> production/governance install where relevant
```

Separate dimensions that must never be collapsed:

```text
implementation state
scientific evidence state
production-policy state
publication-claim state
```

## Common claim-to-receipt contract

For every headline sentence maintain a machine-readable record:

```text
claim_id
paper_id
exact allowed wording
forbidden stronger wording
scope/context/QoI
estimand
evidence artifact(s)
inference artifact
safety/hard-gate artifact
cost artifact
objectivity/independence status
subject SHA
artifact hashes
freshness/cutoff
open successor
```

A manuscript build should fail when a quantitative/status sentence no longer matches the bound receipt.

## Framework completion criterion

Do not define completion as “many modules exist.” Define one bounded release as ready when:

1. active mechanic registry is explicit and hash-bound;
2. every active mechanic has implementation/test/evidence/paper/open-question coordinates;
3. every scientific-positive mechanic has strongest-parent residual or is explicitly inherited/prior-art infrastructure;
4. every negative mechanic has safe fallback/retirement semantics;
5. projection write boundaries are tested;
6. all publication claims bind receipts;
7. current PDFs build from the exact release subject;
8. independent/open-human coordinates remain honest.

New literature, external systems, reviewer objections or a newly registered mechanic can reopen the framework after that release.