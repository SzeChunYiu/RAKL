# AI Capability Shaping and Research Cognitive Architecture

Status: candidate method layer, research-only  
Date: 2026-08-09

## 1. Principle

RAKL should not assume a uniformly capable AI and then ask it to "reason better" everywhere.

Instead, each atomic cognitive operation should be placed inside an environment that:

1. exposes the model to the representation and tools that make its useful capabilities easiest to express;
2. constrains or externalizes predictable failure modes;
3. routes operations the model performs poorly to a better-suited mechanism when available;
4. preserves provenance so system-level success is not misreported as intrinsic model improvement; and
5. measures the intervention against a simpler matched baseline before it can become default behavior.

The working design principle is:

> **Amplify what the model does well; externalize what it does unreliably; substitute what can be checked more reliably elsewhere; preserve what it tends to forget; and measure every scaffold against a simpler matched baseline.**

This is a method-layer proposal. It does not change the Constitution.

## 2. Model capability is not system capability

For a task family `T`, base model `M`, research architecture `A`, and declared external resources `E`, define observed system behavior abstractly as

\[
Y(T)=F(M,A,E;T).
\]

RAKL therefore distinguishes:

- **model capability** — behavior attributable to `M` under a declared minimal interface;
- **model-utilization amplification** — `A` causes the same model to express a capability more reliably without adding the capability from an external oracle;
- **failure suppression** — `A` reduces a known model failure mode;
- **external capability substitution** — a solver, database, checker, deterministic program, or other resource performs an operation the model cannot reliably perform itself;
- **specialist complementation** — another model/module contributes a distinct capability;
- **routing gain** — a router sends each atomic operation to the mechanism best suited to it;
- **system capability** — the behavior of the composed `F(M,A,E;T)` system.

A successful external solver can improve system capability while providing zero evidence that the base model's intrinsic mathematical capability improved. RAKL must keep these statements separate.

## 3. Capability-shaping operator

For atomic research operation `k`, define a candidate shaping operator

\[
\mathcal O_k=(S_k,W_k,G_k,C_k,V_k,H_k),
\]

where:

- `S_k` — model strengths intentionally exploited;
- `W_k` — predictable failure modes targeted;
- `G_k` — amplification mechanisms that expose/use `S_k`;
- `C_k` — compensators that suppress or externalize `W_k`;
- `V_k` — verification/oracle contract;
- `H_k` — handoff and memory contract to the next atomic operation.

An operator without a named target failure mode or target strength is presumed decorative until evidence shows otherwise.

Every operator must also declare:

```text
atomic operation
base-model identity/configuration
allowed resources/tools
information visible to the model
information withheld from the model
output contract
blocking validity invariants
non-blocking meta-QoIs
cost accounting
falsifier
rollback/default behavior
```

## 4. Six forms of capability shaping

### 4.1 Amplify

Expose a model strength more effectively.

Examples:

- ask for many independent hypotheses when generative breadth is useful;
- translate an object into several representations when cross-vocabulary synthesis is useful;
- use domain stripping and structural schemas when remote analogy is useful;
- use local task context when long global context dilutes attention.

### 4.2 Constrain

Make invalid behavior harder or impossible.

Examples:

- typed schemas;
- unit constraints;
- causal-direction constraints;
- frozen answer contracts;
- predeclared mapping families;
- explicit authority transitions.

### 4.3 Externalize

Move fragile internal state into persistent explicit artifacts.

Examples:

- negative-evidence ledgers;
- terminology maps;
- frozen benchmark packets;
- provenance graphs;
- unresolved-assumption queues;
- distinguishing-probe certificates.

### 4.4 Verify

Use an appropriate oracle to detect or reject failures before promotion.

Possible oracle classes include:

```text
deterministic execution
symbolic/math solver
schema/type/unit checker
retrieval-backed source verification
held-out experiment
independent review context
adversarial counterexample search
```

Self-reflection may be useful, but same-context reflection is not independent verification.

### 4.5 Substitute or complement

Where a model is predictably weak and a better mechanism exists, use it.

Examples:

- calculator instead of mental arithmetic;
- parser instead of free-form extraction;
- search index instead of unaided memory;
- theorem prover for formal obligations;
- specialist model for a narrow recognition operation.

The resulting gain is a system-level gain and must be attributed accordingly.

### 4.6 Route and decompose

Do not require one monolithic reasoning trajectory to perform every operation.

```text
problem
-> atomic operation
-> capability/failure contract
-> best admissible mechanism
-> typed handoff
-> local verifier
-> next operation
```

A good architecture turns one long fragile chain into many bounded operations whose contracts are easier to test.

## 5. Capability map for RAKL

| Atomic operation | Strength to exploit | Typical weakness | Candidate RAKL compensator |
|---|---|---|---|
| decomposition | rapid generation of subproblems | missing hidden dependencies / over-splitting | dependency checks + residual-driven reopening |
| search | semantic/vocabulary breadth | surface attraction / familiar-domain bias | multi-route search + L0-L6 abstraction + route attribution |
| hypothesis generation | high generative diversity | premature convergence / narrative lock-in | portfolio branches + null/artifact alternatives + blind branch isolation |
| analogy | abstraction and relational transfer | false friends / transfer overreach | typed witness + `NOT_PRESERVED` + target validation |
| mathematics | symbolic pattern fluency | silent algebra/unit errors | executable checks + dimensional/invariant tests |
| causal reasoning | mechanism proposal | correlation-to-mechanism escalation | causal graph/intervention contract + ancestry requirements |
| synthesis | broad integration | flattening incompatible contexts | Knowledge Atlas transition maps + context-scoped gluing |
| review | objection generation | self-preference / same-context reinforcement | isolated/adversarial review + evidence-grounded concern IDs |
| memory | reconstructive summarization | forgotten nulls/refutations | immutable negative-history and provenance ledgers |
| confidence | useful qualitative uncertainty cues | overconfidence / poor calibration | evidence-governed authority rather than confidence-governed promotion |
| stopping | semantic judgment | premature closure / endless search | novelty-after-dedup saturation + independent flat rounds |

