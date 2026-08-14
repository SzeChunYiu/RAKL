# CORPUS_PLAN — BENEFIT-L4-NAVIGATION-V1

Status: frozen construction procedure. No corpus has been generated; no labels exist
beyond the NON-EVIDENTIAL worked example at the bottom of this file.

## Reuse decision

CONSTRUCT. Scan of `research/`, `src/`, `tests/` (2026-08-14, greps for
`navigation corpus`, `solve rate`, `support corpus`) found no labeled matched-budget
solve corpus. `research/navigation_dynamics_parallel_v1/` is a dynamics study with
rounds/results, not a gold-labeled budget-matched population;
`src/rakl/backward_multiseed_benchmark.py` is a different benchmark family;
`tests/test_support_solver.py`-style unit fixtures bind no corpus to the L4
observable.

## Generator (known-answer world; no network)

A seeded parametric generator (`--seed`, single `random.Random` stream) samples hidden
support hypergraphs and scatters them across rendered source pools. Ground truth
lives in the hidden world, not in any arm's decision rule.

1. **Hidden world.** 8–14 atoms; a designated start atom and goal atom; typed edges
   with cost and licensing layer; 0–2 obstruction covers (sets of atoms pairwise fine
   and jointly unrealizable — the datum a pairwise-only distillation drops); a target
   contract (required authority, description tokens drawn from a seeded lexicon).
   The admissible route (when one exists) needs h hops; h per class below.
2. **Source pool.** 8–16 sources. Each on-path source carries 1–3 true facts (edges,
   sometimes an obstruction declaration); distractor sources carry real but
   off-path edges or nothing relevant. Each source renders `index_tokens`
   (atom ids it mentions + lexicon tokens) visible to BOTH arms before payment, and
   its full typed content only after read (arm A, cost 1.0) or distillation
   (arm B, cost 2.0). Mid-chain sources are "buried": their index tokens share
   little with the target description; distractor sources are engineered to share
   much (the lexical trap that makes greedy raw reading hard and both arms' first
   pick honest).
3. **Budgets.** S* = exact minimal covering source count (minimal set cover of an
   admissible route's facts, computed exactly at generation). Budget classes:
   TIGHT = 2·S*, MEDIUM = 4·S*, LOOSE = 8·S* budget units (frozen in PROTOCOL.json).
4. **World sampling by class** (composition frozen in PROTOCOL.json, N=400):
   - **N1 (120)** DEEP_CHAIN_MEDIUM: h ∈ 3..5, buried mid-chain, MEDIUM budget.
     Gold: SOLVABLE. (Primary class.)
   - **N2 (60)** DEEP_CHAIN_TIGHT: as N1 at TIGHT budget. Gold: SOLVABLE.
     (Honest-cost class; outside the PROMOTE scope — distillation cannot amortize.)
   - **N3 (60)** DEEP_CHAIN_LOOSE: as N1 at LOOSE budget. Gold: SOLVABLE.
     (Non-inferiority gate: the claim must not invert when budget stops binding.)
   - **N4 (40)** SHALLOW_SINGLE_HOP_MEDIUM: h = 1, S* = 1, the one source is
     lexically obvious. Gold: SOLVABLE. (SFH floor class: charges arm B's 2×
     overhead where navigation cannot pay off.)
   - **N5 (60)** DISTRACTOR_HEAVY_MEDIUM: as N1 with distractor sources engineered
     to outrank every on-path source lexically. Gold: SOLVABLE. (Mechanism stress.)
   - **N6 (30)** OBSTRUCTED_DECOY_MEDIUM: the lexically obvious route realizes an
     obstruction cover; an alternative admissible route exists. Gold: SOLVABLE.
     (Only obstruction-aware navigation avoids wasting budget on the decoy.)
   - **N7 (30)** UNSOLVABLE_MEDIUM: no admissible route exists (goal disconnected,
     or every structural route under-licensed or obstructed). Gold: UNSOLVABLE.
     (False-solve guard rows; correct behavior is NOT_SOLVED.)
5. **Record schema.** `world_id`, `class`, `budget_class`, `budget_units`,
   `gold_label`, `label_minted_at` (UTC ISO, written at generation), `target`
   {start_atom, goal_atom, required_authority, description_tokens}, `sources`
   [{source_id, index_tokens, edges, obstructions}], `minimal_source_count`,
   `generator_seed`. A rendering-faithfulness check re-verifies at generation that
   the union of rendered facts reproduces the hidden world's solvability; a
   mismatch drops the row before freeze.
6. **Freeze.** Corpus JSON is sha256-hashed and entered into the RSHEA receipt chain
   (`process_telemetry_to_receipts`) BEFORE any arm executes. Arm harnesses receive
   a copy stripped of `gold_label` and `minimal_source_count`. EVALUATOR.py enforces
   label-before-arm chronology and the arm-policy drift checks.

## Label-independence safeguards

- Gold = pure function of the hidden world at generation time (exact route search
  over the full fact set). No arm, LLM, or human prediction participates.
- **No LLM labeling.** If an LLM is later used at all, it may only paraphrase
  surface renderings; it never sees or writes `gold_label`, `edges`,
  `obstructions`, or `minimal_source_count`, and an exact-match guard verifies atom
  ids survive verbatim. Any violation drops the row.
- **Human/oracle audit.** 40 worlds (10%) sampled by seed. The auditor sees only the
  rendered world description + the gold label — never arm outputs
  (`auditor_saw_arm_outputs: false`). Disagreement ≥ 0.05 ⇒ CANNOT_CHECK.

## A-priori expectations (deterministic arms; recorded to make the design honest)

At MEDIUM budget on deep chains, arm A's lexical order spends most of its 4·S* reads
on high-overlap distractors before reaching buried mid-chain sources; arm B spends
2·S* units re-buying its first lexical mistake, then frontier/repair guidance selects
on-path sources directly. Directionally SR_B > SR_A on N1/N5/N6, SR_B ≈ SR_A on N3
(both should saturate), SR_B < SR_A likely on N2, and SR_B slightly below SR_A on N4
is priced by the 0.70 floor (B solves single-hop worlds whenever budget ≥ 2, which
MEDIUM guarantees, so the floor is expected to hold with margin). FSR expected 0 for
both deterministic arms. These are expectations, not results; exact magnitudes,
nulls, and receipts are what the run certifies.

## Worked example — NON-EVIDENTIAL (illustration only, not corpus rows, not labels)

| class | world (rendered gist) | world fact | gold |
|---|---|---|---|
| N1 | 4-hop chain a0→…→a4 across 4 buried sources, 8 distractors, budget 4·S* | admissible route exists at authority 2 | SOLVABLE |
| N2 | same family at budget 2·S* | route exists; zero-waste acquisition required | SOLVABLE |
| N4 | single source carries a0→a1, index tokens match target | one-hop solve | SOLVABLE |
| N6 | obvious route realizes obstruction {a1,a2,a5}; detour via a6 admissible | decoy cover jointly unrealizable | SOLVABLE |
| N7 | every structural route contains an edge licensed below demand | no admissible route | UNSOLVABLE |

These five rows carry zero evidential weight; the real corpus is generated, hashed,
and receipted only in the execution run.
