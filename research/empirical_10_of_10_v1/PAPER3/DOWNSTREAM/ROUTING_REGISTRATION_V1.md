# Paper II disjoint downstream routing study — preregistration v1

Status: `FROZEN_PRE_DEVELOPMENT_OUTCOME`

This study asks whether the applicability contract improves **actions**, not merely pair classification. It is disjoint from the four-family primary confirmatory packet and from the six-family robustness confirmatory packet.

## Scientific question

Given the same set of retrieved candidate source episodes/methods, does applicability-aware routing reduce invalid transfer while preserving useful distant transfer and target-task success relative to semantic, relational and mechanism-alignment routing?

## Frozen families and task source

Use the six robustness-extension families registered in `../OBJECTIVE/ROBUSTNESS_REGISTRATION_V1.md`. Downstream task seeds and exact instances must be disjoint from objective classification development/confirmatory items.

Development seed: `2026081221`.
Confirmatory seed and n are frozen only after development power/precision checks and before confirmatory generation.

## Episode construction

Each target episode contains an unordered candidate set with at minimum:

1. one verifier-valid but semantically distant transfer;
2. one semantically attractive applicability-invalid transfer whose derived mechanism/effect can still appear plausible;
3. one unresolved candidate requiring `CANNOT_CHECK`;
4. optional distractor(s) balanced so candidate position/ID/family cannot identify the valid choice.

The target-world verifier, not the routing policy, determines whether executing the selected transfer succeeds.

## Frozen arms

A. `SEMANTIC_TOP1`
- rank candidates by frozen surface/semantic score and execute top one.

B. `RELATIONAL_TOP1`
- rank/accept by relation/invariant projection; no applicability boundary/precondition gate.

C. `MECHANISM_TOP1`
- rank/accept by derived-effect / mechanism projection; no separately registered applicability gate.

D. `FULL_APPLICABILITY_GATE`
- semantic ranking may nominate candidates, but execute only the highest-ranked candidate licensed by the full applicability contract; skip rejected/unknown candidates.

E. `FULL_HYBRID_RECOVERY`
- same full gate, but after rejecting/abstaining on a nominated near miss, continue to the next candidate until a licensed transfer is found or the registered attempt budget is exhausted.

All deterministic arms receive the same candidate records; preprocessing/check cost is counted separately.

## Co-primary outcomes

1. target-task success rate;
2. invalid-transfer execution rate;
3. valid-distant transfer retention;
4. recovery success after a rejected semantic near miss.

Secondary:
- correct abstention on unresolved candidate sets;
- candidate attempts/checks per target;
- verifier calls;
- structural obligation evaluations;
- deterministic wall time.

No token/provider-cost claim is made for the deterministic study because no external model is invoked.

## Safety / utility criteria

The full-gate story is supported only if:

- invalid-transfer execution is lower than MECHANISM_TOP1;
- target-task success is higher than or noninferior to MECHANISM_TOP1 with registered noninferiority margin 0.02;
- valid-distant retention is no more than 0.02 below MECHANISM_TOP1;
- FULL_HYBRID_RECOVERY shows positive recovery on near-miss episodes rather than succeeding by blanket abstention;
- no family exhibits a registered catastrophic harm reversal.

## Statistical unit and inference

Independent unit = target episode. Arms share the same episode/candidate set, so primary comparisons are paired. Development determines confirmatory n from the paired success/invalid-transfer discordance structure with two-sided alpha 0.05 and target power 0.80, then n is rounded to equal family allocation.

Family-level robustness is reported separately and cannot be replaced by pooled candidate-level counts.

## Anti-degeneracy

Before confirmatory outcome access require:

- shuffled candidate order;
- opaque candidate IDs;
- semantic-validity decorrelation within family;
- a valid-distant candidate in every standard episode so always-refuse fails;
- an applicability-invalid high-semantic/mechanism candidate so always-execute fails;
- unresolved-only control episodes for abstention correctness;
- no family/item-type label exposed to routing arms.

## Claim boundary

Success supports downstream utility only in the registered generated exact-verifier routing environment. It does not establish improved real scientific research, natural-language witness extraction, independent-human validation or superiority to a frontier LLM research agent.
