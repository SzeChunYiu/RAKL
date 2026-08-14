# ORION / RAKL_SOLVER architecture establishment audit — v1

Status: **point-in-time status artifact** (2026-08-14, branch wip-623 @ 74a5fe61).
Same-context analysis, **not independent review**. Grants no authority. Verdicts here
upgrade nothing; preserved negatives cited below remain immutable.

## Object

The target architecture carves the system as ORION (meta-operator, 8 capabilities)
operating RAKL_SOLVER (11 pipeline steps). This audit grades each of the 19 nodes on
five coordinates mirroring `research/framework_ladder/ladder.json`'s non-compensatory
readiness policy: MATH (spec + mechanization), MECHANICS (modules + tests), GATES
(falsifiable + audited), BENEFIT (measured vs baseline), VERDICT.

**Global constraint on every verdict:** `research/mechanism_benefit_ledger/ledger.json`
records ZERO demonstrated benefits across Papers I–VI; all 8 ladder layers have
`benefit_measured=false`; the computed frontier is **L0**. Under the non-compensatory
rule, full ESTABLISHED is unreachable for every node until benefit obligations run.
Verdicts below therefore grade the other four coordinates honestly.

Mechanization home: `formal/RaklFormal.lean` (Lean 4, no mathlib, zero axioms;
17 claims MECHANIZED, 1 PAPER_PROOF_COMPLETE per
`research/paper1_formal_closure/theorem_inventory.json`). `~/orion-lean` /
`scripts/orion_saturation` are LUNARC-side or worktree-local, not canonical here.

## RAKL_SOLVER unit (11 steps)

