# SELF-RAKL Research Round 020 — Bounded Epistemic Context and Engineering Closure

Date: 2026-08-09

Starting `main`: `268bedaf800b344193ea2f9d8314d2626182bf28`

Entering framework status: `ACTIVE_NON_FLAT`; latest derived inventory reported 24 registered high-impact method steps and 24 open or unbenchmarked steps.

## 1. User/native residual

RAKL's deliberate preservation of source projections, negative history, typed relations, benchmarks, receipts and recursive fibers creates a scaling risk: the persistent knowledge state grows faster than the context that an ordinary LLM can consume economically or reliably.

Current `ResearchMemory` already has a useful invariant: append-only records plus explicit supersession. It does not yet solve active-context materialization. The architecture therefore had a hidden assumption that the relevant historical state could be made visible to the LLM without an explicit context policy.

The engineering objective was frozen as:

> Keep the canonical epistemic archive lossless and growing while bounding the task-specific LLM working context without silently dropping falsifiers, authority prerequisites or reconstructability.

## 2. Frozen expert panel

Six perspectives were fixed before implementation.

1. **LLM memory-systems researcher** — virtual memory, persistent agents and context compaction. Task: separate storage from model-visible working memory.
2. **Information-retrieval / hierarchical summarization researcher** — multi-resolution retrieval, selective augmentation and query-conditioned compression. Task: determine whether to retrieve, summarize or compress first.
3. **Database / storage-systems engineer** — content-addressed payloads, indexes, materialized views, cache reconstruction and append-only histories. Task: make growth manageable without deleting scientific state.
4. **Algorithms / optimization researcher** — budgeted coverage, deterministic selection, approximation and complexity. Task: formulate bounded context compilation with explicit costs.
5. **Scientific-provenance epistemologist** — claim scope, evidence ancestry, lossy projections and negative history. Task: specify which material compression must never erase.
6. **Adversarial release engineer** — installation, overflow, cache corruption, restart/replay and observability. Task: turn "ready to use" into executable closure criteria rather than a narrative claim.

These role-separated passes shared one orchestration context and are not counted as independent review.

## 3. Baseline audit

Observed at run start:

```text
main = 268bedaf800b344193ea2f9d8314d2626182bf28
open issues = 0
Constitution = unchanged
latest exact-head test workflow = completed success
ResearchMemory = append-only + supersession, no bounded context compiler
FRAMEWORK_FIBER_INVENTORY_019 = 24 high-impact steps, 24 open/unbenchmarked
```

The Constitution already registers context/token efficiency as a method meta-QoI and prompting/context policy as a replaceable module, so this work does not require a Class-C amendment.

## 4. External projections

### 4.1 Virtual context management

MemGPT treats finite LLM context as a fast memory tier backed by larger external memory and moves information between tiers. Current Letta implementations continue to expose core/in-context memory plus archival state and practical compaction/recompile mechanisms.

**RAKL absorption:** persistent epistemic storage and LLM-visible context must be separate architectural objects.

### 4.2 Recursive and hierarchical retrieval

RAPTOR recursively clusters and summarizes document chunks so retrieval can operate at multiple abstraction levels. Recent hierarchical memory-navigation systems such as HORMA retain links between summarized entities and raw trajectories and explicitly optimize minimal sufficient working context.

**RAKL absorption:** multi-resolution views are useful, but a summary must remain a projection with a path back to exact evidence.

### 4.3 Selective compression

RECOMP compresses retrieved evidence and can selectively provide no augmentation when retrieval is unhelpful. LLMLingua/LongLLMLingua and LLMLingua-2 show large token/latency reductions are possible through prompt compression. Newer query-conditioned compression work argues against compressing all information irrespective of the query.

**RAKL absorption:** first select the right epistemic material; only then apply optional textual compression. Compression is subordinate to authority and reconstructability.

### 4.4 Budget-aware control

ContextBudget explicitly formulates context management as a budget-constrained decision process.

**RAKL absorption:** context budget becomes a registered operation constraint rather than an emergency truncation threshold.

