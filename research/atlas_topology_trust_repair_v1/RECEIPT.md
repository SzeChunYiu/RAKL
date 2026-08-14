# Receipt — atlas_gluing declared-topology trust repair (v1)

## Defect

`evaluate_atlas_gluing` (src/rakl/atlas_gluing.py, pre-fix lines ~463-528) trusted
caller-declared topology booleans — `cover_connected`, `cover_has_cycles`,
`cycle_basis_complete`, and cycle-witness paths — without ever recomputing them
from `trial.transitions`. A hostile atlas stripped to a single transition, with
the triangle declarations left intact, still returned
`GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY`.

Found by: P0.2 falsifiability sweep, branch `solver/gate-falsifiability-sweep-v1`
@ `928495eb` (PR #645), finding 2, frozen in
`research/solver_gate_falsifiability_sweep_v1/reproduce_insensitive_findings.py`
(`finding_2_atlas_declared_topology_trust`, reproduced with keep(A-B) and
keep(B-C)).

## Fix

At the gate, recompute the cover topology from the validated transition set
(`_recompute_cover_topology`: vertices = declared charts; one edge per distinct
(unordered chart pair, overlap_id)):

- **cover_connected**: declared `True` but recomputed disconnected →
  `CANNOT_CHECK` with `declared_topology_mismatch:cover_connected`. Declared
  `False` keeps the fail-closed `PARTIAL_ATLAS_ONLY` verdict (recomputation can
  refute an optimistic declaration but cannot verify semantic sufficiency of a
  bridge, so a pessimistic declaration is accepted).
- **cover_has_cycles**: declared value compared against the recomputed
  independent-cycle count (exact for the declared cover); either-direction
  mismatch → `CANNOT_CHECK` with `declared_topology_mismatch:cover_has_cycles`.
- **cycle witnesses**: each witness `chart_path` must be a closed walk over
  declared charts using declared transition edges; otherwise `CANNOT_CHECK`
  with `declared_topology_mismatch:cycle_witnesses`.
- **cycle_basis_complete**: witness cycles' GF(2) rank in the cover graph's
  cycle space must reach the recomputed independent-cycle count; shortfall →
  `CANNOT_CHECK` with `declared_topology_mismatch:cycle_basis_complete`. When
  parallel distinct overlaps between the same chart pair make the path→edge
  mapping ambiguous, the declaration is genuinely unrecomputable and is marked
  untrusted (`declared_topology_untrusted:cycle_basis_complete`,
  `CANNOT_CHECK`) rather than assumed true.

Mismatches produce the module's typed `CANNOT_CHECK` outcome — no silent trust,
no hard exception.

## Before / after (frozen hostile case)

| Case | Before (928495eb sweep) | After |
| --- | --- | --- |
| keep(A-B), declarations intact | `GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY` | `CANNOT_CHECK` — `('declared_topology_mismatch:cover_connected', 'declared_topology_mismatch:cover_has_cycles')` |
| keep(B-C), declarations intact | `GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY` | `CANNOT_CHECK` — `('declared_topology_mismatch:cover_connected', 'declared_topology_mismatch:cover_has_cycles')` |
| consistent triangle control | `GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY` | unchanged `GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY`, reasons tuple unchanged, no `declared_topology*` reason (no-alarm case asserted) |

Expected discriminator from the sweep handoff (GLUED → CANNOT_CHECK): confirmed.

## Test evidence

Single targeted invocation, no xdist:

```text
python3 -m pytest tests/test_atlas_gluing.py -p no:cacheprovider
============================= test session starts ==============================
platform darwin -- Python 3.13.12, pytest-8.4.2, pluggy-1.6.0
collected 28 items
tests/test_atlas_gluing.py ............................                  [100%]
============================== 28 passed in 0.15s ==============================
```

21 pre-existing tests pass unmodified (including
`test_disconnected_cover_remains_partial_atlas`, which declares
`cover_connected=False` on a syntactically connected triangle — pessimistic
declaration, fail-closed verdict preserved). 7 new hostile/control tests:

- `test_single_transition_keep_ab_contradicts_declared_topology`
- `test_single_transition_keep_bc_contradicts_declared_topology`
- `test_consistent_declarations_still_glue_without_topology_alarm` (no-alarm control)
- `test_declared_acyclic_cover_with_actual_cycles_is_cannot_check`
- `test_cycle_witness_path_outside_transition_graph_is_cannot_check`
- `test_declared_complete_cycle_basis_that_does_not_span_is_cannot_check`
- `test_parallel_overlap_edges_leave_cycle_basis_declaration_untrusted`
  (cannot-recompute path)

## Pin check

`atlas_gluing.py` is not hash-pinned: no reference in `schemas/`, no
`.github/workflows/` mention, no entry in
`docs/EVALUATOR_DEPENDENCY_PINNING.md`. `src/rakl/method_specs.py` and
`src/rakl/research_cycle.py` reference it by file path only (no content
hashes). No pins broken.

## Scope note

This is a same-context repair by the implementing session; it is analysis, not
independent scientific review. The GLUED verdict remains proposal-only; nothing
here promotes any atlas result.
