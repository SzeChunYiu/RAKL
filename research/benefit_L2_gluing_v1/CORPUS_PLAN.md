# CORPUS_PLAN — BENEFIT-L2-GLUING-V1

Status: frozen construction procedure. No corpus has been generated; no labels exist
beyond the NON-EVIDENTIAL worked example at the bottom of this file.

## Reuse decision

CONSTRUCT. Scan of `research/`, `src/`, `tests/` (2026-08-14, greps for
`wrong_gluing`, `gluing corpus`, `parity corpus`) found no labeled atlas-gluing
corpus. `tests/test_atlas_gluing.py` holds unit fixtures (including the P0.2 hostile
declared-topology cases); `formal/RaklFormal.lean` proves the construction but binds
no measured data; `research/framework_ladder/ladder.json` registers the
wrong-gluing-rate observable but binds no data.

## Generator (known-answer world; no network)

A seeded parametric generator (`--seed`, single `random.Random` stream) samples
constraint covers and renders atlas instances. Ground truth (global realizability) is
computed EXACTLY at generation time by exhaustive assignment search over the hidden
world's constraint structure (≤ 6 binary variables, ≤ 64 assignments) — before any
rendering, before any arm exists in the process.

1. **Hidden world.** A cover of 3–6 charts over 3–6 binary variables. Each chart
   constrains 2–3 variables via an allowed-assignment table. Overlaps are the shared
   variables of chart pairs; each cover's overlap graph is generated without parallel
   overlap edges (one distinct overlap per chart pair), so cycle-basis completeness
   is exactly recomputable — matching the repaired `atlas_gluing` semantics
   (`research/atlas_topology_trust_repair_v1/RECEIPT.md`). Surface identities
   (variable names, chart names, value labels) are seeded-permuted at rendering so
   surface form carries no class signal.
