# Bounded Epistemic Context Architecture

Status: support architecture v0.1. The canonical archive remains lossless; active prompt materialization is bounded and reconstructable.

## 1. Scaling problem

RAKL is intentionally expansive. It preserves source projections, typed relations, contradictions, failed hypotheses, supersession history, evidence lineage, review artifacts, benchmarks, method changes and open fibers. That is scientifically desirable but operationally dangerous if the active LLM context grows with the archive.

The design requirement is therefore:

> **Knowledge may grow without forcing prompt length to grow with it.**

RAKL separates persistent epistemic storage from the operation-specific working context.

## 2. Four memory tiers

### Tier 0 — immutable canonical archive

Lossless content-addressed payloads and append-only metadata. Raw evidence, exact claim spans, old refutations and superseded records remain reconstructable.

This tier is not injected wholesale into the LLM context.

### Tier 1 — indexes and multi-resolution materialized views

Regenerable search structures over the archive:

- semantic and lexical indexes;
- fiber/object/context indexes;
- evidence and lineage indexes;
- supersession and negative-history indexes;
- hierarchical summaries at source, fiber, atlas and project levels.

A summary is a **projection**, not replacement evidence. Compact views carry source record IDs. Lossy views also carry an erasure ledger describing information deliberately omitted.

### Tier 2 — epistemic working set

A task-specific collection selected under a token budget. It contains only the context required for the current operation plus high-value complementary material.

### Tier 3 — transient generation context

The final prompt presented to a model: compact constitutional/kernel instructions, the current operation contract, compiled working-set material, and reserved output/tool budget.

Tier 3 can use an ordinary LLM. The model need not remember the entire RAKL archive because it can request rehydration from lower tiers through tools.

## 3. Context is compiled, not accumulated

For an operation `a` on fiber `f` with question/QoI `q`, define the candidate memory views `V` and budget `B`.

The compiler solves a budgeted materialization problem:

\[
C^* = \arg\max_{C \subseteq V} U(C \mid a,f,q)
\quad \text{s.t.}\quad
\operatorname{tokens}(C) \le B,
\quad M(a,f,q) \subseteq C,
\]

where `M` is a mandatory epistemic set.

The support implementation uses deterministic marginal weighted coverage per token rather than claiming a universal optimal utility model.

## 4. Mandatory epistemic set

The following may become mandatory depending on the operation:

- object, question/QoI, context and evidence cutoff;
- the applicable Constitution/kernel slice;
- active residual and target fiber;
- registered falsifiers and relevant negative history;
- both sides of a contradiction being adjudicated;
- assumptions required for the current inference;
- mechanism ancestry required for mechanistic authority;
- evidence/lineage coordinates needed for an independence claim;
- transition/path certificates needed for a GLUE/JUMP/bridge claim;
- frozen benchmark/evaluator identity needed for method promotion.

Mandatory material is never dropped just to satisfy a token budget. If it cannot fit, the compiler returns `CANNOT_COMPILE`.

## 5. Optional selection by marginal coverage

After mandatory material is placed, optional views compete for the remaining budget by new decision/fiber coverage per token. Coverage atoms may include:

```text
facet
hypothesis
mechanism
assumption
contradiction side
falsifier
authority prerequisite
evidence source
lineage branch
open residual
QoI implication
```

If two records cover the same atoms, the second receives no utility merely because it is another document. Additional evidence can still be selected when it contributes a distinct evidence/authority/lineage atom.

This makes semantic deduplication operational inside context selection.

## 6. Query/fiber-specific materialization

High generic salience is not enough. Optional records outside the current fiber/operation scope are excluded unless an explicit transition or dependency makes them relevant.

The context compiler therefore acts after routing. Search/retrieval may have high recall; context materialization is a narrower authority- and task-aware operation.

## 7. Reconstructable compression

RAKL distinguishes:

```text
selection compression
textual compression
storage compression
```

### Selection compression

Do not load irrelevant records. This is the first and safest reduction.

### Textual compression

Summaries, extractive spans or prompt-compression methods may reduce selected material further. They are subordinate projections with provenance and erasure metadata.

### Storage compression

Canonical payloads can be content-addressed, deduplicated and compressed physically without changing their semantic identity.

The three layers must not be conflated. In particular, a short summary must never overwrite the only copy of exact evidence needed to reconstruct an authority claim.

## 8. Hierarchical views

A future multi-resolution store should expose at least:

```text
project synopsis
  -> object/fiber synopsis
      -> semantic object/evidence packet
          -> exact raw source span / experiment artifact
```

The LLM starts at the smallest useful view and expands downward only where the operation requires more authority or detail.

This is compatible with recursive-summary retrieval traditions, but RAKL adds explicit scientific authority and erasure constraints.

## 9. Context manifest

Every compiled prompt should be reproducible from a machine-readable manifest containing:

```text
operation_id
object_id
fiber_id
question_or_qoi
budget
selected_record_ids
omitted_record_ids
covered_atoms
missing_required_atoms
rehydration pointers
summary/source hashes
compiler version
selection reasons
```

The manifest is evidence about what the LLM actually had available. This is critical for review, debugging and replay.

## 10. Context packet anatomy for an ordinary LLM

A practical prompt should be assembled in layers rather than from the full repository:

```text
A. compact epistemic kernel
B. current task/object/QoI and operation contract
C. active residual + required authority scope
D. compiled evidence/knowledge working set
E. relevant negative-history guards
F. available tool/API contracts
G. output schema and stopping rule
```

Long explanations of unrelated RAKL fibers are not included. If the model needs them, it calls the memory/index interface.

## 11. Failure semantics

The compiler must distinguish:

```text
COMPILED
CANNOT_COMPILE
```

`CANNOT_COMPILE` is appropriate when mandatory evidence or required coverage cannot fit the registered budget. The caller may respond by:

- increasing budget;
- decomposing the operation into a smaller fiber;
- executing multiple staged passes;
- replacing a raw view with a validated compact view;
- changing the downstream claim scope.

It must not silently remove the falsifier or authority prerequisite that caused the overflow.

## 12. Scientific benchmark program

The frozen Round-020 known-answer benchmark tests critical-refutation retention, mandatory-over-budget honesty, duplicate reduction, two-sided contradiction preservation, mechanism ancestry, fiber isolation, summary rehydration, negative-history replay guards, lineage redundancy, determinism and marginal coverage.

The next empirical round must compare at matched budgets:

```text
full history
recency truncation
similarity top-k
summary-only
RAKL budgeted epistemic compilation
```

Metrics include downstream task correctness, authority leakage, negative-history retention, required-evidence recall, token ratio, latency and cost.

## 13. Relationship to external work

RAKL does not claim invention of virtual memory, hierarchical retrieval or prompt compression. Relevant external projections include MemGPT/Letta virtual context management, RAPTOR recursive summary trees, RECOMP selective compressed augmentation, LLMLingua prompt compression, recent budget-aware context management and hierarchical memory navigation.

The narrower RAKL contribution under test is the use of **epistemic mandatory sets, authority-aware/fiber-aware selection, reconstructable lossy views, negative-history guards and fail-closed context compilation** inside an evidence-governed scientific research method.

## 14. Activation boundary

`src/rakl/context_compiler.py` is support infrastructure. It selects metadata-level context items. It does not:

- summarize source text;
- retrieve remote evidence;
- alter canonical memory;
- activate routing;
- mint scientific authority;
- decide that a scientific problem is closed.

Those integrations require separate frozen benchmarks.
