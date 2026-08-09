# Paper Draft Addendum — Analogy Discovery as a Four-Gate Process

Status: manuscript module, provisional  
Date: 2026-08-09

## Why end-to-end analogy accuracy is insufficient

A scientific-analogy system can fail before it ever reasons about the analogy. The desired source may be absent from the search corpus, present but not retrieved, retrieved but not structurally recognized, or correctly mapped while the transferred target hypothesis fails empirically. These are scientifically different failures and should not share one error label.

RAKL therefore refines the JUMP lifecycle into four observable gates:

```text
CORPUS AVAILABILITY
        ↓
RETRIEVAL
        ↓
WITNESS CONSTRUCTION / RECOGNITION
        ↓
TARGET TRANSFER TEST
```

This extends the earlier retrieval-versus-recognition distinction with an explicit corpus-coverage gate and a target-test boundary.

## Retrieval and recognition use different evidence

Retrieval is evaluated against a frozen candidate corpus and hidden designated analogues. Its primary observables are candidate identity, rank, top-k recall, retrieval route and cost. Structural recognition is evaluated only after a candidate has been surfaced and requires a typed mapping witness with preserved and non-preserved correspondences, scope, probe family, admissible mapping family, constraints and evidence.

A surface-semantic score may be useful for retrieval but cannot substitute for relational recognition. Conversely, a strong mapper cannot repair a retriever that never surfaced the relevant source without that repair being counted as a different retrieval attempt.

## Route attribution

A distant analogue may be surfaced by one representation and missed by another. RAKL therefore records whether each candidate came from lexical, embedding, domain-stripped relational, graph/structural, equation or another declared route. Route attribution permits incremental-recall ablations such as:

```text
embedding only
vs
embedding + domain-stripped relational
vs
embedding + graph/structural
vs
multi-view portfolio
```

The purpose is diagnostic, not to assume that a richer route is always better.

## Contrastive near-misses

Recognition should be tested against difficult negative candidates rather than only unrelated distractors. A useful near-miss may share vocabulary, roles and much of the relational graph while violating one decisive coordinate such as causal direction, unit compatibility, regime, intervention semantics or a required invariant.

A rejected near-miss should emit a distinguishing-probe certificate. This makes negative analogy evidence reusable in later retrieval and mapping rounds.

## Cross-analogy motifs remain proposal evidence

Multiple distant analogies can reveal a structural motif that recurs across domains. RAKL may compute the intersection of preserved structures across valid witnesses, but the result remains proposal-level evidence. Shared surface templates, shared source ancestry or correlated retrieval pipelines can create false confirmation, and even genuinely independent cross-domain witnesses do not validate a target-domain mechanism or intervention.

Thus:

```text
cross-analogy structural agreement
    != target validation
    != mechanism identification
    != decision authority
```

## Benchmark chronology and leakage

Analogy retrieval benchmarks are unusually vulnerable to leakage because the evaluator necessarily knows which distant sources are designated analogues. The retriever and mapper must not receive those identifiers, hidden relevance labels or answer keys. Search queries, abstraction templates, top-k and mapping criteria must be frozen before hidden labels are inspected. Post-hoc query edits invalidate the untouched retrieval claim rather than becoming evidence that the original retriever succeeded.

## Falsifiable consequences

The four-gate decomposition earns runtime complexity only if it improves diagnostics or scientific decisions on a frozen real-paper corpus. Registered tests include whether:

1. corpus-coverage failures are separated from retriever failures;
2. route attribution identifies incremental recall from abstraction/structural retrieval;
3. relation-aware recognition rejects surface-plausible near-misses better than embedding similarity alone;
4. cross-analogy motif confirmation reduces coincidence without creating authority leakage;
5. a simple lexical+embedding baseline matches richer routes under the same top-k, model, corpus and cost budget.

If the richer decomposition adds no diagnostic or retrieval value, it should remain explanatory instrumentation rather than mandatory active complexity.

## Novelty boundary

RAKL does not claim novelty for mechanism-aligned analogy retrieval, cross-analogy confirmation, stage-decomposed scientific discovery benchmarks, multi-stage analogy annotation, abstraction-assisted structural mapping, graph/subgraph retrieval, or relational-overlap scoring. The narrower candidate contribution is the way a scientific Knowledge Atlas records analogy discovery as a provenance-preserving, authority-bounded sequence of corpus coverage, retrieval, witnessed recognition and target testing while retaining failed mappings and preventing later stages from silently rewriting earlier failures.
