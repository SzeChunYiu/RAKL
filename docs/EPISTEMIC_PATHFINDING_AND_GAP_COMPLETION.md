# Epistemic Pathfinding, Gap Completion, and Post-Saturation Expansion

Status: research-only theory layer  
Date: 2026-08-09  
This document does not amend the Constitution and does not activate a new runtime policy.

## 1. The target is not the largest lattice

RAKL should not optimize for maximal accumulation of papers or semantic objects.

A scientific inquiry has a registered target

\[
\tau=(q,\alpha,\gamma),
\]

where `q` is the target question/QoI, `alpha` is the authority layer required to answer it, and `gamma` is the target context.

The useful object is the smallest evidence-governed support structure that can connect admissible evidence to `tau` without context drift, authority escalation, or unsupported transition composition.

A linear path is only a special case. Most scientific answers require multiple prerequisites to converge, so the natural object is a typed support **hypergraph**.

## 2. Support hyperpaths

Let

\[
G_t=(V_t,E_t,H_t)
\]

be the current scoped epistemic graph, with semantic/evidence objects `V_t`, pairwise typed transitions `E_t`, and multi-premise support relations `H_t`.

A target-support certificate is a subgraph

\[
P_\tau\subseteq G_t
\]

such that every step preserves its declared context, relation type, evidence lineage, uncertainty, and authority contract.

The path may contain, for example:

```text
source observation
+ calibration relation
+ mechanistic intermediate
+ boundary condition
+ independent experiment
-> identified mechanism
-> target QoI
```

The endpoint is not authorized merely because a graph path exists. Every transition must be licensed at the layer required by `tau`.

This generalizes the existing multi-hop bridge layer: `BRIDGE_TO` remains useful navigation, while an authority-bearing target support structure requires stronger path-level evidence.

## 3. Goal-conditioned search

RAKL should support bidirectional search:

```text
forward:
what target-relevant claims are reachable from current evidence?

backward:
what prerequisites would be required to justify the target authority?
```

The intersection defines a **path corridor**: the locally relevant region of the knowledge atlas for this question.

This is also a context-efficiency principle. A normal LLM need not materialize the full lattice. It can receive only:

```text
target contract
current path corridor
unresolved bottlenecks
candidate next actions
relevant negative history
necessary evidence/provenance pointers
```

The full atlas remains external and reconstructable.

## 4. A missing corner is an epistemic cut

Suppose no authority-valid support hyperpath reaches `tau`.

The failure can often be localized to a set of unresolved prerequisites that intersects every admissible target-support structure. Call this an **epistemic cut set**:

\[
B_\tau=\{b_1,\ldots,b_k\}.
\]

A minimal cut set is not merely a missing citation. Its members can include:

```text
missing context coordinate
missing identity resolution
missing transition map
missing mechanistic intermediate
missing calibration
missing parameter or regime boundary
missing mathematical lemma
missing measurement
missing experiment/intervention
missing ontology relation
missing formalism capable of representing the residual
```

The key research question becomes:

> What is the smallest scientifically admissible completion that would make a target-support route testable or reachable?

## 5. Gap completion is proposal generation, not truth

For a blocker `b`, a proposer may generate completion candidates

\[
\mathcal G(b,K_t)=\{g_1,g_2,\ldots\}.
\]

A candidate gap fill can be:

- retrieved from an unsearched source tradition;
- derived formally from existing premises;
- produced by ontology/identity reconciliation;
- transferred analogically from another domain;
- proposed as a new mechanism or formalism;
- instantiated as a new experiment or measurement request.

But a generated node or edge enters canonical knowledge only through the existing evidence gate.

Therefore:

```text
plausible missing piece != filled scientific gap
```

Unsupported completions remain `CONJECTURE_ONLY`, `CANNOT_CHECK`, `PARTIALLY_IDENTIFIED`, or `BLOCKED` as appropriate.

## 6. Gap filling can end in impossibility

A scientifically useful result is sometimes that the missing corner cannot be filled under the current observation regime.

Examples:

```text
no experiment in the allowed intervention class separates the mechanisms
no transition map can preserve the required invariant
available measurements identify only a set, not one theory
required context variable is fundamentally unobserved
```

In such cases RAKL should record an impossibility/non-identifiability object rather than invent a bridge.

Thus gap completion has two success modes:

1. construct and validate the missing support element; or
2. prove or strongly identify why the target is unreachable under the registered evidence/experiment class.

## 7. Active gap-closing actions

When probabilities are defensible, candidate actions can be ranked by target-relevant information gain and expected path closure per cost.

A path-aware utility can extend the existing action selector:

\[
u(a\mid K_t,\tau)=\frac{
\lambda_Q I(Q;Y_a\mid K_t)
+\lambda_M Sep(a,\mathcal V_t)
+\lambda_R \mathbb E[\Delta Reach_\tau]
+\lambda_B \mathbb E[\Delta Block_\tau]
}{Cost(a)}.
\]

