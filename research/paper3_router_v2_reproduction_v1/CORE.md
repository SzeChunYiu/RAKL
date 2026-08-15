# Router v2 reconstruction — Paper III, 21 families / 2,688 cases

**Terminal: `PARTIALLY_CORROBORATED` — manuscript correction required.**
Read-first index. Machine record: [`RECONSTRUCTION_RECEIPT.json`](RECONSTRUCTION_RECEIPT.json).
Pre-execution freeze: [`PRE_EXECUTION_FREEZE.json`](PRE_EXECUTION_FREEZE.json). Case set: `CASES.jsonl` (2,688 rows).

Negative addressed: `research/negative_frontier_v1/NEG-p3-router-v2-unreproducible.md`.
Nothing here *re*-produces anything — no artifact ever generated the quoted numbers. This is
what a faithful reconstruction under the frozen protocol measures.

## Prose vs measured

| quantity | prose | measured | agrees |
|---|---|---|---|
| `n_cases` / `n_families` | 2688 / 21 | 2688 / 21 | yes |
| `route_plus_negative_trace_exact` | 1.0 | 1.0 | yes |
| `unsafe_route_rate` | 0.0 | 0.0 | yes |
| `cannot_check_recall` | 1.0 | 1.0 | yes |
| `viable_route_recall` | 1.0 | 1.0 | yes |
| `hostile_mutations_caught` | 12/12 | 12/12 | yes |
| **composite parent information ceiling** | **0.6190476 (=13/21)** | **0.5610119** | **no** |
| **composite parent unsafe rate** | **0.3095238 (=13/42)** | **0.2187500** | **no** |

The six that agree are the counts and the four ceiling-pinned metrics. The two that carry
variance do not agree, and they are the two a reconstruction cannot pin down: they are
properties of the parent projection over *this* case set. Their quoted values stay unbacked.
Resubstitution ceiling is 0.671875, also not 13/21 — the disagreement is not a definition artifact.

## Severance (the whole point)

Gold = **generator design intent**, committed per family at construction, never recomputed from
the record. The candidate receives `candidate_view(case)`: gold, family and case id are
structurally absent. Audited by AST scan before execution (`severance_audit`, exits non-zero on
failure); no probe may target a gold field. An independent declarative *oracle* was rejected as
the gold source — it computes the same function as the candidate, so exact accuracy would hold
1.0 under every perturbation, which is exactly the sibling harness's defect.

## Can the gate fail? Yes — all six conditions

| registered condition | falsifiable | moved in isolation by |
|---|---|---|
| `strict_exact` | yes | `AUDIT_TRACE_ONLY_DROP` (proves the "+negative trace" half is load-bearing) |
| `strict_unsafe` | yes | `AUDIT_SWAP_SEARCH_FOR_JUMP` (moves unsafe, not CANNOT_CHECK recall) |
| `strict_cannot_check_recall` | yes | **never in isolation** — see below |
| `strict_legal_route_recall` | yes | `AUDIT_DOWNGRADE_VIABLE_ROUTES` (fail-closed, leaves unsafe at 0) |
| `composite_information_ceiling` | yes | evidence only: `keep_only_ALL_STRUCTURAL_REJECTED_LIFT` |
| `all_mutations_caught` | yes | evidence only: `drop_sole_catcher_of_*` (7 mutations have one catcher) |

All 12 registered mutations are caught (`FAIL_WITHOUT_TYPED_REJECTION` by 4 families,
`DROP_NEGATIVE_HISTORY` by 7, seven mutations by exactly one). Every strict condition is
`SENSITIVE 8/8` to four separate evidence shuffles and to full randomisation.

Two honest limits, both declared in the freeze before execution:
- `cannot_check_recall` cannot fail unless `unsafe` also fails — a CANNOT_CHECK miss *is* an
  unauthorised route. Reported as **structurally implied, not degenerate**: it is moved by
  evidence perturbation, unlike the sibling harness where it could not move at all.
- No candidate mutant can move `composite_information_ceiling`; it is a parent-projection
  property. Its falsifier is necessarily an evidence perturbation, and one was found.

**The audit's structural prediction is refuted.** `UNREPRODUCIBLE_V2_RESULT.json` predicted this
instrument shares the sibling's self-grading defect ("four thresholds at ceilings its metrics
could not leave"). With gold severed, the thresholds sit at ceilings *and the metrics leave them*.
The prediction was recorded so it could be checked; it has been, and it does not hold.

## Second unbacked claim found

The manuscript's "the failed first validation instrument for this plane is separately preserved"
is also unbacked. Only the terminal string `INSTRUMENT_DEFECT_TWO_MUTATIONS_NOT_EXERCISED`
survives, in `PROTOCOL_FREEZE.json` and three audit files. Scope: basename `find` for
`*validation_v1*` and for any `paper3_publication_validation*` directory (only `_v2` exists);
`git log --all -S` on the token returns four commits, none adding a routing instrument;
`git grep -l` returns four files, all v2 protocol/audit metadata.

## Manuscript correction

`publication/papers/paper-03-method-evolution-mechanics/sections/04b_obstruction_transformation_memory.tex`
— rewritten in this branch. Preserves the CANNOT_CHECK history verbatim, adds the reconstruction
and its measured values, states the two disagreements, records the refuted prediction, and
corrects the preservation claim. Scope unchanged: generated structured state, not model efficacy;
production conformance remains the exact-head test surface. Grants no scientific authority.
