# Paper Draft Module — Bounded Epistemic Context for an Expanding Knowledge Atlas

Status: manuscript module, provisional. Software support exists; real-agent comparative context-efficiency experiments remain open.

## Scaling scientific memory without scaling the prompt

RAKL deliberately retains more state than a conventional agent transcript: contextual source projections, typed equivalence relations, evidence lineage, contradictions, null and refuted hypotheses, supersession history, open fibers and method-evaluation receipts. Naively concatenating this state into every model call would make the method progressively more expensive and could reduce reasoning quality through irrelevant-context interference.

We therefore separate the **persistent epistemic state** from the **LLM working context**. The former is append-only and reconstructable. The latter is an operation-specific materialized view compiled under an explicit token budget.

For operation `a`, fiber `f` and question/QoI `q`, RAKL compiles a context set

\[
C^* = \arg\max_{C \subseteq V} U(C\mid a,f,q)
\quad \text{subject to}\quad
\mathrm{tokens}(C)\le B,\; M(a,f,q)\subseteq C,
\]

where `V` denotes retrievable memory views, `B` is the registered working-context budget and `M` is a mandatory epistemic set. Mandatory material can include relevant falsifiers, negative history, both sides of an adjudicated contradiction, assumptions, mechanism ancestry, evidence-lineage coordinates or evaluator identities. If the mandatory set exceeds the budget, the system must fail closed rather than silently remove the evidence that makes a conclusion difficult.

The current deterministic support implementation does not claim to solve the global optimization problem. It uses marginal weighted coverage per token after mandatory material is placed. A record has no value merely because it is another citation; it must contribute a new registered facet, hypothesis, evidence branch, contradiction side, authority prerequisite or other coverage atom. This connects semantic deduplication directly to context cost.

## Multi-resolution reconstructable views

External memory is organized conceptually into four tiers: an immutable canonical archive, regenerable indexes and hierarchical summaries, a compiled epistemic working set and the transient model prompt. Compact summaries remain projections. They carry identifiers of their source records, and lossy summaries declare erased dimensions so that the original evidence can be rehydrated when an operation needs more detail or authority.

This differs from treating summarization as forgetting. Physical storage compression and semantic prompt compression are also separated. Raw evidence may be content-addressed and compressed without changing semantic identity, while textual prompt compression is allowed only after task-relevant material has been selected.

## Relationship to prior work

The architecture is informed by established and current memory/context systems rather than claimed as a new memory hierarchy. MemGPT introduced virtual context management using multiple memory tiers. RAPTOR retrieves across recursive abstraction levels. RECOMP selectively compresses retrieved evidence, while LLMLingua and LongLLMLingua demonstrate that prompt-level compression can substantially reduce input cost. Recent ContextBudget work treats context management as a budget-constrained decision problem, and hierarchical memory-navigation work such as HORMA learns to retrieve minimal sufficient context while preserving links to raw trajectories.

The candidate RAKL contribution is narrower: **scientific context compilation is constrained by epistemic obligations**. Negative evidence, authority prerequisites and unresolved contradictions can be mandatory even when a relevance model would otherwise discard them. Lossy views remain reconstructable and do not mint additional authority.

## Falsifiable evaluation

The preregistered comparison is:

```text
full-history context
recency truncation
similarity top-k
summary-only
RAKL bounded epistemic context
```

under matched model, task packet and token budget. Primary outcomes are required-evidence recall, negative-history retention, cross-axis authority leakage, downstream decision/task quality, input tokens, latency and cost. If a simpler baseline matches the RAKL compiler on epistemic integrity at equal or lower cost, the richer selection machinery does not earn mandatory status.

The initial software benchmark consists only of known-answer and hostile context-packing worlds and therefore supports a component-contract claim, not a real-agent superiority claim.
