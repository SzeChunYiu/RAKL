# RAKL — Claude Code entrypoint

Keep this file small. It is recurring context; the full research method is loaded on demand.

## When doing RAKL research

Use the project skill at `.claude/skills/rakl/SKILL.md`.

Do **not** preload all of `docs/`, `research/`, or the historical Self-RAKL ledger. Follow the skill router and read only the workflow/core files needed for the active atomic problem.

## Repository rules

- Scientific/model output is proposal-only until evidence/governance gates pass.
- Preserve nulls, refutations and failed generations; never rewrite negative history to make a later candidate look cleaner.
- Context/population/measurement must be aligned before contradiction or equivalence claims.
- Prediction/representation does not mint mechanism or identification authority.
- Freeze benchmarks, thresholds, candidate identity and evaluators before result access when the workflow requires it.
- Same-context or same-session critique is useful but is not independent review.
- Do not modify `docs/CONSTITUTION.md`, protected evaluator/workflow files, or promotion criteria as a shortcut to make a candidate pass.
- If current evidence is insufficient, return `BLOCKED`, `CANNOT_CHECK`, or `CANNOT_COMPILE` rather than guessing.

## Token/context policy

Prefer pointers and exact file reads over copying large histories into the chat. Query the current target/fiber first, then materialize only the relevant evidence, negative history, falsifiers and authority prerequisites.

Use the RAKL CLI/project runtime for persistent evidence and packets rather than treating conversation history as canonical memory.
