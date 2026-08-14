# Self-RAKL Research 045 — Research-Machine Workflow v2

**Status:** workflow challenger / development evidence only.  
**Frozen parent:** `main@b7747f21b58e8f827b1dab1a487739b83722af28`.  
**Target surfaces:** problem solving, literature absorption, saturation/stopping, process observability, Self-RAKL routing.  
**Scientific authority:** none.

## 1. Weakness localized in the incumbent workflow

The incumbent already has strong Apple/GLUE/JUMP, obstruction memory, negative-history and saturation principles. The missing integration is narrower:

1. ordinary `problem-solving.md` opens knowledge fibers but does not make **bounded quantified knowledge saturation** an explicit stage transition before serious candidate work;
2. literature absorption extracts rich semantic objects but does not define an executable round receipt or stopping controller;
3. the canonical metrology contract says every consequential method surface should emit `ProcessTelemetry`, but the ordinary workflow does not make this instrumentation a first-class execution requirement;
4. the incumbent principles say semantic saturation is not paper count and native residuals reopen fibers, but they do not explicitly state the persistent-cache behavior: **do not rerun global literature saturation on every local iteration**;
5. model/tool tier selection, including quantized/local models, is not tied explicitly to observational-epoch identity in the ordinary reading workflow.

This is classified as a workflow/integration gap, not evidence that the underlying Apple Principle or saturation machinery is wrong.

## 2. Self-RAKL literature/best-practice findings

### Iterative search and stopping must be explicit

Systematic-review methodology treats search design as iterative, emphasizes documenting stopping rationale, and notes diminishing returns. Modern active-screening work also reports that no single stopping rule is uniformly reliable across datasets. The design consequence for RAKL is a **hybrid bounded stopping rule**: semantic flatness + route coverage + residual absence + freshness, rather than one paper-count or "N irrelevant items" rule.

### Retrieval should be evidence-grounded and intent-adaptive

Recent agentic literature-retrieval work treats search as iterative intent refinement rather than one-shot query generation and separates expensive intent reasoning from cheaper high-volume retrieval/ranking. RAKL should therefore allow measured model/tool tiering while keeping primary-source identity outside the generative model's authority.

### Metareasoning should charge its own cost

Value-of-computation work shows that reasoning about whether further computation is useful can reduce unnecessary inference cost. RAKL's workflow should therefore record expected benefit, observed benefit and cost for search/read/experiment/verification actions rather than assume that more reasoning is always better.

### Intrinsic metacognition requires process-level self-evaluation

Self-improvement literature increasingly distinguishes fixed reflection loops from agents that model and adapt their own learning processes. RAKL already has the governance and observability substrate; the workflow must expose process metrics so Self-RAKL can identify the actual bottleneck surface.

## 3. Internal project evidence: current saturation campaign

The recent `research/p5_p6_saturation_v1` campaign is an internal discriminator for premature stopping.

- Round 001: `NOT_SATURATED`; the verdict lists **10** new load-bearing semantic object families.
- Round 002: `NOT_SATURATED`; **6** additional load-bearing object families absent from round 001.
- Round 003: `NOT_SATURATED`; **5** additional load-bearing object families absent from rounds 001–002.

The important observation is not the absolute count. It is that **materially different route families continued to expand the candidate basis in every round**. A one-shot literature pass or paper-count threshold would therefore have stopped too early on the project's own current research frontier.

No search-cost normalization is available in these round artifacts, so this record does not claim a measured efficiency gain.

## 4. Challenger design

The challenger introduces:

- `KnowledgeAcquisitionRound`: typed search/read/normalize receipt;
- persistent knowledge state with explicit invalidation/reopen conditions;
- bounded knowledge-saturation decision using the existing `saturation_vector.py`;
- required route-family coverage in addition to zero recent novelty;
- native residual and freshness precedence over a stale saturation certificate;
- reading indicators that distinguish raw source inventory from retained semantic gain;
- explicit model/tool/quantization identity in the observational epoch;
- per-process observability requirements in the ordinary problem-solving workflow;
- Self-RAKL triggers based on repeated process evidence rather than one failure.

## 5. Development tests

The local executable development suite contains eleven adversarial workflow-control tests:

1. no search rounds -> continue search;
2. any retained semantic novelty -> cannot claim saturation;
3. independent flat route families + complete route coverage -> bounded saturation;
4. many duplicate/redundant papers cannot substitute for route coverage;
5. native knowledge residual reopens a previously saturated fiber;
6. freshness event reopens incrementally without deleting prior history;
7. semantic-yield metrics distinguish retained novelty from raw inventory;
8. categorized novelty must be bound to retained semantic identity;
9. "relevant source" must be among processed source identities;
10. a historical residual that merely triggered a past reading round does not keep the fiber reopened after the active residual is resolved;
11. the same semantic identity cannot be counted as newly retained in multiple rounds.

Development result: **11/11 pass** in the standalone compatibility harness.

This is evidence that the workflow-control contract is executable. It is not evidence of superior scientific problem-solving outcomes.

## 6. Expected performance effects to test after merge

### Primary process QoIs

- false-saturation rate ↓;
- missed-key-source rate ↓;
- semantic novelty per search/query ↑ or unchanged at lower cost;
- unnecessary full-resaturation rate ↓;
- cost per retained semantic object ↓;
- residual-conditioned route-switch latency ↓;
- false semantic merge / false transfer non-increasing;
- process telemetry completeness ↑;
- model/tool cost with matched extraction fidelity ↓ where cheaper tiers are used.

### System-level QoIs

- time/cost to first decisive falsifier;
- residual closure per resource;
- transfer success on fresh problems;
- baseline-only success / RAKL interference;
- calibration of process-success predictions;
- frequency and precision of Self-RAKL bottleneck localization.

## 7. Required matched benchmark

A later confirmatory benchmark should compare at least:

```text
A: incumbent workflow
B: research-machine workflow v2
```

under the same model/tool versions, source-access policy, problem set, evaluator and resource ceiling.

Include:

- knowledge-rich tasks where premature stopping matters;
- tasks where initial knowledge is already sufficient and unnecessary reading should be avoided;
- tasks with a late residual that should trigger targeted resaturation;
- fast-moving domains requiring freshness refresh;
- hostile irrelevant-literature loads;
- at least one problem where APPLE JUMP is useful and one where it should stay inactive.

Primary outcome must remain a vector. Hard evidence/provenance/authority failures are non-compensatory.

## 8. Verdict

**DEVELOPMENT_CHALLENGER_READY_FOR_REAL_REPO_TESTS**

The workflow integration gap is real and the new control semantics pass the adversarial development harness. Promotion to an incumbent RAKL workflow requires real-repo tests plus a matched problem-solving benchmark/fresh assurance.