### 4.5 Memory evaluation

MemGym isolates memory performance from general reasoning/tool-use ability.

**RAKL absorption:** context/memory architecture must be benchmarked as its own fiber before whole-system gains are attributed to it.

## 5. Central architecture: archive != context

RAKL now distinguishes four tiers.

```text
Tier 0 immutable canonical archive
  -> Tier 1 indexes and multi-resolution materialized views
      -> Tier 2 operation-specific epistemic working set
          -> Tier 3 transient LLM prompt
```

The archive may grow. The prompt does not grow proportionally.

Compact views are cache/materialization objects. They do not replace raw evidence. A compact view carries `source_record_ids`; a lossy compact view additionally declares `erasure_tags` describing omitted information.

## 6. Epistemic mandatory set

A relevance model is not allowed to discard every low-similarity item. For a given operation, some records are mandatory because omitting them would change the authority of the result.

Examples:

```text
registered falsifier
relevant negative-history event
both sides of an active contradiction
mechanism ancestry prerequisite
assumption required by the inference
lineage coordinate needed for independence
bridge/transition certificate required by composition
evaluator/subject identity needed for promotion
```

If mandatory material exceeds the budget, the correct outcome is `CANNOT_COMPILE`.

This is the major difference between ordinary retrieval relevance and scientific context materialization.

## 7. Frozen benchmark

Before implementation, two research-only commits were made directly to `main`:

1. `SELF_RAKL_RESEARCH_020_CONTEXT_FROZEN_BENCHMARK.json` froze 12 known-answer/hostile context worlds and their meta-QoIs.
2. `ENGINEERING_CLOSURE_PROGRAM_020.json` froze the release-closure interpretation and explicitly recorded that global closure is not yet allowed.

The context benchmark covers:

- a critical refutation hidden among 100 irrelevant records;
- mandatory material larger than the token budget;
- duplicate semantic objects;
- two-sided contradictions;
- mechanism ancestry;
- target-fiber isolation;
- summary rehydration pointers and erasure metadata;
- negative-history replay guards;
- duplicate coverage/shared-lineage style redundancy;
- deterministic equal-score selection;
- marginal coverage per token;
- empty relevant sets without filler.

## 8. Supporting implementation

Candidate branch:

```text
self-rakl/round020-context-compiler
```

New module:

```text
src/rakl/context_compiler.py
```

Core objects:

```text
ContextItem
ContextCompileRequest
ContextCompileReport
ContextCompileVerdict
compile_epistemic_context
```

The algorithm is intentionally small and deterministic.

### Step 1

Load explicitly mandatory items. If their cost exceeds the registered budget, return `CANNOT_COMPILE`.

### Step 2

Filter optional items by relevance and target fiber.

### Step 3

Repeatedly choose the fitting item with highest **new weighted coverage per token**. Ties are deterministic.

### Step 4

Do not select items with zero marginal coverage merely to fill the prompt.

### Step 5

If registered required coverage is still missing, return `CANNOT_COMPILE` rather than describing the partial packet as sufficient.

### Step 6

Return rehydration record IDs for selected compact views.

The implementation is support-only. It cannot retrieve payloads, summarize text, mutate memory, route tools or mint authority.

## 9. Execution evidence

The first implementation/API candidate head was:

```text
999442396f319916cf9dc91a9bf6fb32e82fa859
```

GitHub Actions run `31318643928`, job `93257935660`, checked out that exact branch head. `pytest` executed successfully with:

```text
232 passed in 3.25s
```

This is intermediate authority only because research/docs/receipts were staged afterward. Final exact-SHA CI remains required before promotion.

The CI log also reconfirms the previously open evaluator-dependency issue: the workflow text still references `actions/checkout@v4` and `actions/setup-python@v5`, which resolved at runtime to concrete action commits. Round 020 does not alter that protected workflow because dependency pinning has its own open fiber.

## 10. Engineering closure program