`Reach_tau` measures target-support reachability and `Block_tau` measures elimination of explicit cut-set blockers.

When calibrated probabilities are unavailable, use set-valued alternatives such as:

```text
number of target blockers eliminated
worst-case survivor-set shrinkage
number of admissible paths opened
mechanism-separation guarantee
cost to falsify a proposed completion
```

Do not fabricate probabilities merely to run a graph-search formula.

## 8. Expansion after saturation

A scoped saturation certificate says that the registered search routes are semantically flat for the current fiber and evidence cutoff. It does not mean the atlas cannot grow in any sense.

RAKL distinguishes six post-saturation expansion modes.

### E1 — deductive expansion

Derive new consequences from existing evidenced premises using licensed logic/mathematics.

Authority is inherited only to the level licensed by the premises and derivation system.

### E2 — abductive gap completion

Infer candidate missing intermediates that would explain an obstruction or connect a target-support path.

These are proposals until separately validated.

### E3 — analogical / cross-domain expansion

Search adjacent or alien domains for reusable generators, mechanisms, representations, or discriminators.

The imported object remains a transfer hypothesis until target-domain validation.

### E4 — re-projection

Register a new QoI, observation process, scale, intervention, or representation and project the existing evidence into that new scoped question.

This opens a **new fiber**. It does not retroactively invalidate the old saturation certificate unless the new projection exposes a native residual relevant to the old scope.

### E5 — formal/mechanistic invention

After the R0-R9 conditions in the saturation protocol are met, open a disciplined R10 invention fiber.

A new formalism/mechanism must carry frozen competitors, falsifiers, limiting cases, and explicit predictions before confirmation.

### E6 — active evidence generation

Execute or request a new experiment, measurement, simulation with validated empirical status, observation, or source acquisition.

This produces genuinely new input and can reopen the original saturated fiber.

## 9. No-input expansion cannot manufacture empirical facts

Without new external evidence, RAKL can expand:

```text
derived consequences
candidate hypotheses
candidate mechanisms
candidate transition maps
candidate experiments
new abstractions/representations
new target questions
```

It cannot honestly create a new empirical observation merely because a proposer generated one.

This yields a hard boundary:

\[
\text{generative expansion}\not\Rightarrow\text{empirical authority}.
\]

A post-saturation invention may be scientifically valuable even while remaining unconfirmed.

## 10. Generative saturation

Post-saturation invention itself can become locally flat.

A scoped invention fiber may stop when materially different generative routes add no new non-equivalent, falsifiable, target-relevant proposal after deduplication and independent review.

This is not global closure. A new source, experiment, representation, target QoI, or benchmark residual can reopen the relevant fiber.

## 11. Efficiency consequence: search the corridor, not the universe

Goal-conditioned pathfinding gives RAKL a second compression mechanism beyond summary memory.

Instead of placing the whole atlas in context, compile the **minimal decision-relevant corridor** around:

```text
target QoI / authority
current surviving support paths
minimal blockers/cut sets
highest-value gap-closing actions
negative-history entries that constrain those paths
```

This can make a growing external lattice usable by ordinary-context LLMs.

## 12. Related-work boundary

RAKL does not claim invention of graph path reasoning, knowledge-graph completion, abduction, hypothesis chains, automated conjecture generation, or active experiment design.

Adjacent work includes:

- SciAgents (arXiv:2409.05556), which uses ontological knowledge graphs and multi-agent reasoning for scientific discovery;
- HypoChainer (arXiv:2507.17209), which forms and strengthens knowledge-graph-supported hypothesis chains;
- DARK (arXiv:2510.11462), which unifies deductive and abductive reasoning in knowledge graphs;
- LeanConjecturer (arXiv:2506.22005), which generates and filters formal mathematical conjectures.

The candidate RAKL contribution is narrower: target-conditioned support structures are embedded in an authority-scoped contextual atlas; missing path elements become explicit residual fibers; gap fills remain non-authoritative until evidenced; and post-saturation generation is separated from empirical authority.

## 13. Required empirical tests before activation

A future executable path/gap module should face frozen known-answer and hostile worlds including:

```text
direct valid path
multi-premise hyperpath
missing context coordinate
retrievable missing bridge
unsupported plausible bridge
mixed-authority escalation path
empty regime-intersection path
non-identifiable target
multiple alternative local paths
minimal two-blocker cut set
post-saturation logical derivation
post-saturation conjecture with no new evidence
active experiment that reopens saturation
new QoI that opens a new scope without rewriting old history
```

Primary metrics should include:

```text
false target-closure rate
support-path completeness
minimal-blocker localization
unsupported gap-fill authorization rate
context/authority leakage
cost to target closure
context tokens per validated target decision
negative-history preservation
```

Until that benchmark is run, this document is theory and architecture, not evidence of improved scientific utility.
