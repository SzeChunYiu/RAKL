# Multi-Hop Scientific Bridge Composition

Status: research-only support layer  
Date: 2026-08-09

## 1. Why pairwise analogy is not enough

A scientific JUMP may require a chain

\[
A \xrightarrow{W_1} B \xrightarrow{W_2} C \xrightarrow{W_3} \cdots \xrightarrow{W_n} Z.
\]

Each local witness can be valid while the end-to-end inference is invalid. The intermediate object may change identity, a role may be reinterpreted, the preserved invariant may change, the valid regimes may have empty intersection, the question/QoI may drift, or approximation/error semantics may fail to compose.

RAKL therefore distinguishes:

```text
locally witnessed path
        ↓
NAVIGABLE_ONLY
```

from

```text
locally witnessed path
+ shared-node handoff compatibility
+ invariant continuity
+ common QoI
+ global regime intersection
+ explicit evidence lineage
+ certified error-composition semantics
        ↓
COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
```

Neither state mints an endpoint equivalence relation or target-domain authority.

## 2. Path object

For a path with `n` local witnesses, define

\[
P=(W_1,H_1,W_2,H_2,\ldots,H_{n-1},W_n; I,\Gamma,E,\Lambda),
\]

where:

- `W_i` is an independently validated typed similarity witness;
- `H_i` is a typed handoff at the shared intermediate object;
- `I` is the set of explicitly claimed end-to-end invariants;
- `Gamma` is the intersection of the validity regimes of all hops;
- `E` is a declared path-level error contract;
- `Lambda` is evidence-lineage metadata.

`BRIDGE_TO` remains a navigation relation. It means a candidate route exists, not that the endpoint relation has been established.

## 3. Handoff compatibility

For adjacent hops

\[
A\xrightarrow{W_1}B\xrightarrow{W_2}C,
\]

RAKL requires:

1. `target_id(W1) == source_id(W2)`;
2. the handoff identifies the same intermediate object `B`;
3. roles delivered into `B` by `W1` are the roles consumed from `B` by `W2`;
4. the role-compatibility check is explicit and evidenced.

Surface naming is insufficient. `B_1` and `B_2` are not the same junction merely because both are called “feedback,” “state,” or “generator.”

## 4. Invariant continuity

An end-to-end invariant `i` is composable only if every hop explicitly lists `i` in `PRESERVED`.

If any hop lists `i` in `NOT_PRESERVED`, the claimed composition is rejected. If a hop is silent about `i`, composition is `CANNOT_CHECK` rather than guessed.

This prevents a common bridge failure:

```text
A → B preserves feedback structure
B → C preserves threshold structure
therefore A → C preserves feedback
```

The two local analogies can remain useful navigation even though no end-to-end invariant exists.

## 5. QoI and regime continuity

Round 019 uses the conservative v1 rule:

```text
question/QoI is fixed across all hops
```

A future QoI-transition calculus would require its own frozen benchmark and authority rules.

Likewise, local pairwise validity is not enough. End-to-end transfer requires

\[
\Gamma_P = \bigcap_i \Gamma_i \ne \varnothing.
\]

If all hops are locally valid but `Gamma_P` is empty, the path remains `NAVIGABLE_ONLY`.

## 6. Error composition must itself be witnessed

The first Round-019 support implementation treated per-hop numeric approximation bounds as generically additive. The applied-mathematics and adversarial passes rejected that assumption after fresh primary-source review.

The corrective rule is:

> **Numbers called “error” do not compose merely because every hop has one.**

A path may accumulate a numerical error bound only when:

1. every hop names the same error semantics;
2. the composition rule is identified;
3. the composition rule was certified before endpoint outcomes were inspected;
4. the rule is valid for that error semantics;
5. the resulting certified bound remains within the frozen path tolerance.

The current support layer implements only a predeclared `ADDITIVE_UPPER_BOUND` certificate. It deliberately does not assume that arbitrary distances or divergences satisfy a triangle inequality.

This preserves a useful separation:

```text
pairwise approximation values
    !=
certified end-to-end approximation bound
```

## 7. Evidence ancestry

A path can compose structurally even when multiple hops inherit evidence from the same source lineage. But shared ancestry is flagged and must not be counted as independent corroboration.

Therefore:

\[
\text{path length} \ne \text{independent evidence count}.
\]

This connects multi-hop reasoning to RAKL's evidence-lineage and blind-review honesty rules.

## 8. No endpoint-relation minting

Consider

\[
A\overset{\text{OBSERVATIONALLY_EQUIVALENT}}{\longrightarrow}B
\quad\text{and}\quad
B\overset{\text{MATHEMATICALLY_ISOMORPHIC}}{\longrightarrow}C.
\]

RAKL does not infer `SAME_MECHANISM(A,C)`, `OBSERVATIONALLY_EQUIVALENT(A,C)`, or any other typed relation unless a separately registered composition rule for those exact relation classes is proved and benchmarked.

Thus the default composition algebra is deliberately non-transitive:

\[
R_1(A,B) \land R_2(B,C) \not\Rightarrow R_3(A,C).
\]

A valid path creates, at most, a scoped target-transfer hypothesis.

## 9. Target validation

If a composable bridge suggests a target hypothesis, target testing is still a separate gate:

```text
COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY
        ↓ target experiment
TARGET_REFUTED_PATH_WITNESSES_PRESERVED
or
TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED
```

A failed target transfer does not rewrite valid local structural witnesses. It becomes negative atlas history explaining where transfer stopped working.

## 10. Search consequences

Multi-hop search is not optimized only for path depth. Candidate paths should eventually be maintained on a Pareto frontier over at least:

```text
structural continuity
path depth
domain distance
mechanistic diversity
grounding stability
error/transfer risk
evidence independence
validation readiness
cost
```

Deep or diverse paths can be useful for discovery, but depth itself is not evidence. The smallest adequately witnessed path should remain a strong baseline.

## 11. Relationship to GLUE ↔ LIFT ↔ JUMP ↔ PROJECT

A bridge can cross operator boundaries:

```text
APPLE residual
  ↓ LIFT
candidate generator G1
  ↓ JUMP
sibling system B
  ↓ LIFT/JUMP
higher generator G2
  ↓ PROJECT
candidate apple hypothesis
```

Every edge remains locally typed. The entire chain becomes transfer-composable only when the path certificate survives handoff, invariant, QoI, regime, lineage and error-composition checks.

This lets RAKL search adventurous chains while keeping transfer conservative.

## 12. Current authority boundary

`src/rakl/bridge_composition.py` is support-only. It can classify bridge evidence but cannot:

- activate a retrieval/search policy;
- automatically create an endpoint similarity relation;
- promote canonical scientific knowledge;
- establish mechanism identity;
- grant target authority.

Real scientific utility remains unmeasured until a frozen comparative multi-hop benchmark is executed.