The user requirement to make RAKL a complete ready-to-use package was translated into `ENGINEERING_CLOSURE_PROGRAM_020` and `docs/ENGINEERING_CLOSURE.md`.

Every material engineering problem becomes a RAKL fiber with scope, residual, frozen tests, hostile cases, resource budgets, blocking invariants, observability, recovery and closure criteria.

Release readiness is separated into planes:

```text
epistemic core
storage/memory
context/execution
evaluation/governance
user package
scientific validation/publication
```

A release can claim only scoped closure for a frozen reference profile. It cannot claim universal correctness or global scientific completeness.

## 11. Normal-LLM execution principle

The package should make the model stateless with respect to the full framework. A normal LLM receives only:

```text
compact epistemic kernel
current operation contract
object/context/QoI
active fiber and residual
bounded compiled evidence/knowledge packet
relevant negative-history guards
tool contracts
output schema/stopping rule
```

The software owns long-term state, retrieval, manifests, evidence and rehydration.

This turns base-model capability into an explicit dependency that can be benchmarked rather than an implicit requirement to memorize RAKL.

## 12. Retained semantic objects

After deduplication against prior RAKL memory and external work:

1. `LOSSLESS_ARCHIVE_BOUNDED_WORKING_SET_SEPARATION`
2. `EPISTEMIC_MANDATORY_CONTEXT_SET`
3. `FAIL_CLOSED_CONTEXT_OVERFLOW`
4. `RECONSTRUCTABLE_LOSSY_VIEW_CONTRACT`
5. `FIBER_AWARE_MARGINAL_COVERAGE_COMPILATION`
6. `CONTEXT_MANIFEST_AS_EVALUATION_SUBJECT`
7. `ENGINEERING_CLOSURE_AS_RAKL_FIBERS`
8. `SCOPED_RELEASE_PLANE_CLOSURE`

Not counted as novel:

- virtual memory/context tiers;
- RAG;
- hierarchical memory;
- recursive summaries;
- prompt compression;
- budget-aware context management;
- materialized views or content-addressed storage generally.

## 13. New/open child fibers

```text
META_N074_BOUNDED_EPISTEMIC_CONTEXT_COMPILER
META_N075_ENGINEERING_CLOSURE_AND_RELEASE_CONFORMANCE
META_N076_MULTI_RESOLUTION_RECONSTRUCTABLE_MEMORY
META_N077_NORMAL_LLM_REFERENCE_PROFILE
META_N078_END_TO_END_CLEAN_INSTALL_WORKFLOW
```

N074 has support v1 but is not integrated into active routing/model invocation.

## 14. Empirical falsifier

The real context-policy experiment must compare, under matched models/tools/tasks/token budgets:

```text
full history
recency truncation
similarity top-k
summary-only
RAKL bounded epistemic compilation
```

If simpler methods preserve the same required evidence, negative history and downstream decisions at equal or lower cost, the richer context compiler must not become mandatory architecture.

## 15. Saturation/closure verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
context_efficiency_lane = ACTIVE_NON_FLAT
engineering_closure_program = OPEN
same_context_flat_rounds = 0
independent_flat_rounds = 0
global_scientific_closure = NOT_AUTHORIZED
```

The newest derived framework inventory still has all 24 high-impact method steps open or unbenchmarked. A ready-to-use/scientifically closed release therefore remains a program objective, not a completed claim.

## 16. Next discriminators

1. Freeze and implement `META_N076`: content-addressed canonical payload store plus multi-resolution views with source/erasure manifests.
2. Freeze a real matched context-policy benchmark for N074; measure result parity, authority leakage, tokens, latency and cost across ordinary-model profiles.
3. Freeze `META_N077` reference profiles so RAKL's minimum model/context/tool assumptions become explicit and testable.
4. Freeze `META_N078` clean-install/restart workflow and execute it in a fresh environment before calling the package ready to use.
5. Update the framework inventory with release-plane closure evidence rather than manually declaring global closure.
6. Continue N029 evaluator-dependency pinning and N019 durable execution because package reliability cannot be closed while those trust/retry residuals remain open.