| # | Step | Verdict | Math | Load-bearing mechanics | Gate status |
|---|------|---------|------|------------------------|-------------|
| 1 | problem contract | IMPLEMENTED_UNPROVEN | FSS §2, §8 (τ); no Lean | invention(PositiveGoalContract), hard_gates, framework_candidate_freeze, math_context, problem_fibre | freeze-before-result structural; NOT_AUDITED |
| 2 | decomposition | IMPLEMENTED_UNPROVEN | FSS §8 fibers; no Lean | recursive_solver, problem_fibre, tree, problem_solving_algebra | no audited decomposition-quality gate |
| 3 | structuralization | **FRAGMENTED** | FSS §3.x; reduction operator deliberately unformalized | structure_space, structural_types, semantic_shortcut, measurement | **no reduction-fidelity gate at all** |
| 4 | knowledge/solution space | IMPLEMENTED_UNPROVEN | FSS §11; 2 Lean thms | structure_space, typed_lattice, atlas_gluing, content_addressed_archive, multires_memory | invariants coded; NOT_AUDITED |
| 5 | saturation | IMPLEMENTED_UNPROVEN | FSS §12; 2 Lean thms — best math coverage | epistemic_saturation, saturation, saturation_vector, identity_saturation | **only solver gate audited FALSIFIABLE** |
| 6 | structural retrieval | IMPLEMENTED_UNPROVEN | workflow §G; no Lean | semantic_shortcut (+routers v1–v3), obstruction_transformation_corpus, retrieval_benchmark | LIFT invariants coded; NOT_AUDITED |
| 7 | mapping/transport | **GAP** | FSS §3.1–3.2; no Lean | structural_transport_v2, structural_transfer, generator_transport, authority_transport, applicability | **FAIL_OPEN live**: `structural_transport_v2.py:343-355` LICENSED with zero reasons on empty obligations; only worked around in `structure_space.match` |
| 8 | composition | IMPLEMENTED_UNPROVEN | FSS §5; 4 Lean thms — strongest Lean | structure_space.compose, bridge_composition, solution_assembly, quantifier/summation_compatibility, **derivation (untracked)** | obstruction-refusal + no-alarm control; NOT_AUDITED |
| 9 | navigation | IMPLEMENTED_UNPROVEN | FSS §8; greedy optimality PAPER_PROOF only | support_solver, navigation_dynamics/successor/parallel, backward_multiseed, epistemic_search | NOT_AUDITED; dynamics-vs-A* measured NEGATIVE preserved (#519) |
| 10 | verification | IMPLEMENTED_UNPROVEN | FSS §7/§18/§19; bulk of RaklFormal.lean | hard_gates, gate_falsifiability, formal/math_oracles, math_research_assurance, evidence_binding_certificate | auditor works; sweep coverage ~1/11 |
| 11 | residual/trajectory | IMPLEMENTED_UNPROVEN | FSS §8 ρ(r,K_t); 1 Lean thm | support_solver(EpistemicCut), epistemic_trajectory, diagnosis_state_machine, failure_lattice, route_family_health | trajectory evaluator fail-closed; NOT_AUDITED |

Untracked on wip-623: `src/rakl/derivation.py` + `tests/test_derivation.py` — AND-composition
(hyperedge forward closure) over the support hypergraph; closes the multi-premise hole
(support_solver was OR-routes only); re-derives a RaklFormal.lean theorem mechanically from
its dependency graph with a no-alarm underivability control. UNIT_TESTED level; uncommitted.

## ORION unit (8 capabilities)

| # | Capability | Verdict | Key evidence |
|---|-----------|---------|--------------|
| 1 | persistent episode memory | **FRAGMENTED** | strong in-process contracts (experience_substrate, episode_admission); **no durable cross-session episode store**; P7 persists controller epoch+MetricLedger only; de facto record = 146 hand-curated SELF_RAKL receipts |
| 2 | cross-episode failure/success analysis | IMPLEMENTED_UNPROVEN | failure_lattice, research_memory (dual-memory), research_tool_inventory; model-level experience negative preserved |
| 3 | lesson learning | IMPLEMENTED_UNPROVEN | experience_learning, driver_learning; **defect: `shuffle_lesson_verified` probe INSENSITIVE in all audited conditions** — lesson verification decorative in the audited P3 gate |
| 4 | policy learning | IMPLEMENTED_UNPROVEN | search_policy_learning, experience_policy; best-evidenced row: honest measured NEGATIVE (P4 adaptive default revoked; instrument upper bound +0.0246 vs frozen 0.05 gate) |
| 5 | operator acquisition | IMPLEMENTED_UNPROVEN | missing_operator, assimilation, external_agent_registry; sole claimed L7 transfer instance exists only as a ladder.json line — receipt CANNOT_CHECK by ID |
| 6 | challenger evaluation | IMPLEMENTED_UNPROVEN | parent_evaluator, challenge_learning, self_bootstrap; **L6 gates NON_FALSIFIABLE 4/6** (gold label = prediction; thresholds at ceilings); falsifiability auditor itself works |
| 7 | promotion/rollback | **ESTABLISHED** (engineering authority only) | promotion+attestation, governed_intervention, evolution_archive rollback targets; exercised end-to-end in anger: P3 promoted, P4 revoked |
| 8 | self-evolution | IMPLEMENTED_UNPROVEN | full governed pipeline (evolution*, self_hosting_*, meta/shadow_controller); benefit ZERO — MECH-METHOD-EVOLUTION lift NOT_ATTEMPTED, "single largest benefit gap in the programme"; Paper VI 3.31x self-retracted as circular |

RSHEA (P2–P7) coverage: it is the **governance spine, not the learning substance** —
covers promotion (P5), shadow challenger evaluation (P3), controller-state persistence (P7),
telemetry/reporting (P2/P6). Not covered: lesson learning, policy learning, operator
acquisition, episode-level memory. ORION operating loop: `docs/HOURLY_SELF_RND.md` is
doc-only (zero in-repo wiring); `docs/design/orion_mechanics_multiscale_plan/` is
proposal-only, explicitly isolated 2026-08-13.

## Ranked gaps (merged, cross-unit)

1. **Benefit column empty for all 19 nodes** — non-compensatory frontier sits at L0; no node can be ESTABLISHED until obligations run in ladder order.
2. **Transport gate fails open (solver's only GAP verdict)** — `assess_transfer_v2` LICENSED-with-zero-reasons still live; call-site workaround is not a fix; any benefit measured through it is uninterpretable.
3. **Falsifiability audit coverage ~1/11 solver gates; L6 4/6 NON_FALSIFIABLE** — battery exists and has teeth; sweep never completed; registered independent-oracle P3 successor not executed.
4. **No durable episode store** (ORION cap 1) and **structuralization fidelity ungated** (solver step 3) — one hole per unit, both load-bearing for everything downstream.
5. **Core verbs are days old or uncommitted** — support_solver (navigation) is very recent; AND-composition exists only as untracked files; retrieval router carries v1→v3 churn; ORION loop unwired.

## What must NOT be promoted from this artifact

- No verdict upgrades any claim's authority; absence claims are scoped to the searches run.
- IMPLEMENTED_UNPROVEN ≠ "works": every benefit obligation is open.
- The derivation.py demonstration is UNIT_TESTED level, not a measured benefit.
- The structure_space workaround must not be recorded as the transport fail-open fix.
- Preserved negatives (P4 adaptive REFUTED, Paper VI retraction, #519 navigation negative, L6 NON_FALSIFIABLE) remain immutable through all gap-closure work.
