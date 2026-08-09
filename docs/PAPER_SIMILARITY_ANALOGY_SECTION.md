# Paper Draft Module — Similarity, Analogy, and Scientific Jumps

Status: manuscript module, provisional  
Date: 2026-08-09

## Similarity is not a scalar

A central problem in scientific synthesis is deciding whether two pieces of research are about the same underlying object, and separately whether apparently unrelated systems preserve enough structure to support useful transfer. These are different scientific tasks with different error costs. We call the first **GLUE** and the second **JUMP**.

GLUE is conservative. It asks whether two local descriptions can be identified, transformed, or combined at a declared layer and scope without erasing scientific distinctions. JUMP is exploratory. It asks whether a structurally informative correspondence exists between different objects or domains even when lexical and topical similarity are low. A false GLUE can corrupt the canonical knowledge state. A false JUMP is cheaper provided the candidate remains a proposal and is tested before acquiring authority.

We therefore do not define similarity as a universal cosine score. For an atomic scientific object `x` and registered question or quantity of interest `q`, RAKL represents a multi-layer signature containing entities and roles, relations, causal dependencies, mechanism ancestry, equations and invariants, functions, observables, boundary/regime conditions, and available interventions. A similarity claim between objects `A` and `B` requires a witness

\[
W_{A\to B}^{\tau,q}=(\phi,P^+,P^-,\Gamma,\Delta,\mathcal E),
\]

where `phi` is an explicit partial mapping, `P+` records preserved structure, `P-` records known broken correspondences, `Gamma` states the valid scope and regime, `Delta` represents approximation or mapping ambiguity, and `E` records evidence supporting the correspondence.

This makes the mapping itself the primary scientific object. A scalar score may summarize one projection of the witness but cannot replace it.

## Relation types and non-escalation

RAKL separates identity and equivalence relations from analogy and transfer relations. Examples of GLUE-side relations include `SAME_OBJECT`, `EXACT_ISOMORPHISM`, `SAME_GENERATOR`, `SAME_MECHANISM`, `OBSERVATIONALLY_EQUIVALENT`, and `QOI_EQUIVALENT`. Examples of JUMP-side relations include `RELATIONALLY_ANALOGOUS`, `CAUSALLY_ANALOGOUS`, `FUNCTIONALLY_ANALOGOUS`, `SAME_FAILURE_MODE`, `SAME_REGIME_STRUCTURE`, and `BRIDGE_TO`.

The distinction prevents a common authority error. Two systems governed by isomorphic equations are not thereby the same physical mechanism. Two models producing the same observable are not thereby mechanistically equivalent. Two mechanisms producing the same decision for one QoI may be decision-equivalent while remaining scientifically distinct. Cross-layer escalation requires an explicit licensed mapping and supporting evidence.

Classical structure-mapping theory motivates the emphasis on systems of relations rather than shared attributes. More recent scientific-analogy work shows that cross-domain relational analogies can increase solution diversity, while recent mechanism-centric retrieval explicitly rewards mechanistic alignment together with semantic distance. RAKL treats these as prior foundations rather than proprietary ingredients. Its additional constraint is epistemic: analogy is a search and hypothesis-generation operation until target-domain validation occurs.

## Retrieval, recognition, transfer, validation

RAKL decomposes analogical discovery into four stages:

```text
candidate retrieval
-> structural recognition and witness construction
-> transfer hypothesis
-> target-domain validation
```

This decomposition matters because each stage can fail independently. A relevant distant source may exist but never be retrieved. A retrieved source may fail deep structural mapping. A valid structural mapping may support only a narrow inference, while an LLM extrapolates beyond it. Finally, a structurally justified transfer can still fail empirically because the target system contains a material, scale, boundary, or intervention constraint that the source does not share.

Accordingly, the RAKL state distinguishes `CANDIDATE_BRIDGE`, `WITNESSED_ANALOGY`, `TRANSFER_HYPOTHESIS`, and target outcomes such as `TARGET_VALIDATED`, `TARGET_REFUTED`, `PARTIALLY_IDENTIFIED`, or `CANNOT_CHECK`. This is the analogy-specific form of the general rule that proposal generation does not itself create scientific authority.

## Controlled abstraction

To retrieve distant analogies, RAKL projects each atomic object through an abstraction ladder:

```text
L0 exact terminology
L1 domain concept
L2 functional description
L3 causal/mechanistic schema
L4 relational graph
L5 mathematical/dynamical schema
L6 domain-independent structural pattern
```

The purpose is to remove domain nouns while retaining roles, predicates, constraints, invariants and boundary conditions that can seed foreign-domain search. However, abstraction is lossy. Every abstraction step therefore carries an erasure ledger listing removed material assumptions, units, scales, boundary conditions, causal directions, stochastic structure, conservation laws and intervention semantics. An abstract representation may improve retrieval recall without being sufficient to authorize transfer.

## A two-stage retrieval architecture

RAKL uses a coarse-to-fine design. The broad stage retrieves candidates from multiple views such as text semantics, ontology graphs, equations, causal schemas, failure signatures, citation ancestry and domain-stripped queries. The narrow stage performs explicit structural mapping on a much smaller set. This is conceptually compatible with the classical MAC/FAC separation between inexpensive retrieval and expensive structural evaluation, while allowing modern graph, equation and LLM-based retrievers as replaceable modules.

The method therefore asks not only whether a model can recognize an analogy when two examples are presented together, but whether it can discover the distant source in the first place. Retrieval recall and mapping precision are evaluated separately.

## Scientific jump frontier

A useful scientific jump is not merely a remote association. We characterize a candidate with

\[
J(A,B\mid q)=
(S_{deep},D_{surface},U_{transfer},E_{readiness},R_{risk},C_{cost}),
\]

representing deep structural preservation, surface/domain distance, expected transfer value, validation readiness, false-analogy risk and cost. Rather than collapsing these into one universal score, RAKL retains non-dominated candidates on a Pareto frontier subject to minimum structural-witness constraints.

This yields the intended behavior: near-domain high-confidence mappings remain available for exploitation, while distant but structurally strong bridges survive as diversification or moonshot candidates. Random remoteness without a witness does not receive novelty credit.

## Multi-hop scientific bridges

Some useful transfers are not direct. RAKL can traverse

\[
A\to B\to C,
\]

when each hop has an explicit witnessed relation. However, `BRIDGE_TO` is a navigation relation, not an equivalence relation. Composition requires that mapped roles at the intermediate object are compatible, that the same relevant invariant survives the path, and that approximation and regime constraints remain valid. The path may suggest a new experiment even when no direct `A`-to-`C` equivalence exists.

## Falsifiable paper claims

This component earns empirical support only if it predicts selective improvements on frozen tests. Expected signatures include lower false-merge rates for GLUE, higher recall of far-domain analogies with low lexical overlap, better mapping correctness than embedding-only retrieval, lower invalid-transfer rates when the erasure ledger is enforced, and reduced analogy-authority leakage when transfer validation is separated from recognition.

If simpler embedding retrieval plus ordinary LLM comparison matches RAKL on these registered failure modes under matched model, corpus, budget and evaluator conditions, the additional algebra should be retained only as explanatory notation rather than claimed as an empirical method improvement.

## Figure concept

`docs/figures/glue_jump_similarity_plane.svg` is a conceptual schematic rather than measured data. Its horizontal axis represents surface/domain similarity and its vertical axis represents witnessed deep structural preservation. High-surface/high-structure candidates are natural GLUE targets. Low-surface/high-structure candidates are the desired scientific JUMPs. High-surface/low-structure candidates are surface false friends. Low/low candidates are irrelevant remoteness.
