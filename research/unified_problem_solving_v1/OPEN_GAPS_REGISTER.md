# Open gaps register — recursive hardening to zero

Single authoritative TODO consolidating every unresolved finding from the hostile
math audit (15 findings), hostile engineering audit (18 findings), and closure
ledger. Fixed items move to the DONE section with their regression test. Goal state:
this register is empty except DONE, and a fresh hostile audit of the fixed surfaces
finds nothing new (two consecutive clean audit rounds = hardened).

## P0 — soundness (wrong results possible)
- [ ] MATH U1–U6: per HOSTILE_MATH_AUDIT.md — trace-quotient context-binding (U1),
      coverage-certificate ↔ edge-set hash binding + mutation invalidation (U4),
      REFUTES-blind assembly gate + REDUCES_TO direction (U5), and U2/U3/U6 as filed.
      STATUS: fix agent in flight; verify its report, keep its regression tests.
- [ ] ENG: NaN cost passes guards and WINS explicit_lexicographic_select — require
      isfinite in PathCostVector and selection (regression: NaN option must raise).
- [ ] ENG: committed path_quotient_savings.json is stale vs hardened API (4/6 spot
      failures at k=4,p=1.0) — re-run path_quotient_experiment.py against HEAD, recommit
      artifact + plot, and add the experiment to the hardening workflow.

## P1 — ill-posed / adopter-breaking
- [ ] MATH I1–I6 per audit (incl. certificate/runtime-object binding residuals I5).
- [ ] ENG: phase1_v2.py crashes under git-archive zips (git rev-parse assumption) —
      fall back to "UNKNOWN" sha instead of crashing.
- [ ] ENG: operational_map add_edge quadratic (8k edges = 2.36 s) — index adjacency.
- [ ] ENG: no worked quickstart for the 8 unified mechanics (adopter surface) — add
      examples/unified_solver_quickstart.py exercising all mechanics end-to-end.

## P2 — overclaim / CI drift
- [ ] MATH O1–O2: paper text stronger than code — align P05 §11 / P06 §10c wording.
- [ ] ENG CI: hardening workflow compiles papers from committed per-paper figure copies
      while regenerating into paper/figures/generated with no diff gate — add a
      staleness check; make the workflow run the *experiments* whose artifacts it ships.
- [ ] ENG CI: workflow paths predate self-contained paper folders — repoint.

## P3 — open scientific coordinates (gated, not code fixes)
- [ ] Paper IV v2 A100 ladder (jobs 3489133–36) → harvest, honest terminals, finalize §phase1.
- [ ] Field CONSTRUCTION on non-metric domains (preregistered, Paper V lane).
- [ ] Cross-model comparator replication; six-family sign test (Paper II).
- [ ] Independent human review (#216); gate #462 for any positive Paper IV claim.

## DONE (with regression tests)
- [x] Generator seeding PYTHONHASHSEED-salted → sha256 (verified cross-process).
- [x] Train/probe prompt-identical leakage → prompt-level disjoint filter.
- [x] orion alias double-load / enum identity → meta-path finder (identity verified).
- [x] Trace-monoid equivalence+congruence laws → path_congruence.py + 9 property tests.
- [x] Budget-in-metric triangle violation → cost_geometry.py + counterexample test.
- [x] v1 Phase-1 instrument defects (degenerate generator; masked answer token) →
      v2 instrument + retraction in Paper IV.
