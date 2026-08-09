# SELF-RAKL Research 029 — Scoped Self-Evolution Evidence

Date: 2026-08-09  
Starting `main`: `134aee702c48601d716b7de435dc30bd6c6938ba`  
Frozen benchmark: `research/SELF_RAKL_RESEARCH_029_FROZEN_BENCHMARK.json`

## Selected meta-residual

RAKL already has a governed challenger/promotion protocol, but the publication claim **"the system can evolve itself"** was underidentified.

A method can improve the same benchmark used to guide its mutation without learning a transferable research strategy. A recursive optimizer can also repeatedly inspect a supposedly held-out benchmark until that benchmark becomes an effective training signal. Therefore:

```text
self-modification
!= local benchmark improvement
!= transfer
!= fresh evidence of self-evolution
```

The run opened `META_N091_SCOPED_SELF_EVOLUTION_EVIDENCE` and `META_N092_ADAPTIVE_ASSURANCE_RESERVE`.

## Six-role panel

1. **Meta-learning / agent-evolution researcher** — separated procedural ability transfer from one-benchmark optimization.
2. **Adaptive-data-analysis statistician** — treated repeated holdout access as information leakage and assurance consumption.
3. **Evaluation-integrity red-team reviewer** — attacked evaluator capture, benchmark mutation and reward hacking.
4. **Scientific-method reviewer** — required an operational definition for when the word `evolution` is licensed.
5. **Research-software reproducibility engineer** — required exact candidate/evaluator/benchmark identities and preserved lineage.
6. **Top-tier-journal adversarial reviewer** — rejected a headline self-evolution claim without blind held-out transfer and negative-generation reporting.

The panel agreed on a deliberately scoped definition: RAKL may claim **scoped evolution evidence** only for the registered development/assurance distributions, model/tool/resource envelope and evaluator identity.

## Prior-art narrowing

Current primary work materially narrows the novelty envelope.

### Automated Design of Agentic Systems — arXiv:2408.08435

Meta Agent Search automatically invents and recombines agentic systems from an archive of previous discoveries, with transfer across domains/models reported. Therefore automatic agent design, recombination and archive-based improvement are not RAKL inventions.

### EvoAgentBench — arXiv:2607.05202

EvoAgentBench explicitly defines agent self-evolution through procedural ability transfer and reports that current automatic methods do not sustain positive gain in every setting. Therefore transfer-based self-evolution evaluation is itself prior art/neighboring work.

### SkillFoundry — arXiv:2604.03964

SkillFoundry converts heterogeneous scientific resources into validated executable skills with provenance/tests and evolves the skill library through expansion, repair, merge and pruning. Therefore external method/skill assimilation and evolving scientific skill libraries are not standalone RAKL novelty.

### Red Queen Gödel Machine — arXiv:2606.26294

RQGM co-evolves agents and evaluators under controlled non-stationary utilities. Therefore evaluator evolution is not novel by itself; RAKL must instead make the distinction between legitimate scoped evaluator-version changes and evaluator capture operationally testable.

## Retained theoretical refinement

### 1. Local improvement

A child method that improves at least one registered development meta-QoI on a benchmark frozen before observing the result, with blocking invariants clean, has shown:

```text
LOCAL_IMPROVEMENT_ONLY
```

unless transfer evidence is also available.

### 2. Scoped evolution evidence

A stronger state requires:

```text
positive development gain
positive held-out transfer gain
fresh assurance capacity
assurance frozen before method mutation
assurance hidden from proposer
separate/protected evaluator
exact child identity
resource comparability
negative-history preservation
zero blocking invariant failure
```

The authority is scoped rather than global.

### 3. Meta-overfit

Positive development gain plus a registered held-out regression is:

```text
META_OVERFIT
```

and remains immutable negative method history.

### 4. Adaptive assurance reserve

A blind holdout receives a preregistered optimizer-visible exposure budget. Once consumed, the same benchmark may still show observed transfer but cannot indefinitely certify new independent evolution generations.

This is an application of adaptive-evaluation logic rather than a claim that RAKL invented holdout discipline.

## External assimilation as the second evolution channel

The user's desired architecture is broader than endogenous self-editing.

RAKL should improve through two candidate sources:

```text
INTERNAL
native residual -> self-generated method challenger

EXTERNAL
other framework -> atomic operator decomposition -> method challenger
```

Both enter the same governed path.

This avoids two weak formulations:

```text
"RAKL is novel because it can rewrite itself"        -- false/overbroad
"RAKL absorbs every framework into one super-agent" -- scientifically unsafe
```

The stronger target is an **evolving method atlas**.

## New capability-frontier residual

For atomic fiber `f` and scientific context `gamma`, future RAKL should maintain a non-dominated validated method frontier rather than selecting one global winner.

Possible dispositions of an assimilated operator are:

```text
DOMINATE_INCUMBENT
ADD_FRONTIER_POINT
EQUIVALENT
PARALLEL_LOCAL_VIEW
BLOCK
REJECT
CANNOT_CHECK
```

This preserves the Knowledge Atlas principle at the method level: incompatible strengths can coexist under different contexts instead of being forcibly glued.

This frontier is theory-only in Round 029. No active routing or assimilation behavior is changed by it.

## Executable support layer

`src/rakl/evolution.py` adds:

```text
EvolutionVerdict
EvolutionTrial
EvolutionAssessment
AssuranceReserve
SelfEvolutionAssessor
```

Possible verdicts are:

```text
SCOPED_EVOLUTION_EVIDENCE
TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED
LOCAL_IMPROVEMENT_ONLY
META_OVERFIT
NO_IMPROVEMENT
BLOCKED
CANNOT_CHECK
```

The module is support-only. It does not replace `ConstitutionGuard`, promote a challenger, move `main`, alter the Constitution or activate an external method.

## Frozen hostile worlds

The benchmark requires correct handling of:

- blind positive transfer;
- dev-only gain;
- held-out regression;
- blocking invariant failure despite efficiency gain;
- no development gain;
- exhausted holdout exposure;
- optimizer-controlled evaluator;
- missing candidate identity;
- unfrozen assurance chronology;
- undeclared resource mismatch;
- lost negative history;
- fresh rotated assurance for a later generation.

Additional hostile controls reject repeated revealed-holdout certification, benchmark/evaluator mutation and same-context review disguised as assurance.

## First executed candidate evidence

Candidate `1f025d9846d75b06c2f905a72115b19c1fe0ad7d` executed the unchanged GitHub `pytest` workflow on exact candidate identity and returned:

```text
337 passed in 7.96s
```

The run used the already pinned action SHAs, bound checkout to the evaluated subject and ran on `ubuntu-24.04`.

This is implementation-contract evidence only. It is **not** evidence that RAKL has already achieved transferable multi-generation self-evolution.

## Top-tier paper discriminator

The prospective headline experiment should compare:

```text
fixed RAKL
unconstrained self-editing
development-benchmark-only evolution
RAKL governed self-evolution
RAKL governed self-evolution + external method assimilation
```

across repeated generations with separate:

```text
DEVELOPMENT
TRANSFER
FRESH/ROTATED ASSURANCE
```

planes.

A strong positive result would show accumulated improvements on fresh assurance packets across multiple generations while blocking invariants, evaluator separation and negative-history preservation remain intact.

A null/refuted result is equally important: if gains remain local, fail transfer, or require repeated assurance reuse, the self-evolution claim must be narrowed.

## Saturation

```text
state = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

New 2026 prior art narrowed multiple claims and opened the capability-frontier and assurance-reserve objects. Independent novelty review and prospective multi-generation experiments remain open.
