# Design Constitution

These rules are load-bearing. New mechanics may optimize routing and problem solving; they may not silently weaken Orion's epistemic boundaries.

## C1 — Evidence governs

```text
LLM proposal
search rank
field potential
mechanic score
representation score
conductance
analogy strength
memory frequency
```

are **routing signals**, not evidence and not authority.

Only the existing evidence-bearing paths may change scientific authority.

## C2 — Root QoI preservation

Every local action must preserve a reconstructable link to the root goal.

Required identifier chain:

```text
root_problem_id
root_qoi_id
problem_atom_id
fibre_snapshot_hash
representation_id
scale_id
mechanic_action_id
candidate_subject_hash
verification_receipt
```

A local gain without root traceability is not root progress.

## C3 — Negative history is append-only

Failed representations, routes, field branches, operators and verifier choices are retained.

They may be down-weighted or scoped. They may not be erased merely because a later run succeeds.

## C4 — No field-to-authority shortcut

`SolutionPotentialField`, `Conductance`, `ArrivalTime`, `ValueEstimate`, or any learned equivalent has:

```text
authority_effect = PROPOSAL_ONLY
```

A path proposed by a perfect field still requires ordinary execution and verification.

## C5 — Representation is scoped

A representation transform must declare:

```text
source representation
target representation
preserved coordinates
non-preserved coordinates
assumptions
inverse/reconstruction status
verification route
```

No hidden loss may be treated as equivalence.

## C6 — Scale transitions are contracts

Refinement/coarsening must be explicit.

For transition \(T_{s\rightarrow s'}\), record:

\[
W_T=(P^+,P^-,A,E)
\]

where:

- \(P^+\): guaranteed preserved quantities;
- \(P^-\): known lost/approximated quantities;
- \(A\): assumptions;
- \(E\): validation evidence.

## C7 — Local flatness is never global coverage

The implementation must preserve a non-zero exploration/coverage lane unless an explicit complete-space theorem makes it unnecessary.

A local residual of zero must not by itself certify global absence of hidden fine-scale structure.

## C8 — Same-context scoring is not independent validation

A learned field evaluated on its training graph or a mechanic router evaluated on development tasks has no fresh-transfer status.

## C9 — Baselines are first-class

Every challenger benchmark must include the simplest credible baselines.

For field search, at minimum:

```text
BFS / uniform-cost where appropriate
A* with available admissible heuristic where appropriate
current Orion controller
random or uniform mechanic routing
oracle routing (upper bound)
```

If a simpler method matches the challenger, record:

```text
COMPLEXITY_NOT_EARNED
```

## C10 — Matched resource accounting

Track:

```text
model calls
tool calls
verifier calls
retrieval calls
tokens
CPU/GPU time
wall time
graph expansions
memory reads
representation transforms
field solves
```

Do not claim solver improvement from hidden extra compute.

## C11 — No private-chain dependency

All controller decisions must be reproducible from bounded recorded state, not private chain-of-thought.

Store:

```text
input state features
candidate actions
scores / intervals / reasons
chosen action
observable result
cost
verification result
```

## C12 — Backward compatibility before promotion

New modules should be importable without changing existing behavior.

Integration into `v3_runtime.py` or the default search loop is a later gate.

## C13 — No metaphor privilege

Lightning, slime mould, ant colonies, optics, multigrid, renormalization, proof search, convex lifting and other inspirations are all **mechanism donors**.

No source family gets privileged truth status because the analogy is attractive.

## C14 — Atomic attribution

End-to-end gains must be decomposed enough to answer:

```text
Was improvement caused by:
- better diagnosis?
- more compute?
- representation?
- scale?
- field routing?
- retrieval?
- auxiliary object invention?
- verifier scheduling?
```

If not identifiable, the claim remains system-level only.

## C15 — Rejection is useful output

A challenger that fails fresh tests should create:

```text
failure record
scope of failure
negative-history entry
possible repair hypotheses
```

and remain available as a parent data point.
