# Independent review protocol

This protocol adapts `Yuan1z0825/nature-skills`, `skills/nature-reviewer/SKILL.md`, source commit `1ea82ffff20f40077bf84b74182f55eeaf3d111d`, to mathematical discovery.

## Frozen packet

Before review, freeze one immutable packet containing only:

- candidate identifier and hashes;
- exact theorem statement and definitions;
- assumptions and allowed parent results;
- proof artifact or informal proof manuscript;
- proof-DAG dependency list;
- verifier receipts already available;
- claimed novelty and significance, if any;
- known failed branches relevant to the candidate.

Do not include a shared concern ledger or hints from an earlier reviewer.

## Three-review rule

Generate exactly three reports in genuinely separate contexts/invocations when possible, each receiving the same frozen packet and only a predeclared emphasis lens.

- **Lens A — logical soundness**. Quantifiers, reductions, hidden assumptions, circularity, edge cases, theorem-to-root binding.
- **Lens B — complexity/barrier audit**. Relativization, natural-proofs, algebrization, uniformity/nonuniformity, reduction direction, asymptotics.
- **Lens C — novelty and mathematical value**. Prior-art equivalence, stronger parent results, usefulness of the claimed lemma, whether the claimed advance actually moves the root obstruction.

A report generated in a shared context is same-context critique, not independent review, and must be labeled as such.

## Report fields

Every major concern has a stable ID and contains:

- claim pointer;
- evidence/proof pointer;
- blocking yes/no;
- exact concern;
- why it matters;
- resolution test.

Each report is frozen before another report is shown to it. Only then may a fourth pass synthesize consensus and disagreement.

## Root rule

No amount of reviewer enthusiasm creates proof authority. Review can block or contextualize promotion, but only an exact proof certificate can mint theorem authority.
