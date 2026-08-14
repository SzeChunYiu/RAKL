# Evaluator Integrity Merge-Order Incident (PR #710)

Status: incident record + binding process correction
Date: 2026-08-15

## What happened

PR #710 (branch head `94841693f7a27bc69f248d03434acfcf5eadd970`,
"registry: apply round004 amendments and move drift anchor to 3f472e6d")
was squash-merged to main as `5a092c08396a51fe3cc3c826b67de52f89eebe0b`
at 2026-08-14T22:55:29Z. The trusted-parent-evaluator verdict for that
candidate concluded only after the merge:

- PR #710's `test` workflow completed at 22:58:31Z — three minutes
  post-merge, because the single serial self-hosted runner was still
  draining the concurrent #706/#707 queue.
- Its completion fired `trusted-parent-evaluator` run `31848662490`
  (created 22:58:31Z, started 23:17:12Z, concluded 23:17:27Z).
- Verdict: `valid=false`, reasons
  `protected parent input changed: tests/test_active_mechanic_packet_registry.py`
  and `protected parent input changed: tests/test_active_packet_preflight.py`;
  baseline (merge base) `4eebbbef004107564c3ffffa6190b7d91e894fa9`,
  candidate `94841693f7a27bc69f248d03434acfcf5eadd970`.

## Why the protected edits were forced

Round 004's basis expansion made the registry revaluation mandatory: the
active-packet-registry drift gate fails closed until the registry is
revalidated against the new saturation evidence. The two frozen tests
asserted the pre-round-004 ACTIVE set and exemplar bindings, so against
the revalidated registry every variant of "revert the originals and add
successor test files" leaves the reverted assertions contradicting the
live registry. No pytest-green state exists without editing those two
files in place.

This deviates from the authorized pattern in
`docs/EVALUATOR_DEPENDENCY_PINNING.md`: the protected-input change was
not pre-declared as a migration with an authority chain; it was bundled
into the governance revaluation PR under the session's standing lane
authorization.

## Firewall evidence preserved

The rejection is preserved as evidence that the protected-input firewall
is operational. The evaluator flagged exactly the two in-place edits and
nothing else (`changed_paths` matched the protected subset of the PR
diff; `missing_paths=[]`, `unsafe_paths=[]`). The defect was in merge
ordering, not in the evaluator.

## Absorbed state

The edits are part of the protected baseline as of `5a092c08`: subsequent
candidates are diffed against their own merge base, so evaluator-integrity
returns success on later heads (verified on `f2f9beaf`, #709).

`publication` and `pytest` check-runs showing `cancelled` on intermediate
main heads during the 2026-08-14/15 merge train are concurrency
supersession (`cancel-in-progress`) on the serial runner, not failures.
Only a completed conclusion is a verdict.

## Process correction (binding)

1. A PR may be merged only when ALL check-runs on its head are
   `completed` — including deferred `workflow_run` checks.
   `trusted-parent-evaluator` fires only after the `test` workflow
   completes; on the serial runner that can lag tens of minutes behind
   the merge-ready state. "Visible checks green" is not mergeable;
   zero pending check-runs is.
2. Any PR that must edit a protected input (an existing file under
   `tests/`, or the protected workflow/source list) shall pre-declare the
   migration and its authority per `docs/EVALUATOR_DEPENDENCY_PINNING.md`,
   and shall expect and preserve the evaluator's REJECT rather than
   merge ahead of it.
3. If the evaluator rejects a protected change that was not pre-declared,
   the merge is a defect even when pytest is green. Record it here;
   never relabel the rejection.
