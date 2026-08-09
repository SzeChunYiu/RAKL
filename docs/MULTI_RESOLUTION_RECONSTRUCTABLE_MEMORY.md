# Multi-resolution reconstructable memory

Status: support-layer method module. This document does not amend the RAKL Constitution and does not claim real-agent or scientific validity.

## Motivation

RAKL deliberately separates the lossless epistemic archive from the bounded working context. That creates a second problem: compact and high-level views are useful for navigation, but they must not silently replace, overwrite, or strengthen the evidence from which they were derived.

A derived memory view is therefore treated as a projection over canonical records, not as a new source of truth.

For a view `v`, write

\[
v = T(s_1,\ldots,s_k),
\]

where each direct source `s_i` is pinned by immutable record identity and payload hash. Repeatedly expanding direct sources gives a canonical source closure

\[
C(v)=\operatorname{roots}(v).
\]

RAKL requires `C(v)` to be finite, acyclic, fully resolvable and content-pinned before the view is considered valid.

## Three distinct reconstruction states

RAKL does not use the word *reconstructable* as a single vague property.

- `VALID_CANONICAL`: the record is itself a canonical leaf.
- `SOURCE_REHYDRATABLE`: the view can be traced back to all canonical source records, but the view alone is not claimed to recover erased content.
- `REGENERATION_VERIFIED`: an externally executed witness has verified exact regeneration for a declared lossless transform.
- `INVALID`: lineage, hash, erasure, authority or required-root invariants failed.

A lossy summary can be source-rehydratable while being impossible to invert from its own text. This distinction prevents a pointer-backed summary from being mislabeled as a lossless evidence representation.

## Lossy views and erasure

Every lossy view must declare what it erased. The erasure ledger is descriptive metadata; it is not proof that all losses have been enumerated. The canonical source closure remains the authority-bearing escape hatch when a downstream operation needs exact wording, numbers, assumptions, negative evidence or other omitted coordinates.

## Authority non-escalation

Derived views are cache/representation objects. They may preserve authority certificates already carried by direct sources but cannot mint a new certificate. If synthesis creates a genuinely new epistemic claim, that claim must enter canonical RAKL memory with its own evidence and promotion path.

This is intentionally conservative and consistent with the RAKL scientific-authority poset: representation convenience does not imply mechanistic, identification, grounding or decision authority.

## Contradictions and negative history

A coarse view can declare canonical records that are mandatory roots. This is used for registered contradictions, refutations and other negative-history objects. A view that claims to summarize a two-sided contradiction but can reach only one side is invalid rather than a successful simplification.

## Why this is not ordinary hierarchical memory

Hierarchical agent memory is established prior art. Recent systems organize histories at multiple temporal or semantic scales, retrieve coarse summaries before detailed turns, or use high-density representations to locate verbatim evidence. RAKL does not claim those ideas as novel.

The narrower RAKL contribution under test is the conjunction of:

1. immutable canonical source leaves;
2. hash-pinned transitive source closure;
3. explicit lossy erasure metadata;
4. source rehydration distinguished from exact regeneration;
5. externally witnessed exact-regeneration claims;
6. representation-level authority non-escalation;
7. registered contradiction/negative-history root preservation.

These are support contracts, not evidence that the richer design improves downstream research.

## Current empirical boundary

The frozen Round-021 benchmark tests known-answer and hostile metadata worlds only. Real value remains open. A future matched benchmark must compare flat canonical memory, rolling summaries, ordinary vector retrieval, hierarchical memory without these contracts, and this reconstructable RAKL layer under the same model, tasks, corpus and budget.

If simpler memory preserves source recall, negative evidence, contradiction coverage and downstream decisions at equal or lower cost, the richer layer should remain optional.
