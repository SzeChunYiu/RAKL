# Paper Draft Addendum — Real Benchmark Semantics: Relevance Is Not Analogy

Status: provisional manuscript module  
Date: 2026-08-09

## Benchmark labels are projections, not universal truth

A cross-domain retrieval benchmark can identify a source as relevant without establishing that source and target are equivalent under every scientific relation RAKL cares about. This matters especially for scientific inspiration datasets: a useful inspiration can be methodologically relevant while differing in causal mechanism, mathematical regime, units, observation process or intervention semantics.

For target problem `t` and candidate source `s`, RAKL therefore separates three evaluator-side variables:

\[
Y_R(s,t) \in \{0,1\},
\]

indicating benchmark-designated **retrieval relevance**;

\[
Y_S(s,t;q,\phi,\Gamma) \in \{\mathrm{valid},\mathrm{reject},\mathrm{cannot\ check}\},
\]

indicating whether an explicit typed mapping witness preserves the registered structure for question/QoI `q`, admissible mapping family `\phi` and regime `\Gamma`; and

\[
Y_T(s,t;h)
\]

indicating the result of a separately frozen **target-domain transfer test** for transferred hypothesis, method or intervention `h`.

The default non-escalation rule is

\[
Y_R \not\Rightarrow Y_S,
\qquad
Y_S \not\Rightarrow Y_T.
\]

This does not deny that the variables can be correlated. It prevents an evaluator from silently changing the meaning of its evidence.

## MIR as a retrieval chart

The Methodology Inspiration Retrieval benchmark provides a useful real-science chart for `Y_R`: can a system retrieve methodological inspirations associated with a scientific research problem? RAKL can compare lexical, embedding, domain-stripped relational and graph/structural routes on this chart, provided the corpus, split, model, top-k, evaluator and hidden-label policy are frozen.

MIR does not by itself certify a RAKL relation such as `CAUSALLY_ANALOGOUS`, `DYNAMICALLY_EQUIVALENT` or `MATHEMATICALLY_ISOMORPHIC`. Those claims require a separate witness and relation-specific falsifiers.

This separation is particularly important for evaluating JUMP. If a richer route retrieves more MIR gold inspirations, RAKL may conclude that retrieval relevance improved. It may not yet conclude that deep-analogy recall improved unless the retrieved sources also pass the structural-witness evaluator.

## IsoSci as a separate structural attribution chart

IsoSci targets a different question: whether performance transfers across domain-different but structurally isomorphic scientific problems, and whether apparent reasoning improvement can instead be explained by domain-knowledge retrieval.

That makes IsoSci potentially useful for testing a structural-reasoning/knowledge-attribution axis, while MIR tests paper/inspiration retrieval. RAKL should not average these into one 'analogy score'. They are local charts with different observation operators.

## Corpus identity is part of the experiment

For a benchmark corpus `C`, the experimental object is not merely a dataset name. A trial should identify

\[
I(C)=(\mathrm{source},\mathrm{revision},\mathrm{artifact},\mathrm{content\ hash},\mathrm{split}).
\]

A mutable viewer or dataset frontend is a transport/presentation layer. Failure or change in that layer must not silently alter `I(C)`.

Round 016 encountered a concrete example: a plausible IsoSci dataset reference recorded in the frozen packet was later found to be incorrect. RAKL preserved the frozen record and issued an erratum rather than rewriting history. This is a native example of negative-history preservation applied to benchmark identity.

## Coverage is not retrieval recall

Let `G` be the evaluator-designated relevant set, `C` the frozen candidate corpus and `R_k` the top-`k` retrieval result.

RAKL records

\[
\mathrm{coverage}(G,C)=\frac{|G\cap C|}{|G|}
\]

separately from

\[
\mathrm{recall@k}_{C}
=\frac{|R_k\cap G\cap C|}{|G\cap C|}.
\]

If `G` is not fully contained in `C`, the missing portion is a corpus-coverage residual. Charging it to the retriever confounds two different mechanisms.

## Capability attribution for richer routes

A graph or structural retriever may use additional resources. Under RAKL's capability-shaping framework, route comparison must distinguish:

```text
same model + same resources + different workflow
    -> candidate model-utilization / routing gain

different external graph/index/resource set
    -> system-level gain with resource delta
```

The second can be valuable, but it is a different scientific claim.

## Falsifiable signatures

This module earns empirical support if, on a real frozen corpus:

- corpus coverage failures are correctly separated from retriever misses;
- hidden labels and post-hoc query edits are caught;
- structural routes improve `Y_S`-validated analogue recall rather than merely domain distance;
- resource-dependent gains are attributed to system resources rather than the base model;
- a valid structural witness can remain preserved when a target transfer is refuted;
- simpler lexical/embedding routes are retained when richer routes fail to improve registered valid-witness QoIs after cost.

A decisive null is equally informative: if lexical+embedding retrieval matches structural routes on real valid-witness recall, near-miss rejection, transfer utility and cost, structural retrieval remains optional rather than becoming mandatory RAKL complexity.

## Novelty boundary

RAKL does not claim novelty for scientific inspiration retrieval, graph retrieval, cross-domain analogy, isomorphic benchmarks, recall/MRR or reasoning-versus-retrieval decomposition. The narrower candidate contribution is an evidence-governance discipline in which benchmark labels, structural witnesses, transfer tests, corpus identity and resource attribution retain distinct authority throughout an analogy-discovery pipeline.