This table is a research map, not proof that each compensator works.

## 6. Capability gain must be decomposed

For matched baseline `B` and shaped system `S`, do not report one undifferentiated uplift.

At minimum record a vector

\[
\Delta C =
(\Delta Q, -\Delta F, -\Delta B, \Delta I, -\Delta K, -\Delta L),
\]

where:

- `Q` — task quality/success;
- `F` — rate of the targeted failure mode;
- `B` — blocking validity violations;
- `I` — information gain or useful coverage;
- `K` — cost per valid result;
- `L` — latency per valid result.

Blocking validity regressions dominate non-blocking improvements.

No weighted scalar is allowed to hide a blocking regression.

## 7. Attribution contract

A valid **workflow-only / model-utilization** claim requires:

```text
same base model identity
same model configuration
same frozen task packet
same answer/output contract
same evaluator
same hidden labels
same declared external-resource set
matched accounting
operator frozen before outcome inspection
```

If external resources differ, the comparison may still establish a **system capability gain**, but the attribution must change to `EXTERNAL_CAPABILITY_SUBSTITUTION`, `SPECIALIST_COMPLEMENTATION`, or another declared resource-sensitive class.

If resource differences are hidden, the trial is invalid.

## 8. Research algorithm as a capability transformer

RAKL can now evaluate a research method not only by final-answer quality but by how it transforms a model's error profile.

For cognitive operation `k`, define two diagnostics:

\[
G_k = \frac{Q_k^{\mathrm{shaped}}}{Q_k^{\mathrm{baseline}}}
\]

for a suitable positive-quality measure, and

\[
R_k = 1-\frac{F_k^{\mathrm{shaped}}}{F_k^{\mathrm{baseline}}}
\]

for a registered failure rate.

These are diagnostics, not universal objectives. They are invalid when denominators, task populations, resources, or evaluators are not comparable.

A strong RAKL operator should ideally show one or both of:

```text
capability expression ↑
target failure mode ↓
```

while preserving blocking invariants.

## 9. The smallest-compensator rule

More scaffolding is not intrinsically better.

For each weakness, compare at least:

```text
minimal baseline
smallest targeted compensator
richer scaffold if justified
```

Prefer the smallest operator on the non-dominated quality/validity/cost frontier.

If a simpler baseline matches the richer scaffold, keep the richer scaffold optional and preserve the null result.

## 10. Research cognitive architecture

The long-term RAKL architecture should be a graph of bounded cognitive contracts rather than one giant prompt:

```text
DECOMPOSE
   ↓
SEARCH / RETRIEVE
   ↓
NORMALIZE
   ↓
ABSTRACT / MAP
   ↓
GENERATE CANDIDATES
   ↓
DISCRIMINATE
   ↓
VERIFY
   ↓
SYNTHESIZE
   ↓
PROMOTE OR PRESERVE NEGATIVE RESULT
```

Each node should eventually expose:

```text
strength profile
failure profile
input contract
output contract
allowed tools/resources
verification oracle
negative-history dependency
benchmark/meta-QoIs
cost profile
fallback
```

This makes intelligence partly a property of the **architecture of bounded operations**, rather than requiring one model invocation to be universally competent.

## 11. Relationship to the similarity/JUMP lane

The similarity work is a concrete example of capability shaping.

A model is weak at spontaneous far-domain retrieval, so RAKL does not merely prompt "be more creative". It converts the operation into:

```text
L0-L6 abstraction
-> domain stripping
-> multi-route retrieval
-> typed structural witness
-> contrastive near-miss rejection
-> target-domain transfer test
```

The algorithm changes the environment around the model so that remote analogy becomes a measured search operation rather than a request for inspiration.

Conversely, if the frozen real-paper benchmark shows that a simple lexical+embedding route matches this richer pipeline, the richer path should not be mandatory.

## 12. Prior-art boundary

RAKL does not claim invention of agent scaffolding, decomposition, tool use, verifier loops, specialist routing, persistent memory, multi-agent workflows, or agent-computer interfaces.

Relevant prior work already demonstrates both sides of the design problem:

- workflow/interface design can materially alter what an LM-based system accomplishes;
- adaptive verification and external tools can improve reliability;
- complex/multi-agent scaffolds can also fail to beat simpler matched baselines.

The candidate RAKL contribution is narrower: **treat capability shaping itself as an atomic, evidence-governed research object with explicit strength/failure contracts, attribution classes, blocking validity constraints, matched-model ablations, negative-result preservation, and no automatic promotion from system uplift to model-capability claims.**

This remains provisional until executed benchmarks support it.

## 13. Frozen evaluation packet

The first hostile benchmark is:

`research/SELF_RAKL_RESEARCH_015_FROZEN_BENCHMARK.json`

It was frozen before the Round-015 support implementation.
