# RAKLBench — Benchmarking the Research Method Itself

RAKL must not claim end-to-end self-improvement merely because one generated report looks better.

RAKLBench evaluates the atomic scientific-research capabilities on which the whole method depends.

## 1. Evaluation philosophy

A workflow challenger is tested on the same frozen benchmark packet as the incumbent.

Report:

```text
quality
blocking validity failures
cost / tokens / latency
variance across runs
failure modes
```

Do not collapse blocking validity and convenience into one average score.

## 2. Blocking benchmark axes

### B0 — Evidence grounding

Can the system distinguish retrieved/source-supported facts from its own hypotheses?

Planted failure: a plausible unsupported claim.

### B1 — Object/facet decomposition

Can the system distinguish the object from one projection and discover missing facets?

Known-answer world: the apple color/shape/taste/texture example.

### B2 — Context-before-contradiction

Can it avoid calling context-dependent claims contradictory?

Known-answer world: red ripe cultivar vs green unripe cultivar.

### B3 — False split detection

Can it recognize the same mathematical object under different notation/coordinates?

### B4 — False merge detection

Can it keep distinct microscopic mechanisms separate when they share an effective/observed law?

### B5 — Representation versus mechanism

Can it label a high-performing predictive representation without inventing microscopic authority?

### B6 — Residual routing

Given a planted failure signature, does it reopen the correct R0–R10/fiber dimensions rather than search unrelated models?

### B7 — Discriminator selection

Does it prefer an experiment/query that meaningfully separates the surviving hypotheses rather than simply producing more data?

### B8 — Validator honesty

Can a checker PASS a clean world, FAIL a planted violation and return CANNOT_CHECK on missing evidence?

### B9 — Negative-history preservation

Does a successor preserve a historical null/refutation rather than overwriting it?

### B10 — Review independence

Does the system distinguish same-context reflection from genuinely isolated frozen reviewer reports?

### B11 — Saturation honesty

Does it refuse saturation when a required search route is missing, when an independent round adds a new semantic object, or when a native residual reopens the fiber?

### B12 — Constitutional self-modification

Does it prevent the proposing LLM from silently weakening a core axiom in order to improve its benchmark?

## 3. Optimization axes

After blocking axes pass, compare:

```text
semantic recall
false-novelty rate
missing-facet yield
contradiction yield
mechanism discrimination
information gain / query
information gain / cost
source diversity
primary-source fraction
context/token cost
runtime
reproducibility
```

## 4. Long-horizon tests

A self-improving system can pass atomic tasks yet fail over many cycles.

Long-horizon RAKLBench should test:

- persistent memory across sessions;
- no resurrection of refuted ideas without versioning;
- no confirmation-set contamination;
- saturation wall detection;
- branch diversity under repeated improvement;
- recovery after introducing a new tool/action surface;
- exact trial accounting across workflow variants;
- convergence versus oscillation of self-modifications;
- rollback after a bad promoted workflow.

## 5. External benchmark adapters

RAKL should use established external benchmarks where they measure a relevant facet rather than creating bespoke tests for everything.

Potential adapters include scientific-agent task benchmarks, literature discovery benchmarks, ML-engineering research tasks and general long-horizon agent evaluations.

External benchmark scores are **projections on RAKL quality**, not global truth. Record exactly which RAKL facet each benchmark measures and which it does not.

## 6. Benchmark contamination

Every benchmark task has a trial/use ledger.

Separate:

```text
DEVELOPMENT
META_TRAIN
META_VALIDATION
READ_ONCE_CONFIRMATION
PUBLIC_REGRESSION
```

Repeated hourly self-improvement must not turn a read-once confirmation set into a training set.

Adaptive benchmarking requires separate prospective tasks or valid sequential evidence.

## 7. Direct-to-main requirement

An automated Class B workflow change may become active only when:

1. benchmark packet was frozen before the candidate result;
2. all applicable blocking axes pass;
3. at least one registered optimization axis improves;
4. regressions are reported;
5. test/cost/trial receipts are committed;
6. old workflow remains recoverable.

If the environment cannot execute the benchmark, the candidate remains research/proposal state.
