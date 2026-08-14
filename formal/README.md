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
- **No axioms.** Every mechanized theorem reports `does not depend on any axioms` —
  fully constructive, no classical choice, no `propext`/`funext`.

What is *not* here: the finite-basis cardinality bound (needs a finiteness development),
and 11 of Paper I's 17 theorem-like claims, which remain `UNREVIEWED`. Mechanization
reduces the external formal-review obligation (issue #216); it does not discharge it.