2. **Atlas sampling by class** (composition frozen in PROTOCOL.json, N=400):
   - **G1 (100)** GLUEABLE_ACYCLIC: tree covers (no cycles), globally satisfiable.
     Gold: GLUEABLE. (No-alarm floor rows for both arms.)
   - **G2 (100)** GLUEABLE_CYCLIC_TWINS: cyclic covers, all cycle holonomies
     consistent, globally satisfiable. Gold: GLUEABLE. Constructed as the exact
     pairwise twins of G3 (60 rows) and G4 (40 rows): each G2 row is the
     `consistentCover`-family member whose canonical pairwise record (transitions +
     overlap restrictions) is byte-identical to its parity twin's. This
     materializes Lean `covers_agree_on_pairwise_data`.
   - **G3 (60)** PARITY_OBSTRUCTION_K3: the mechanized three-context parity
     construction (`ParityObstruction` in formal/RaklFormal.lean; Paper I
     02_compatibility_authority.tex:64): three charts XY/YZ/XZ, agreement on two
     overlaps, disagreement on the third; every overlap restriction is total
     (`parity_restrictions_are_total`), so all pairwise checks pass; no global
     section (`parity_charts_have_no_global_section`). Gold: NOT_GLUEABLE.
     `twin_id` names the G2 twin.
   - **G4 (40)** PARITY_OBSTRUCTION_K4_TO_K6: generalized parity cycles of length
     4–6 with an odd number of disagreement edges — pairwise-total restrictions,
     consistent-looking overlaps, no global section. Prevents the measurement from
     overfitting to the k=3 instance. Gold: NOT_GLUEABLE. `twin_id` names the even-
     parity G2 twin.
   - **G5 (60)** PAIRWISE_INCOMPATIBLE: one overlap genuinely conflicts (the shared
     variable's restrictions are disjoint), so even the pairwise record shows a
     failure. Gold: NOT_GLUEABLE. (Arm A's no-alarm rows: the pairwise baseline
     must refuse these, keeping it an honest baseline rather than a straw man.)
   - **G6 (40)** GLUEABLE_OBSTRUCTION_RECORD_INCOMPLETE: as G1/G2 in the world
     (genuinely glueable), but the rendered record omits one cycle-witness
     `evidence_ids` entry — a field ONLY the obstruction arm reads. Gold: GLUEABLE.
     (Charges arm B's fail-closed refusal; the incompleteness never touches
     pairwise fields, so arm A is unaffected by construction.)
3. **Rendering.** Machine fields per row: `charts`, `variables`, `transitions`
   (chart pair, `overlap_id`, `pairwise_pass`, `fields_complete_pairwise`,
   `overlap_restrictions` — the projections of the constraint tables onto shared
   variables, i.e. exactly what a pairwise record retains), `constraint_tables`
   (full per-chart allowed assignments — the global data a pairwise-only
   representation discards), `cycle_witnesses` (one per independent cycle;
   `composition_consistent` reflects the world's holonomy), `twin_id`, plus a
   deterministic `surface_text` description. Arm A reads `transitions` only; all
   other fields are present in its input and deliberately ignored.
4. **Rendering-faithfulness check** (generation-time, pre-freeze): the rendered
   `constraint_tables` must have the same exact satisfiability as the hidden world,
   and every twin pair's canonical pairwise records must be byte-identical. Any
   violation drops the row and redraws. The evaluator re-verifies both at run time
   (CANNOT_CHECK on violation).
5. **Record schema.** `atlas_id`, `class`, `gold_label`, `label_minted_at` (UTC ISO,
   written at generation), machine fields above, `world_id`, `generator_seed`.
6. **Freeze.** Corpus JSON is sha256-hashed and entered into the RSHEA receipt chain
   (`process_telemetry_to_receipts`) BEFORE any arm executes. Arm harnesses receive a
   gold-stripped copy. EVALUATOR.py enforces label-before-arm chronology, the
   arm-rule drift checks, and the twin bound.

## Label-independence safeguards

- Gold = exact satisfiability of the hidden world, computed at generation time. No
  arm, LLM, or human prediction participates. (Structural counter to the L6-gate
  defect.)
- **No LLM labeling.** If an LLM is later used at all, it may only paraphrase
  `surface_text`; it never sees or writes `gold_label`, `constraint_tables`,
  `cycle_witnesses`, `twin_id`, or `class`, and every paraphrase is re-checked by an
  exact-match guard. Any violation drops the row.
- **Human/oracle audit.** 40 atlases (10%) sampled by seed. The auditor sees only the
  rendered atlas description + the gold label — never arm outputs
  (`auditor_saw_arm_outputs: false` in the audit receipt). Disagreement ≥ 0.05 ⇒
  CANNOT_CHECK for the whole run.

## A-priori expectations (deterministic arms; recorded to make the design honest)

Arm A (pairwise-only) accepts G1, G2, G3, G4, G6 and refuses G5:
WGR_A = 100/400 = 0.25, GCA_A = 1.0. Arm B accepts G1, G2 and refuses G3, G4
(obstructed), G5 (pairwise reject), G6 (incomplete record): WGR_B = 0.00,
GCA_B = 200/240 ≈ 0.83 — above the frozen 0.70 floor by design. On the 100 twin
pairs the pairwise arm errs exactly once per pair (wrong gluing on the parity row),
which is the theorem's floor realized as data. These are expectations, not results;
the run certifies them under randomized realization together with the nulls and
receipts.

## Worked example — NON-EVIDENTIAL (illustration only, not corpus rows, not labels)

| class | cover (gist) | world fact | gold |
|---|---|---|---|
| G2 | XY: x=y; YZ: y=z; XZ: x=z (triangle) | all holonomies consistent; x=y=z solves it | GLUEABLE |
| G3 | XY: x=y; YZ: y=z; XZ: x≠z (triangle) | pairwise record identical to the row above; no assignment satisfies all three | NOT_GLUEABLE |
| G4 | 5-cycle with one disagreement edge | odd parity around the cycle; no global section | NOT_GLUEABLE |
| G5 | overlap on y demands y=0 in one chart, y=1 in the other | pairwise conflict visible locally | NOT_GLUEABLE |
| G6 | solvable triangle; cycle witness present but its evidence field empty | genuinely glueable; obstruction record incomplete | GLUEABLE |

These five rows carry zero evidential weight; the real corpus is generated, hashed,
and receipted only in the execution run.
