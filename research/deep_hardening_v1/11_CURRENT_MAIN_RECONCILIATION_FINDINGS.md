# Current-main reconciliation findings at the frozen base

These are findings against `main@3c24a9f78722ee5fa47ee3527e7e0e774aff91c6`, separate from defects in the old handoffs.

## C0 — open-gap register is internally inconsistent

The current `research/unified_problem_solving_v1/OPEN_GAPS_REGISTER.md` says P2 is empty / all P2 items moved to DONE, but directly below it still contains an unchecked P2 item:

```text
ENG CI: workflow paths predate self-contained paper folders — repoint.
```

The current workflow already references the self-contained Paper IV/V/VI directories, so this may be a **stale register checkbox** rather than a live workflow defect. It still violates the rule that the register is the single authoritative TODO. The receiving session should inspect the actual intended path coverage and either close the item with evidence or reopen it precisely.

## C1 — branch/release governance is not enforced by repository protection

At the observed base, GitHub reports `main` as unprotected and required status-check enforcement off. The source commit is also unsigned in the GitHub commit metadata. This does not make the code incorrect, but it weakens the claim that source/CI gates are governance-enforced rather than convention-enforced.

Recommended operational hardening:

- protect `main` with a repository ruleset;
- require the relevant hardening/full-test workflows before merge;
- disallow direct force pushes/deletion;
- require reviewed pull requests for authority/trust-manifest changes;
- use signed release tags/commits where feasible;
- preserve exact Actions SHA pins already used by current workflows.

These settings are repository governance, not something this source ZIP can safely apply.

## C2 — V3 state identity remains Python-`repr` based

Current `state_fingerprint` v1 intentionally preserves historical semantics; `state_fingerprint_v2` also hashes `repr(state)`. The correct fix is not to silently change v2. This packet adds a V3 canonical commitment for dual-write migration.

## C3 — training projection/catalog identity remains `repr` based

Current training projection uses `repr` for its catalog/snapshot hashes. This packet adds a canonical snapshot **and canonical structural-catalog** assurance digest while preserving the legacy hash.

## C4 — structural boundary/evidence ambiguity and non-preserved witness properties

Current `StructuralObject.boundary_map` is a dict comprehension but the constructor does not reject duplicate boundary keys, so contradictory duplicate boundaries can silently collapse to the last value. Relation signatures and evidence IDs are also not required unique, and witness/chart evidence can contain blank/duplicate IDs. The packet’s exact-base editor verifies Git blob `daa032e8d005e9b38e25bd9f777d9f5a5775946b` before closing these integrity gaps; `CURRENT_MAIN_STRUCTURAL_TYPE_GUARDS.patch` is included as a human-review diff.

### Non-preservation use semantics

Current `StructuralWitness` stores non-preserved properties. The basic transfer assessment tests identities, role mapping, relations, invariants, QoI and boundaries but does not reject a use merely because that use depends on a property explicitly known not to transport. This packet adds a protected use-site contract with separately resolved preservation receipts.

## C5 — old small residual packet has a packaging/test-surface defect

Its documented `PYTHONPATH=proposed_modules` setup does not expose a `rakl` package even though its tests import `rakl.*`. This packet preserves the substantive residual ideas but supersedes that package layout.

## C6 — remaining P3 items are scientific, not implementation debt

The current register keeps the v2 A100 ladder, field construction on non-metric domains, cross-model comparator replication and independent human review open. This unified packet adds further neural/VTG/cognitive-compilation scientific coordinates. None should be moved to DONE merely because their interfaces now exist.


## C7 — TCSQ has two exact-base fail-closed edge cases

At the frozen base, `QuotientValidationReport` rejects negative approximation tolerance but does not reject `NaN` or positive infinity; `NaN < 0` is false. Also, `forbidden_losses` is checked only against unconditional `erased_coordinates`, not `conditionally_erased_coordinates`. The exact-base editor verifies semantic-quotient blob `b23147c4904d2a45bc3eb7e89f16d349eb8a2991`, then closes both cases.

Separately, a passing validation report is still a data object a caller can construct. The additive `semantic_quotient_assurance.py` therefore provides the recommended production materialization path that requires a resolved verifier/replay receipt bound to the exact report, proposal, source and evidence content.

## C8 — scientific evidence lineage can be malformed

At the frozen base, a multi-node lineage cycle is not rejected by `_terminal_evidence`: traversal exits when a node repeats and returns that repeated node. Starting from different members of the same cycle can therefore produce different apparent terminal roots. An upstream ID that is never registered is also returned as though it were a terminal root. Because the authority contract uses terminal roots to detect non-independent evidence, malformed provenance must fail closed.

The exact-base editor verifies scientific-authority blob `92f45e80863f6a2b6437ce3342619c1e788da2ce`, replaces terminal traversal with cycle/unresolved-parent detection, and adds full-repository regressions.

## C9 — integration needs one epoch-level composition receipt

The framework now has many deliberately separate typed planes. That separation is correct, but it creates a cross-module risk: valid objects can still be combined from different base commits, subjects or unresolved receipt sets. `unified_integration_contract.py` adds a non-authoritative manifest/readiness gate for one experiment/integration epoch. It does **not** flatten the authority domains.
