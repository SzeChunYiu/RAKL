# Paper Addendum — Goal-Conditioned Epistemic Pathfinding and Gap Completion

Status: manuscript-development note  
Date: 2026-08-09  
This file does not change RAKL runtime behavior.

## Candidate paper framing

Scientific literature should not be represented merely as a collection of documents to summarize. After projection, normalization, and provenance extraction, it forms a contextual evidence atlas containing many possible support routes toward a registered scientific target.

For a target

\[
\tau=(q,\alpha,\gamma),
\]

RAKL asks not only:

> What does the literature say?

but:

> What is the smallest authority-valid support structure connecting current evidence to the target, and what unresolved prerequisite blocks that structure if no such route exists?

This reframes research from global information accumulation toward **goal-conditioned epistemic navigation**.

## Why a hyperpath rather than a simple path

A single chain is insufficient for many scientific conclusions. A mechanism may require several premises simultaneously: an observed phenomenon, an interaction law, a boundary condition, and an intervention result. RAKL therefore treats the target support object as a typed hypergraph/subgraph rather than assuming one linear reasoning chain.

A route is valid only when context, relation type, authority scope, uncertainty, and evidence lineage remain licensed throughout the support structure.

## Missing lattice regions as scientific objects

When all authority-valid support structures toward the target are blocked, RAKL records the blocking set itself.

A minimal blocker can be a missing measurement, context coordinate, mechanistic intermediate, transition theorem, calibration, identity resolution, or experiment. We call the smallest unresolved set intersecting all admissible target-support structures an **epistemic cut set**.

The method then converts the cut set into new atomic research fibers. Candidate completions can be retrieved, derived, analogically proposed, experimentally measured, or formally invented. Importantly, proposal generation does not fill the gap epistemically; verification still governs admission into canonical knowledge.

## Post-saturation discovery

Scoped literature saturation does not imply that scientific reasoning must stop. RAKL separates:

1. deductive expansion from existing evidence;
2. abductive proposal of missing intermediates;
3. cross-domain analogical transfer;
4. re-projection under new questions or observation coordinates;
5. disciplined formal/mechanistic invention;
6. active generation of genuinely new evidence through experiments or observations.

The first five can expand the proposal or derived lattice without new external data. They cannot manufacture new empirical authority. The sixth can produce new evidence and reopen a previously saturated fiber.

## Efficiency implication

Goal-conditioned pathfinding also provides a systems-level compression principle. Instead of sending an ever-growing knowledge lattice to the LLM, RAKL can compile a target-specific **path corridor** containing only the target contract, currently viable support routes, minimal blockers, relevant negative history, and evidence pointers required to evaluate the next action.

This suggests a publishable efficiency hypothesis:

> A path-corridor compiler can preserve target-level epistemic validity while reducing context length relative to broad-context lattice materialization.

The hypothesis must be tested against a baseline that receives the same evidence universe and tool access.

## Related-work boundary

The paper should explicitly credit adjacent graph-reasoning and hypothesis-generation systems. SciAgents (arXiv:2409.05556) explores scientific knowledge graphs for cross-domain discovery. HypoChainer (arXiv:2507.17209) constructs and strengthens knowledge-graph-supported hypothesis chains. DARK (arXiv:2510.11462) unifies deductive and abductive reasoning on knowledge graphs. LeanConjecturer (arXiv:2506.22005) demonstrates large-scale formal conjecture generation.

RAKL should therefore not claim novelty for graph paths, knowledge-graph completion, abduction, or conjecture generation individually.

The candidate contribution is their placement inside a contextual and authority-scoped scientific update protocol in which:

```text
connectivity != support
plausible completion != evidence
new conjecture != empirical knowledge
saturation != universal closure
```

## Required figure

A useful manuscript figure should show three panels:

```text
A. Reachable target
Evidence charts -> typed support hyperpath -> target QoI

B. Missing corner
Evidence charts -> [epistemic cut set] -> target blocked
                         |
                         +-> search / derive / experiment / invent

C. Post-saturation expansion
SATURATED_SCOPED
  -> deduction
  -> abduction
  -> analogy
  -> re-projection
  -> R10 invention
  -> experiment -> NEW EVIDENCE -> REOPENED_BY_RESIDUAL
```

The visual should distinguish proposal nodes from evidence-authorized nodes.

## Headline empirical discriminator

Freeze tasks where the true support graph and missing prerequisites are known. Compare:

```text
broad-context LLM synthesis
naive shortest graph path
target-conditioned RAKL support hyperpath + cut-set routing
```

Under matched model, evidence, tool, and token budgets measure:

```text
false target closure
support completeness
gap localization accuracy
unsupported completion rate
context/authority leakage
tokens to valid closure
```

The strongest paper result would be simultaneous improvement in epistemic validity and context efficiency, rather than pathfinding accuracy alone.
