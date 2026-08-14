# Machine-checked core of Paper I

Lean 4, **no mathlib** — builds in seconds, no cache, no network beyond the toolchain.

```bash
cd formal && lean RaklFormal.lean    # exit 0 == all proofs accepted
```

Status per claim lives in `../research/paper1_formal_closure/theorem_inventory.json`.
`MECHANIZED` there is the only reviewer-independent status in the inventory: a proof
accepted by the Lean kernel does not rest on the judgement of whoever wrote it.

Two properties are checked in CI and worth stating explicitly:

- **The build can fail.** A deliberately false lemma is rejected by the kernel. A green
  check that could never go red would be worthless.
- **No axioms.** *Every* theorem in the file reports `does not depend on any axioms` —
  fully constructive, no classical choice, no `propext`/`funext`. The audit covers all
  of them, not a selected subset, so a theorem cannot be added without being audited.

A note on `decide`: it is safe for the Bool/Nat decisions used here, but the core
`Decidable` instance for **list membership** routes through `propext`. One such leak was
caught by the audit during this pass and replaced with an explicit membership term.

What is *not* here: the finite-basis cardinality bound (needs a finiteness development),
and greedy optimality (`03_workspace.tex:48`), which has been read line by line with no
gap found but is not machine-checked. No claim is `UNREVIEWED`. Mechanization reduces the
external formal-review obligation (issue #216); it does not discharge it, and nothing in
this directory is independent review.
