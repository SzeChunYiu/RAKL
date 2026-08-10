# Bounded Epistemic Saturation

**Status:** implementation contract for recursive research and manuscript release  
**Scope:** formal/software stopping discipline. A bounded saturation certificate is never a certificate of unrestricted scientific completeness.

## Project principle

RAKL continues expanding a registered research state while a meaningful discovery, derivation, evidence, contradiction, negative result, novelty correction, assumption correction, unresolved-fiber update, or discovery-route update is still being found. A research lane may stop only after deliberately heterogeneous attempts to expand it become substantively flat under a fixed measurement basis.

This is the operational interpretation of “accumulate knowledge until it stops growing.” The word *growing* refers to epistemically meaningful state change, not raw file size, number of notes, graph nodes, citation count, or prose length.

## Saturation basis

`SaturationBasis` freezes the semantics needed for longitudinal flatness:

- research/manuscript scope;
- object identity policy;
- discovery-route family version;
- novelty / nearest-work equivalence policy;
- evidence / authority policy.

The basis has a content-derived fingerprint. If any basis coordinate changes, the comparison is invalid rather than being interpreted as renewed scientific growth.

## Marginal growth vector

`EpistemicGrowthVector` records nine non-compensatory coordinates for a research/review round:

1. mechanisms or function owners added;
2. derivations or formal consequences added;
3. independent evidence roots added;
4. contradictions or counterexamples added;
5. negative results added;
6. novelty / prior-art boundary updates;
7. assumption or scope updates;
8. unresolved-fiber updates;
9. discovery-route updates.

A round is substantively flat only when all nine coordinates are zero. Representation-only changes are recorded separately. Rewriting a paragraph, splitting a file, renaming an equivalent object, or adding a redundant citation cannot manufacture epistemic growth.

## Certificate rule

`audit_bounded_epistemic_saturation()` can return `BOUNDED_SATURATED` only when the required number of final rounds are all substantively flat and, for every round in that suffix:

- bounded OWMD closure is satisfied;
- discovery-route coverage is stable;
- the omission audit passes;
- the nearest-work equivalence audit passes;
- no blocking research fibers remain;
- the freshness scan reaches the required cutoff.

A new substantive object resets the consecutive-flat-round count. A later freshness requirement can also expire an older certificate.

`SaturationReport.absolute_complete` is always `False`.

## Relation to the epistemic lattice

The historical atom/witness/path object remains a `TypedCompatibilityComplex`, because pairwise compatibility does not supply a partial order or meet/join operations.

A genuine lattice appears only after a closure operator is declared. If

\[
\operatorname{cl}:\mathcal P(A)\to\mathcal P(A)
\]

is extensive, monotone and idempotent, its fixed points form a complete lattice under inclusion. Intersections are meets and closure-of-union is join. A bounded-saturated state is therefore interpretable as a fixed point of a declared bounded epistemic expansion/closure operator, not as an assertion that the unrestricted scientific world is complete.

## Manuscript use

The long-form *Epistemic Mechanics* paper uses the same release principle. Each recursive research/review pass records its marginal growth. If a pass discovers relevant prior art, a stronger counterexample, a missing theorem assumption, a new evidence root, or an unresolved mechanism, the paper reopens and the new knowledge is assimilated. Only repeated flat passes under a stable basis can support a bounded-saturation release verdict.

The manuscript is a projection of the broader project state: it need not include every RAKL object, but it must include every object required to make its own claims, proofs, evidence roles, scope boundaries and nearest-work comparisons defensible.
