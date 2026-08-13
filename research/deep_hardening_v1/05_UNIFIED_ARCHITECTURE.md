# Unified architecture: RAKL + TCSQ + StructuralWitness + VTG + training

## The ideas occupy different planes

```text
A. EPISTEMIC / AUTHORITY
   evidence, claims, context, provenance, support/attack,
   identified sets, negative history, authority certificates

B. EXACT SOLVER SUBSTRATE
   typed states, legal transformations, proof DAG/hypergraph,
   path equivalence/congruence, exact verifier/replay receipts

C. DERIVED SOLVER PROJECTIONS
   TCSQ, abstraction/refinement, representation atlas/portals,
   directed cost geometry, learned solvability geometry, pi_solve

D. SEARCH / CONTROL
   applicability gate, best-first/branching/MCTS/flow policies,
   trajectories, coverage, staleness, compute allocation

E. LEARNING / MODEL EVOLUTION
   exact structural identity bundle, pi_train(theta), mastery probes,
   bounded training update, fresh assurance, model promotion
```

No arrow from C, D or E directly enters A. They can generate **proposals/evidence-acquisition actions**; only the registered epistemic verification/promotion path moves scientific authority.

## Unified solving loop

```text
human problem
  -> formalization candidate
  -> specification-fidelity gate
  -> freeze OperationalSubject
  -> canonical problem state / Problem Fibre
  -> optional validated TCSQ
  -> exact/sound operational map
  -> choose chart / verified portal
  -> construct or load scoped geometry
  -> applicability + local navigation
  -> search trajectory
  -> assemble solution constellation / proof DAG
  -> replay/verify in original semantics
  -> authority gate
  -> residual / failure episode
  -> typed mechanic diagnosis
  -> discriminator
  -> repair only implicated layer
```

## TCSQ vs StructuralWitness vs VTG

### TCSQ

Question: **which distinctions can be erased for this registered QoI/context while preserving the target decision/verification obligations?**

It is a derived view of a canonical source. It may be exact or approximate. Approximate use must carry a composable error budget.

### StructuralWitness

Question: **what structure can be transported from source to target in this direction, under which boundaries, and what is known not to be preserved?**

It is not an equivalence certificate and is allowed to be one-way/non-transitive.

### VTG

Question: **given an exact operational subject and a target region, does a routing geometry help find verifier-valid routes locally and cheaply?**

VTG does not define transformation legality or truth. It consumes exact/replay-assured topology and produces routing-only artifacts. Exact/admissible/consistent heuristic certification remains owned by the existing `fieldability.GeometryArtifactIdentity` / `CertificationWitness`; the VTG sidecar binds that identity rather than creating a second certification ontology.

## Allocentric vs egocentric geometry

Keep two distinct objects:

```text
world/operator geometry: d_Omega,R(x,y)
    intrinsic directed transformation cost / relation

problem-conditioned solvability field: V_P(x)
    routing estimate toward target region under the frozen subject/policy/support
```

The first can have exact algebraic laws. The second may be learned, approximate, stale or wrong.

## Search trajectory vs solution constellation

```text
trajectory: s0 -> s1 -> ... -> sn
certificate: DAG/hypergraph of premises and verified dependencies
```

A trajectory may contain failures/backtracking that have no place in the final proof. A proof may require branches not represented by one linear trajectory.

## Exact shared structural substrate across learning stages

The strong candidate is not merely “use structure”. It is:

```text
same content-bound StructuralIdentityBundle
   -> external retrieval/reasoning
   -> training item/mastery projection at theta_t
   -> training objective/receipt
   -> inference-time retrieval/transport on fresh tasks
```

Every stage binding records the exact same bundle hash. A renamed/recomputed “equivalent” object is not counted as exact identity reuse without a separately proven identity/equivalence contract.

## Cognitive compilation

```text
external RAKL residual
  -> typed diagnosis + frozen discriminator
  -> structural training proposal
  -> bounded challenger weight update
  -> training receipt with pi_epi invariant
  -> disjoint fresh assurance by separate evaluator
  -> model promotion eligibility
  -> explicit governance decision
```

Model promotion is not scientific-claim promotion.


## One integration epoch, without one mega-ontology

The packet adds `UnifiedMechanicsManifest` as a **composition receipt**, not a new canonical state. It binds:

```text
base commit
+ V3 state commitment
+ structural identity bundle
+ optional operational subject / geometry
+ resolved quotient-validation receipt
+ resolved witness-use receipt
+ training assurance
+ exact shared-identity reuse receipt
+ cognitive-compilation fresh assurance
+ exact-base guard receipt
```

`READY_FOR_INTEGRATION_TEST` means only that these surfaces are identity-consistent and the requested external receipts resolve. It grants no proof/scientific/model-promotion authority. This closes the atomic gap between “each module is locally fail-closed” and “the assembled experiment is coherently bound.”

## TCSQ trust edge

Keep three levels distinct:

```text
QuotientProposal              proposal only
QuotientValidationReport      validation data object
ResolvedQuotientValidationReceipt  externally resolved verifier/replay binding
```

New production solver integrations should materialize through the resolved-receipt sidecar. This preserves the existing TCSQ hash/data model while preventing a self-declared passing report from becoming the trust root.
