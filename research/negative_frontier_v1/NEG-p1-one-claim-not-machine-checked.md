# `one of eighteen numbered formal claims is NOT machine-checked (Lean covers 17/18)`

**Paper:** I  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** no

## Where the manuscript states it

- `publication/papers/paper-01-epistemic-mechanics/sections/03_workspace.tex:61`
- `publication/papers/paper-01-epistemic-mechanics/sections/06_appendices.tex:173`

## Receipt

- **`receipt_path`:** `research/paper1_formal_closure/theorem_inventory.json` — **verified present**
- supporting: `RaklFormal.lean (Lean 4, toolchain 4.14.0, cited in 06_appendices.tex:173)`

## What happened

The artifact's Lean 4 development machine-checks seventeen of the paper's eighteen numbered formal claims in full. The exception is the workspace top-k optimality theorem. Its INGREDIENTS are machine-checked -- the exchange step (swapping a selected item for an unselected one of at least equal utility never decreases the objective), the availability of a swap partner derived from feasibility rather than asserted, and top-k optimality against a tie-safe predicate quantifying over ANY maximal r_p-subset, which repairs the tie-ambiguity in the phrase 'the top r_p candidates'. The ASSEMBLY of those ingredients into the stated theorem is not machine-checked; that theorem's status rests on the paper proof. The mechanized statements also encode utilities as naturals, so they cover a non-negative special case of the real-valued statement.

## One-stage attribution

licence. The formal-verification licence stops one level below the stated claim: ingredients are discharged by the kernel, the composition is not.

## Lever

Assemble the three checked ingredients into the stated optimality theorem in Lean, and generalize the utility encoding from naturals to reals (or state the theorem over naturals). Both are ordinary Lean work against an existing development; no new mathematics is implied by the manuscript.

## Class justification

Lean 4 toolchain 4.14.0 runs locally and deterministically; the missing step is composition of already-checked lemmas plus a numeric-domain generalization.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
